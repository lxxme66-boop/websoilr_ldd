import asyncio
import aiohttp
import json
import logging
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
import requests

logger = logging.getLogger(__name__)


class SkyworkClient:
    """Skywork本地大模型客户端
    
    支持通过vLLM或其他推理框架运行Skywork模型
    """
    
    def __init__(self, 
                 base_url: str = "http://localhost:8000",
                 model_path: str = "/mnt/storage/models/Skywork/Skywork-R1V3-38B",
                 timeout: int = 600,
                 api_type: str = "vllm"):  # vllm, openai_compatible, transformers
        """
        初始化Skywork客户端
        
        Args:
            base_url: 模型服务地址
            model_path: 模型路径
            timeout: 请求超时时间（秒）
            api_type: API类型 (vllm, openai_compatible, transformers)
        """
        self.base_url = base_url.rstrip('/')
        self.model_path = model_path
        self.timeout = timeout
        self.api_type = api_type
        self.session = None
        
        # API配置
        self.api_config = {
            "vllm": {
                "generate_endpoint": "/v1/completions",
                "chat_endpoint": "/v1/chat/completions",
                "models_endpoint": "/v1/models"
            },
            "openai_compatible": {
                "generate_endpoint": "/completions",
                "chat_endpoint": "/chat/completions",
                "models_endpoint": "/models"
            }
        }
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout)
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.session:
            await self.session.close()
    
    def check_connection(self) -> bool:
        """检查模型服务连接"""
        try:
            endpoint = self.api_config.get(self.api_type, {}).get("models_endpoint", "/v1/models")
            response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to connect to Skywork service: {e}")
            return False
    
    def get_available_models(self) -> List[str]:
        """获取可用的模型列表"""
        try:
            endpoint = self.api_config.get(self.api_type, {}).get("models_endpoint", "/v1/models")
            response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if self.api_type == "vllm":
                    return [model['id'] for model in data.get('data', [])]
                else:
                    return data.get('models', [])
            else:
                logger.error(f"Failed to get models: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"Error getting available models: {e}")
            return []
    
    async def generate(self, prompt: str, **kwargs) -> Optional[str]:
        """
        生成文本
        
        Args:
            prompt: 输入提示
            **kwargs: 其他参数（temperature, max_tokens, top_p等）
            
        Returns:
            生成的文本
        """
        if not self.session:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            )
        
        # 构建请求参数
        endpoint = self.api_config.get(self.api_type, {}).get("generate_endpoint", "/v1/completions")
        
        payload = {
            "model": self.model_path,
            "prompt": prompt,
            "temperature": kwargs.get("temperature", 0.8),
            "max_tokens": kwargs.get("max_tokens", 4096),
            "top_p": kwargs.get("top_p", 0.9),
            "frequency_penalty": kwargs.get("frequency_penalty", 0),
            "presence_penalty": kwargs.get("presence_penalty", 0),
            "stop": kwargs.get("stop", None)
        }
        
        # 移除None值
        payload = {k: v for k, v in payload.items() if v is not None}
        
        try:
            async with self.session.post(
                f"{self.base_url}{endpoint}",
                json=payload
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if self.api_type == "vllm":
                        return data['choices'][0]['text']
                    else:
                        return data.get('choices', [{}])[0].get('text', '')
                else:
                    error_text = await response.text()
                    logger.error(f"Generation failed: {response.status} - {error_text}")
                    return None
        except Exception as e:
            logger.error(f"Error during generation: {e}")
            return None
    
    async def chat(self, messages: List[Dict[str, str]], **kwargs) -> Optional[str]:
        """
        聊天对话
        
        Args:
            messages: 消息列表 [{"role": "user/assistant/system", "content": "..."}]
            **kwargs: 其他参数
            
        Returns:
            生成的回复
        """
        if not self.session:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            )
        
        endpoint = self.api_config.get(self.api_type, {}).get("chat_endpoint", "/v1/chat/completions")
        
        payload = {
            "model": self.model_path,
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.8),
            "max_tokens": kwargs.get("max_tokens", 4096),
            "top_p": kwargs.get("top_p", 0.9),
            "frequency_penalty": kwargs.get("frequency_penalty", 0),
            "presence_penalty": kwargs.get("presence_penalty", 0),
            "stop": kwargs.get("stop", None)
        }
        
        # 移除None值
        payload = {k: v for k, v in payload.items() if v is not None}
        
        try:
            async with self.session.post(
                f"{self.base_url}{endpoint}",
                json=payload
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data['choices'][0]['message']['content']
                else:
                    error_text = await response.text()
                    logger.error(f"Chat failed: {response.status} - {error_text}")
                    return None
        except Exception as e:
            logger.error(f"Error during chat: {e}")
            return None
    
    async def batch_generate(self, prompts: List[str], **kwargs) -> List[Optional[str]]:
        """批量生成文本"""
        tasks = [self.generate(prompt, **kwargs) for prompt in prompts]
        return await asyncio.gather(*tasks)
    
    async def batch_chat(self, conversations: List[List[Dict[str, str]]], **kwargs) -> List[Optional[str]]:
        """批量聊天对话"""
        tasks = [self.chat(messages, **kwargs) for messages in conversations]
        return await asyncio.gather(*tasks)


class SkyworkTransformersClient:
    """使用Transformers库直接加载Skywork模型的客户端"""
    
    def __init__(self, 
                 model_path: str = "/mnt/storage/models/Skywork/Skywork-R1V3-38B",
                 device: str = "auto",
                 load_in_8bit: bool = False,
                 load_in_4bit: bool = False):
        """
        初始化Transformers客户端
        
        Args:
            model_path: 模型路径
            device: 设备类型
            load_in_8bit: 是否使用8bit量化
            load_in_4bit: 是否使用4bit量化
        """
        self.model_path = model_path
        self.device = device
        self.load_in_8bit = load_in_8bit
        self.load_in_4bit = load_in_4bit
        self.model = None
        self.tokenizer = None
        
    def load_model(self):
        """加载模型"""
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
            import torch
            
            # 加载tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_path,
                trust_remote_code=True
            )
            
            # 配置模型加载参数
            model_kwargs = {
                "trust_remote_code": True,
                "device_map": self.device if self.device == "auto" else None,
            }
            
            if self.load_in_8bit:
                model_kwargs["load_in_8bit"] = True
            elif self.load_in_4bit:
                model_kwargs["load_in_4bit"] = True
                model_kwargs["bnb_4bit_compute_dtype"] = torch.float16
            else:
                model_kwargs["torch_dtype"] = torch.float16
            
            # 加载模型
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_path,
                **model_kwargs
            )
            
            if self.device != "auto" and not (self.load_in_8bit or self.load_in_4bit):
                self.model = self.model.to(self.device)
            
            logger.info(f"Successfully loaded Skywork model from {self.model_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return False
    
    def generate(self, prompt: str, **kwargs) -> Optional[str]:
        """生成文本"""
        if not self.model or not self.tokenizer:
            if not self.load_model():
                return None
        
        try:
            # Tokenize输入
            inputs = self.tokenizer(prompt, return_tensors="pt")
            if self.device != "auto":
                inputs = inputs.to(self.device)
            
            # 生成参数
            gen_kwargs = {
                "max_new_tokens": kwargs.get("max_tokens", 4096),
                "temperature": kwargs.get("temperature", 0.8),
                "top_p": kwargs.get("top_p", 0.9),
                "do_sample": True,
                "pad_token_id": self.tokenizer.pad_token_id,
                "eos_token_id": self.tokenizer.eos_token_id,
            }
            
            # 生成
            with torch.no_grad():
                outputs = self.model.generate(**inputs, **gen_kwargs)
            
            # 解码输出
            generated_text = self.tokenizer.decode(
                outputs[0][inputs['input_ids'].shape[1]:], 
                skip_special_tokens=True
            )
            
            return generated_text
            
        except Exception as e:
            logger.error(f"Error during generation: {e}")
            return None
    
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> Optional[str]:
        """聊天对话"""
        # 将消息列表转换为单个prompt
        prompt = ""
        for msg in messages:
            role = msg['role']
            content = msg['content']
            if role == 'system':
                prompt += f"System: {content}\n\n"
            elif role == 'user':
                prompt += f"User: {content}\n\n"
            elif role == 'assistant':
                prompt += f"Assistant: {content}\n\n"
        
        prompt += "Assistant: "
        
        return self.generate(prompt, **kwargs)


# 工厂函数
def create_skywork_client(client_type: str = "vllm", **kwargs) -> Union[SkyworkClient, SkyworkTransformersClient]:
    """
    创建Skywork客户端
    
    Args:
        client_type: 客户端类型 (vllm, transformers)
        **kwargs: 客户端参数
        
    Returns:
        Skywork客户端实例
    """
    if client_type == "transformers":
        return SkyworkTransformersClient(**kwargs)
    else:
        return SkyworkClient(api_type=client_type, **kwargs)