#!/bin/bash
# 智能QA生成系统 - 快速开始脚本
# 提供常用的运行示例和快捷命令

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 打印带颜色的信息
print_header() {
    echo -e "${CYAN}========================================${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${CYAN}========================================${NC}"
}

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

# 检查环境
check_environment() {
    print_header "检查运行环境"
    
    # 检查Python
    if command -v python3 &> /dev/null; then
        local python_version=$(python3 --version)
        print_success "Python: $python_version"
    else
        print_error "未找到Python3，请先安装Python"
        exit 1
    fi
    
    # 检查必要文件
    local required_files=("run_pipeline.py" "doubao_main_batch_inference.py" "clean_data.py")
    for file in "${required_files[@]}"; do
        if [ -f "$file" ]; then
            print_success "找到文件: $file"
        else
            print_error "缺少必要文件: $file"
            exit 1
        fi
    done
    
    # 检查配置文件
    if [ -f "config.json" ]; then
        print_success "找到配置文件: config.json"
    elif [ -f "config_templates.json" ]; then
        print_warning "未找到config.json，使用模板创建..."
        cp config_templates.json config.json
        print_info "请编辑config.json文件，设置API密钥和模型路径"
    else
        print_warning "未找到配置文件，将使用默认配置"
    fi
    
    # 创建必要目录
    local directories=("data/input" "data/output" "logs" "temp")
    for dir in "${directories[@]}"; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir"
            print_info "创建目录: $dir"
        fi
    done
    
    echo
}

# 显示主菜单
show_main_menu() {
    print_header "智能QA生成系统 - 快速开始"
    echo
    echo "请选择要执行的操作："
    echo
    echo "  1. 完整流水线处理 (推荐)"
    echo "  2. 分步骤处理"
    echo "  3. 批量处理多个目录"
    echo "  4. 质量检查现有数据"
    echo "  5. 查看示例命令"
    echo "  6. 环境检查和配置"
    echo "  7. 查看帮助文档"
    echo "  0. 退出"
    echo
}

# 完整流水线处理
run_full_pipeline() {
    print_header "完整流水线处理"
    
    # 获取用户输入
    echo "请输入以下信息："
    
    read -p "输入PDF文件夹路径 [data/input]: " input_path
    input_path=${input_path:-"data/input"}
    
    read -p "输出结果路径 [data/output]: " output_path
    output_path=${output_path:-"data/output"}
    
    echo "选择专业领域："
    echo "  1. 半导体 (semiconductor)"
    echo "  2. 光学 (optics)"
    read -p "请选择 [1]: " domain_choice
    domain_choice=${domain_choice:-1}
    
    case $domain_choice in
        1) domain="semiconductor" ;;
        2) domain="optics" ;;
        *) domain="semiconductor" ;;
    esac
    
    read -p "批处理大小 [100]: " batch_size
    batch_size=${batch_size:-100}
    
    read -p "质量阈值 [0.7]: " quality_threshold
    quality_threshold=${quality_threshold:-0.7}
    
    # 确认信息
    echo
    print_info "配置信息确认："
    print_info "- 输入路径: $input_path"
    print_info "- 输出路径: $output_path"
    print_info "- 专业领域: $domain"
    print_info "- 批处理大小: $batch_size"
    print_info "- 质量阈值: $quality_threshold"
    echo
    
    read -p "确认开始处理？ [y/N]: " confirm
    if [[ ! $confirm =~ ^[Yy]$ ]]; then
        print_info "操作已取消"
        return
    fi
    
    # 执行处理
    print_info "开始执行完整流水线..."
    
    python run_pipeline.py \
        --mode full_pipeline \
        --input_path "$input_path" \
        --output_path "$output_path" \
        --domain "$domain" \
        --batch_size "$batch_size" \
        --quality_threshold "$quality_threshold" \
        --enhanced_quality \
        --verbose
    
    if [ $? -eq 0 ]; then
        print_success "完整流水线处理完成！"
        print_info "结果保存在: $output_path"
    else
        print_error "处理过程中出现错误"
    fi
}

# 分步骤处理
run_step_by_step() {
    print_header "分步骤处理"
    
    echo "选择要执行的步骤："
    echo "  1. 数据召回"
    echo "  2. 数据清理"
    echo "  3. QA生成"
    echo "  4. 质量控制"
    echo "  0. 返回主菜单"
    
    read -p "请选择步骤 [1]: " step_choice
    step_choice=${step_choice:-1}
    
    case $step_choice in
        1) run_data_retrieval ;;
        2) run_data_cleaning ;;
        3) run_qa_generation ;;
        4) run_quality_control ;;
        0) return ;;
        *) print_error "无效选择"; return ;;
    esac
}

