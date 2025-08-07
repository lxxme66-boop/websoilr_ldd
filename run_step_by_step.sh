#!/bin/bash
# 智能文本QA生成系统 - 分步运行脚本
# 此脚本允许您逐步运行流水线的各个阶段

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

print_stage() {
    echo -e "${BLUE}[STAGE]${NC} $1"
}

# 配置文件路径
CONFIG_FILE="${CONFIG_FILE:-config.json}"

# 显示菜单
show_menu() {
    echo ""
    echo "智能文本QA生成系统 - 分步运行"
    echo "=============================="
    echo "1. 文本召回 (Text Retrieval)"
    echo "2. 数据清理 (Data Cleaning)"
    echo "3. QA生成 (QA Generation)"
    echo "4. 质量控制 (Quality Control)"
    echo "5. 最终处理 (Final Processing)"
    echo "6. 运行完整流水线 (Run Full Pipeline)"
    echo "7. 检查系统状态 (Check System Status)"
    echo "8. 清理输出文件 (Clean Output Files)"
    echo "0. 退出 (Exit)"
    echo ""
}

# 文本召回阶段
run_text_retrieval() {
    print_stage "运行文本召回阶段..."
    
    # 检查输入目录
    echo -n "请输入PDF/文本文件目录 [默认: data/pdfs]: "
    read input_dir
    input_dir=${input_dir:-data/pdfs}
    
    if [ ! -d "$input_dir" ]; then
        print_error "目录不存在: $input_dir"
        return 1
    fi
    
    # 统计文件
    pdf_count=$(find "$input_dir" -name "*.pdf" | wc -l)
    txt_count=$(find "$input_dir" -name "*.txt" | wc -l)
    
    print_info "找到 $pdf_count 个PDF文件，$txt_count 个文本文件"
    
    if [ $((pdf_count + txt_count)) -eq 0 ]; then
        print_warning "没有找到可处理的文件"
        return 1
    fi
    
    # 运行文本召回
    python3 run_pipeline.py \
        --config "$CONFIG_FILE" \
        --stage text_retrieval \
        --input_dir "$input_dir"
    
    print_info "文本召回完成！输出保存在: data/retrieved/"
}

# 数据清理阶段
run_data_cleaning() {
    print_stage "运行数据清理阶段..."
    
    # 检查是否有召回的数据
    if [ ! -f "data/retrieved/total_response.pkl" ]; then
        print_error "未找到召回数据！请先运行文本召回阶段。"
        return 1
    fi
    
    # 运行数据清理
    python3 run_pipeline.py \
        --config "$CONFIG_FILE" \
        --stage data_cleaning
    
    print_info "数据清理完成！输出保存在: data/cleaned/"
}

# QA生成阶段
run_qa_generation() {
    print_stage "运行QA生成阶段..."
    
    # 检查是否有清理后的数据
    if [ ! -f "data/cleaned/total_response.json" ]; then
        print_error "未找到清理后的数据！请先运行数据清理阶段。"
        return 1
    fi
    
    # 选择专业领域
    echo "请选择专业领域:"
    echo "1. 半导体 (semiconductor)"
    echo "2. 光学 (optics)"
    echo "3. 材料 (materials)"
    echo "4. 通用 (general)"
    echo -n "请输入选择 [1-4]: "
    read domain_choice
    
    case $domain_choice in
        1) domain="semiconductor";;
        2) domain="optics";;
        3) domain="materials";;
        4) domain="general";;
        *) domain="semiconductor";;
    esac
    
    print_info "使用领域: $domain"
    
    # 运行QA生成
    python3 run_pipeline.py \
        --config "$CONFIG_FILE" \
        --stage qa_generation \
        --domain "$domain"
    
    print_info "QA生成完成！输出保存在: data/qa_results/"
}

# 质量控制阶段
run_quality_control() {
    print_stage "运行质量控制阶段..."
    
    # 检查是否有QA数据
    qa_files=$(find data/qa_results -name "*.json" 2>/dev/null | wc -l)
    if [ "$qa_files" -eq 0 ]; then
        print_error "未找到QA数据！请先运行QA生成阶段。"
        return 1
    fi
    
    # 设置质量阈值
    echo -n "请输入质量阈值 (0.0-1.0) [默认: 0.7]: "
    read threshold
    threshold=${threshold:-0.7}
    
    # 运行质量控制
    python3 run_pipeline.py \
        --config "$CONFIG_FILE" \
        --stage quality_control \
        --quality_threshold "$threshold"
    
    print_info "质量控制完成！输出保存在: data/quality_checked/"
}

