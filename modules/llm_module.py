"""
LLM Module for Finance Accountant Agent

This module handles the loading and inference of open-source Large Language Models
from Hugging Face's Transformers library. It supports quantized models for
efficient inference on consumer hardware.

Features:
- Model loading with quantization options (4-bit, 8-bit)
- Async inference with timeout handling
- Graceful fallback for complex queries
- Caching for performance
- Streaming response capability

Dependencies:
- transformers: Hugging Face's transformers library
- torch: PyTorch for model inference
- accelerate: For optimized inference
- bitsandbytes: For quantization support
"""

import asyncio
import functools
import logging
import time
from typing import Dict, List, Optional, Union

import torch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    StoppingCriteria,
    StoppingCriteriaList,
    TextIteratorStreamer,
)

from config.settings import settings

logger = logging.getLogger(__name__)

# Global model and tokenizer instances
_model = None
_tokenizer = None


class LLMTimeoutError(Exception):
    """Exception raised when LLM inference times out."""
    pass


class FinanceStoppingCriteria(StoppingCriteria):
    """Custom stopping criteria for financial text generation."""

    def __init__(self, stop_strings: List[str], tokenizer):
        self.stop_strings = stop_strings
        self.tokenizer = tokenizer

    def __call__(self, input_ids, scores, **kwargs):
        # Check if any of the stop strings appear in the generated text
        generated_text = self.tokenizer.decode(input_ids[0])
        for stop_string in self.stop_strings:
            if stop_string in generated_text:
                return True
        return False


async def load_model():
    """
    Load the LLM model and tokenizer asynchronously.

    Returns:
        tuple: (model, tokenizer)
    """
    global _model, _tokenizer

    if _model is None or _tokenizer is None:
        logger.info(f"Loading LLM model: {settings.LLM_MODEL_NAME}")

        # Configure quantization
        quantization_config = None
        if settings.LLM_QUANTIZATION == "4bit":
            quantization_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_use_double_quant=True,
            )
        elif settings.LLM_QUANTIZATION == "8bit":
            quantization_config = BitsAndBytesConfig(load_in_8bit=True)

        loop = asyncio.get_event_loop()

        # Load tokenizer
        _tokenizer = await loop.run_in_executor(
            None, lambda: AutoTokenizer.from_pretrained(settings.LLM_MODEL_NAME)
        )

        # Load model with quantization if specified
        _model = await loop.run_in_executor(
            None,
            lambda: AutoModelForCausalLM.from_pretrained(
                settings.LLM_MODEL_NAME,
                quantization_config=quantization_config,
                device_map="auto",
                torch_dtype=torch.float16,
                trust_remote_code=True,
            ),
        )

        logger.info("LLM model loaded successfully")

    return _model, _tokenizer


async def generate_text(
    prompt: str,
    system_prompt: Optional[str] = None,
    max_new_tokens: Optional[int] = None,
    temperature: float = 0.7,
    top_p: float = 0.9,
    stop_strings: Optional[List[str]] = None,
    stream: bool = False,
) -> Union[str, asyncio.StreamReader]:
    """
    Generate text using the loaded LLM.

    Args:
        prompt: The user prompt
        system_prompt: Optional system prompt for instruction-tuned models
        max_new_tokens: Maximum number of tokens to generate
        temperature: Sampling temperature
        top_p: Nucleus sampling parameter
        stop_strings: List of strings that should trigger stopping
        stream: Whether to stream the response

    Returns:
        Generated text or a stream of text chunks

    Raises:
        LLMTimeoutError: If inference times out
    """
    model, tokenizer = await load_model()

    # Prepare the input prompt
    if system_prompt:
        input_text = f"<s>[INST] {system_prompt}\n\n{prompt} [/INST]"
    else:
        input_text = prompt

    # Tokenize input
    inputs = tokenizer(input_text, return_tensors="pt").to(model.device)

    # Configure generation parameters
    gen_kwargs = {
        "input_ids": inputs.input_ids,
        "max_new_tokens": max_new_tokens or settings.LLM_MAX_NEW_TOKENS,
        "temperature": temperature,
        "top_p": top_p,
        "do_sample": temperature > 0,
    }

    # Add stopping criteria if specified
    if stop_strings:
        stopping_criteria = FinanceStoppingCriteria(stop_strings, tokenizer)
        gen_kwargs["stopping_criteria"] = StoppingCriteriaList([stopping_criteria])

    try:
        loop = asyncio.get_event_loop()

        if stream:
            # Streaming setup
            streamer = TextIteratorStreamer(tokenizer, skip_prompt=True)
            gen_kwargs["streamer"] = streamer

            # Create a stream reader/writer
            stream_reader = asyncio.StreamReader()
            stream_writer = asyncio.StreamReaderProtocol(stream_reader)
            await loop.connect_read_pipe(lambda: stream_writer, asyncio.subprocess.PIPE)

            # Kick off generation in executor
            loop.run_in_executor(None, functools.partial(model.generate, **gen_kwargs))

            # Feed tokens into the reader
            for chunk in streamer:
                stream_reader.feed_data(chunk.encode())
            stream_reader.feed_eof()
            return stream_reader

        else:
            # Synchronous generation with timeout
            output_ids = await asyncio.wait_for(
                loop.run_in_executor(None, lambda: model.generate(**gen_kwargs)),
                timeout=settings.LLM_TIMEOUT_SECONDS,
            )

            # Skip the prompt tokens
            prompt_length = inputs.input_ids.shape[1]
            generated_ids = output_ids[0][prompt_length:]
            generated_text = tokenizer.decode(generated_ids, skip_special_tokens=True)
            return generated_text.strip()

    except asyncio.TimeoutError:
        logger.warning(f"LLM inference timed out after {settings.LLM_TIMEOUT_SECONDS}s")
        if settings.LLM_FALLBACK_ENABLED:
            return settings.LLM_FALLBACK_TEXT
        raise LLMTimeoutError(f"Inference timed out after {settings.LLM_TIMEOUT_SECONDS} seconds")

    except Exception as e:
        logger.error(f"Error during LLM inference: {str(e)}")
        if settings.LLM_FALLBACK_ENABLED:
            return settings.LLM_FALLBACK_TEXT
        raise
