"""
Voice Input Module for Finance Accountant Agent

This module handles the speech-to-text conversion using OpenAI's Whisper model.
It processes audio files and returns transcribed text.

Features:
- Audio file processing (multiple formats)
- Whisper model loading with appropriate size selection
- Language detection or specification
- Async processing with timeout handling

Dependencies:
- whisper: OpenAI's speech recognition model
- ffmpeg: For audio processing
- torch: PyTorch for model inference
"""

import asyncio
import io
import logging
import os
import tempfile
from pathlib import Path
from typing import Optional, Union

import torch
import whisper
from fastapi import UploadFile

from config.settings import settings

logger = logging.getLogger(__name__)

# Global model instance for reuse
_whisper_model = None


async def load_whisper_model():
    """
    Load the Whisper STT model asynchronously.

    Returns:
        A loaded Whisper model instance
    """
    global _whisper_model

    if _whisper_model is None:
        # Load in a separate thread to avoid blocking
        loop = asyncio.get_event_loop()
        _whisper_model = await loop.run_in_executor(
            None, lambda: whisper.load_model(settings.STT_MODEL_SIZE)
        )
        logger.info(f"Loaded Whisper model: {settings.STT_MODEL_SIZE}")

    return _whisper_model


async def process_audio_file(file_path: Union[str, Path]) -> str:
    """
    Process an audio file and return the transcribed text.

    Args:
        file_path: Path to the audio file

    Returns:
        Transcribed text from the audio
    """
    model = await load_whisper_model()

    # Process in a separate thread to avoid blocking
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None,
        lambda: model.transcribe(
            str(file_path),
            language=settings.STT_LANGUAGE,
            fp16=torch.cuda.is_available(),
        ),
    )

    return result["text"].strip()


async def process_voice_input(audio_file: UploadFile) -> str:
    """
    Process uploaded audio file and return transcribed text.

    Args:
        audio_file: UploadFile object containing audio data

    Returns:
        Transcribed text from the audio

    Raises:
        Exception: If audio processing fails
    """
    try:
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            # Write the uploaded file content to the temp file
            content = await audio_file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name

        try:
            # Process the audio file
            transcript = await process_audio_file(temp_file_path)
            logger.info(f"Transcribed audio: {transcript[:50]}...")
            return transcript
        finally:
            # Clean up the temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

    except Exception as e:
        logger.error(f"Error processing voice input: {str(e)}")
        raise Exception(f"Failed to process audio: {str(e)}")
