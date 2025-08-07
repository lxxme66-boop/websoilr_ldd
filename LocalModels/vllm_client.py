"""
vLLM Client for Local Model Serving

This module provides a client interface for vLLM-based model serving.
vLLM is a high-throughput serving engine for large language models.
"""

import os
import asyncio
import json
import logging
from typing import Dict, List, Optional, Union, AsyncGenerator
from openai import AsyncOpenAI, OpenAI
import aiohttp
import requests

logger = logging.getLogger(__name__)


class VLLMClient:
    """Client for interacting with vLLM model server"""
    
    def __init__(self, 
                 base_url: str = "http://localhost:8000",
                 model_path: str = None,
                 api_key: str = "EMPTY",
                 timeout: int = 300,
                 max_retries: int = 3):
        """
        Initialize vLLM client
        
        Args:
            base_url: Base URL for vLLM server
            model_path: Path to the model (used for server startup)
            api_key: API key (usually "EMPTY" for local vLLM)
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries
        """
        self.base_url = base_url.rstrip('/')
        self.model_path = model_path
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries
        
        # OpenAI-compatible clients
        self.client = OpenAI(
            api_key=api_key,
            base_url=f"{self.base_url}/v1",
            timeout=timeout
        )
        
        self.async_client = AsyncOpenAI(
            api_key=api_key,
            base_url=f"{self.base_url}/v1",
            timeout=timeout
        )
        
        self._server_process = None
        
    def start_server(self, 
                    model_path: str = None,
                    gpu_memory_utilization: float = 0.9,
                    max_model_len: int = 32768,
                    tensor_parallel_size: int = 1,
                    port: int = 8000,
                    **kwargs):
        """
        Start vLLM server process
        
        Args:
            model_path: Path to the model
            gpu_memory_utilization: GPU memory fraction to use
            max_model_len: Maximum sequence length
            tensor_parallel_size: Number of GPUs for tensor parallelism
            port: Port to run server on
            **kwargs: Additional vLLM arguments
        """
        import subprocess
        
        model_path = model_path or self.model_path
        if not model_path:
            raise ValueError("Model path must be provided")
            
        # Check if server is already running
        if self.is_server_running():
            logger.info("vLLM server is already running")
            return
            
        cmd = [
            "python", "-m", "vllm.entrypoints.openai.api_server",
            "--model", model_path,
            "--port", str(port),
            "--gpu-memory-utilization", str(gpu_memory_utilization),
            "--max-model-len", str(max_model_len),
            "--tensor-parallel-size", str(tensor_parallel_size),
            "--trust-remote-code"
        ]
        
        # Add additional arguments
        for key, value in kwargs.items():
            cmd.extend([f"--{key.replace('_', '-')}", str(value)])
            
        logger.info(f"Starting vLLM server with command: {' '.join(cmd)}")
        
        try:
            self._server_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait for server to start
            import time
            for i in range(30):  # Wait up to 30 seconds
                if self.is_server_running():
                    logger.info("vLLM server started successfully")
                    return
                time.sleep(1)
                
            raise RuntimeError("vLLM server failed to start within timeout")
            
        except Exception as e:
            logger.error(f"Failed to start vLLM server: {e}")
            raise
            
    def stop_server(self):
        """Stop vLLM server process"""
        if self._server_process:
            self._server_process.terminate()
            self._server_process.wait()
            self._server_process = None
            logger.info("vLLM server stopped")
            
    def is_server_running(self) -> bool:
        """Check if vLLM server is running"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except:
            return False
            
    async def generate(self,
                      prompt: str,
                      system_prompt: str = None,
                      temperature: float = 0.7,
                      max_tokens: int = 2048,
                      top_p: float = 0.9,
                      **kwargs) -> str:
        """
        Generate text using vLLM
        
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
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = await self.async_client.chat.completions.create(
                model=self.model_path or "default",
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                **kwargs
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error generating text with vLLM: {e}")
            raise
            
    async def generate_stream(self,
                            prompt: str,
                            system_prompt: str = None,
                            temperature: float = 0.7,
                            max_tokens: int = 2048,
                            top_p: float = 0.9,
                            **kwargs) -> AsyncGenerator[str, None]:
        """
        Generate text using vLLM with streaming
        
        Args:
            prompt: User prompt
            system_prompt: System prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            top_p: Top-p sampling parameter
            **kwargs: Additional generation parameters
            
        Yields:
            Generated text chunks
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            stream = await self.async_client.chat.completions.create(
                model=self.model_path or "default",
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                stream=True,
                **kwargs
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error(f"Error streaming text with vLLM: {e}")
            raise
            
    def generate_sync(self,
                     prompt: str,
                     system_prompt: str = None,
                     temperature: float = 0.7,
                     max_tokens: int = 2048,
                     top_p: float = 0.9,
                     **kwargs) -> str:
        """
        Synchronous text generation
        
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
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_path or "default",
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                **kwargs
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error generating text with vLLM: {e}")
            raise


def create_vllm_client(config: Dict) -> VLLMClient:
    """
    Create vLLM client from configuration
    
    Args:
        config: Configuration dictionary
        
    Returns:
        VLLMClient instance
    """
    vllm_config = config.get('models', {}).get('local_models', {}).get('vllm', {})
    
    return VLLMClient(
        base_url=vllm_config.get('base_url', 'http://localhost:8000'),
        model_path=vllm_config.get('model_name') or config.get('models', {}).get('default_model'),
        api_key=vllm_config.get('api_key', 'EMPTY'),
        timeout=vllm_config.get('timeout', 300)
    )