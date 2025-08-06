#!/bin/bash

# Text QA Generation Pipeline Script
# 支持多模态处理、本地模型、专业领域定制和数据改写功能

set -e  # 遇到错误时退出

# 默认配置
DEFAULT_BATCH_SIZE=50
DEFAULT_POOL_SIZE=100
DEFAULT_MAX_TASKS=1000
DEFAULT_INDEX=343
DEFAULT_QUALITY_THRESHOLD=0.7
DEFAULT_CONCURRENCY=5

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${PURPLE}[STEP]${NC} $1"
}

# 帮助信息
show_help() {
    echo -e "${CYAN}Text QA Generation Pipeline${NC}"
    echo ""
    echo "用法: $0 [OPTIONS]"
    echo ""
    echo "选项:"
    echo "  --mode MODE                 运行模式 (text|pdf|multimodal|rewrite|quality_check)"
    echo "  --input_dir DIR            输入目录"
    echo "  --output_dir DIR           输出目录 (默认: data/output)"
    echo "  --model_type TYPE          模型类型 (api|ollama|vllm|transformers)"
    echo "  --model_name NAME          模型名称"
    echo "  --domain DOMAIN            专业领域 (semiconductor|optics|materials)"
    echo "  --batch_size SIZE          批处理大小 (默认: $DEFAULT_BATCH_SIZE)"
    echo "  --pool_size SIZE           并发池大小 (默认: $DEFAULT_POOL_SIZE)"
    echo "  --index INDEX              Prompt索引 (默认: $DEFAULT_INDEX)"
    echo "  --quality_threshold FLOAT  质量阈值 (默认: $DEFAULT_QUALITY_THRESHOLD)"
    echo "  --enhanced_quality         启用增强质量检查"
    echo "  --rewrite                  启用数据改写"
    echo "  --professional             启用专业增强"
    echo "  --help                     显示此帮助信息"
    echo ""
    echo "运行模式:"
    echo "  text        - 纯文本问答生成"
    echo "  pdf         - PDF文档处理和问答生成"
    echo "  multimodal  - 多模态（图文）问答生成"
    echo "  rewrite     - 数据改写和增强"
    echo "  quality_check - 质量检查和评估"
    echo ""
    echo "示例:"
    echo "  $0 --mode text --input_dir data/texts --model_type ollama"
    echo "  $0 --mode pdf --input_dir data/pdfs --domain semiconductor"
    echo "  $0 --mode rewrite --input_dir data/qa_pairs.json --professional"
    echo ""
}

# 解析命令行参数
MODE="text"
INPUT_DIR=""
OUTPUT_DIR="data/output"
MODEL_TYPE="api"
MODEL_NAME=""
DOMAIN="semiconductor"
BATCH_SIZE=$DEFAULT_BATCH_SIZE
POOL_SIZE=$DEFAULT_POOL_SIZE
INDEX=$DEFAULT_INDEX
QUALITY_THRESHOLD=$DEFAULT_QUALITY_THRESHOLD
ENHANCED_QUALITY=false
REWRITE=false
PROFESSIONAL=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --mode)
            MODE="$2"
            shift 2
            ;;
        --input_dir)
            INPUT_DIR="$2"
            shift 2
            ;;
        --output_dir)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        --model_type)
            MODEL_TYPE="$2"
            shift 2
            ;;
        --model_name)
            MODEL_NAME="$2"
            shift 2
            ;;
        --domain)
            DOMAIN="$2"
            shift 2
            ;;
        --batch_size)
            BATCH_SIZE="$2"
            shift 2
            ;;
        --pool_size)
            POOL_SIZE="$2"
            shift 2
            ;;
        --index)
            INDEX="$2"
            shift 2
            ;;
        --quality_threshold)
            QUALITY_THRESHOLD="$2"
            shift 2
            ;;
        --enhanced_quality)
            ENHANCED_QUALITY=true
            shift
            ;;
        --rewrite)
            REWRITE=true
            shift
            ;;
        --professional)
            PROFESSIONAL=true
            shift
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            log_error "未知参数: $1"
            show_help
            exit 1
            ;;
    esac
done

# 检查必需的参数
if [[ -z "$INPUT_DIR" ]]; then
    log_error "必须指定输入目录 --input_dir"
    exit 1
fi

# 创建输出目录
mkdir -p "$OUTPUT_DIR"
mkdir -p logs

