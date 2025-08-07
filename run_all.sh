#!/bin/bash
# 智能文本QA生成系统 - 一键运行脚本
# 此脚本将运行完整的QA生成流水线

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 打印带颜色的信息
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# 检查Python环境
check_python() {
    if ! command -v python3 &> /dev/null; then
        print_error "Python3 未安装！请先安装Python 3.8或更高版本。"
        exit 1
    fi
    
    python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    print_info "检测到Python版本: $python_version"
}

# 检查依赖
check_dependencies() {
    print_info "检查系统依赖..."
    
    # 检查必要的Python包
    missing_packages=()
    
    for package in openai asyncio json logging pathlib; do
        if ! python3 -c "import $package" 2>/dev/null; then
            missing_packages+=($package)
        fi
    done
    
    if [ ${#missing_packages[@]} -ne 0 ]; then
        print_warning "缺少以下Python包: ${missing_packages[*]}"
        print_info "正在安装缺失的包..."
        pip install -r requirements.txt
    else
        print_info "所有依赖已满足"
    fi
}

# 检查本地模型服务
check_local_models() {
    print_info "检查本地模型服务..."
    
    # 读取配置文件中的设置
    use_local=$(python3 -c "import json; config=json.load(open('config.json')); print(config['api']['use_local_models'])")
    
    if [ "$use_local" = "True" ]; then
        print_info "已启用本地模型支持"
        
        # 检查vLLM服务
        vllm_enabled=$(python3 -c "import json; config=json.load(open('config.json')); print(config['models']['local_models']['vllm']['enabled'])")
        if [ "$vllm_enabled" = "True" ]; then
            vllm_url=$(python3 -c "import json; config=json.load(open('config.json')); print(config['models']['local_models']['vllm']['base_url'])")
            if curl -s "$vllm_url/health" > /dev/null 2>&1; then
                print_info "vLLM服务运行正常"
            else
                print_warning "vLLM服务未运行，尝试启动..."
                # 这里可以添加启动vLLM的命令
                print_warning "请手动启动vLLM服务或使用其他模型后端"
            fi
        fi
    else
        print_info "使用API模式"
    fi
}

# 创建必要的目录
setup_directories() {
    print_info "创建必要的目录结构..."
    
    directories=(
        "data/pdfs"
        "data/texts"
        "data/input"
        "data/output"
        "data/retrieved"
        "data/cleaned"
        "data/qa_results"
        "data/quality_checked"
        "data/final_output"
        "logs"
        "temp/cache"
    )
    
    for dir in "${directories[@]}"; do
        mkdir -p "$dir"
    done
    
    print_info "目录结构创建完成"
}

# 运行流水线
run_pipeline() {
    print_info "开始运行QA生成流水线..."
    
    # 设置默认参数
    CONFIG_FILE="${CONFIG_FILE:-config.json}"
    INPUT_DIR="${INPUT_DIR:-data/pdfs}"
    STAGES="${STAGES:-all}"
    
    print_info "配置文件: $CONFIG_FILE"
    print_info "输入目录: $INPUT_DIR"
    print_info "运行阶段: $STAGES"
    
    # 检查输入目录
    if [ ! -d "$INPUT_DIR" ]; then
        print_error "输入目录不存在: $INPUT_DIR"
        exit 1
    fi
    
    # 检查是否有输入文件
    file_count=$(find "$INPUT_DIR" -type f \( -name "*.pdf" -o -name "*.txt" \) | wc -l)
    if [ "$file_count" -eq 0 ]; then
        print_warning "输入目录中没有找到PDF或文本文件"
        print_info "请将要处理的文件放入: $INPUT_DIR"
        exit 1
    fi
    
    print_info "找到 $file_count 个待处理文件"
    
    # 运行Python脚本
    python3 run_pipeline.py \
        --config "$CONFIG_FILE" \
        --input_dir "$INPUT_DIR" \
        --stages "$STAGES" \
        2>&1 | tee logs/pipeline_$(date +%Y%m%d_%H%M%S).log
    
    # 检查运行结果
    if [ ${PIPESTATUS[0]} -eq 0 ]; then
        print_info "流水线运行成功！"
        
        # 显示结果统计
        if [ -f "data/final_output/pipeline_report.json" ]; then
            print_info "生成报告:"
            python3 -c "
import json
report = json.load(open('data/final_output/pipeline_report.json'))
print(f\"  - 总QA对数: {report.get('total_qa_pairs', 0)}\")
print(f\"  - 质量通过率: {report.get('quality_pass_rate', 0):.2%}\")
print(f\"  - 处理时间: {report.get('total_duration', 0):.1f}秒\")
"
        fi
    else
        print_error "流水线运行失败！请查看日志文件。"
        exit 1
    fi
}

# 显示使用帮助
show_help() {
    echo "智能文本QA生成系统 - 一键运行脚本"
    echo ""
    echo "使用方法:"
    echo "  ./run_all.sh [选项]"
    echo ""
    echo "选项:"
    echo "  -h, --help          显示帮助信息"
    echo "  -c, --config FILE   指定配置文件 (默认: config.json)"
    echo "  -i, --input DIR     指定输入目录 (默认: data/pdfs)"
    echo "  -s, --stages STAGES 指定运行阶段 (默认: all)"
    echo "                      可选: all, text_retrieval, qa_generation, quality_control"
    echo "  --check-only        仅检查环境，不运行流水线"
    echo ""
    echo "示例:"
    echo "  ./run_all.sh                          # 使用默认配置运行"
    echo "  ./run_all.sh -i data/texts            # 处理文本文件"
    echo "  ./run_all.sh -s qa_generation         # 仅运行QA生成阶段"
    echo "  ./run_all.sh --check-only             # 仅检查环境"
}

# 主函数
main() {
    print_info "智能文本QA生成系统 v2.0"
    print_info "================================"
    
    # 解析命令行参数
    CHECK_ONLY=false
    
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
            -i|--input)
                INPUT_DIR="$2"
                shift 2
                ;;
            -s|--stages)
                STAGES="$2"
                shift 2
                ;;
            --check-only)
                CHECK_ONLY=true
                shift
                ;;
            *)
                print_error "未知选项: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # 执行检查
    check_python
    check_dependencies
    setup_directories
    check_local_models
    
    if [ "$CHECK_ONLY" = true ]; then
        print_info "环境检查完成！"
        exit 0
    fi
    
    # 运行流水线
    run_pipeline
    
    print_info "================================"
    print_info "所有任务完成！"
    print_info "输出文件位于: data/final_output/"
}

# 运行主函数
main "$@"