#!/bin/bash

# 智能文本QA生成系统 - 本地模型运行脚本

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

# 显示菜单
show_menu() {
    echo ""
    echo "==================================="
    echo "  智能文本QA生成系统 - 本地模型版"
    echo "==================================="
    echo ""
    echo "请选择运行模式："
    echo ""
    echo "  1) 一键运行（运行所有阶段）"
    echo "  2) 分步运行"
    echo "  3) 启动Skywork模型服务"
    echo "  4) 启动Ollama服务"
    echo "  5) 检查系统状态"
    echo "  6) 清理输出文件"
    echo "  0) 退出"
    echo ""
}

# 检查Python环境
check_python() {
    if ! command -v python &> /dev/null; then
        print_error "Python未安装"
        return 1
    fi
    
    python_version=$(python -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    print_info "Python版本: $python_version"
    return 0
}

# 检查依赖
check_dependencies() {
    print_info "检查系统依赖..."
    
    # 检查Python
    if ! check_python; then
        return 1
    fi
    
    # 检查必要的Python包
    missing_packages=""
    for package in "openai" "asyncio" "aiohttp" "requests"; do
        if ! python -c "import $package" 2>/dev/null; then
            missing_packages="$missing_packages $package"
        fi
    done
    
    if [ -n "$missing_packages" ]; then
        print_warning "缺少Python包:$missing_packages"
        print_info "请运行: pip install -r requirements.txt"
        return 1
    fi
    
    print_success "依赖检查通过"
    return 0
}

# 检查模型服务状态
check_model_services() {
    print_info "检查模型服务状态..."
    
    # 检查Skywork/vLLM服务
    if curl -s http://localhost:8000/v1/models > /dev/null 2>&1; then
        print_success "Skywork/vLLM服务运行中 (端口 8000)"
        skywork_status=1
    else
        print_warning "Skywork/vLLM服务未运行"
        skywork_status=0
    fi
    
    # 检查Ollama服务
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        print_success "Ollama服务运行中 (端口 11434)"
        ollama_status=1
    else
        print_warning "Ollama服务未运行"
        ollama_status=0
    fi
    
    if [ $skywork_status -eq 0 ] && [ $ollama_status -eq 0 ]; then
        print_error "没有可用的模型服务"
        print_info "请先启动Skywork或Ollama服务"
        return 1
    fi
    
    return 0
}

# 创建必要的目录
create_directories() {
    print_info "创建必要的目录..."
    
    directories=(
        "data/pdfs"
        "data/texts"
        "output/qa_pairs"
        "output/quality_checked"
        "output/rewritten"
        "logs"
    )
    
    for dir in "${directories[@]}"; do
        mkdir -p "$dir"
    done
    
    print_success "目录创建完成"
}

# 一键运行所有阶段
run_all_stages() {
    print_info "开始一键运行所有阶段..."
    
    # 检查依赖和服务
    if ! check_dependencies; then
        return 1
    fi
    
    if ! check_model_services; then
        return 1
    fi
    
    # 创建目录
    create_directories
    
    # 运行pipeline
    print_info "启动完整流水线..."
    python run_pipeline.py
    
    if [ $? -eq 0 ]; then
        print_success "所有阶段运行完成！"
        print_info "输出文件位于 output/ 目录"
    else
        print_error "运行过程中出现错误"
        return 1
    fi
}

# 分步运行菜单
run_step_by_step() {
    while true; do
        echo ""
        echo "--- 分步运行菜单 ---"
        echo "1) 文本召回 (text_retrieval)"
        echo "2) QA生成 (qa_generation)"
        echo "3) 质量检查 (quality_check)"
        echo "4) 数据改写 (rewrite_enhancement)"
        echo "5) 运行指定阶段组合"
        echo "0) 返回主菜单"
        echo ""
        read -p "请选择: " step_choice
        
        case $step_choice in
            1)
                print_info "运行文本召回阶段..."
                python run_pipeline.py --stage text_retrieval
                ;;
            2)
                print_info "运行QA生成阶段..."
                python run_pipeline.py --stage qa_generation
                ;;
            3)
                print_info "运行质量检查阶段..."
                python run_pipeline.py --stage quality_check
                ;;
            4)
                print_info "运行数据改写阶段..."
                python run_pipeline.py --stage rewrite_enhancement
                ;;
            5)
                read -p "输入要运行的阶段（用逗号分隔）: " stages
                print_info "运行阶段: $stages"
                python run_pipeline.py --stages "$stages"
                ;;
            0)
                break
                ;;
            *)
                print_error "无效选择"
                ;;
        esac
    done
}

