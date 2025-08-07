"""
Local Model Manager

This module provides a unified interface for managing different local model backends
(vLLM, Transformers, Ollama) and selecting the appropriate one based on configuration.
"""

import os
import json
import logging
from typing import Dict, List, Optional, Union, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class LocalModelManager:
    """Manager for local model backends"""
    
    def __init__(self, config: Dict):
        """
        Initialize Local Model Manager
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.api_config = config.get('api', {})
        self.models_config = config.get('models', {})
        self.local_models_config = self.models_config.get('local_models', {})
        
        self.use_local_models = self.api_config.get('use_local_models', False)
        self.local_model_priority = self.api_config.get('local_model_priority', ['vllm', 'ollama', 'transformers'])
        
        self.available_backends = self._check_available_backends()
        self.active_client = None
        self.active_backend = None
        
        if self.use_local_models:
            self._initialize_client()
            
    def _check_available_backends(self) -> List[str]:
        """Check which local model backends are available"""
        available = []
        
        # Check vLLM
        try:
            import vllm
            if self.local_models_config.get('vllm', {}).get('enabled', False):
                available.append('vllm')
        except ImportError:
            logger.debug("vLLM not available")
            
        # Check Ollama
        try:
            from .ollama_client import OllamaClient
            if self.local_models_config.get('ollama', {}).get('enabled', False):
                # Check if Ollama service is running
                import requests
                ollama_config = self.local_models_config.get('ollama', {})
                base_url = ollama_config.get('base_url', 'http://localhost:11434')
                try:
                    response = requests.get(f"{base_url}/api/tags", timeout=2)
                    if response.status_code == 200:
                        available.append('ollama')
                except:
                    logger.debug("Ollama service not running")
        except ImportError:
            logger.debug("Ollama client not available")
            
        # Check Transformers
        try:
            import transformers
            import torch
            if self.local_models_config.get('transformers', {}).get('enabled', False):
                available.append('transformers')
        except ImportError:
            logger.debug("Transformers not available")
            
        logger.info(f"Available local model backends: {available}")
        return available
        
    def _initialize_client(self):
        """Initialize the appropriate local model client"""
        if not self.available_backends:
            logger.warning("No local model backends available")
            return
            
        # Try backends in priority order
        for backend in self.local_model_priority:
            if backend in self.available_backends:
                try:
                    if backend == 'vllm':
                        self._init_vllm_client()
                    elif backend == 'ollama':
                        self._init_ollama_client()
                    elif backend == 'transformers':
                        self._init_transformers_client()
                        
                    if self.active_client:
                        self.active_backend = backend
                        logger.info(f"Initialized {backend} as local model backend")
                        break
                except Exception as e:
                    logger.error(f"Failed to initialize {backend}: {e}")
                    continue
                    
        if not self.active_client:
            logger.error("Failed to initialize any local model backend")
            
    def _init_vllm_client(self):
        """Initialize vLLM client"""
        from .vllm_client import create_vllm_client
        
        vllm_config = self.local_models_config.get('vllm', {})
        
        # Check if we need to start the server
        client = create_vllm_client(self.config)
        
        if not client.is_server_running():
            logger.info("Starting vLLM server...")
            model_path = vllm_config.get('model_name') or self.models_config.get('default_model')
            
            client.start_server(
                model_path=model_path,
                gpu_memory_utilization=vllm_config.get('gpu_memory_utilization', 0.9),
                max_model_len=vllm_config.get('max_model_len', 32768),
                tensor_parallel_size=vllm_config.get('tensor_parallel_size', 1)
            )
            
        self.active_client = client
        
    def _init_ollama_client(self):
        """Initialize Ollama client"""
        from .ollama_client import create_ollama_client
        self.active_client = create_ollama_client(self.config)
        
    def _init_transformers_client(self):
        """Initialize Transformers client"""
        from .transformers_client import create_transformers_client
        self.active_client = create_transformers_client(self.config)
        
    async def generate(self, 
                      prompt: str,
                      system_prompt: str = None,
                      temperature: float = None,
                      max_tokens: int = None,
                      **kwargs) -> str:
        """
        Generate text using the active local model
        
        Args:
            prompt: User prompt
            system_prompt: System prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional generation parameters
            
        Returns:
            Generated text
        """
        if not self.active_client:
            raise RuntimeError("No local model client initialized")
            
        # Get default parameters from config
        qa_config = self.models_config.get('qa_generator_model', {})
        temperature = temperature or qa_config.get('temperature', 0.8)
        max_tokens = max_tokens or qa_config.get('max_tokens', 4096)
        
        # Generate based on backend type
        if self.active_backend == 'vllm':
            return await self.active_client.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
        elif self.active_backend == 'ollama':
            return await self.active_client.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
        elif self.active_backend == 'transformers':
            # Transformers client might not have async method
            return await self.active_client.agenerate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
        else:
            raise RuntimeError(f"Unknown backend: {self.active_backend}")
            
    def generate_sync(self,
                     prompt: str,
                     system_prompt: str = None,
                     temperature: float = None,
                     max_tokens: int = None,
                     **kwargs) -> str:
        """
        Synchronous text generation
        
        Args:
            prompt: User prompt
            system_prompt: System prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional generation parameters
            
        Returns:
            Generated text
        """
        if not self.active_client:
            raise RuntimeError("No local model client initialized")
            
        # Get default parameters from config
        qa_config = self.models_config.get('qa_generator_model', {})
        temperature = temperature or qa_config.get('temperature', 0.8)
        max_tokens = max_tokens or qa_config.get('max_tokens', 4096)
        
        # Generate based on backend type
        if hasattr(self.active_client, 'generate_sync'):
            return self.active_client.generate_sync(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
        else:
            # Fallback to regular generate for backends that don't have generate_sync
            return self.active_client.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            
    def get_client(self):
        """Get the active client instance"""
        return self.active_client
        
    def get_backend_name(self) -> str:
        """Get the name of the active backend"""
        return self.active_backend
        
    def is_available(self) -> bool:
        """Check if local models are available and initialized"""
        return self.active_client is not None
        
    def shutdown(self):
        """Shutdown the local model backend"""
        if self.active_client and self.active_backend == 'vllm':
            self.active_client.stop_server()
            

def get_available_models(config: Dict) -> List[str]:
    """
    Get list of available local models
    
    Args:
        config: Configuration dictionary
        
    Returns:
        List of available model names
    """
    manager = LocalModelManager(config)
    models = []
    
    for backend in manager.available_backends:
        backend_config = config.get('models', {}).get('local_models', {}).get(backend, {})
        model_name = backend_config.get('model_name')
        if model_name:
            models.append(f"{backend}:{model_name}")
            
    # Also add default model
    default_model = config.get('models', {}).get('default_model')
    if default_model:
        models.append(f"default:{default_model}")
        
    return models