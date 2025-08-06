#!/bin/bash

# 智能文本QA生成系统 - 分步运行脚本
# 允许用户单独运行流水线的各个步骤

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# 打印函数
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

print_step() {
    echo -e "${CYAN}[STEP]${NC} $1"
}

# 显示菜单
show_menu() {
    echo ""
    echo "======================================"
    echo "   智能文本QA生成系统 - 分步运行"
    echo "======================================"
    echo ""
    echo "请选择要运行的步骤:"
    echo ""
    echo "  1) 文本召回与提取 (text_retrieval)"
    echo "  2) 数据清理与预处理 (data_cleaning)"
    echo "  3) QA对生成 (qa_generation)"
    echo "  4) 质量控制与筛选 (quality_control)"
    echo "  5) 运行完整流水线 (all)"
    echo ""
    echo "  6) 启动vLLM服务"
    echo "  7) 启动Ollama服务"
    echo "  8) 检查服务状态"
    echo ""
    echo "  9) 查看输出结果"
    echo "  10) 清理输出目录"
    echo "  11) 查看日志"
    echo ""
    echo "  0) 退出"
    echo ""
}

# 运行指定阶段
run_stage() {
    local stage=$1
    local stage_name=$2
    
    print_step "运行 $stage_name"
    
    # 检查配置文件
    if [ ! -f "config.json" ]; then
        print_error "配置文件 config.json 不存在"
        return 1
    fi
    
    # 运行阶段
    python run_pipeline.py --stage "$stage"
    
    if [ $? -eq 0 ]; then
        print_success "$stage_name 完成"
    else
        print_error "$stage_name 失败"
        return 1
    fi
}

# 启动vLLM服务
start_vllm() {
    print_info "启动vLLM服务..."
    
    # 读取模型路径
    MODEL_PATH=$(python -c "import json; config=json.load(open('config.json')); print(config.get('models', {}).get('skywork', {}).get('model_path', '/mnt/storage/models/Skywork/Skywork-R1V3-38B'))")
    
    if [ ! -d "$MODEL_PATH" ]; then
        print_error "模型文件不存在: $MODEL_PATH"
        return 1
    fi
    
    # 检查是否已经运行
    if pgrep -f "vllm.entrypoints.openai.api_server" > /dev/null; then
        print_warning "vLLM服务已经在运行"
        return 0
    fi
    
    # 创建日志目录
    mkdir -p logs
    
    # 启动服务
    print_info "启动vLLM服务，模型: $MODEL_PATH"
    nohup python -m vllm.entrypoints.openai.api_server \
        --model "$MODEL_PATH" \
        --host 0.0.0.0 \
        --port 8000 \
        --tensor-parallel-size 1 \
        --gpu-memory-utilization 0.9 \
        > logs/vllm_server.log 2>&1 &
    
    VLLM_PID=$!
    echo $VLLM_PID > logs/vllm.pid
    
    print_info "等待服务启动..."
    sleep 10
    
    # 检查服务
    if curl -s http://localhost:8000/v1/models > /dev/null 2>&1; then
        print_success "vLLM服务启动成功 (PID: $VLLM_PID)"
        echo "日志文件: logs/vllm_server.log"
    else
        print_error "vLLM服务启动失败"
        echo "请查看日志: tail -f logs/vllm_server.log"
        return 1
    fi
}

# 启动Ollama服务
start_ollama() {
    print_info "启动Ollama服务..."
    
    # 检查Ollama是否安装
    if ! command -v ollama &> /dev/null; then
        print_error "Ollama未安装"
        echo "请先安装Ollama:"
        echo "  curl -fsSL https://ollama.ai/install.sh | sh"
        return 1
    fi
    
    # 检查是否已经运行
    if pgrep -f "ollama serve" > /dev/null; then
        print_warning "Ollama服务已经在运行"
        return 0
    fi
    
    # 启动服务
    nohup ollama serve > logs/ollama_server.log 2>&1 &
    OLLAMA_PID=$!
    echo $OLLAMA_PID > logs/ollama.pid
    
    print_info "等待服务启动..."
    sleep 5
    
    # 检查服务
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        print_success "Ollama服务启动成功 (PID: $OLLAMA_PID)"
        
        # 列出可用模型
        print_info "可用模型:"
        ollama list
    else
        print_error "Ollama服务启动失败"
        return 1
    fi
}

# 检查服务状态
check_services() {
    echo ""
    print_info "检查服务状态..."
    echo ""
    
    # 检查vLLM
    echo -n "vLLM服务: "
    if curl -s http://localhost:8000/v1/models > /dev/null 2>&1; then
        echo -e "${GREEN}运行中${NC}"
        if [ -f "logs/vllm.pid" ]; then
            echo "  PID: $(cat logs/vllm.pid)"
        fi
    else
        echo -e "${RED}未运行${NC}"
    fi
    
    # 检查Ollama
    echo -n "Ollama服务: "
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo -e "${GREEN}运行中${NC}"
        if [ -f "logs/ollama.pid" ]; then
            echo "  PID: $(cat logs/ollama.pid)"
        fi
    else
        echo -e "${RED}未运行${NC}"
    fi
    
    # 检查GPU状态
    echo ""
    if command -v nvidia-smi &> /dev/null; then
        print_info "GPU状态:"
        nvidia-smi --query-gpu=name,memory.used,memory.total,utilization.gpu --format=csv,noheader,nounits | \
        awk -F', ' '{printf "  %s: %s/%s MB (GPU利用率: %s%%)\n", $1, $2, $3, $4}'
    fi
}

