import requests
import json
import asyncio
import aiohttp
from typing import Dict, Any, List, Optional, AsyncGenerator
import logging
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)


class SkyworkClient:
    """Skywork本地模型客户端，支持通过vLLM运行"""
    
    def __init__(self, base_url: str = "http://localhost:8000", 
                 model_path: str = "/mnt/storage/models/Skywork/Skywork-R1V3-38B", 
                 timeout: int = 600):
        """
        初始化Skywork客户端
        
        Args:
            base_url: vLLM服务地址
            model_path: 模型路径
            timeout: 请求超时时间（秒）
        """
        self.base_url = base_url.rstrip('/')
        self.model_path = model_path
        self.timeout = timeout
        self.client = AsyncOpenAI(
            base_url=f"{self.base_url}/v1",
            api_key="EMPTY",  # vLLM不需要真实的API key
            timeout=timeout
        )
        
    def check_connection(self) -> bool:
        """检查vLLM服务连接"""
        try:
            response = requests.get(f"{self.base_url}/v1/models", timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to connect to vLLM: {e}")
            return False
    
    def get_available_models(self) -> List[str]:
        """获取可用的模型列表"""
        try:
            response = requests.get(f"{self.base_url}/v1/models", timeout=10)
            if response.status_code == 200:
                data = response.json()
                return [model['id'] for model in data.get('data', [])]
            else:
                logger.error(f"Failed to get models: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"Error getting available models: {e}")
            return []
    
    async def chat(self, messages: List[Dict[str, str]], **kwargs) -> Optional[str]:
        """
        聊天接口
        
        Args:
            messages: 消息列表
            **kwargs: 其他参数（temperature, max_tokens等）
            
        Returns:
            生成的文本
        """
        try:
            # 设置默认参数
            params = {
                "model": self.model_path,
                "messages": messages,
                "temperature": kwargs.get("temperature", 0.7),
                "max_tokens": kwargs.get("max_tokens", 4096),
                "top_p": kwargs.get("top_p", 0.9),
                "stream": False
            }
            
            response = await self.client.chat.completions.create(**params)
            
            if response and response.choices:
                return response.choices[0].message.content
            else:
                logger.error("No response from model")
                return None
                
        except Exception as e:
            logger.error(f"Error in chat: {e}")
            return None
    
    async def generate(self, prompt: str, **kwargs) -> Optional[str]:
        """
        生成文本（兼容接口）
        
        Args:
            prompt: 输入提示
            **kwargs: 其他参数
            
        Returns:
            生成的文本
        """
        messages = [{"role": "user", "content": prompt}]
        return await self.chat(messages, **kwargs)
    
    async def chat_stream(self, messages: List[Dict[str, str]], **kwargs) -> AsyncGenerator[str, None]:
        """
        流式聊天接口
        
        Args:
            messages: 消息列表
            **kwargs: 其他参数
            
        Yields:
            生成的文本片段
        """
        try:
            params = {
                "model": self.model_path,
                "messages": messages,
                "temperature": kwargs.get("temperature", 0.7),
                "max_tokens": kwargs.get("max_tokens", 4096),
                "top_p": kwargs.get("top_p", 0.9),
                "stream": True
            }
            
            stream = await self.client.chat.completions.create(**params)
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error(f"Error in chat stream: {e}")
            yield f"Error: {str(e)}"


# 工具函数
def start_vllm_server(model_path: str, port: int = 8000, gpu_memory_utilization: float = 0.9):
    """
    启动vLLM服务器的命令示例
    
    在终端运行:
    python -m vllm.entrypoints.openai.api_server \
        --model /mnt/storage/models/Skywork/Skywork-R1V3-38B \
        --port 8000 \
        --gpu-memory-utilization 0.9 \
        --max-model-len 4096 \
        --trust-remote-code
    """
    import subprocess
    
    cmd = [
        "python", "-m", "vllm.entrypoints.openai.api_server",
        "--model", model_path,
        "--port", str(port),
        "--gpu-memory-utilization", str(gpu_memory_utilization),
        "--max-model-len", "4096",
        "--trust-remote-code"
    ]
    
    logger.info(f"Starting vLLM server with command: {' '.join(cmd)}")
    return subprocess.Popen(cmd)