# 启动Skywork服务
start_skywork_service() {
    print_info "启动Skywork vLLM服务..."
    
    if [ -f "start_skywork_server.sh" ]; then
        chmod +x start_skywork_server.sh
        ./start_skywork_server.sh
    else
        print_error "找不到 start_skywork_server.sh"
        print_info "手动启动命令："
        echo "python -m vllm.entrypoints.openai.api_server \\"
        echo "    --model /mnt/storage/models/Skywork/Skywork-R1V3-38B \\"
        echo "    --port 8000 \\"
        echo "    --gpu-memory-utilization 0.9"
    fi
}

# 启动Ollama服务
start_ollama_service() {
    print_info "启动Ollama服务..."
    
    # 检查Ollama是否安装
    if ! command -v ollama &> /dev/null; then
        print_error "Ollama未安装"
        print_info "请运行: curl -fsSL https://ollama.com/install.sh | sh"
        return 1
    fi
    
    # 启动Ollama
    print_info "在后台启动Ollama服务..."
    nohup ollama serve > logs/ollama.log 2>&1 &
    
    sleep 3
    
    # 检查是否启动成功
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        print_success "Ollama服务启动成功"
        
        # 检查是否有模型
        models=$(ollama list 2>/dev/null | grep -v "NAME" | wc -l)
        if [ "$models" -eq 0 ]; then
            print_warning "没有安装任何模型"
            print_info "推荐安装: ollama pull qwen:14b"
        fi
    else
        print_error "Ollama服务启动失败"
        return 1
    fi
}

# 检查系统状态
check_system_status() {
    echo ""
    echo "=== 系统状态检查 ==="
    echo ""
    
    # 检查Python
    check_python
    
    # 检查GPU
    if command -v nvidia-smi &> /dev/null; then
        print_info "GPU信息:"
        nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader
    else
        print_warning "未检测到NVIDIA GPU"
    fi
    
    # 检查模型服务
    check_model_services
    
    # 检查数据目录
    print_info "数据目录状态:"
    if [ -d "data/pdfs" ]; then
        pdf_count=$(find data/pdfs -name "*.pdf" 2>/dev/null | wc -l)
        print_info "PDF文件数量: $pdf_count"
    fi
    
    if [ -d "data/texts" ]; then
        text_count=$(find data/texts -name "*.txt" 2>/dev/null | wc -l)
        print_info "文本文件数量: $text_count"
    fi
    
    # 检查输出目录
    if [ -d "output" ]; then
        print_info "输出目录内容:"
        ls -la output/
    fi
}

# 清理输出文件
clean_output() {
    print_warning "即将清理所有输出文件..."
    read -p "确定要继续吗？(y/N) " confirm
    
    if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
        rm -rf output/*
        rm -rf logs/*
        print_success "输出文件已清理"
    else
        print_info "取消清理操作"
    fi
}

# 主循环
main() {
    # 检查是否在正确的目录
    if [ ! -f "run_pipeline.py" ]; then
        print_error "请在项目根目录运行此脚本"
        exit 1
    fi
    
    while true; do
        show_menu
        read -p "请输入选择: " choice
        
        case $choice in
            1)
                run_all_stages
                ;;
            2)
                run_step_by_step
                ;;
            3)
                start_skywork_service
                ;;
            4)
                start_ollama_service
                ;;
            5)
                check_system_status
                ;;
            6)
                clean_output
                ;;
            0)
                print_info "退出程序"
                exit 0
                ;;
            *)
                print_error "无效的选择，请重试"
                ;;
        esac
        
        echo ""
        read -p "按Enter键继续..."
    done
}

# 运行主程序
main