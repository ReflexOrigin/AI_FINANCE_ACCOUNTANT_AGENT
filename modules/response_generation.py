"""
Response Generation Module for Finance Accountant Agent

This module handles the generation of text responses and optionally converts
them to speech using TTS engines.

Features:
- Text response formatting for finance operations
- TTS using Mozilla TTS or pyttsx3
- Response templating based on operation context
- Financial data visualization suggestions
- Citation of sources from RAG retrieval
- Voice style customization

Dependencies:
- rag_module: For context information from retrieved documents
- llm_module: For response generation using LLM
- Optional TTS engines: Mozilla TTS or pyttsx3
"""

import asyncio
import io
import json
import logging
import os
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Union

from config.settings import settings

logger = logging.getLogger(__name__)


async def generate_text_response(operation_result: Dict) -> str:
    if "error" in operation_result:
        return f"I'm sorry, but I encountered an error: {operation_result['error']}"
    if "formatted_response" in operation_result:
        return operation_result["formatted_response"]
    if "result" in operation_result and isinstance(operation_result["result"], str):
        return operation_result["result"]

    operation_info = ""
    if "_metadata" in operation_result:
        metadata = operation_result["_metadata"]
        operation = metadata.get("operation", "unknown")
        operation_info = f" for {operation}"

    if "data" in operation_result and isinstance(operation_result["data"], dict):
        return format_data_response(operation_result["data"], operation_info)

    return json.dumps(operation_result, indent=2)


def format_data_response(data: Dict, operation_info: str) -> str:
    if "message" in data:
        return data["message"]

    lines = [f"Here's the information{operation_info}:"]
    for key, value in data.items():
        if key.startswith("_"):
            continue
        readable_key = key.replace("_", " ").title()

        if isinstance(value, dict):
            lines.append(f"\n{readable_key}:")
            for subkey, subvalue in value.items():
                sub_readable = subkey.replace("_", " ").title()
                lines.append(f" - {sub_readable}: {subvalue}")
        elif isinstance(value, list):
            lines.append(f"\n{readable_key}:")
            for item in value:
                if isinstance(item, dict):
                    lines.append(" -")
                    for item_key, item_value in item.items():
                        item_readable = item_key.replace("_", " ").title()
                        lines.append(f"   {item_readable}: {item_value}")
                else:
                    lines.append(f" - {item}")
        else:
            lines.append(f"\n{readable_key}: {value}")
    return "\n".join(lines)


async def text_to_speech(text: str) -> bytes:
    if not settings.ENABLE_TTS:
        raise Exception("TTS is disabled in configuration")

    try:
        if settings.TTS_ENGINE.lower() == "mozilla":
            return await mozilla_tts(text)
        elif settings.TTS_ENGINE.lower() == "pyttsx3":
            return await pyttsx3_tts(text)
        else:
            raise ValueError(f"Unsupported TTS engine: {settings.TTS_ENGINE}")
    except Exception as e:
        logger.error(f"Error in TTS conversion: {str(e)}")
        raise


async def mozilla_tts(text: str) -> bytes:
    try:
        from TTS.utils.manage import ModelManager
        from TTS.utils.synthesizer import Synthesizer

        manager = ModelManager()
        model_path, config_path, model_item = manager.download_model("tts_models/en/ljspeech/tacotron2-DDC")
        vocoder_path, vocoder_config_path, _ = manager.download_model("vocoder_models/en/ljspeech/multiband-melgan")

        synthesizer = Synthesizer(
            model_path, config_path,
            vocoder_path=vocoder_path,
            vocoder_config_path=vocoder_config_path
        )

        loop = asyncio.get_event_loop()
        wavs = await loop.run_in_executor(None, lambda: synthesizer.tts(text))

        with io.BytesIO() as buffer:
            synthesizer.save_wav(wavs, buffer)
            return buffer.getvalue()

    except Exception as e:
        logger.error(f"Error in Mozilla TTS: {str(e)}")
        raise


async def pyttsx3_tts(text: str) -> bytes:
    try:
        import pyttsx3

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            temp_path = temp_file.name

        try:
            loop = asyncio.get_event_loop()

            def _tts_task():
                engine = pyttsx3.init()
                if settings.TTS_VOICE_ID:
                    engine.setProperty("voice", settings.TTS_VOICE_ID)
                engine.setProperty("rate", settings.TTS_SPEECH_RATE * 200)
                engine.save_to_file(text, temp_path)
                engine.runAndWait()

            await loop.run_in_executor(None, _tts_task)

            with open(temp_path, "rb") as audio_file:
                audio_content = audio_file.read()

            return audio_content

        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    except Exception as e:
        logger.error(f"Error in pyttsx3 TTS: {str(e)}")
        raise
