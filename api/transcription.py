"""
Audio transcription service using Soniox API.
Key behaviours:
1. Speaker diarization with language-aware processing (via Soniox)
2. Timing accuracy with segment grouping
3. Robust error handling and validation
4. Post-processing for speaker consistency
"""

import logging
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
import requests
import re

from .config import SONIOX_API_KEY, SONIOX_API_BASE_URL, SONIOX_MODEL_ID

logger = logging.getLogger(__name__)


def _clean_unicode(text: str) -> str:
    """Common unicode sanitization without stripping spaces."""
    if not text:
        return ""
    try:
        # Remove replacement chars
        text = text.replace("\ufffd", "")
        # Remove zero-width / directional markers
        text = re.sub(r"[\u200b-\u200f\u202a-\u202e\u2060-\u206f\ufeff]", "", text)
        # Ensure valid UTF-8
        text = text.encode("utf-8", errors="ignore").decode("utf-8")
        # Drop any invalid codepoints
        text = "".join(char for char in text if ord(char) < 0x110000)
    except (UnicodeEncodeError, UnicodeDecodeError) as e:
        logger.warning(f"Encoding error while sanitizing text: {e}")
        try:
            text = text.encode("ascii", errors="ignore").decode("ascii")
        except Exception:
            text = ""
    return text


def sanitize_text(text: str) -> str:
    """
    Sanitize text for full transcripts (safe to trim leading/trailing spaces).
    """
    if not text:
        return ""
    return _clean_unicode(text).strip()


def sanitize_token_text(text: str) -> str:
    """
    Sanitize Soniox token text **without** stripping leading/trailing spaces.
    Token strings already encode intra-word spacing (e.g., \" மே\", \" ம\") and
    stripping would break Tamil word boundaries in the UI.
    """
    if not text:
        return ""
    return _clean_unicode(text)


