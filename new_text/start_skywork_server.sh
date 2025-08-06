#!/bin/bash

# Skywork vLLM 服务器启动脚本

echo "=== Skywork vLLM 服务器启动脚本 ==="
echo ""

# 配置参数
MODEL_PATH="/mnt/storage/models/Skywork/Skywork-R1V3-38B"
PORT=8000
GPU_MEMORY_UTILIZATION=0.9
MAX_MODEL_LEN=4096

# 检查模型文件是否存在
if [ ! -d "$MODEL_PATH" ]; then
    echo "错误: 模型路径不存在: $MODEL_PATH"
    echo "请确保模型已下载到正确的位置"
    exit 1
fi

# 检查是否已安装vLLM
if ! python -c "import vllm" 2>/dev/null; then
    echo "错误: vLLM未安装"
    echo "请运行: pip install vllm"
    exit 1
fi

# 检查端口是否被占用
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null ; then
    echo "警告: 端口 $PORT 已被占用"
    echo "尝试停止现有服务..."
    pkill -f "vllm.entrypoints.openai.api_server"
    sleep 2
fi

# 启动vLLM服务器
echo "启动Skywork模型服务器..."
echo "模型路径: $MODEL_PATH"
echo "服务端口: $PORT"
echo "GPU内存使用率: $GPU_MEMORY_UTILIZATION"
echo "最大模型长度: $MAX_MODEL_LEN"
echo ""

# 启动命令
python -m vllm.entrypoints.openai.api_server \
    --model "$MODEL_PATH" \
    --port $PORT \
    --gpu-memory-utilization $GPU_MEMORY_UTILIZATION \
    --max-model-len $MAX_MODEL_LEN \
    --trust-remote-code \
    --served-model-name "skywork" \
    --api-key "EMPTY" \
    --dtype auto \
    --max-num-seqs 256

# 注意：
# - 如果遇到内存不足，可以降低 --gpu-memory-utilization 的值
# - 如果需要更长的上下文，可以增加 --max-model-len 的值
# - 使用 --dtype half 可以减少内存使用