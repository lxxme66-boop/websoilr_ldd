#!/bin/bash
# 智能文本QA生成系统 - 整合版快速启动脚本
# 提供便捷的命令来运行各种功能和配置

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 系统信息
SYSTEM_NAME="智能文本QA生成系统 - 整合版"
VERSION="2.0.0"

# 默认配置
DEFAULT_CONFIG="config.json"
DEFAULT_DOMAIN="semiconductor"
DEFAULT_BATCH_SIZE=50
DEFAULT_QUALITY_THRESHOLD=0.7

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

print_header() {
    echo -e "${PURPLE}========================================${NC}"
    echo -e "${PURPLE}$1${NC}"
    echo -e "${PURPLE}========================================${NC}"
}

# 显示帮助信息
show_help() {
    print_header "$SYSTEM_NAME v$VERSION"
    echo ""
    echo "使用方法: $0 [命令] [选项]"
    echo ""
    echo "可用命令:"
    echo "  help                    显示此帮助信息"
    echo "  setup                   初始化环境和配置"
    echo "  check                   检查系统环境和依赖"
    echo "  full                    运行完整流水线"
    echo "  retrieval               仅运行文本召回"
    echo "  cleaning                仅运行数据清理"
    echo "  generation              仅运行QA生成"
    echo "  quality                 仅运行质量控制"
    echo "  local-models            配置和使用本地模型"
    echo "  multimodal              启用多模态处理"
    echo "  batch                   批量处理多个域"
    echo "  monitor                 监控系统性能"
    echo "  test                    运行测试样例"
    echo ""
    echo "选项:"
    echo "  --input PATH            输入路径 (必需)"
    echo "  --domain DOMAIN         专业领域 (semiconductor|optics|materials)"
    echo "  --config CONFIG         配置文件路径"
    echo "  --batch-size SIZE       批处理大小"
    echo "  --quality-threshold T   质量阈值 (0.0-1.0)"
    echo "  --use-local-models      使用本地模型"
    echo "  --enable-multimodal     启用多模态处理"
    echo "  --verbose               详细输出"
    echo ""
    echo "示例:"
    echo "  $0 setup                              # 初始化环境"
    echo "  $0 full --input data/pdfs             # 运行完整流水线"
    echo "  $0 full --input data/pdfs --domain optics --use-local-models"
    echo "  $0 batch --input data/pdfs            # 批量处理多个领域"
    echo "  $0 local-models                       # 配置本地模型"
    echo ""
}

# 检查系统环境
check_environment() {
    print_header "检查系统环境"
    
    # 检查Python
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
        print_success "Python 3 已安装: $PYTHON_VERSION"
    else
        print_error "Python 3 未安装"
        exit 1
    fi
    
    # 检查pip
    if command -v pip3 &> /dev/null; then
        print_success "pip3 已安装"
    else
        print_error "pip3 未安装"
        exit 1
    fi
    
    # 检查配置文件
    if [[ -f "$DEFAULT_CONFIG" ]]; then
        print_success "配置文件存在: $DEFAULT_CONFIG"
    else
        print_warning "配置文件不存在，将创建默认配置"
    fi
    
    # 检查必需目录
    REQUIRED_DIRS=("data" "logs" "temp")
    for dir in "${REQUIRED_DIRS[@]}"; do
        if [[ -d "$dir" ]]; then
            print_success "目录存在: $dir"
        else
            print_info "创建目录: $dir"
            mkdir -p "$dir"
        fi
    done
    
    # 检查Python包
    print_info "检查Python依赖包..."
    REQUIRED_PACKAGES=("pandas" "numpy" "aiohttp" "PyMuPDF")
    for package in "${REQUIRED_PACKAGES[@]}"; do
        if python3 -c "import $package" &> /dev/null; then
            print_success "包已安装: $package"
        else
            print_warning "包未安装: $package"
        fi
    done
}

# 初始化环境
setup_environment() {
    print_header "初始化环境"
    
    # 创建目录结构
    print_info "创建目录结构..."
    DIRS=(
        "data/input" "data/pdfs" "data/texts"
        "data/output" "data/retrieved" "data/cleaned" 
        "data/qa_results" "data/quality_checked" "data/final_output"
        "temp" "temp/cache" "logs"
    )
    
    for dir in "${DIRS[@]}"; do
        mkdir -p "$dir"
        print_success "创建目录: $dir"
    done
    
    # 安装依赖
    if [[ -f "requirements.txt" ]]; then
        print_info "安装Python依赖..."
        pip3 install -r requirements.txt
        print_success "依赖安装完成"
    else
        print_warning "requirements.txt 文件不存在"
    fi
    
    # 创建示例配置
    if [[ ! -f "$DEFAULT_CONFIG" ]]; then
        print_info "创建示例配置文件..."
        create_sample_config
    fi
    
    print_success "环境初始化完成！"
}