# 最终处理阶段
run_final_processing() {
    print_stage "运行最终处理阶段..."
    
    # 运行最终处理
    python3 run_pipeline.py \
        --config "$CONFIG_FILE" \
        --stage final_processing
    
    print_info "最终处理完成！输出保存在: data/final_output/"
    
    # 显示统计信息
    if [ -f "data/final_output/pipeline_report.json" ]; then
        print_info "生成统计:"
        python3 -c "
import json
report = json.load(open('data/final_output/pipeline_report.json'))
print(f'  总QA对数: {report.get(\"total_qa_pairs\", 0)}')
print(f'  质量通过率: {report.get(\"quality_pass_rate\", 0):.2%}')
print(f'  处理时间: {report.get(\"total_duration\", 0):.1f}秒')
"
    fi
}

# 运行完整流水线
run_full_pipeline() {
    print_stage "运行完整流水线..."
    
    echo -n "请输入输入目录 [默认: data/pdfs]: "
    read input_dir
    input_dir=${input_dir:-data/pdfs}
    
    python3 run_pipeline.py \
        --config "$CONFIG_FILE" \
        --input_dir "$input_dir" \
        --stages all
    
    print_info "完整流水线运行完成！"
}

# 检查系统状态
check_system_status() {
    print_stage "检查系统状态..."
    
    # 检查Python版本
    python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    print_info "Python版本: $python_version"
    
    # 检查配置文件
    if [ -f "$CONFIG_FILE" ]; then
        print_info "配置文件: $CONFIG_FILE ✓"
        
        # 显示关键配置
        use_local=$(python3 -c "import json; config=json.load(open('$CONFIG_FILE')); print(config['api']['use_local_models'])")
        print_info "本地模型: $use_local"
        
        if [ "$use_local" = "True" ]; then
            # 检查vLLM
            vllm_enabled=$(python3 -c "import json; config=json.load(open('$CONFIG_FILE')); print(config['models']['local_models']['vllm']['enabled'])")
            if [ "$vllm_enabled" = "True" ]; then
                vllm_url=$(python3 -c "import json; config=json.load(open('$CONFIG_FILE')); print(config['models']['local_models']['vllm']['base_url'])")
                if curl -s "$vllm_url/health" > /dev/null 2>&1; then
                    print_info "vLLM服务: 运行中 ✓"
                else
                    print_warning "vLLM服务: 未运行 ✗"
                fi
            fi
        fi
    else
        print_error "配置文件不存在: $CONFIG_FILE"
    fi
    
    # 检查各阶段输出
    echo ""
    print_info "各阶段输出状态:"
    
    stages=(
        "data/retrieved:文本召回"
        "data/cleaned:数据清理"
        "data/qa_results:QA生成"
        "data/quality_checked:质量控制"
        "data/final_output:最终输出"
    )
    
    for stage in "${stages[@]}"; do
        IFS=':' read -r dir name <<< "$stage"
        if [ -d "$dir" ] && [ "$(ls -A $dir 2>/dev/null)" ]; then
            file_count=$(find "$dir" -type f | wc -l)
            echo "  - $name: $file_count 个文件 ✓"
        else
            echo "  - $name: 无数据 ✗"
        fi
    done
}

# 清理输出文件
clean_output_files() {
    print_stage "清理输出文件..."
    
    echo "警告：这将删除所有输出文件！"
    echo -n "确定要继续吗？[y/N]: "
    read confirm
    
    if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
        dirs=(
            "data/retrieved"
            "data/cleaned"
            "data/qa_results"
            "data/quality_checked"
            "data/final_output"
            "temp/cache"
        )
        
        for dir in "${dirs[@]}"; do
            if [ -d "$dir" ]; then
                rm -rf "$dir"/*
                print_info "已清理: $dir"
            fi
        done
        
        print_info "所有输出文件已清理"
    else
        print_info "取消清理操作"
    fi
}

# 主循环
main() {
    print_info "智能文本QA生成系统 v2.0 - 分步运行模式"
    
    while true; do
        show_menu
        echo -n "请选择操作 [0-8]: "
        read choice
        
        case $choice in
            1) run_text_retrieval;;
            2) run_data_cleaning;;
            3) run_qa_generation;;
            4) run_quality_control;;
            5) run_final_processing;;
            6) run_full_pipeline;;
            7) check_system_status;;
            8) clean_output_files;;
            0) 
                print_info "感谢使用！再见！"
                exit 0
                ;;
            *)
                print_error "无效的选择，请重试"
                ;;
        esac
        
        echo ""
        echo -n "按回车键继续..."
        read
    done
}

# 运行主程序
main