# 数据召回
run_data_retrieval() {
    print_info "执行数据召回..."
    
    read -p "PDF文件夹路径 [data/input]: " pdf_path
    pdf_path=${pdf_path:-"data/input"}
    
    read -p "输出文件夹 [data/retrieved]: " storage_folder
    storage_folder=${storage_folder:-"data/retrieved"}
    
    read -p "处理任务数量 [1000]: " task_number
    task_number=${task_number:-1000}
    
    python run_pipeline.py \
        --mode retrieval \
        --input_path "$pdf_path" \
        --output_path "$storage_folder" \
        --selected_task_number "$task_number" \
        --verbose
}

# 数据清理
run_data_cleaning() {
    print_info "执行数据清理..."
    
    read -p "输入pickle文件路径 [data/retrieved/total_response.pkl]: " input_file
    input_file=${input_file:-"data/retrieved/total_response.pkl"}
    
    read -p "输出文件夹 [data/cleaned]: " output_folder
    output_folder=${output_folder:-"data/cleaned"}
    
    python run_pipeline.py \
        --mode cleaning \
        --input_path "$input_file" \
        --output_path "$output_folder" \
        --verbose
}

# QA生成
run_qa_generation() {
    print_info "执行QA生成..."
    
    read -p "输入JSON文件路径 [data/cleaned/total_response.json]: " input_file
    input_file=${input_file:-"data/cleaned/total_response.json"}
    
    read -p "输出文件夹 [data/qa_results]: " output_folder
    output_folder=${output_folder:-"data/qa_results"}
    
    echo "选择专业领域："
    echo "  1. 半导体 (semiconductor)"
    echo "  2. 光学 (optics)"
    read -p "请选择 [1]: " domain_choice
    domain_choice=${domain_choice:-1}
    
    case $domain_choice in
        1) domain="semiconductor" ;;
        2) domain="optics" ;;
        *) domain="semiconductor" ;;
    esac
    
    python run_pipeline.py \
        --mode qa_generation \
        --input_path "$input_file" \
        --output_path "$output_folder" \
        --domain "$domain" \
        --enhanced_quality \
        --verbose
}

# 质量控制
run_quality_control() {
    print_info "执行质量控制..."
    
    read -p "输入QA文件路径 [data/qa_results/results_343.json]: " input_file
    input_file=${input_file:-"data/qa_results/results_343.json"}
    
    read -p "输出文件夹 [data/quality_checked]: " output_folder
    output_folder=${output_folder:-"data/quality_checked"}
    
    python run_pipeline.py \
        --mode quality_control \
        --input_path "$input_file" \
        --output_path "$output_folder" \
        --verbose
}

# 批量处理
run_batch_processing() {
    print_header "批量处理多个目录"
    
    print_info "使用批量处理脚本处理多个PDF文件夹"
    
    read -p "输入目录列表 (空格分隔) [data/pdfs1 data/pdfs2]: " input_dirs
    input_dirs=${input_dirs:-"data/pdfs1 data/pdfs2"}
    
    read -p "输出基础目录 [data/batch_results]: " output_base
    output_base=${output_base:-"data/batch_results"}
    
    read -p "并行任务数 [2]: " parallel_jobs
    parallel_jobs=${parallel_jobs:-2}
    
    # 检查批量处理脚本
    if [ ! -f "batch_process.sh" ]; then
        print_error "未找到batch_process.sh脚本"
        return
    fi
    
    # 使脚本可执行
    chmod +x batch_process.sh
    
    # 执行批量处理
    ./batch_process.sh \
        --output "$output_base" \
        --jobs "$parallel_jobs" \
        --verbose \
        $input_dirs
}

# 质量检查现有数据
check_existing_data() {
    print_header "质量检查现有数据"
    
    read -p "QA数据文件路径: " qa_file
    
    if [ ! -f "$qa_file" ]; then
        print_error "文件不存在: $qa_file"
        return
    fi
    
    print_info "开始质量检查..."
    
    python run_pipeline.py \
        --mode quality_control \
        --input_path "$qa_file" \
        --output_path "$(dirname "$qa_file")/quality_checked" \
        --verbose
}

