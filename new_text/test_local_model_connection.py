#!/usr/bin/env python3
"""
测试本地模型连接脚本
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from LocalModels.skywork_client import SkyworkClient
from LocalModels.ollama_client import OllamaClient
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_skywork():
    """测试Skywork模型连接"""
    print("\n=== 测试Skywork模型连接 ===")
    
    client = SkyworkClient(
        base_url="http://localhost:8000",
        model_path="/mnt/storage/models/Skywork/Skywork-R1V3-38B"
    )
    
    # 检查连接
    if client.check_connection():
        print("✓ Skywork/vLLM服务连接成功")
        
        # 获取可用模型
        models = client.get_available_models()
        print(f"可用模型: {models}")
        
        # 测试生成
        try:
            messages = [
                {"role": "system", "content": "你是一个有帮助的助手。"},
                {"role": "user", "content": "请用一句话介绍什么是半导体。"}
            ]
            
            print("\n发送测试请求...")
            response = await client.chat(messages, temperature=0.7, max_tokens=100)
            
            if response:
                print(f"✓ 模型响应成功:")
                print(f"  {response}")
            else:
                print("✗ 模型响应失败")
                
        except Exception as e:
            print(f"✗ 测试失败: {e}")
    else:
        print("✗ Skywork/vLLM服务未运行")
        print("  请运行: ./start_skywork_server.sh")


async def test_ollama():
    """测试Ollama模型连接"""
    print("\n=== 测试Ollama模型连接 ===")
    
    client = OllamaClient(
        base_url="http://localhost:11434",
        model_name="qwen:7b"
    )
    
    # 检查连接
    if client.check_connection():
        print("✓ Ollama服务连接成功")
        
        # 获取可用模型
        models = client.get_available_models()
        print(f"可用模型: {models}")
        
        if not models:
            print("  提示: 没有安装模型，请运行: ollama pull qwen:7b")
            return
        
        # 测试生成
        try:
            messages = [
                {"role": "system", "content": "你是一个有帮助的助手。"},
                {"role": "user", "content": "请用一句话介绍什么是光学。"}
            ]
            
            print("\n发送测试请求...")
            response = await client.chat(messages, temperature=0.7, max_tokens=100)
            
            if response:
                print(f"✓ 模型响应成功:")
                print(f"  {response}")
            else:
                print("✗ 模型响应失败")
                
        except Exception as e:
            print(f"✗ 测试失败: {e}")
    else:
        print("✗ Ollama服务未运行")
        print("  请运行: ollama serve")


async def main():
    """主测试函数"""
    print("智能文本QA生成系统 - 本地模型连接测试")
    print("=" * 50)
    
    # 测试Skywork
    await test_skywork()
    
    # 测试Ollama
    await test_ollama()
    
    print("\n" + "=" * 50)
    print("测试完成")


if __name__ == "__main__":
    asyncio.run(main())