log_info "启动 Text QA Generation Pipeline"
log_info "运行模式: $MODE"
log_info "输入目录: $INPUT_DIR"
log_info "输出目录: $OUTPUT_DIR"
log_info "模型类型: $MODEL_TYPE"

# 检查依赖
check_dependencies() {
    log_step "检查依赖..."
    
    # 检查Python环境
    if ! command -v python &> /dev/null; then
        log_error "Python 未安装"
        exit 1
    fi
    
    # 检查必需的Python包
    python -c "import asyncio, json, aiohttp" 2>/dev/null || {
        log_error "缺少必需的Python包，请运行: pip install -r requirements.txt"
        exit 1
    }
    
    # 检查本地模型服务
    if [[ "$MODEL_TYPE" == "ollama" ]]; then
        if ! curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
            log_warning "Ollama服务未运行，请先启动: ollama serve"
        else
            log_success "Ollama服务运行正常"
        fi
    elif [[ "$MODEL_TYPE" == "vllm" ]]; then
        if ! curl -s http://localhost:8000/health >/dev/null 2>&1; then
            log_warning "vLLM服务未运行"
        else
            log_success "vLLM服务运行正常"
        fi
    fi
    
    log_success "依赖检查完成"
}

# 文本模式处理
run_text_mode() {
    log_step "执行文本问答生成..."
    
    # 检查输入目录
    if [[ ! -d "$INPUT_DIR" ]]; then
        log_error "输入目录不存在: $INPUT_DIR"
        exit 1
    fi
    
    # 文本召回和处理
    log_info "步骤 1/4: 文本处理和召回"
    python text_main_batch_inference.py \
        --txt_path "$INPUT_DIR" \
        --storage_folder "$OUTPUT_DIR" \
        --index $INDEX \
        --parallel_batch_size $BATCH_SIZE \
        --selected_task_number $DEFAULT_MAX_TASKS \
        --model_type $MODEL_TYPE \
        --model_name "$MODEL_NAME"
    
    # 数据清洗
    log_info "步骤 2/4: 数据清洗"
    python clean_text_data.py \
        --input_file "$OUTPUT_DIR/total_response.pkl" \
        --output_file "$OUTPUT_DIR"
    
    # QA生成
    log_info "步骤 3/4: QA对生成"
    python text_qa_generation.py \
        --file_path "$OUTPUT_DIR/total_response.json" \
        --index $INDEX \
        --pool_size $POOL_SIZE \
        --output_file "$OUTPUT_DIR" \
        --model_type $MODEL_TYPE \
        --model_name "$MODEL_NAME" \
        --domain "$DOMAIN"
    
    # 质量检查
    if [[ "$ENHANCED_QUALITY" == true ]]; then
        log_info "步骤 4/4: 增强质量检查"
        python text_qa_generation.py \
            --file_path "$OUTPUT_DIR/results_$INDEX.json" \
            --output_file "$OUTPUT_DIR" \
            --check_task True \
            --enhanced_quality True \
            --quality_threshold $QUALITY_THRESHOLD \
            --model_type $MODEL_TYPE
    else
        log_info "跳过质量检查"
    fi
    
    log_success "文本模式处理完成"
}

# PDF模式处理
run_pdf_mode() {
    log_step "执行PDF多模态处理..."
    
    # PDF处理
    log_info "步骤 1/5: PDF文档处理"
    python MultiModal/pdf_processor.py \
        --input "$INPUT_DIR" \
        --output "$OUTPUT_DIR/processed" \
        --markdown
    
    # 多模态召回
    log_info "步骤 2/5: 多模态召回"
    python text_main_batch_inference.py \
        --pdf_path "$OUTPUT_DIR/processed" \
        --storage_folder "$OUTPUT_DIR" \
        --index $INDEX \
        --parallel_batch_size $BATCH_SIZE \
        --model_type $MODEL_TYPE
    
    # 数据清洗
    log_info "步骤 3/5: 数据清洗"
    python clean_text_data.py \
        --input_file "$OUTPUT_DIR/total_response.pkl" \
        --output_file "$OUTPUT_DIR"
    
    # QA生成
    log_info "步骤 4/5: 多模态QA生成"
    python text_qa_generation.py \
        --file_path "$OUTPUT_DIR/total_response.json" \
        --index $INDEX \
        --pool_size $POOL_SIZE \
        --output_file "$OUTPUT_DIR" \
        --model_type $MODEL_TYPE \
        --domain "$DOMAIN" \
        --multimodal True
    
    # 质量检查
    if [[ "$ENHANCED_QUALITY" == true ]]; then
        log_info "步骤 5/5: 质量检查"
        python model_rewrite/data_label.py \
            --data-path "$OUTPUT_DIR/results_$INDEX.json" \
            --output-path "$OUTPUT_DIR/quality_report.json" \
            --model-type $MODEL_TYPE
    fi
    
    log_success "PDF模式处理完成"
}