# 查看输出结果
view_results() {
    echo ""
    print_info "输出结果统计:"
    echo ""
    
    # 检查各个输出目录
    if [ -d "data/output/retrieved" ]; then
        RETRIEVED_COUNT=$(find data/output/retrieved -name "*.txt" 2>/dev/null | wc -l)
        echo "提取的文本文件: $RETRIEVED_COUNT"
    fi
    
    if [ -d "data/output/cleaned" ]; then
        CLEANED_COUNT=$(find data/output/cleaned -name "*.txt" 2>/dev/null | wc -l)
        echo "清理后的文本文件: $CLEANED_COUNT"
    fi
    
    if [ -d "data/output/qa_pairs" ]; then
        QA_FILES=$(find data/output/qa_pairs -name "*.json" 2>/dev/null | wc -l)
        if [ $QA_FILES -gt 0 ]; then
            QA_COUNT=$(find data/output/qa_pairs -name "*.json" -exec grep -c '"question"' {} \; | awk '{sum+=$1} END {print sum}')
            echo "生成的QA对: ${QA_COUNT:-0} (在 $QA_FILES 个文件中)"
        else
            echo "生成的QA对: 0"
        fi
    fi
    
    if [ -f "data/output/quality/quality_report.json" ]; then
        echo ""
        print_info "质量报告:"
        python -c "
import json
with open('data/output/quality/quality_report.json', 'r') as f:
    report = json.load(f)
    print(f'  总QA对数: {report.get(\"total_count\", 0)}')
    print(f'  通过质量检查: {report.get(\"passed_count\", 0)}')
    print(f'  平均质量分数: {report.get(\"average_score\", 0):.2f}')
"
    fi
    
    echo ""
    read -p "是否查看示例QA对？(y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # 查找第一个QA文件
        QA_FILE=$(find data/output/qa_pairs -name "*.json" 2>/dev/null | head -1)
        if [ -n "$QA_FILE" ]; then
            echo ""
            print_info "示例QA对 (来自 $QA_FILE):"
            python -c "
import json
with open('$QA_FILE', 'r') as f:
    data = json.load(f)
    qa_pairs = data.get('qa_pairs', [])[:2]  # 显示前2个
    for i, qa in enumerate(qa_pairs, 1):
        print(f'\n示例 {i}:')
        print(f'问题: {qa.get(\"question\", \"\")}')
        print(f'答案: {qa.get(\"answer\", \"\")[:200]}...' if len(qa.get('answer', '')) > 200 else f'答案: {qa.get(\"answer\", \"\")}')
"
        fi
    fi
}

# 清理输出目录
clean_output() {
    print_warning "清理输出目录将删除所有生成的文件！"
    read -p "确定要继续吗？(y/n) " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf data/output/*
        rm -rf data/temp/*
        mkdir -p data/output/{retrieved,cleaned,qa_pairs,quality,final}
        mkdir -p data/temp
        print_success "输出目录已清理"
    else
        print_info "取消清理"
    fi
}

# 查看日志
view_logs() {
    echo ""
    print_info "可用日志文件:"
    echo ""
    
    logs=(
        "logs/pipeline.log:主流水线日志"
        "logs/vllm_server.log:vLLM服务日志"
        "logs/ollama_server.log:Ollama服务日志"
        "TextGeneration/logs/:文本生成日志"
    )
    
    for i in "${!logs[@]}"; do
        IFS=':' read -r file desc <<< "${logs[$i]}"
        if [ -f "$file" ] || [ -d "$file" ]; then
            echo "  $((i+1))) $desc ($file)"
        fi
    done
    
    echo "  0) 返回主菜单"
    echo ""
    read -p "选择要查看的日志 (输入数字): " choice
    
    case $choice in
        1)
            if [ -f "logs/pipeline.log" ]; then
                tail -f logs/pipeline.log
            else
                print_error "日志文件不存在"
            fi
            ;;
        2)
            if [ -f "logs/vllm_server.log" ]; then
                tail -f logs/vllm_server.log
            else
                print_error "日志文件不存在"
            fi
            ;;
        3)
            if [ -f "logs/ollama_server.log" ]; then
                tail -f logs/ollama_server.log
            else
                print_error "日志文件不存在"
            fi
            ;;
        4)
            if [ -d "TextGeneration/logs" ]; then
                latest_log=$(ls -t TextGeneration/logs/*.log 2>/dev/null | head -1)
                if [ -n "$latest_log" ]; then
                    tail -f "$latest_log"
                else
                    print_error "没有找到日志文件"
                fi
            else
                print_error "日志目录不存在"
            fi
            ;;
        0)
            return
            ;;
        *)
            print_error "无效选择"
            ;;
    esac
}

# 主循环
main() {
    while true; do
        show_menu
        read -p "请输入选择 (0-11): " choice
        
        case $choice in
            1)
                run_stage "text_retrieval" "文本召回与提取"
                ;;
            2)
                run_stage "data_cleaning" "数据清理与预处理"
                ;;
            3)
                run_stage "qa_generation" "QA对生成"
                ;;
            4)
                run_stage "quality_control" "质量控制与筛选"
                ;;
            5)
                print_info "运行完整流水线..."
                ./run_all.sh
                ;;
            6)
                start_vllm
                ;;
            7)
                start_ollama
                ;;
            8)
                check_services
                ;;
            9)
                view_results
                ;;
            10)
                clean_output
                ;;
            11)
                view_logs
                ;;
            0)
                print_info "退出程序"
                exit 0
                ;;
            *)
                print_error "无效选择，请输入 0-11"
                ;;
        esac
        
        echo ""
        read -p "按回车键继续..." -n 1 -r
    done
}

# 运行主程序
main