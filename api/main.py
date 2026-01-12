"""
FastAPI application main file.
"""

import logging
from pathlib import Path
from typing import Dict, Any

from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError

from .schemas import TranscriptionResponse
from .transcription import transcribe_audio
from .scoring import score_transcript
from .reporting import generate_report

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Audio Transcription and Review API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors with better logging."""
    logger.error(f"Request validation error: {exc.errors()}")
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc), "errors": exc.errors()}
    )


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Audio Transcription and Review API",
        "version": "1.0.0",
        "endpoints": {
            "transcribe": "/transcribe-audio",
            "score": "/score-transcript",
            "report": "/generate-report"
        }
    }


@app.post("/transcribe-audio")
async def transcribe_audio_endpoint(file: UploadFile = File(...)):
    """
    Transcribe audio file endpoint.
    
    Accepts an audio file and returns transcription with speaker-wise segments and timing.
    """
    # Handle case where filename might be None
    import uuid
    filename = file.filename or f"audio_{uuid.uuid4().hex[:8]}"
    logger.info(f"Received transcription request for file: {filename}")
    logger.info(f"Content type: {file.content_type}")
    
    # Create temporary directory for uploaded files
    tmp_dir = Path(".tmp_audio")
    tmp_dir.mkdir(parents=True, exist_ok=True)
    
    # Save uploaded file temporarily - ensure safe filename
    audio_path = tmp_dir / filename
    
    try:
        # Save uploaded file
        with open(audio_path, "wb") as f:
            content = await file.read()
            if not content:
                logger.error("Uploaded file is empty")
                raise HTTPException(status_code=400, detail="Uploaded file is empty")
            f.write(content)
        
        logger.info(f"Saved uploaded file to: {audio_path} (size: {len(content)} bytes)")
        
        # Transcribe audio
        transcription_result = await transcribe_audio(audio_path)
        
        logger.info(f"Transcription completed for {filename}")
        logger.info(f"Found {len(transcription_result.get('speaker_segments', []))} speaker segments")
        
        # Return transcription response
        return JSONResponse(content=transcription_result)
        
    except ValueError as e:
        logger.error(f"Transcription error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing audio file {file.filename}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing audio file: {str(e)}"
        )
    finally:
        # Clean up temporary file
        try:
            if audio_path.exists():
                audio_path.unlink()
                logger.info(f"Cleaned up temporary file: {audio_path}")
        except Exception as e:
            logger.warning(f"Could not clean up temporary file: {e}")


@app.post("/score-transcript")
async def score_transcript_endpoint(transcript_data: Dict[str, Any]):
    """
    Score transcript endpoint using OpenAI.
    
    Supports both V1 (binary yes/no/na) and V2 (granular 0-max scoring).
    
    Expected input:
    {
        "transcription": "Full transcript text...",
        "speaker_segments": [...] (optional),
        "version": "v1" or "v2" (optional, defaults to "v1")
    }
    """
    version = transcript_data.get("version", "v2").lower()
    logger.info(f"Received score transcript request (version: {version})")
    
    try:
        if version == "v2":
            # Use V2 scoring system
            from .scoring_v2 import score_transcript_main
            score_result = score_transcript_main(transcript_data)
        else:
            # Use V1 scoring system (default)
            score_result = score_transcript(transcript_data)
        
        return JSONResponse(content=score_result)
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error scoring transcript: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error scoring transcript: {str(e)}"
        )


@app.post("/generate-report")
async def generate_report_endpoint(
    transcript_data: Dict[str, Any],
    score_data: Dict[str, Any]
):
    """
    Generate report endpoint (dummy - to be implemented later).
    
    Accepts transcript and score data and returns a report.
    """
    logger.info("Received generate report request")
    
    try:
        report_result = generate_report(transcript_data, score_data)
        return JSONResponse(content=report_result)
    except Exception as e:
        logger.error(f"Error generating report: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error generating report: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