# 数据改写模式
run_rewrite_mode() {
    log_step "执行数据改写和增强..."
    
    if [[ ! -f "$INPUT_DIR" ]]; then
        log_error "输入文件不存在: $INPUT_DIR"
        exit 1
    fi
    
    local template_type="basic"
    if [[ "$PROFESSIONAL" == true ]]; then
        template_type="professional"
    fi
    
    log_info "使用模板类型: $template_type"
    
    python model_rewrite/data_generation.py \
        --data-path "$INPUT_DIR" \
        --output-path "$OUTPUT_DIR/rewritten_qa.json" \
        --concurrency $DEFAULT_CONCURRENCY \
        --model-type $MODEL_TYPE \
        --model-name "$MODEL_NAME" \
        --template-type $template_type
    
    log_success "数据改写完成"
}

# 质量检查模式
run_quality_check_mode() {
    log_step "执行质量检查..."
    
    if [[ ! -f "$INPUT_DIR" ]]; then
        log_error "输入文件不存在: $INPUT_DIR"
        exit 1
    fi
    
    python model_rewrite/data_label.py \
        --data-path "$INPUT_DIR" \
        --output-path "$OUTPUT_DIR/quality_report.json" \
        --concurrency $DEFAULT_CONCURRENCY \
        --model-type $MODEL_TYPE \
        --model-name "$MODEL_NAME"
    
    log_success "质量检查完成"
}

# 多模态模式处理
run_multimodal_mode() {
    log_step "执行多模态问答生成..."
    
    # 组合PDF和文本处理
    run_pdf_mode
    
    # 如果启用改写，执行改写
    if [[ "$REWRITE" == true ]]; then
        log_info "执行数据改写增强..."
        run_rewrite_mode
    fi
    
    log_success "多模态模式处理完成"
}

# 显示结果统计
show_results() {
    log_step "处理结果统计"
    
    if [[ -f "$OUTPUT_DIR/results_$INDEX.json" ]]; then
        local qa_count=$(python -c "import json; data=json.load(open('$OUTPUT_DIR/results_$INDEX.json')); print(len(data) if isinstance(data, list) else sum(len(item.get('qa_pairs', [])) for item in data))")
        log_success "生成QA对数量: $qa_count"
    fi
    
    if [[ -f "$OUTPUT_DIR/quality_report.json" ]]; then
        local pass_rate=$(python -c "import json; data=json.load(open('$OUTPUT_DIR/quality_report.json')); print(f\"{data.get('summary', {}).get('pass_rate', 0)*100:.1f}%\")")
        log_success "质量通过率: $pass_rate"
    fi
    
    if [[ -f "$OUTPUT_DIR/rewritten_qa.json" ]]; then
        local rewrite_count=$(python -c "import json; data=json.load(open('$OUTPUT_DIR/rewritten_qa.json')); print(len(data))")
        log_success "改写数据数量: $rewrite_count"
    fi
    
    log_info "输出目录: $OUTPUT_DIR"
    log_info "日志文件: logs/"
}

# 主执行流程
main() {
    # 记录开始时间
    local start_time=$(date +%s)
    
    # 检查依赖
    check_dependencies
    
    # 根据模式执行相应处理
    case $MODE in
        text)
            run_text_mode
            ;;
        pdf)
            run_pdf_mode
            ;;
        multimodal)
            run_multimodal_mode
            ;;
        rewrite)
            run_rewrite_mode
            ;;
        quality_check)
            run_quality_check_mode
            ;;
        *)
            log_error "不支持的运行模式: $MODE"
            show_help
            exit 1
            ;;
    esac
    
    # 显示结果
    show_results
    
    # 计算运行时间
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    local hours=$((duration / 3600))
    local minutes=$(((duration % 3600) / 60))
    local seconds=$((duration % 60))
    
    log_success "Pipeline 执行完成！"
    log_info "总耗时: ${hours}h ${minutes}m ${seconds}s"
}

# 错误处理
trap 'log_error "Pipeline 执行失败，请检查错误日志"; exit 1' ERR

# 执行主函数
main "$@"