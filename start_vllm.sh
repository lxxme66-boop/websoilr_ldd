#!/bin/bash
# 启动vLLM服务器脚本

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# 默认参数
MODEL_PATH="/mnt/storage/models/Skywork/Skywork-R1V3-38B"
PORT=8000
GPU_MEMORY=0.9
MAX_MODEL_LEN=32768
TENSOR_PARALLEL=1

# 显示帮助
show_help() {
    echo "vLLM服务启动脚本"
    echo ""
    echo "使用方法:"
    echo "  ./start_vllm.sh [选项]"
    echo ""
    echo "选项:"
    echo "  -m, --model PATH        模型路径 (默认: $MODEL_PATH)"
    echo "  -p, --port PORT         服务端口 (默认: $PORT)"
    echo "  -g, --gpu-memory FRAC   GPU内存使用率 (默认: $GPU_MEMORY)"
    echo "  -l, --max-len LENGTH    最大序列长度 (默认: $MAX_MODEL_LEN)"
    echo "  -t, --tensor-parallel N 张量并行数 (默认: $TENSOR_PARALLEL)"
    echo "  -h, --help              显示帮助信息"
    echo ""
    echo "示例:"
    echo "  ./start_vllm.sh                    # 使用默认设置"
    echo "  ./start_vllm.sh -p 8080            # 使用8080端口"
    echo "  ./start_vllm.sh -g 0.8 -t 2        # 使用80% GPU内存，2卡并行"
}

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        -m|--model)
            MODEL_PATH="$2"
            shift 2
            ;;
        -p|--port)
            PORT="$2"
            shift 2
            ;;
        -g|--gpu-memory)
            GPU_MEMORY="$2"
            shift 2
            ;;
        -l|--max-len)
            MAX_MODEL_LEN="$2"
            shift 2
            ;;
        -t|--tensor-parallel)
            TENSOR_PARALLEL="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            print_error "未知选项: $1"
            show_help
            exit 1
            ;;
    esac
done

# 检查模型路径
if [ ! -d "$MODEL_PATH" ]; then
    print_error "模型路径不存在: $MODEL_PATH"
    exit 1
fi

# 检查vLLM是否安装
if ! python3 -c "import vllm" 2>/dev/null; then
    print_error "vLLM未安装！"
    print_info "请运行: pip install vllm"
    exit 1
fi

# 检查端口是否被占用
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    print_warning "端口 $PORT 已被占用"
    echo -n "是否要终止占用该端口的进程？[y/N]: "
    read confirm
    if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
        kill $(lsof -Pi :$PORT -sTCP:LISTEN -t)
        sleep 2
    else
        print_error "请选择其他端口或手动停止占用端口的进程"
        exit 1
    fi
fi

# 显示配置信息
print_info "vLLM服务配置:"
echo "  模型路径: $MODEL_PATH"
echo "  服务端口: $PORT"
echo "  GPU内存使用率: $GPU_MEMORY"
echo "  最大序列长度: $MAX_MODEL_LEN"
echo "  张量并行数: $TENSOR_PARALLEL"

# 启动vLLM服务
print_info "正在启动vLLM服务..."

python3 -m vllm.entrypoints.openai.api_server \
    --model "$MODEL_PATH" \
    --port $PORT \
    --gpu-memory-utilization $GPU_MEMORY \
    --max-model-len $MAX_MODEL_LEN \
    --tensor-parallel-size $TENSOR_PARALLEL \
    --trust-remote-code \
    --served-model-name "skywork-38b" \
    --api-key "EMPTY" \
    2>&1 | tee logs/vllm_$(date +%Y%m%d_%H%M%S).log