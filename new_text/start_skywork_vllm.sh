#!/bin/bash

# Skywork vLLM服务启动脚本

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 默认配置
MODEL_PATH="/mnt/storage/models/Skywork/Skywork-R1V3-38B"
PORT=8000
HOST="0.0.0.0"
GPU_MEMORY_UTILIZATION=0.9
TENSOR_PARALLEL_SIZE=1

# 打印信息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# 显示帮助
show_help() {
    echo "Skywork vLLM服务启动脚本"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -h, --help                  显示帮助信息"
    echo "  -m, --model PATH            模型路径 (默认: $MODEL_PATH)"
    echo "  -p, --port PORT             服务端口 (默认: $PORT)"
    echo "  --host HOST                 服务地址 (默认: $HOST)"
    echo "  --gpu-memory FRACTION       GPU显存使用率 (默认: $GPU_MEMORY_UTILIZATION)"
    echo "  --tensor-parallel SIZE      张量并行大小 (默认: $TENSOR_PARALLEL_SIZE)"
    echo "  --stop                      停止vLLM服务"
    echo "  --status                    检查服务状态"
    echo ""
    echo "示例:"
    echo "  $0                          # 使用默认配置启动"
    echo "  $0 -p 8080                  # 在8080端口启动"
    echo "  $0 --gpu-memory 0.8         # 使用80%的GPU显存"
    echo "  $0 --stop                   # 停止服务"
}

# 解析参数
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -m|--model)
            MODEL_PATH="$2"
            shift 2
            ;;
        -p|--port)
            PORT="$2"
            shift 2
            ;;
        --host)
            HOST="$2"
            shift 2
            ;;
        --gpu-memory)
            GPU_MEMORY_UTILIZATION="$2"
            shift 2
            ;;
        --tensor-parallel)
            TENSOR_PARALLEL_SIZE="$2"
            shift 2
            ;;
        --stop)
            STOP_SERVICE=true
            shift
            ;;
        --status)
            CHECK_STATUS=true
            shift
            ;;
        *)
            print_error "未知选项: $1"
            show_help
            exit 1
            ;;
    esac
done

# 检查服务状态
check_status() {
    if pgrep -f "vllm.entrypoints.openai.api_server" > /dev/null; then
        print_success "vLLM服务正在运行"
        if [ -f "logs/vllm.pid" ]; then
            echo "PID: $(cat logs/vllm.pid)"
        fi
        
        # 测试API
        if curl -s http://localhost:$PORT/v1/models > /dev/null 2>&1; then
            print_success "API服务正常"
            echo "服务地址: http://localhost:$PORT"
            
            # 显示加载的模型
            echo ""
            print_info "已加载的模型:"
            curl -s http://localhost:$PORT/v1/models | python -m json.tool | grep -A1 '"id"' || true
        else
            print_warning "API服务未响应"
        fi
    else
        print_info "vLLM服务未运行"
    fi
    
    # 显示GPU状态
    if command -v nvidia-smi &> /dev/null; then
        echo ""
        print_info "GPU状态:"
        nvidia-smi --query-gpu=name,memory.used,memory.total,utilization.gpu --format=csv,noheader,nounits | \
        awk -F', ' '{printf "  %s: %s/%s MB (利用率: %s%%)\n", $1, $2, $3, $4}'
    fi
}

# 停止服务
stop_service() {
    print_info "停止vLLM服务..."
    
    if pgrep -f "vllm.entrypoints.openai.api_server" > /dev/null; then
        pkill -f "vllm.entrypoints.openai.api_server"
        sleep 2
        
        if pgrep -f "vllm.entrypoints.openai.api_server" > /dev/null; then
            print_warning "服务仍在运行，强制终止..."
            pkill -9 -f "vllm.entrypoints.openai.api_server"
        fi
        
        print_success "vLLM服务已停止"
        
        # 清理PID文件
        rm -f logs/vllm.pid
    else
        print_info "vLLM服务未运行"
    fi
}

# 启动服务
start_service() {
    # 检查模型路径
    if [ ! -d "$MODEL_PATH" ]; then
        print_error "模型路径不存在: $MODEL_PATH"
        exit 1
    fi
    
    # 检查是否已运行
    if pgrep -f "vllm.entrypoints.openai.api_server" > /dev/null; then
        print_warning "vLLM服务已在运行"
        check_status
        exit 0
    fi
    
    # 检查vLLM是否安装
    if ! python -c "import vllm" 2>/dev/null; then
        print_error "vLLM未安装"
        echo "请运行: pip install vllm"
        exit 1
    fi
    
    # 创建日志目录
    mkdir -p logs
    
    # 显示配置信息
    echo ""
    print_info "启动配置:"
    echo "  模型路径: $MODEL_PATH"
    echo "  服务地址: $HOST:$PORT"
    echo "  GPU显存使用率: $GPU_MEMORY_UTILIZATION"
    echo "  张量并行大小: $TENSOR_PARALLEL_SIZE"
    echo ""
    
    # 启动服务
    print_info "启动vLLM服务..."
    
    nohup python -m vllm.entrypoints.openai.api_server \
        --model "$MODEL_PATH" \
        --host "$HOST" \
        --port "$PORT" \
        --tensor-parallel-size "$TENSOR_PARALLEL_SIZE" \
        --gpu-memory-utilization "$GPU_MEMORY_UTILIZATION" \
        --trust-remote-code \
        > logs/vllm_server.log 2>&1 &
    
    VLLM_PID=$!
    echo $VLLM_PID > logs/vllm.pid
    
    print_info "等待服务启动 (PID: $VLLM_PID)..."
    
    # 等待服务启动
    for i in {1..30}; do
        if curl -s http://localhost:$PORT/v1/models > /dev/null 2>&1; then
            echo ""
            print_success "vLLM服务启动成功！"
            echo "服务地址: http://localhost:$PORT"
            echo "日志文件: logs/vllm_server.log"
            echo ""
            echo "使用以下命令查看日志:"
            echo "  tail -f logs/vllm_server.log"
            echo ""
            echo "使用以下命令停止服务:"
            echo "  $0 --stop"
            exit 0
        fi
        echo -n "."
        sleep 2
    done
    
    echo ""
    print_error "服务启动超时"
    echo "请查看日志文件: logs/vllm_server.log"
    tail -n 20 logs/vllm_server.log
    exit 1
}

# 主逻辑
if [ "$CHECK_STATUS" = true ]; then
    check_status
elif [ "$STOP_SERVICE" = true ]; then
    stop_service
else
    start_service
fi