def merge_consecutive_speaker_segments(segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Merge consecutive segments from the same speaker, regardless of time gap.
    
    Args:
        segments: List of speaker segments
        
    Returns:
        Merged list of segments
    """
    if not segments:
        return []
    
    merged = []
    current = segments[0].copy()
    
    for next_seg in segments[1:]:
        # If the next segment is from the same speaker, always merge it so that
        # UI display does not split continuous speaker turns into multiple rows.
        if current["speaker"] == next_seg["speaker"]:
            # Merge segments and sanitize merged text
            current["end_time"] = next_seg["end_time"]
            merged_text = current["text"].strip() + " " + next_seg["text"].strip()
            current["text"] = sanitize_text(merged_text)
        else:
            # Save current and start new
            merged.append(current)
            current = next_seg.copy()
    
    # Add last segment
    merged.append(current)
    return merged


def normalize_speaker_labels(segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Normalize speaker labels to be more readable (Speaker 1, Speaker 2, etc.)
    
    Args:
        segments: List of speaker segments
        
    Returns:
        Segments with normalized speaker labels
    """
    if not segments:
        return []
    
    # Find unique speakers in order of first appearance
    speaker_map = {}
    speaker_counter = 1
    
    for seg in segments:
        speaker_id = seg["speaker"]
        if speaker_id not in speaker_map:
            speaker_map[speaker_id] = f"Speaker {speaker_counter}"
            speaker_counter += 1
    
    # Apply mapping
    normalized = []
    for seg in segments:
        normalized_seg = seg.copy()
        normalized_seg["speaker"] = speaker_map[seg["speaker"]]
        normalized.append(normalized_seg)
    
    return normalized


async def transcribe_audio(audio_file_path: Path,
                           merge_threshold: float = 0.5,
                           normalize_speakers: bool = True) -> Dict[str, Any]:
    """
    Transcribe audio using Soniox with speaker diarization.
    
    Args:
        audio_file_path: Path to the audio file
        merge_threshold: Seconds threshold for merging consecutive segments (default 0.5)
        normalize_speakers: Whether to use readable speaker labels (default True)
        
    Returns:
        Dictionary containing:
            - transcription: Full text transcription
            - speaker_segments: List of segments with speaker, timing, and text
            - language_code: Always 'en' (English)
            - duration: Total audio duration
            - speaker_count: Number of unique speakers detected
            - metadata: Additional info including detected_language from API
        
    Raises:
        ValueError: If API key is not set or transcription fails
    """
    if not SONIOX_API_KEY:
        raise ValueError("SONIOX_API_KEY environment variable is not set")

    logger.info(f"Transcribing audio file: {audio_file_path}")

    # Validate file exists and is readable
    if not audio_file_path.exists():
        raise ValueError(f"Audio file not found: {audio_file_path}")

    file_size = audio_file_path.stat().st_size
    logger.info(f"Audio file size: {file_size / (1024*1024):.2f} MB")

    # --- Soniox async STT flow: upload file -> create transcription -> poll -> fetch tokens ---
    session = requests.Session()
    session.headers["Authorization"] = f"Bearer {SONIOX_API_KEY}"

    try:
        # 1) Upload audio file to get file_id
        logger.info("Uploading audio file to Soniox ...")
        with open(audio_file_path, "rb") as f:
            upload_res = session.post(
                f"{SONIOX_API_BASE_URL}/v1/files",
                files={"file": f},
                timeout=600,
            )
        upload_res.raise_for_status()
        upload_json = upload_res.json()
        file_id = upload_json.get("id")
        if not file_id:
            raise ValueError(f"Soniox upload did not return file id: {upload_json}")
        logger.info("Soniox file_id: %s", file_id)

        # 2) Build config for transcription
        # Configuration tuned for in‑person review calls:
        # - Strong language hints (Tamil + English) so the model does not confuse speakers
        #   when code‑switching.
        # - Speaker diarization explicitly enabled.
        config: Dict[str, Any] = {
                                    "model": SONIOX_MODEL_ID,
                                    "language_hints": ["en", "ta"],
                                    "enable_language_identification": True,
                                    "enable_speaker_diarization": True,
                                    "context": {
                                        "general": [
                                            {"key": "domain", "value": "Real estate"},
                                            {"key": "topic", "value": "Property review conversation"},
                                            {"key": "speakers", "value": "Agent and customer"},
                                            {"key": "language", "value": "Tamil with English words or completely English"}
                                        ],
                                        "text": "In-person real estate review conversation between two speakers "
                                                "(agent and customer), both in Tamil with some English words, or else completely in English. "
                                                "Clearly separate the two speakers when performing speaker diarization."
                                                "As it is a recorded call, some words can lead to mistranscription, hear the audio carefully and provide the accurate transcription."
                                    },
                                    "client_reference_id": str(audio_file_path.name),
                                    "file_id": file_id,
                                }

        logger.info("Creating Soniox transcription with config: %s", config)
        create_res = session.post(
            f"{SONIOX_API_BASE_URL}/v1/transcriptions",
            json=config,
            timeout=600,
        )
        create_res.raise_for_status()
        create_json = create_res.json()
        transcription_id = create_json.get("id")
        if not transcription_id:
            raise ValueError(f"Soniox create_transcription did not return id: {create_json}")
        logger.info("Soniox transcription_id: %s", transcription_id)

        # 3) Poll until transcription is completed
        logger.info("Waiting for Soniox transcription to complete ...")
        while True:
            status_res = session.get(
                f"{SONIOX_API_BASE_URL}/v1/transcriptions/{transcription_id}",
                timeout=60,
            )
            status_res.raise_for_status()
            status_json = status_res.json()
            status = status_json.get("status")
            if status == "completed":
                break
            if status == "error":
                raise ValueError(
                    f"Soniox transcription error: {status_json.get('error_message', 'Unknown error')}"
                )
            time.sleep(1)

        # 4) Fetch final transcript tokens
        logger.info("Fetching Soniox transcript tokens ...")
        transcript_res = session.get(
            f"{SONIOX_API_BASE_URL}/v1/transcriptions/{transcription_id}/transcript",
            timeout=600,
        )
        transcript_res.raise_for_status()
        transcript_json = transcript_res.json()
        logger.info("Soniox transcript response: %s", transcript_json)
        tokens: List[Dict[str, Any]] = transcript_json.get("tokens") or []
        if not tokens:
            raise ValueError("Soniox transcript response did not contain any tokens")

        logger.info("Received %d tokens from Soniox", len(tokens))

        # 5) Build full transcript text.
        # Prefer Soniox top-level "text" (already properly spaced), fall back to tokens.
        full_transcript = sanitize_text(
            transcript_json.get("text", "")
            or "".join(
                sanitize_token_text(tok.get("text", "")) for tok in tokens if tok.get("text")
            )
        )

        # 6) Build speaker segments from tokens with timing
        segments: List[Dict[str, Any]] = []
        current_seg: Optional[Dict[str, Any]] = None

        for tok in tokens:
            text = sanitize_token_text(tok.get("text", ""))
            if not text:
                continue

            speaker = tok.get("speaker", "UNKNOWN")

            # Soniox tokens may expose timing as seconds (start_time/end_time)
            # or milliseconds (start_ms/end_ms). Prefer seconds; fall back to ms/1000.
            raw_start = tok.get("start_time")
            if raw_start is None:
                raw_start = tok.get("start_ms")
                start = float(raw_start) / 1000.0 if raw_start is not None else 0.0
            else:
                start = float(raw_start)

            raw_end = tok.get("end_time")
            if raw_end is None:
                raw_end = tok.get("end_ms")
                end = float(raw_end) / 1000.0 if raw_end is not None else start
            else:
                end = float(raw_end)

            # Start new segment if speaker changes or gap is large
            if (
                current_seg is None
                or current_seg["speaker"] != speaker
                or start - current_seg["end_time"] > merge_threshold
            ):
                if current_seg is not None:
                    segments.append(current_seg)
                current_seg = {
                    "speaker": speaker,
                    "start_time": start / 1000.0 if start > 1000 else start,
                    "end_time": end / 1000.0 if end > 1000 else end,
                    "text": text,
                }
            else:
                # Append token text directly; Soniox tokens already encode spacing.
                current_seg["end_time"] = end / 1000.0 if end > 1000 else end
                current_seg["text"] += text

        if current_seg is not None:
            segments.append(current_seg)

        logger.info("Initial segments built from tokens: %d", len(segments))

        # Convert segments to structured format
        speaker_segments = []
        total_duration = 0.0
        
        for idx, segment in enumerate(segments):
            # Try multiple possible field names for speaker
            speaker_id = (
                segment.get("speaker") or 
                segment.get("speaker_id") or 
                segment.get("speaker_label") or 
                f"SPEAKER_UNKNOWN_{idx}"
            )
            
            # Get timing info with validation.
            # Earlier we stored timings under "start_time"/"end_time" when building
            # segments from tokens, so prefer those keys and fall back to "start"/"end"
            # if present (for future compatibility).
            start_time = float(
                segment.get("start_time", segment.get("start", 0.0))
            )
            end_time = float(
                segment.get("end_time", segment.get("end", 0.0))
            )
            # Sanitize segment text to handle encoding issues, especially for multilingual content
            segment_text = sanitize_text(segment.get("text", ""))
            
            # Skip empty segments
            if not segment_text:
                continue
            
            # Validate timing
            if end_time < start_time:
                logger.warning(f"Invalid timing in segment {idx}: end < start")
                end_time = start_time + 1.0  # Fallback
            
            speaker_segments.append({
                "speaker": speaker_id,
                "start_time": round(start_time, 2),
                "end_time": round(end_time, 2),
                "duration": round(end_time - start_time, 2),
                "text": segment_text
            })
            
            # Track maximum end time for total duration
            if end_time > total_duration:
                total_duration = end_time
        
        logger.info(f"Processed {len(speaker_segments)} valid segments")
        
        # Get unique speakers before processing
        unique_speakers_raw = set(seg["speaker"] for seg in speaker_segments)
        logger.info(f"Detected {len(unique_speakers_raw)} unique speakers")
        
        # Post-processing: Merge consecutive segments from same speaker (regardless of gap)
        before_merge = len(speaker_segments)
        speaker_segments = merge_consecutive_speaker_segments(speaker_segments)
        logger.info(f"Merged segments: {before_merge} → {len(speaker_segments)}")
        
        # Normalize speaker labels for readability
        if normalize_speakers:
            speaker_segments = normalize_speaker_labels(speaker_segments)
            logger.info("Applied normalized speaker labels")
        
        # Final statistics
        unique_speakers = set(seg["speaker"] for seg in speaker_segments)
        speaker_count = len(unique_speakers)
        
        logger.info(f"Final: {speaker_count} speakers, {len(speaker_segments)} segments")
        logger.info(f"Total duration: {total_duration:.2f}s ({total_duration/60:.1f}min)")
        
        # Log speaker statistics
        for speaker in sorted(unique_speakers):
            speaker_segs = [s for s in speaker_segments if s["speaker"] == speaker]
            total_time = sum(s["duration"] for s in speaker_segs)
            logger.info(f"  {speaker}: {len(speaker_segs)} segments, {total_time:.1f}s")
        
        # Always use 'en' as language_code (English)
        # Store detected language in metadata for reference
        
        return {
            "transcription": full_transcript,
            "speaker_segments": speaker_segments,
            "duration": round(total_duration, 2),
            "speaker_count": speaker_count,
            "metadata": {
                "file_name": audio_file_path.name,
                "file_size_mb": round(file_size / (1024*1024), 2),
                "speakers": sorted(list(unique_speakers)),
            }
        }
        
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error from Soniox API: {e}")
        error_msg = str(e)
        if e.response is not None:
            try:
                error_detail = e.response.json()
                error_msg = f"API Error: {error_detail.get('message', e.response.text)}"
            except:
                error_msg = f"API Error: {e.response.text[:500]}"
        raise ValueError(f"Transcription API error: {error_msg}")
        
    except requests.exceptions.Timeout:
        logger.error("Request to Soniox API timed out")
        raise ValueError("Transcription request timed out. File may be too large.")
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error calling Soniox API: {str(e)}")
        raise ValueError(f"Network error during transcription: {str(e)}")
        
    except Exception as e:
        logger.error(f"Unexpected error during transcription: {str(e)}", exc_info=True)
        raise ValueError(f"Transcription failed: {str(e)}")


def format_transcript_for_display(result: Dict[str, Any], 
                                  time_format: str = "seconds") -> str:
    """
    Format transcription result for readable display.
    
    Args:
        result: Transcription result from transcribe_audio()
        time_format: "seconds" or "minutes" (default: "seconds")
        
    Returns:
        Formatted string with speaker-wise transcript
    """
    lines = []
    lines.append("=" * 70)
    lines.append("TRANSCRIPTION RESULT")
    lines.append("=" * 70)
    
    # Add metadata
    metadata = result.get("metadata", {})
    if metadata:
        lines.append(f"\nFile: {metadata.get('file_name', 'Unknown')}")
        lines.append(f"Size: {metadata.get('file_size_mb', 0):.2f} MB")
    
    lines.append(f"Duration: {result['duration']:.2f}s ({result['duration']/60:.1f}min)")
    lines.append(f"Speakers: {result['speaker_count']}")
    lines.append("\n" + "=" * 70)
    lines.append("SPEAKER-WISE TRANSCRIPT")
    lines.append("=" * 70 + "\n")
    
    # Format each segment
    for seg in result["speaker_segments"]:
        if time_format == "minutes":
            start_min = int(seg["start_time"] // 60)
            start_sec = seg["start_time"] % 60
            end_min = int(seg["end_time"] // 60)
            end_sec = seg["end_time"] % 60
            time_str = f"[{start_min:02d}:{start_sec:05.2f} - {end_min:02d}:{end_sec:05.2f}]"
        else:
            time_str = f"[{seg['start_time']:.2f}s - {seg['end_time']:.2f}s]"
        
        lines.append(f"{seg['speaker']} {time_str}")
        lines.append(f"  {seg['text']}")
        lines.append("")
    
    return "\n".join(lines)