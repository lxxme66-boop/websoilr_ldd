#!/bin/bash

# 智能文本QA生成系统 - 一键运行脚本
# 自动执行完整的QA生成流程

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 显示帮助信息
show_help() {
    echo "智能文本QA生成系统 - 一键运行脚本"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -h, --help              显示帮助信息"
    echo "  -c, --config FILE       指定配置文件 (默认: config.json)"
    echo "  -m, --model TYPE        模型类型 (skywork/ollama/api)"
    echo "  -s, --skip-check        跳过环境检查"
    echo "  -d, --debug             开启调试模式"
    echo "  -p, --parallel NUM      并发数 (默认: 20)"
    echo "  --vllm                  启动vLLM服务"
    echo "  --clean                 清理输出目录"
    echo ""
    echo "示例:"
    echo "  $0                      # 使用默认配置运行"
    echo "  $0 -m skywork --vllm    # 使用Skywork模型并启动vLLM"
    echo "  $0 -c custom.json       # 使用自定义配置文件"
}

# 默认参数
CONFIG_FILE="config.json"
MODEL_TYPE=""
SKIP_CHECK=false
DEBUG_MODE=false
PARALLEL_NUM=20
START_VLLM=false
CLEAN_OUTPUT=false

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -c|--config)
            CONFIG_FILE="$2"
            shift 2
            ;;
        -m|--model)
            MODEL_TYPE="$2"
            shift 2
            ;;
        -s|--skip-check)
            SKIP_CHECK=true
            shift
            ;;
        -d|--debug)
            DEBUG_MODE=true
            shift
            ;;
        -p|--parallel)
            PARALLEL_NUM="$2"
            shift 2
            ;;
        --vllm)
            START_VLLM=true
            shift
            ;;
        --clean)
            CLEAN_OUTPUT=true
            shift
            ;;
        *)
            print_error "未知选项: $1"
            show_help
            exit 1
            ;;
    esac
done

# 检查Python环境
check_python_env() {
    print_info "检查Python环境..."
    
    if ! command -v python &> /dev/null; then
        print_error "未找到Python，请先安装Python 3.8+"
        exit 1
    fi
    
    PYTHON_VERSION=$(python -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    print_info "Python版本: $PYTHON_VERSION"
    
    # 检查虚拟环境
    if [[ -z "$VIRTUAL_ENV" ]]; then
        print_warning "未激活虚拟环境，建议在虚拟环境中运行"
        echo "运行以下命令创建并激活虚拟环境:"
        echo "  python -m venv venv"
        echo "  source venv/bin/activate"
        read -p "是否继续？(y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

# 检查依赖
check_dependencies() {
    print_info "检查依赖包..."
    
    # 检查requirements.txt是否存在
    if [ ! -f "requirements.txt" ]; then
        print_error "未找到requirements.txt文件"
        exit 1
    fi
    
    # 检查关键包是否安装
    python -c "import torch" 2>/dev/null || {
        print_warning "PyTorch未安装，正在安装..."
        pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
    }
    
    python -c "import openai" 2>/dev/null || {
        print_warning "OpenAI包未安装，正在安装..."
        pip install openai
    }
}

# 检查模型服务
check_model_service() {
    print_info "检查模型服务..."
    
    # 读取配置文件中的模型类型
    if [ -z "$MODEL_TYPE" ]; then
        MODEL_TYPE=$(python -c "import json; config=json.load(open('$CONFIG_FILE')); print(config.get('api', {}).get('local_model_type', 'ollama'))")
    fi
    
    print_info "使用模型类型: $MODEL_TYPE"
    
    case $MODEL_TYPE in
        skywork)
            # 检查vLLM服务
            if curl -s http://localhost:8000/v1/models > /dev/null 2>&1; then
                print_success "vLLM服务已运行"
            else
                if [ "$START_VLLM" = true ]; then
                    print_info "启动vLLM服务..."
                    start_vllm_service
                else
                    print_warning "vLLM服务未运行，请手动启动或使用 --vllm 选项"
                fi
            fi
            ;;
        ollama)
            # 检查Ollama服务
            if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
                print_success "Ollama服务已运行"
            else
                print_warning "Ollama服务未运行，请先启动: ollama serve"
            fi
            ;;
        api)
            print_info "使用API模型，跳过本地服务检查"
            ;;
        *)
            print_warning "未知的模型类型: $MODEL_TYPE"
            ;;
    esac
}

# 启动vLLM服务
start_vllm_service() {
    print_info "启动vLLM服务..."
    
    # 读取模型路径
    MODEL_PATH=$(python -c "import json; config=json.load(open('$CONFIG_FILE')); print(config.get('models', {}).get('skywork', {}).get('model_path', '/mnt/storage/models/Skywork/Skywork-R1V3-38B'))")
    
    # 检查模型文件是否存在
    if [ ! -d "$MODEL_PATH" ]; then
        print_error "模型文件不存在: $MODEL_PATH"
        exit 1
    fi
    
    # 启动vLLM服务（后台运行）
    nohup python -m vllm.entrypoints.openai.api_server \
        --model "$MODEL_PATH" \
        --host 0.0.0.0 \
        --port 8000 \
        --tensor-parallel-size 1 \
        --gpu-memory-utilization 0.9 \
        > logs/vllm_server.log 2>&1 &
    
    VLLM_PID=$!
    echo $VLLM_PID > logs/vllm.pid
    
    print_info "等待vLLM服务启动..."
    sleep 10
    
    # 检查服务是否成功启动
    if curl -s http://localhost:8000/v1/models > /dev/null 2>&1; then
        print_success "vLLM服务启动成功 (PID: $VLLM_PID)"
    else
        print_error "vLLM服务启动失败，请查看日志: logs/vllm_server.log"
        exit 1
    fi
}

