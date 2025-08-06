"""
LocalModels package for supporting various local model backends
"""

from .ollama_client import OllamaClient
from .skywork_client import SkyworkClient, SkyworkTransformersClient, create_skywork_client

__all__ = [
    'OllamaClient',
    'SkyworkClient', 
    'SkyworkTransformersClient',
    'create_skywork_client'
]

# Version info
__version__ = '1.1.0'

# Available backends
AVAILABLE_BACKENDS = {
    'ollama': OllamaClient,
    'skywork_vllm': SkyworkClient,
    'skywork_transformers': SkyworkTransformersClient
}

def get_backend(backend_name: str, **kwargs):
    """
    Get a backend client by name
    
    Args:
        backend_name: Name of the backend
        **kwargs: Arguments for the backend client
        
    Returns:
        Backend client instance
    """
    if backend_name not in AVAILABLE_BACKENDS:
        raise ValueError(f"Unknown backend: {backend_name}. Available: {list(AVAILABLE_BACKENDS.keys())}")
    
    if backend_name == 'skywork_vllm':
        return create_skywork_client('vllm', **kwargs)
    elif backend_name == 'skywork_transformers':
        return create_skywork_client('transformers', **kwargs)
    else:
        return AVAILABLE_BACKENDS[backend_name](**kwargs)