# 创建示例配置文件
create_sample_config() {
    cat > "$DEFAULT_CONFIG" << 'EOF'
{
  "system_info": {
    "name": "智能文本QA生成系统 - 整合版",
    "version": "2.0.0",
    "description": "功能完整的智能文本问答生成系统"
  },
  "api": {
    "ark_url": "http://your-api-endpoint/v1",
    "api_key": "your-api-key-here",
    "timeout": 600,
    "max_retries": 3,
    "retry_delay": 1
  },
  "models": {
    "qa_generator_model": {
      "type": "openai_compatible",
      "path": "/path/to/your/model",
      "temperature": 0.8,
      "max_tokens": 4096
    },
    "local_models": {
      "ollama": {
        "enabled": false,
        "base_url": "http://localhost:11434",
        "model_name": "qwen:7b"
      }
    }
  },
  "processing": {
    "batch_size": 50,
    "pool_size": 100,
    "quality_threshold": 0.7
  },
  "professional_domains": {
    "default_domain": "semiconductor",
    "semiconductor": {
      "keywords": ["IGZO", "TFT", "OLED", "半导体"]
    },
    "optics": {
      "keywords": ["光谱", "光学", "激光"]
    }
  }
}
EOF
    print_success "示例配置文件已创建: $DEFAULT_CONFIG"
    print_warning "请编辑配置文件设置您的API密钥和模型路径"
}

# 配置本地模型
setup_local_models() {
    print_header "配置本地模型"
    
    # 检查Ollama
    if command -v ollama &> /dev/null; then
        print_success "Ollama 已安装"
        
        # 启动Ollama服务
        print_info "启动Ollama服务..."
        ollama serve &
        sleep 3
        
        # 检查可用模型
        print_info "检查可用模型..."
        if ollama list | grep -q "qwen"; then
            print_success "Qwen模型已安装"
        else
            print_info "下载Qwen模型..."
            ollama pull qwen:7b
        fi
        
        # 更新配置启用本地模型
        if [[ -f "$DEFAULT_CONFIG" ]]; then
            python3 -c "
import json
with open('$DEFAULT_CONFIG', 'r') as f:
    config = json.load(f)
config['models']['local_models']['ollama']['enabled'] = True
config['api']['use_local_models'] = True
with open('$DEFAULT_CONFIG', 'w') as f:
    json.dump(config, f, indent=2, ensure_ascii=False)
"
            print_success "配置已更新为使用本地模型"
        fi
    else
        print_warning "Ollama 未安装"
        print_info "安装Ollama..."
        curl -fsSL https://ollama.ai/install.sh | sh
        print_success "Ollama 安装完成，请重新运行此命令"
    fi
}

# 运行完整流水线
run_full_pipeline() {
    local input_path="$1"
    local domain="${2:-$DEFAULT_DOMAIN}"
    local config="${3:-$DEFAULT_CONFIG}"
    local use_local="${4:-false}"
    local enable_multimodal="${5:-false}"
    local batch_size="${6:-$DEFAULT_BATCH_SIZE}"
    local quality_threshold="${7:-$DEFAULT_QUALITY_THRESHOLD}"
    
    print_header "运行完整流水线"
    print_info "输入路径: $input_path"
    print_info "专业领域: $domain"
    print_info "使用本地模型: $use_local"
    print_info "多模态处理: $enable_multimodal"
    
    # 构建命令
    local cmd="python3 run_pipeline.py --mode full_pipeline --input_path '$input_path' --domain '$domain' --config '$config' --batch_size $batch_size --quality_threshold $quality_threshold"
    
    if [[ "$use_local" == "true" ]]; then
        cmd="$cmd --use_local_models"
    fi
    
    if [[ "$enable_multimodal" == "true" ]]; then
        cmd="$cmd --enable_multimodal"
    fi
    
    print_info "执行命令: $cmd"
    eval $cmd
}

# 批量处理多个领域
run_batch_processing() {
    local input_base="$1"
    local config="${2:-$DEFAULT_CONFIG}"
    
    print_header "批量处理多个领域"
    
    local domains=("semiconductor" "optics" "materials")
    
    for domain in "${domains[@]}"; do
        local domain_path="$input_base/$domain"
        if [[ -d "$domain_path" ]]; then
            print_info "处理领域: $domain"
            run_full_pipeline "$domain_path" "$domain" "$config"
            print_success "领域 $domain 处理完成"
        else
            print_warning "领域目录不存在: $domain_path"
        fi
    done
    
    print_success "批量处理完成"
}

# 运行性能监控
run_monitoring() {
    print_header "系统性能监控"
    
    # 创建监控脚本
    cat > temp/monitor.py << 'EOF'
import psutil
import time
import json
from datetime import datetime

def monitor_system():
    while True:
        stats = {
            'timestamp': datetime.now().isoformat(),
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('/').percent,
            'load_avg': psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None
        }
        
        print(f"[{stats['timestamp']}] CPU: {stats['cpu_percent']:.1f}% | Memory: {stats['memory_percent']:.1f}% | Disk: {stats['disk_percent']:.1f}%")
        
        with open('logs/performance.json', 'a') as f:
            json.dump(stats, f)
            f.write('\n')
        
        time.sleep(10)

if __name__ == "__main__":
    monitor_system()
EOF
    
    print_info "启动性能监控..."
    python3 temp/monitor.py
}

