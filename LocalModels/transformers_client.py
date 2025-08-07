"""
Transformers Client for Local Model Loading

This module provides a client interface for loading models directly
using HuggingFace transformers library.
"""

import os
import asyncio
import json
import logging
from typing import Dict, List, Optional, Union, AsyncGenerator
import torch
from transformers import (
    AutoModelForCausalLM, 
    AutoTokenizer,
    TextStreamer,
    BitsAndBytesConfig
)
from threading import Thread

logger = logging.getLogger(__name__)


class TransformersClient:
    """Client for loading and using models with HuggingFace transformers"""
    
    def __init__(self,
                 model_name: str,
                 device: str = "auto",
                 torch_dtype: str = "auto",
                 load_in_8bit: bool = False,
                 load_in_4bit: bool = False,
                 trust_remote_code: bool = True,
                 max_memory: Dict[int, str] = None):
        """
        Initialize Transformers client
        
        Args:
            model_name: Model name or path
            device: Device to load model on ("auto", "cuda", "cpu")
            torch_dtype: Data type for model weights ("auto", "float16", "float32", "bfloat16")
            load_in_8bit: Whether to load model in 8-bit precision
            load_in_4bit: Whether to load model in 4-bit precision
            trust_remote_code: Whether to trust remote code
            max_memory: Maximum memory per GPU
        """
        self.model_name = model_name
        self.device = device
        self.torch_dtype = torch_dtype
        self.load_in_8bit = load_in_8bit
        self.load_in_4bit = load_in_4bit
        self.trust_remote_code = trust_remote_code
        self.max_memory = max_memory
        
        self.model = None
        self.tokenizer = None
        self._load_model()
        
    def _get_torch_dtype(self):
        """Get torch dtype from string"""
        if self.torch_dtype == "auto":
            return "auto"
        elif self.torch_dtype == "float16":
            return torch.float16
        elif self.torch_dtype == "float32":
            return torch.float32
        elif self.torch_dtype == "bfloat16":
            return torch.bfloat16
        else:
            return "auto"
            
    def _get_device_map(self):
        """Get device map for model loading"""
        if self.device == "auto":
            return "auto"
        elif self.device == "cuda":
            return {"": 0}
        elif self.device == "cpu":
            return {"": "cpu"}
        else:
            return self.device
            
    def _load_model(self):
        """Load model and tokenizer"""
        logger.info(f"Loading model: {self.model_name}")
        
        try:
            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                trust_remote_code=self.trust_remote_code,
                padding_side="left"
            )
            
            # Set pad token if not set
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
                
            # Prepare model loading arguments
            model_kwargs = {
                "pretrained_model_name_or_path": self.model_name,
                "trust_remote_code": self.trust_remote_code,
                "device_map": self._get_device_map(),
            }
            
            # Set dtype
            torch_dtype = self._get_torch_dtype()
            if torch_dtype != "auto":
                model_kwargs["torch_dtype"] = torch_dtype
                
            # Set quantization config
            if self.load_in_4bit:
                model_kwargs["quantization_config"] = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_compute_dtype=torch.float16,
                    bnb_4bit_use_double_quant=True,
                    bnb_4bit_quant_type="nf4"
                )
            elif self.load_in_8bit:
                model_kwargs["quantization_config"] = BitsAndBytesConfig(
                    load_in_8bit=True
                )
                
            # Set max memory if specified
            if self.max_memory:
                model_kwargs["max_memory"] = self.max_memory
                
            # Load model
            self.model = AutoModelForCausalLM.from_pretrained(**model_kwargs)
            
            # Move to device if not using device_map
            if self.device != "auto" and not (self.load_in_4bit or self.load_in_8bit):
                self.model = self.model.to(self.device)
                
            logger.info(f"Model loaded successfully: {self.model_name}")
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise
            
    def generate(self,
                prompt: str,
                system_prompt: str = None,
                temperature: float = 0.7,
                max_tokens: int = 2048,
                top_p: float = 0.9,
                top_k: int = 50,
                repetition_penalty: float = 1.0,
                **kwargs) -> str:
        """
        Generate text using transformers
        
        Args:
            prompt: User prompt
            system_prompt: System prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            top_p: Top-p sampling parameter
            top_k: Top-k sampling parameter
            repetition_penalty: Repetition penalty
            **kwargs: Additional generation parameters
            
        Returns:
            Generated text
        """
        # Format prompt with system prompt if provided
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        else:
            full_prompt = prompt
            
        # Tokenize input
        inputs = self.tokenizer(
            full_prompt,
            return_tensors="pt",
            truncation=True,
            max_length=self.model.config.max_position_embeddings - max_tokens
        )
        
        # Move to device
        if self.device != "auto" and self.device != "cpu":
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
        # Generate
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                top_k=top_k,
                repetition_penalty=repetition_penalty,
                do_sample=temperature > 0,
                pad_token_id=self.tokenizer.pad_token_id,
                eos_token_id=self.tokenizer.eos_token_id,
                **kwargs
            )
            
        # Decode output
        generated_text = self.tokenizer.decode(
            outputs[0][inputs['input_ids'].shape[1]:],
            skip_special_tokens=True
        )
        
        return generated_text
        
    def generate_stream(self,
                       prompt: str,
                       system_prompt: str = None,
                       temperature: float = 0.7,
                       max_tokens: int = 2048,
                       top_p: float = 0.9,
                       top_k: int = 50,
                       repetition_penalty: float = 1.0,
                       **kwargs) -> Generator[str, None, None]:
        """
        Generate text with streaming using transformers
        
        Args:
            prompt: User prompt
            system_prompt: System prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            top_p: Top-p sampling parameter
            top_k: Top-k sampling parameter
            repetition_penalty: Repetition penalty
            **kwargs: Additional generation parameters
            
        Yields:
            Generated text chunks
        """
        # Format prompt with system prompt if provided
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        else:
            full_prompt = prompt
            
        # Tokenize input
        inputs = self.tokenizer(
            full_prompt,
            return_tensors="pt",
            truncation=True,
            max_length=self.model.config.max_position_embeddings - max_tokens
        )
        
        # Move to device
        if self.device != "auto" and self.device != "cpu":
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
        # Create streamer
        streamer = TextStreamer(
            self.tokenizer,
            skip_prompt=True,
            skip_special_tokens=True
        )
        
        # Generate with streaming
        generation_kwargs = dict(
            **inputs,
            max_new_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            repetition_penalty=repetition_penalty,
            do_sample=temperature > 0,
            pad_token_id=self.tokenizer.pad_token_id,
            eos_token_id=self.tokenizer.eos_token_id,
            streamer=streamer,
            **kwargs
        )
        
        # Run generation in thread to enable streaming
        thread = Thread(target=self.model.generate, kwargs=generation_kwargs)
        thread.start()
        
        # Note: For true streaming, you would need to implement a custom streamer
        # that yields tokens. This is a simplified version.
        thread.join()
        
    async def agenerate(self,
                       prompt: str,
                       system_prompt: str = None,
                       temperature: float = 0.7,
                       max_tokens: int = 2048,
                       top_p: float = 0.9,
                       **kwargs) -> str:
        """
        Async wrapper for generate method
        
        Args:
            prompt: User prompt
            system_prompt: System prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            top_p: Top-p sampling parameter
            **kwargs: Additional generation parameters
            
        Returns:
            Generated text
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self.generate,
            prompt,
            system_prompt,
            temperature,
            max_tokens,
            top_p,
            **kwargs
        )


def create_transformers_client(config: Dict) -> TransformersClient:
    """
    Create Transformers client from configuration
    
    Args:
        config: Configuration dictionary
        
    Returns:
        TransformersClient instance
    """
    transformers_config = config.get('models', {}).get('local_models', {}).get('transformers', {})
    
    return TransformersClient(
        model_name=transformers_config.get('model_name') or config.get('models', {}).get('default_model'),
        device=transformers_config.get('device', 'auto'),
        torch_dtype=transformers_config.get('torch_dtype', 'auto'),
        load_in_8bit=transformers_config.get('load_in_8bit', False),
        load_in_4bit=transformers_config.get('load_in_4bit', False),
        trust_remote_code=transformers_config.get('trust_remote_code', True),
        max_memory=transformers_config.get('max_memory')
    )