# 显示示例命令
show_examples() {
    print_header "示例命令"
    
    cat << 'EOF'
以下是一些常用的命令示例：

1. 完整流水线处理：
   python run_pipeline.py \
       --mode full_pipeline \
       --input_path data/pdfs \
       --output_path data/results \
       --domain semiconductor

2. 只执行数据召回：
   python run_pipeline.py \
       --mode retrieval \
       --input_path data/pdfs \
       --output_path data/retrieved \
       --selected_task_number 1000

3. 数据清理：
   python run_pipeline.py \
       --mode cleaning \
       --input_path data/retrieved/total_response.pkl \
       --output_path data/cleaned

4. QA生成（半导体领域）：
   python run_pipeline.py \
       --mode qa_generation \
       --input_path data/cleaned/total_response.json \
       --output_path data/qa_results \
       --domain semiconductor \
       --enhanced_quality

5. 质量控制：
   python run_pipeline.py \
       --mode quality_control \
       --input_path data/qa_results/results_343.json \
       --output_path data/quality_checked

6. 批量处理多个目录：
   ./batch_process.sh \
       --output data/batch_results \
       --domain semiconductor \
       --jobs 3 \
       data/pdfs1 data/pdfs2 data/pdfs3

7. 试运行模式（查看配置但不执行）：
   python run_pipeline.py \
       --mode full_pipeline \
       --input_path data/pdfs \
       --output_path data/results \
       --dry_run

8. 跳过数据召回，从清理开始：
   python run_pipeline.py \
       --mode full_pipeline \
       --input_path data/pdfs \
       --output_path data/results \
       --skip_retrieval \
       --retrieved_file data/retrieved/total_response.pkl

EOF
}

# 环境检查和配置
setup_environment() {
    print_header "环境检查和配置"
    
    # 检查Python包
    print_info "检查Python依赖包..."
    
    local required_packages=("asyncio" "json" "argparse" "pathlib")
    for package in "${required_packages[@]}"; do
        if python3 -c "import $package" 2>/dev/null; then
            print_success "已安装: $package"
        else
            print_warning "缺少包: $package"
        fi
    done
    
    # 检查可选包
    print_info "检查可选依赖包..."
    local optional_packages=("PyMuPDF" "Pillow" "matplotlib")
    for package in "${optional_packages[@]}"; do
        if python3 -c "import $package" 2>/dev/null; then
            print_success "已安装: $package"
        else
            print_info "可选包未安装: $package"
        fi
    done
    
    # 配置文件设置
    if [ -f "config.json" ]; then
        print_success "配置文件存在"
        
        read -p "是否要编辑配置文件？ [y/N]: " edit_config
        if [[ $edit_config =~ ^[Yy]$ ]]; then
            if command -v nano &> /dev/null; then
                nano config.json
            elif command -v vi &> /dev/null; then
                vi config.json
            else
                print_info "请手动编辑config.json文件"
            fi
        fi
    else
        print_warning "配置文件不存在，创建默认配置..."
        cat > config.json << 'EOF'
{
  "api": {
    "ark_url": "http://0.0.0.0:8080/v1",
    "api_key": "your-api-key-here"
  },
  "models": {
    "default_model": "/mnt/storage/models/Skywork/Skywork-R1V3-38B",
    "qa_generator_model": {
      "path": "/mnt/storage/models/Skywork/Skywork-R1V3-38B",
      "type": "api"
    }
  },
  "processing": {
    "batch_size": 100,
    "max_concurrent": 20,
    "quality_threshold": 0.7,
    "selected_task_number": 1000
  },
  "domains": {
    "semiconductor": {
      "prompts": [343, 3431, 3432],
      "keywords": ["IGZO", "TFT", "OLED", "半导体"],
      "quality_criteria": "high"
    },
    "optics": {
      "prompts": [343, 3431, 3432],
      "keywords": ["光谱", "光学", "激光"],
      "quality_criteria": "high"
    }
  }
}
EOF
        print_success "已创建默认配置文件"
        print_warning "请编辑config.json文件，设置正确的API密钥和模型路径"
    fi
}

# 查看帮助文档
show_help() {
    print_header "帮助文档"
    
    cat << 'EOF'
智能QA生成系统使用指南

系统组成：
- 数据召回：从PDF文档中提取相关文本内容
- 数据清理：对提取的数据进行格式化和清理
- QA生成：基于清理后的数据生成问答对
- 质量控制：对生成的QA进行质量检查和改进

主要脚本：
- run_pipeline.py：主流水线脚本
- batch_process.sh：批量处理脚本
- quick_start.sh：快速开始脚本（当前脚本）

配置文件：
- config.json：主配置文件，包含API密钥、模型路径等

目录结构：
- data/input：输入数据目录
- data/output：输出结果目录
- logs/：日志文件目录
- temp/：临时文件目录

更多信息请查看README.md文件。
EOF
}

# 主循环
main() {
    # 检查环境
    check_environment
    
    while true; do
        show_main_menu
        read -p "请选择操作 [1]: " choice
        choice=${choice:-1}
        
        echo
        
        case $choice in
            1) run_full_pipeline ;;
            2) run_step_by_step ;;
            3) run_batch_processing ;;
            4) check_existing_data ;;
            5) show_examples ;;
            6) setup_environment ;;
            7) show_help ;;
            0) 
                print_success "感谢使用智能QA生成系统！"
                exit 0
                ;;
            *)
                print_error "无效选择，请重新输入"
                ;;
        esac
        
        echo
        read -p "按回车键继续..." 
        echo
    done
}

# 脚本入口
if [ "${BASH_SOURCE[0]}" == "${0}" ]; then
    main "$@"
fi