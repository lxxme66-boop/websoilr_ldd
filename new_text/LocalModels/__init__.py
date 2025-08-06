"""
Local model clients for the text generation system
"""

from .ollama_client import OllamaClient
from .skywork_client import SkyworkClient

__all__ = ['OllamaClient', 'SkyworkClient']

# Check available backends
import importlib

AVAILABLE_BACKENDS = {}

# Check Ollama
try:
    import requests
    response = requests.get("http://localhost:11434/api/tags", timeout=2)
    if response.status_code == 200:
        AVAILABLE_BACKENDS['ollama'] = True
except:
    AVAILABLE_BACKENDS['ollama'] = False

# Check vLLM
try:
    import requests
    response = requests.get("http://localhost:8000/v1/models", timeout=2)
    if response.status_code == 200:
        AVAILABLE_BACKENDS['vllm'] = True
except:
    AVAILABLE_BACKENDS['vllm'] = False

print(f"Available local model backends: {AVAILABLE_BACKENDS}")