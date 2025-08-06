#!/bin/bash

echo "配置本地 Skywork-R1V3-38B 模型..."

# 检查模型路径是否存在
MODEL_PATH="/mnt/storage/models/Skywork/Skywork-R1V3-38B"
if [ ! -d "$MODEL_PATH" ]; then
    echo "错误：模型路径不存在: $MODEL_PATH"
    exit 1
fi

echo "找到模型路径: $MODEL_PATH"

# 方案1：使用 vLLM 启动模型服务（推荐用于生产环境）
echo ""
echo "=== 方案1：使用 vLLM ==="
echo "安装 vLLM（需要 GPU）："
echo "pip install vllm"
echo ""
echo "启动 vLLM 服务："
echo "python -m vllm.entrypoints.openai.api_server \\"
echo "    --model $MODEL_PATH \\"
echo "    --host 0.0.0.0 \\"
echo "    --port 8080 \\"
echo "    --max-model-len 4096 \\"
echo "    --gpu-memory-utilization 0.9"

# 方案2：使用 transformers 直接加载（适合开发测试）
echo ""
echo "=== 方案2：使用 Transformers ==="
echo "安装依赖："
echo "pip install transformers torch accelerate"
echo ""
echo "配置已更新，可以直接使用 transformers 模式"

# 更新配置文件
echo ""
echo "=== 更新配置文件 ==="
cat > skywork_config_update.json << 'EOF'
{
  "api": {
    "ark_url": "http://localhost:8080/v1",
    "use_local_models": true,
    "local_model_priority": ["vllm", "transformers", "ollama"]
  },
  "models": {
    "default_model": "/mnt/storage/models/Skywork/Skywork-R1V3-38B",
    "local_models": {
      "vllm": {
        "enabled": true,
        "base_url": "http://localhost:8080",
        "model_name": "/mnt/storage/models/Skywork/Skywork-R1V3-38B",
        "timeout": 600
      },
      "transformers": {
        "enabled": true,
        "model_name": "/mnt/storage/models/Skywork/Skywork-R1V3-38B",
        "device": "auto",
        "torch_dtype": "auto",
        "load_in_4bit": false,
        "load_in_8bit": true
      }
    }
  }
}
EOF

echo "配置更新已保存到 skywork_config_update.json"
echo ""
echo "=== 使用说明 ==="
echo "1. 使用 vLLM（推荐）："
echo "   - 先启动 vLLM 服务（见上面的命令）"
echo "   - 然后运行：python run_pipeline.py --use_local_models --model_type vllm"
echo ""
echo "2. 使用 Transformers（开发测试）："
echo "   - 直接运行：python run_pipeline.py --use_local_models --model_type transformers"
echo ""
echo "3. 更新现有配置："
echo "   - 将 skywork_config_update.json 的内容合并到 config.json"