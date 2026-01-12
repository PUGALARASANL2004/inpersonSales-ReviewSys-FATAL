"""
Report generation service.

This module generates a high‑level qualitative report from:
- the full transcript (with optional speaker segments)
- the detailed scoring output from `scoring.score_transcript`.

The report focuses on:
- overall summary of the call
- agent summary (well‑performed areas & areas of improvement)
- client summary.
"""

import logging
from typing import Dict, Any

from openai import OpenAI

from .config import OPENAI_API_KEY, OPENAI_MODEL, AZURE_ENDPOINT

logger = logging.getLogger(__name__)


def _build_report_prompt(transcript_data: Dict[str, Any], score_data: Dict[str, Any]) -> str:
    """Create a prompt for OpenAI to generate structured call summaries."""
    transcript = transcript_data.get("transcription", "").strip()
    speaker_segments = transcript_data.get("speaker_segments", [])

    criteria_scores = score_data.get("criteria_scores", [])

    # Compact view of scores to keep prompt smaller but informative
    scores_text_lines = []
    for c in criteria_scores:
        scores_text_lines.append(
            f"- {c.get('name', c.get('id'))} (ID: {c.get('id')}): "
            f"Response={c.get('response')}, "
            f"Points={c.get('points_awarded')}/{c.get('max_points')}"
        )
    scores_text = "\n".join(scores_text_lines)

    # Speaker segments text (optional, helps distinguish agent vs client)
    segments_lines = []
    for seg in speaker_segments[:200]:  # safety cap
        speaker = seg.get("speaker", "Unknown")
        start = seg.get("start_time", 0.0)
        end = seg.get("end_time", start)
        text = str(seg.get("text", "")).strip()
        segments_lines.append(
            f"- {speaker} [{start:.1f}s - {end:.1f}s]: {text}"
        )
    segments_text = "\n".join(segments_lines) if segments_lines else "Not available"

    prompt = f"""
You are an expert QA coach for pre‑sales real estate calls.
You will receive:
- The full call transcript.
- Optional speaker segments (who spoke when and what).
- A structured scoring output across multiple quality parameters.

Based on this, generate THREE concise but information‑rich summaries:
1) overall_summary: Overall narrative of the call, including call purpose, flow, and outcome.
2) agent_summary:
   - well_performed: 3–6 short bullet points describing what the AGENT did well, grounded in the scores and transcript.
   - areas_of_improvement: 3–6 short bullet points describing what the AGENT should improve.
3) client_summary: Short summary (2–5 sentences) about the CLIENT’s behaviour, interest level, objections and final stance.

IMPORTANT GUIDELINES:
- Use simple, direct language that can be shown as‑is in a UI.
- Refer to the agent as "agent" or "associate" and to the other party as "customer" or "client".
- Use the scoring to guide emphasis (high‑scoring areas → strengths, low‑scoring areas → improvements) but always ground statements in the transcript behaviour.
- Do NOT quote excessively; paraphrase where possible.
- Keep each bullet point or sentence focused on a single clear idea.
- You may highlight only the MOST IMPORTANT words or short phrases by wrapping them in Markdown-style bold markers, e.g. **strong rapport building**, **project knowledge inaccurate**, **customer clearly disinterested**. Do not overuse bold; reserve it for the truly key ideas.

RETURN FORMAT (STRICT):
Return ONLY a single JSON object with this exact shape:
{{
  "overall_summary": "string",
  "agent_summary": {{
    "well_performed": ["string", "string", "..."],
    "areas_of_improvement": ["string", "string", "..."]
  }},
  "client_summary": "string"
}}

=== SCORING DATA (for context) ===
Total Score: {score_data.get('total_score')}/{score_data.get('total_points')} ({score_data.get('percentage')}%)
Criteria:
{scores_text}

=== SPEAKER SEGMENTS (optional) ===
{segments_text}

=== FULL TRANSCRIPT ===
{transcript}
"""
    return prompt


def generate_report(transcript_data: Dict[str, Any], score_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate a qualitative report from transcript and score data.

    Args:
        transcript_data: Dictionary containing transcription data
            Expected keys:
                - transcription: Full transcript text
                - speaker_segments: List of speaker segments with timing
        score_data: Dictionary from `score_transcript` with scoring data

    Returns:
        Dictionary with report:
        {
          "summaries": {
             "overall_summary": "...",
             "agent_summary": {
                 "well_performed": [...],
                 "areas_of_improvement": [...]
             },
             "client_summary": "..."
          },
          // basic flags kept for backward‑compatibility
          "transcript_available": bool,
          "score_available": bool
        }
    """
    logger.info("Generating report from transcript and scores")

    if not OPENAI_API_KEY:
        raise ValueError("AZURE_KEY or OPENAI_API_KEY environment variable is not set")

    transcript = transcript_data.get("transcription", "")
    if not transcript or not transcript.strip():
        raise ValueError("Transcript is empty or missing for report generation")

    if not score_data:
        raise ValueError("Score data is required for report generation")

    # Use Azure OpenAI endpoint if configured
    client = OpenAI(
        api_key=OPENAI_API_KEY,
        base_url=AZURE_ENDPOINT
    )

    prompt = _build_report_prompt(transcript_data, score_data)

    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert QA coach generating concise, structured summaries "
                        "for a call review dashboard. Respond ONLY with a single JSON object "
                        "matching the specified schema."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content

        import json

        summaries = json.loads(content or "{}")

        # Minimal sanity fallback to avoid crashing UI
        if not isinstance(summaries, dict):
            raise ValueError("Report JSON is not an object")

        logger.info("Report generation completed successfully")

        return {
            "summaries": summaries,
            "transcript_available": bool(transcript_data.get("transcription")),
            "score_available": bool(score_data),
        }

    except Exception as e:
        logger.error(f"Error generating report with OpenAI: {e}")
        # Fail gracefully but keep compatibility fields
        return {
            "summaries": {
                "overall_summary": "Report generation failed.",
                "agent_summary": {
                    "well_performed": [],
                    "areas_of_improvement": [],
                },
                "client_summary": "Could not generate client summary due to an internal error.",
            },
            "transcript_available": bool(transcript_data.get("transcription")),
            "score_available": bool(score_data),
            "error": str(e),
        }
