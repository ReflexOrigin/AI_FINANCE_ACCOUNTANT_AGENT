"""
Finance Accountant Agent - Main FastAPI Application

This module serves as the main entry point for the Finance Accountant Agent.
It initializes the FastAPI application, sets up routes, and coordinates the various
modules of the application.

The API exposes endpoints for:
- Voice-based interaction
- Authentication
- File upload for RAG ingestion
- Direct text queries
- Webhook callbacks

Dependencies:
- FastAPI for API framework
- Modules from the project for business logic
"""

import asyncio
import logging
import os
from typing import Dict, List, Optional, Union

from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

from config.settings import settings
from modules.voice_input import process_voice_input
from modules.intent_recognition import recognize_intent
from modules.operation_manager import OperationManager
from modules.file_manager import ingest_file
from modules.response_generation import generate_text_response, text_to_speech
from modules.security import authenticate_user, get_current_user

# Configure logging
logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Finance Accountant Agent API",
    description="Voice-activated AI assistant for financial operations",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize operation manager
operation_manager = OperationManager()


# Request models
class TextQueryRequest(BaseModel):
    query: str
    context: Optional[Dict] = None


class VoiceQueryResponse(BaseModel):
    text: str
    intent: str
    response_text: str
    audio_url: Optional[str] = None


# Routes
@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "online", "service": "Finance Accountant Agent"}


@app.post("/auth/token")
async def login(username: str = Form(...), password: str = Form(...)):
    """Authenticate user and return access token."""
    token = await authenticate_user(username, password)
    if not token:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    return {"access_token": token, "token_type": "bearer"}


@app.post("/voice/query", response_model=VoiceQueryResponse)
async def voice_query(
    audio_file: UploadFile = File(...), current_user=Depends(get_current_user)
):
    """Process voice query and return text response with optional audio."""
    try:
        # Process voice to text
        transcript = await process_voice_input(audio_file)

        # Recognize intent
        intent_data = await recognize_intent(transcript)

        # Route to appropriate operation
        response = await operation_manager.execute_operation(intent_data)

        # Generate response
        response_text = await generate_text_response(response)

        # Optional TTS
        audio_url = None
        if settings.ENABLE_TTS:
            audio_content = await text_to_speech(response_text)
            # TODO: Handle storing/serving audio file

        return {
            "text": transcript,
            "intent": intent_data["intent"],
            "response_text": response_text,
            "audio_url": audio_url
        }
    except Exception as e:
        logger.error(f"Error processing voice query: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/text/query")
async def text_query(
    request: TextQueryRequest, current_user=Depends(get_current_user)
):
    """Process text query and return response."""
    try:
        # Recognize intent
        intent_data = await recognize_intent(request.query, context=request.context)

        # Route to appropriate operation
        response = await operation_manager.execute_operation(intent_data)

        # Generate response
        response_text = await generate_text_response(response)

        return {"response": response_text, "intent": intent_data["intent"]}
    except Exception as e:
        logger.error(f"Error processing text query: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/files/upload")
async def upload_file(
    file: UploadFile = File(...),
    category: str = Form(...),
    current_user=Depends(get_current_user),
):
    """Upload and ingest a file into the RAG system."""
    try:
        result = await ingest_file(file, category)
        return {"message": "File successfully ingested", "details": result}
    except Exception as e:
        logger.error(f"Error ingesting file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG_MODE,
    )