"""
LLM Module for Finance Accountant Agent

This module handles inference via the Hugging Face Inference API (or a local fallback),
with support for quantized models and timeout handling.

Features:
- Hosted HF Inference API client
- Local quantized model loading (4bit, 8bit, or none)
- Attention mask & pad token handling
- Async inference with timeout and fallback
- Custom stopping criteria support
"""

import httpx
import asyncio
import logging
from typing import List, Optional, Union

import torch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    StoppingCriteria,
    StoppingCriteriaList,
)
from huggingface_hub import InferenceClient

from config.settings import settings

logger = logging.getLogger(__name__)

# Globals
_model = None
_tokenizer = None
_inference_client: Optional[InferenceClient] = None

class LLMTimeoutError(Exception):
    """Raised when inference times out."""
    pass

class FinanceStoppingCriteria(StoppingCriteria):
    """Stop generation on specified tokens."""
    def __init__(self, stop_strings: List[str], tokenizer):
        self.stop_strings = stop_strings
        self.tokenizer = tokenizer
       
    def __call__(self, input_ids, scores, **kwargs):
        text = self.tokenizer.decode(input_ids[0])
        return any(s in text for s in self.stop_strings)


async def _call_deepinfra_api(prompt: str, max_tokens: int, temperature: float, top_p: float, stop: Optional[List[str]] = None) -> str:
    headers = {
        "Authorization": f"Bearer {settings.DEEPINFRA_API_KEY}",
        "Content-Type": "application/json"
    }
    body = {
        "model": settings.LLM_MODEL_NAME,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": temperature,
        "top_p": top_p,
    }
    if stop:
        body["stop"] = stop

    try:
        async with httpx.AsyncClient(timeout=settings.LLM_TIMEOUT_SECONDS) as client:
            response = await client.post("https://api.deepinfra.com/v1/openai/chat/completions", headers=headers, json=body)
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"]
    except Exception as e:
        logger.error(f"DeepInfra API error: {e}")
        if settings.LLM_FALLBACK_ENABLED:
            return settings.LLM_FALLBACK_TEXT
        raise LLMTimeoutError(str(e))


async def _get_inference_client() -> InferenceClient:
    global _inference_client
    if _inference_client is None:
        logger.info(f"Initializing HF InferenceClient for {settings.LLM_MODEL_NAME}")
        _inference_client = InferenceClient(
            model=settings.LLM_MODEL_NAME,
            token=settings.HF_HUB_TOKEN,
            timeout=settings.LLM_TIMEOUT_SECONDS,
        )
    return _inference_client

async def load_local_model():
    """Load and cache a local quantized model and tokenizer."""
    global _model, _tokenizer
    if _model is None or _tokenizer is None:
        _tokenizer = AutoTokenizer.from_pretrained(settings.LLM_MODEL_NAME)
        if _tokenizer.pad_token_id is None:
            _tokenizer.add_special_tokens({'pad_token': _tokenizer.eos_token})
       
        qconf = None
        if settings.LLM_QUANTIZATION == '4bit':
            qconf = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_quant_type='nf4',
                bnb_4bit_use_double_quant=True,
            )
        elif settings.LLM_QUANTIZATION == '8bit':
            qconf = BitsAndBytesConfig(load_in_8bit=True)
       
        _model = AutoModelForCausalLM.from_pretrained(
            settings.LLM_MODEL_NAME,
            quantization_config=qconf,
            device_map='auto',
            torch_dtype=torch.float16,
            trust_remote_code=True,
        )
       
        _model.resize_token_embeddings(len(_tokenizer))
        logger.info("Loaded local LLM model.")

async def generate_text(
    prompt: str,
    system_prompt: Optional[str] = None,
    max_new_tokens: Optional[int] = None,
    temperature: float = 0.7,
    top_p: float = 0.9,
    stop_strings: Optional[List[str]] = None,
    stream: bool = False,
) -> Union[str, asyncio.StreamReader]:
    """Generate text via HF Inference API or local fallback."""
    full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
   
    # Log the formatted prompt for debugging
    logger.debug(f"Full prompt to LLM: {full_prompt[:200]}...")
    
    # Log the stop strings
    if stop_strings:
        logger.debug(f"Using stop strings: {stop_strings}")
    
    if settings.USE_DEEPINFRA_API:
        try:
            return await _call_deepinfra_api(
                prompt=full_prompt,
                max_tokens=max_new_tokens or settings.LLM_MAX_NEW_TOKENS,
                temperature=temperature,
                top_p=top_p,
                stop=stop_strings,
            )
        except Exception as e:
            logger.error(f"DeepInfra call failed: {e}")
            if settings.LLM_FALLBACK_ENABLED:
                return settings.LLM_FALLBACK_TEXT
            raise LLMTimeoutError(str(e))

    # Hosted API path
    if settings.USE_HF_INFERENCE_API:
        client = await _get_inference_client()
        try:
            # Properly pass the stop_strings to the Inference API
            result = await asyncio.to_thread(
                client.text_generation,
                prompt=full_prompt,
                max_new_tokens=max_new_tokens or settings.LLM_MAX_NEW_TOKENS,
                temperature=temperature,
                top_p=top_p,
                stop=stop_strings,  # Ensure stop_strings are passed correctly
                stream=stream,
            )
           
            logger.debug(f"HF API raw output: {result!r}")
           
            if isinstance(result, list):
                return result[0].get('generated_text', '')
            return result
       
        except Exception as e:
            logger.error(f"Inference API error: {e}")
            if settings.LLM_FALLBACK_ENABLED:
                return settings.LLM_FALLBACK_TEXT
            raise LLMTimeoutError(str(e))
   
    # Local fallback
    await load_local_model()
   
    model, tokenizer = _model, _tokenizer
   
    inputs = tokenizer(
        full_prompt,
        return_tensors='pt',
        padding='max_length',
        truncation=True,
        max_length=model.config.max_position_embeddings,
    ).to(model.device)
   
    gen_kwargs = {
        'input_ids': inputs.input_ids,
        'attention_mask': inputs.attention_mask,
        'pad_token_id': tokenizer.pad_token_id,
        'max_new_tokens': max_new_tokens or settings.LLM_MAX_NEW_TOKENS,
        'temperature': temperature,
        'top_p': top_p,
    }
   
    # Ensure stop_strings are properly handled for local generation
    if stop_strings:
        gen_kwargs['stopping_criteria'] = StoppingCriteriaList([
            FinanceStoppingCriteria(stop_strings, tokenizer)
        ])
   
    try:
        loop = asyncio.get_event_loop()
        output = await asyncio.wait_for(
            loop.run_in_executor(None, lambda: model.generate(**gen_kwargs)),
            timeout=settings.LLM_TIMEOUT_SECONDS,
        )
       
        tokens = output[0][inputs.input_ids.size(1):]
        generated_text = tokenizer.decode(tokens, skip_special_tokens=True).strip()
        logger.debug(f"Local model generated: {generated_text[:200]}...")
        return generated_text
   
    except asyncio.TimeoutError:
        logger.warning('Local LLM inference timed out.')
        if settings.LLM_FALLBACK_ENABLED:
            return settings.LLM_FALLBACK_TEXT
        raise LLMTimeoutError('Local inference timed out')