# 运行测试样例
run_test() {
    print_header "运行测试样例"
    
    # 创建测试数据
    print_info "创建测试数据..."
    mkdir -p data/test
    
    # 创建测试配置
    cat > temp/test_config.json << 'EOF'
{
  "api": {
    "ark_url": "http://localhost:8080/v1",
    "api_key": "test-key"
  },
  "processing": {
    "batch_size": 5,
    "quality_threshold": 0.5
  }
}
EOF
    
    # 运行测试
    print_info "运行基础功能测试..."
    python3 -c "
import sys
sys.path.append('.')
from TextQA.dataargument import get_total_responses
print('✓ TextQA模块导入成功')

from TextGeneration.prompts_conf import user_prompts
print('✓ TextGeneration模块导入成功')
print(f'✓ 可用Prompt数量: {len(user_prompts)}')

try:
    from LocalModels.ollama_client import OllamaClient
    print('✓ LocalModels模块导入成功')
except:
    print('⚠ LocalModels模块导入失败（可能未安装相关依赖）')

try:
    from MultiModal.pdf_processor import PDFProcessor
    print('✓ MultiModal模块导入成功')
except:
    print('⚠ MultiModal模块导入失败（可能未安装相关依赖）')
"
    
    print_success "测试完成"
}

# 解析命令行参数
parse_arguments() {
    local command="$1"
    shift
    
    local input_path=""
    local domain="$DEFAULT_DOMAIN"
    local config="$DEFAULT_CONFIG"
    local use_local_models="false"
    local enable_multimodal="false"
    local batch_size="$DEFAULT_BATCH_SIZE"
    local quality_threshold="$DEFAULT_QUALITY_THRESHOLD"
    local verbose="false"
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --input)
                input_path="$2"
                shift 2
                ;;
            --domain)
                domain="$2"
                shift 2
                ;;
            --config)
                config="$2"
                shift 2
                ;;
            --batch-size)
                batch_size="$2"
                shift 2
                ;;
            --quality-threshold)
                quality_threshold="$2"
                shift 2
                ;;
            --use-local-models)
                use_local_models="true"
                shift
                ;;
            --enable-multimodal)
                enable_multimodal="true"
                shift
                ;;
            --verbose)
                verbose="true"
                shift
                ;;
            *)
                print_error "未知选项: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # 根据命令执行相应操作
    case "$command" in
        help|--help|-h)
            show_help
            ;;
        setup)
            setup_environment
            ;;
        check)
            check_environment
            ;;
        full)
            if [[ -z "$input_path" ]]; then
                print_error "完整流水线需要指定 --input 参数"
                exit 1
            fi
            run_full_pipeline "$input_path" "$domain" "$config" "$use_local_models" "$enable_multimodal" "$batch_size" "$quality_threshold"
            ;;
        retrieval)
            if [[ -z "$input_path" ]]; then
                print_error "文本召回需要指定 --input 参数"
                exit 1
            fi
            python3 run_pipeline.py --mode text_retrieval --input_path "$input_path" --domain "$domain" --config "$config"
            ;;
        cleaning)
            if [[ -z "$input_path" ]]; then
                print_error "数据清理需要指定 --input 参数"
                exit 1
            fi
            python3 run_pipeline.py --mode data_cleaning --input_path "$input_path" --config "$config"
            ;;
        generation)
            if [[ -z "$input_path" ]]; then
                print_error "QA生成需要指定 --input 参数"
                exit 1
            fi
            python3 run_pipeline.py --mode qa_generation --input_path "$input_path" --domain "$domain" --config "$config"
            ;;
        quality)
            if [[ -z "$input_path" ]]; then
                print_error "质量控制需要指定 --input 参数"
                exit 1
            fi
            python3 run_pipeline.py --mode quality_control --input_path "$input_path" --quality_threshold "$quality_threshold" --config "$config"
            ;;
        local-models)
            setup_local_models
            ;;
        multimodal)
            if [[ -z "$input_path" ]]; then
                print_error "多模态处理需要指定 --input 参数"
                exit 1
            fi
            run_full_pipeline "$input_path" "$domain" "$config" "$use_local_models" "true" "$batch_size" "$quality_threshold"
            ;;
        batch)
            if [[ -z "$input_path" ]]; then
                print_error "批量处理需要指定 --input 参数"
                exit 1
            fi
            run_batch_processing "$input_path" "$config"
            ;;
        monitor)
            run_monitoring
            ;;
        test)
            run_test
            ;;
        *)
            print_error "未知命令: $command"
            show_help
            exit 1
            ;;
    esac
}

# 主函数
main() {
    if [[ $# -eq 0 ]]; then
        show_help
        exit 0
    fi
    
    parse_arguments "$@"
}

# 运行主函数
main "$@"