# 创建必要的目录
create_directories() {
    print_info "创建必要的目录..."
    
    directories=(
        "data/pdfs"
        "data/texts"
        "data/output/retrieved"
        "data/output/cleaned"
        "data/output/qa_pairs"
        "data/output/quality"
        "data/output/final"
        "data/temp"
        "logs"
        "TextGeneration/logs"
    )
    
    for dir in "${directories[@]}"; do
        mkdir -p "$dir"
    done
    
    print_success "目录创建完成"
}

# 清理输出目录
clean_output() {
    print_info "清理输出目录..."
    
    read -p "确定要清理所有输出文件吗？(y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf data/output/*
        rm -rf data/temp/*
        rm -rf logs/*
        create_directories
        print_success "输出目录已清理"
    else
        print_info "取消清理"
    fi
}

# 检查输入文件
check_input_files() {
    print_info "检查输入文件..."
    
    PDF_COUNT=$(find data/pdfs -name "*.pdf" 2>/dev/null | wc -l)
    TXT_COUNT=$(find data/texts -name "*.txt" 2>/dev/null | wc -l)
    
    print_info "找到 $PDF_COUNT 个PDF文件，$TXT_COUNT 个文本文件"
    
    if [ $PDF_COUNT -eq 0 ] && [ $TXT_COUNT -eq 0 ]; then
        print_warning "未找到任何输入文件"
        echo "请将PDF文件放入 data/pdfs/ 目录"
        echo "或将文本文件放入 data/texts/ 目录"
        exit 1
    fi
}

# 运行流水线步骤
run_pipeline_stage() {
    local stage=$1
    local stage_name=$2
    
    print_info "运行阶段: $stage_name"
    
    if [ "$DEBUG_MODE" = true ]; then
        python run_pipeline.py --stage "$stage" --config "$CONFIG_FILE" --max-concurrent "$PARALLEL_NUM" --debug
    else
        python run_pipeline.py --stage "$stage" --config "$CONFIG_FILE" --max-concurrent "$PARALLEL_NUM"
    fi
    
    if [ $? -eq 0 ]; then
        print_success "$stage_name 完成"
    else
        print_error "$stage_name 失败"
        exit 1
    fi
}

# 主函数
main() {
    echo "======================================"
    echo "   智能文本QA生成系统 - 一键运行"
    echo "======================================"
    echo ""
    
    # 环境检查
    if [ "$SKIP_CHECK" = false ]; then
        check_python_env
        check_dependencies
    fi
    
    # 创建目录
    create_directories
    
    # 清理输出（如果指定）
    if [ "$CLEAN_OUTPUT" = true ]; then
        clean_output
    fi
    
    # 检查输入文件
    check_input_files
    
    # 检查模型服务
    check_model_service
    
    # 记录开始时间
    START_TIME=$(date +%s)
    
    print_info "开始运行完整流水线..."
    echo ""
    
    # 运行各个阶段
    run_pipeline_stage "text_retrieval" "文本召回与提取"
    echo ""
    
    run_pipeline_stage "data_cleaning" "数据清理与预处理"
    echo ""
    
    run_pipeline_stage "qa_generation" "QA对生成"
    echo ""
    
    run_pipeline_stage "quality_control" "质量控制与筛选"
    echo ""
    
    # 计算总耗时
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))
    MINUTES=$((DURATION / 60))
    SECONDS=$((DURATION % 60))
    
    echo ""
    echo "======================================"
    print_success "所有流程执行完成！"
    print_info "总耗时: ${MINUTES}分${SECONDS}秒"
    echo ""
    
    # 显示结果统计
    print_info "结果统计:"
    
    # 统计生成的QA对数量
    QA_COUNT=$(find data/output/qa_pairs -name "*.json" -exec grep -c '"question"' {} \; | awk '{sum+=$1} END {print sum}')
    print_info "生成QA对数量: ${QA_COUNT:-0}"
    
    # 统计通过质量控制的数量
    if [ -f "data/output/quality/quality_report.json" ]; then
        PASSED_COUNT=$(python -c "import json; report=json.load(open('data/output/quality/quality_report.json')); print(report.get('passed_count', 0))")
        print_info "通过质量控制: ${PASSED_COUNT:-0}"
    fi
    
    echo ""
    print_info "输出文件位置:"
    echo "  - 提取的文本: data/output/retrieved/"
    echo "  - 清理后文本: data/output/cleaned/"
    echo "  - 生成的QA对: data/output/qa_pairs/"
    echo "  - 质量报告: data/output/quality/"
    echo "  - 最终结果: data/output/final/"
    echo ""
    
    # 如果启动了vLLM服务，提示如何关闭
    if [ -f "logs/vllm.pid" ]; then
        VLLM_PID=$(cat logs/vllm.pid)
        print_info "vLLM服务运行中 (PID: $VLLM_PID)"
        echo "使用以下命令关闭vLLM服务:"
        echo "  kill $VLLM_PID"
    fi
}

# 运行主函数
main