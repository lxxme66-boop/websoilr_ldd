"""
Model Utilities

Helper functions for model management, size estimation, and configuration.
"""

import os
import json
import logging
from typing import Dict, List, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)


class ModelUtils:
    """Utility functions for model management"""
    
    @staticmethod
    def estimate_model_size(model_name: str) -> Dict[str, float]:
        """
        Estimate model size and resource requirements
        
        Args:
            model_name: Model name or path
            
        Returns:
            Dictionary with size estimates
        """
        # Common model size patterns
        size_patterns = {
            '70b': {'disk_gb': 140, 'ram_gb': 140, 'vram_gb': 80},
            '65b': {'disk_gb': 130, 'ram_gb': 130, 'vram_gb': 75},
            '40b': {'disk_gb': 80, 'ram_gb': 80, 'vram_gb': 48},
            '38b': {'disk_gb': 76, 'ram_gb': 76, 'vram_gb': 45},
            '34b': {'disk_gb': 68, 'ram_gb': 68, 'vram_gb': 40},
            '30b': {'disk_gb': 60, 'ram_gb': 60, 'vram_gb': 36},
            '20b': {'disk_gb': 40, 'ram_gb': 40, 'vram_gb': 24},
            '13b': {'disk_gb': 26, 'ram_gb': 26, 'vram_gb': 16},
            '7b': {'disk_gb': 14, 'ram_gb': 14, 'vram_gb': 8},
            '3b': {'disk_gb': 6, 'ram_gb': 6, 'vram_gb': 4},
            '1.5b': {'disk_gb': 3, 'ram_gb': 3, 'vram_gb': 2},
            '1b': {'disk_gb': 2, 'ram_gb': 2, 'vram_gb': 1.5},
        }
        
        # Extract size from model name
        model_lower = model_name.lower()
        for size_key, requirements in size_patterns.items():
            if size_key in model_lower:
                return requirements
                
        # Default estimate based on common patterns
        if 'xxl' in model_lower:
            return {'disk_gb': 40, 'ram_gb': 40, 'vram_gb': 24}
        elif 'xl' in model_lower:
            return {'disk_gb': 6, 'ram_gb': 6, 'vram_gb': 4}
        elif 'large' in model_lower:
            return {'disk_gb': 1.5, 'ram_gb': 1.5, 'vram_gb': 1}
        elif 'base' in model_lower or 'medium' in model_lower:
            return {'disk_gb': 0.5, 'ram_gb': 0.5, 'vram_gb': 0.5}
        elif 'small' in model_lower or 'tiny' in model_lower:
            return {'disk_gb': 0.25, 'ram_gb': 0.25, 'vram_gb': 0.25}
        else:
            # Conservative default
            return {'disk_gb': 14, 'ram_gb': 14, 'vram_gb': 8}
            
    @staticmethod
    def check_model_compatibility(model_name: str, backend: str) -> bool:
        """
        Check if a model is compatible with a specific backend
        
        Args:
            model_name: Model name or path
            backend: Backend name (vllm, transformers, ollama)
            
        Returns:
            True if compatible, False otherwise
        """
        # vLLM compatibility
        if backend == 'vllm':
            # vLLM supports most transformer models
            unsupported_patterns = ['t5', 'bert', 'roberta', 'xlm']
            model_lower = model_name.lower()
            return not any(pattern in model_lower for pattern in unsupported_patterns)
            
        # Transformers compatibility - supports almost everything
        elif backend == 'transformers':
            return True
            
        # Ollama compatibility - only specific models
        elif backend == 'ollama':
            ollama_models = [
                'llama', 'llama2', 'codellama', 'mistral', 'mixtral',
                'qwen', 'deepseek', 'phi', 'gemma', 'vicuna'
            ]
            model_lower = model_name.lower()
            return any(model in model_lower for model in ollama_models)
            
        return False
        
    @staticmethod
    def get_optimal_backend(model_name: str, available_backends: List[str]) -> Optional[str]:
        """
        Get the optimal backend for a given model
        
        Args:
            model_name: Model name or path
            available_backends: List of available backends
            
        Returns:
            Optimal backend name or None
        """
        # Priority order based on performance
        backend_priority = ['vllm', 'ollama', 'transformers']
        
        for backend in backend_priority:
            if backend in available_backends:
                if ModelUtils.check_model_compatibility(model_name, backend):
                    return backend
                    
        return None
        
    @staticmethod
    def format_model_info(model_name: str, backend: str = None) -> str:
        """
        Format model information for display
        
        Args:
            model_name: Model name or path
            backend: Backend name (optional)
            
        Returns:
            Formatted model information string
        """
        estimates = ModelUtils.estimate_model_size(model_name)
        
        info = f"Model: {model_name}\n"
        if backend:
            info += f"Backend: {backend}\n"
        info += f"Estimated Requirements:\n"
        info += f"  - Disk Space: {estimates['disk_gb']:.1f} GB\n"
        info += f"  - RAM: {estimates['ram_gb']:.1f} GB\n"
        info += f"  - VRAM: {estimates['vram_gb']:.1f} GB\n"
        
        return info
        
    @staticmethod
    def validate_model_path(model_path: str) -> bool:
        """
        Validate if a model path exists and contains model files
        
        Args:
            model_path: Path to model directory
            
        Returns:
            True if valid model path, False otherwise
        """
        if not model_path:
            return False
            
        path = Path(model_path)
        
        # Check if it's a HuggingFace model ID (org/model format)
        if '/' in model_path and not path.exists():
            # Assume it's a valid HF model ID
            return True
            
        # Check local path
        if not path.exists():
            return False
            
        # Check for common model files
        model_files = [
            'config.json',
            'pytorch_model.bin',
            'pytorch_model.bin.index.json',
            'model.safetensors',
            'model.safetensors.index.json'
        ]
        
        return any((path / file).exists() for file in model_files)


def estimate_model_size(model_name: str) -> Dict[str, float]:
    """
    Convenience function to estimate model size
    
    Args:
        model_name: Model name or path
        
    Returns:
        Dictionary with size estimates
    """
    return ModelUtils.estimate_model_size(model_name)