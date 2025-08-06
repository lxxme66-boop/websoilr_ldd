#!/bin/bash
# 智能QA生成系统 - 批量处理脚本
# 用于批量处理多个PDF文件夹

set -e  # 遇到错误立即退出

# 默认配置
DEFAULT_DOMAIN="semiconductor"
DEFAULT_BATCH_SIZE=100
DEFAULT_QUALITY_THRESHOLD=0.7
DEFAULT_OUTPUT_BASE="data/batch_results"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的信息
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

# 显示使用说明
show_help() {
    cat << EOF
智能QA生成系统 - 批量处理脚本

用法: $0 [选项] <输入目录1> [输入目录2] [输入目录3] ...

选项:
    -o, --output <目录>        输出基础目录 (默认: $DEFAULT_OUTPUT_BASE)
    -d, --domain <领域>        专业领域 (默认: $DEFAULT_DOMAIN)
    -b, --batch-size <大小>    批处理大小 (默认: $DEFAULT_BATCH_SIZE)
    -q, --quality <阈值>       质量阈值 (默认: $DEFAULT_QUALITY_THRESHOLD)
    -j, --jobs <数量>          并行任务数 (默认: 1)
    -s, --skip-retrieval       跳过数据召回阶段
    --no-quality-control       禁用质量控制
    --verbose                  详细输出
    --dry-run                  试运行模式
    -h, --help                 显示此帮助信息

示例:
    # 批量处理多个PDF文件夹
    $0 data/pdfs1 data/pdfs2 data/pdfs3

    # 指定输出目录和领域
    $0 -o results -d optics data/pdfs1

    # 并行处理（2个任务同时运行）
    $0 -j 2 data/pdfs1 data/pdfs2 data/pdfs3

    # 跳过数据召回，直接从清理阶段开始
    $0 -s data/cleaned_data1 data/cleaned_data2

EOF
}

# 解析命令行参数
parse_args() {
    OUTPUT_BASE="$DEFAULT_OUTPUT_BASE"
    DOMAIN="$DEFAULT_DOMAIN"
    BATCH_SIZE="$DEFAULT_BATCH_SIZE"
    QUALITY_THRESHOLD="$DEFAULT_QUALITY_THRESHOLD"
    PARALLEL_JOBS=1
    SKIP_RETRIEVAL=false
    NO_QUALITY_CONTROL=false
    VERBOSE=false
    DRY_RUN=false
    INPUT_DIRS=()

    while [[ $# -gt 0 ]]; do
        case $1 in
            -o|--output)
                OUTPUT_BASE="$2"
                shift 2
                ;;
            -d|--domain)
                DOMAIN="$2"
                shift 2
                ;;
            -b|--batch-size)
                BATCH_SIZE="$2"
                shift 2
                ;;
            -q|--quality)
                QUALITY_THRESHOLD="$2"
                shift 2
                ;;
            -j|--jobs)
                PARALLEL_JOBS="$2"
                shift 2
                ;;
            -s|--skip-retrieval)
                SKIP_RETRIEVAL=true
                shift
                ;;
            --no-quality-control)
                NO_QUALITY_CONTROL=true
                shift
                ;;
            --verbose)
                VERBOSE=true
                shift
                ;;
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            -*)
                print_error "未知选项: $1"
                show_help
                exit 1
                ;;
            *)
                INPUT_DIRS+=("$1")
                shift
                ;;
        esac
    done

    # 检查输入目录
    if [ ${#INPUT_DIRS[@]} -eq 0 ]; then
        print_error "请指定至少一个输入目录"
        show_help
        exit 1
    fi

    # 验证输入目录存在
    for dir in "${INPUT_DIRS[@]}"; do
        if [ ! -d "$dir" ] && [ ! -f "$dir" ]; then
            print_error "输入路径不存在: $dir"
            exit 1
        fi
    done
}

# 处理单个目录
process_directory() {
    local input_dir="$1"
    local job_id="$2"
    local total_jobs="$3"
    
    local dir_name=$(basename "$input_dir")
    local output_dir="$OUTPUT_BASE/$dir_name"
    
    print_info "[$job_id/$total_jobs] 开始处理: $input_dir"
    print_info "输出目录: $output_dir"
    
    # 构建命令参数
    local cmd_args=(
        "python" "run_pipeline.py"
        "--mode" "full_pipeline"
        "--input_path" "$input_dir"
        "--output_path" "$output_dir"
        "--domain" "$DOMAIN"
        "--batch_size" "$BATCH_SIZE"
        "--quality_threshold" "$QUALITY_THRESHOLD"
    )
    
    if [ "$SKIP_RETRIEVAL" = true ]; then
        cmd_args+=("--skip_retrieval")
    fi
    
    if [ "$NO_QUALITY_CONTROL" = true ]; then
        cmd_args+=("--enable_quality_control" "false")
    fi
    
    if [ "$VERBOSE" = true ]; then
        cmd_args+=("--verbose")
    fi
    
    if [ "$DRY_RUN" = true ]; then
        cmd_args+=("--dry_run")
    fi
    
    # 执行命令
    local start_time=$(date +%s)
    
    if [ "$DRY_RUN" = true ]; then
        print_info "试运行命令: ${cmd_args[*]}"
        return 0
    fi
    
    # 创建日志文件
    local log_file="$OUTPUT_BASE/logs/batch_${dir_name}_$(date +%Y%m%d_%H%M%S).log"
    mkdir -p "$(dirname "$log_file")"
    
    # 执行处理
    if "${cmd_args[@]}" > "$log_file" 2>&1; then
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        print_success "[$job_id/$total_jobs] 处理完成: $dir_name (耗时: ${duration}秒)"
        print_info "日志文件: $log_file"
        
        # 生成简要报告
        if [ -f "$output_dir"/pipeline_*/05_final/pipeline_summary.txt ]; then
            local summary_file=$(find "$output_dir" -name "pipeline_summary.txt" | head -1)
            print_info "处理报告: $summary_file"
        fi
        
        return 0
    else
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        print_error "[$job_id/$total_jobs] 处理失败: $dir_name (耗时: ${duration}秒)"
        print_error "错误日志: $log_file"
        return 1
    fi
}

# 并行处理函数
parallel_process() {
    local total_dirs=${#INPUT_DIRS[@]}
    local active_jobs=0
    local job_pids=()
    local job_counter=1
    local failed_jobs=0
    
    print_info "开始批量处理 $total_dirs 个目录，并行度: $PARALLEL_JOBS"
    
    # 创建输出目录
    mkdir -p "$OUTPUT_BASE/logs"
    
    for input_dir in "${INPUT_DIRS[@]}"; do
        # 等待可用的job槽位
        while [ $active_jobs -ge $PARALLEL_JOBS ]; do
            # 检查已完成的任务
            for i in "${!job_pids[@]}"; do
                local pid=${job_pids[i]}
                if ! kill -0 $pid 2>/dev/null; then
                    # 任务已完成
                    wait $pid
                    local exit_code=$?
                    if [ $exit_code -ne 0 ]; then
                        ((failed_jobs++))
                    fi
                    unset job_pids[i]
                    ((active_jobs--))
                fi
            done
            sleep 1
        done
        
        # 启动新任务
        process_directory "$input_dir" $job_counter $total_dirs &
        local pid=$!
        job_pids+=($pid)
        ((active_jobs++))
        ((job_counter++))
        
        print_info "启动任务 PID: $pid"
    done
    
    # 等待所有任务完成
    print_info "等待所有任务完成..."
    for pid in "${job_pids[@]}"; do
        if [ -n "$pid" ]; then
            wait $pid
            local exit_code=$?
            if [ $exit_code -ne 0 ]; then
                ((failed_jobs++))
            fi
        fi
    done
    
    # 输出最终统计
    local success_jobs=$((total_dirs - failed_jobs))
    print_info "批量处理完成！"
    print_success "成功处理: $success_jobs/$total_dirs"
    
    if [ $failed_jobs -gt 0 ]; then
        print_warning "失败任务: $failed_jobs/$total_dirs"
        print_info "请查看日志文件了解失败原因"
    fi
    
    return $failed_jobs
}

# 生成批量处理报告
generate_batch_report() {
    local report_file="$OUTPUT_BASE/batch_report_$(date +%Y%m%d_%H%M%S).json"
    local summary_file="$OUTPUT_BASE/batch_summary.txt"
    
    print_info "生成批量处理报告..."
    
    # 收集所有pipeline报告
    local pipeline_reports=()
    for input_dir in "${INPUT_DIRS[@]}"; do
        local dir_name=$(basename "$input_dir")
        local output_dir="$OUTPUT_BASE/$dir_name"
        
        # 查找pipeline报告文件
        local report_files=$(find "$output_dir" -name "pipeline_report.json" 2>/dev/null || true)
        if [ -n "$report_files" ]; then
            pipeline_reports+=($report_files)
        fi
    done
    
    # 生成汇总报告
    cat > "$summary_file" << EOF
智能QA生成系统 - 批量处理汇总报告
$(date)
========================================

处理配置:
- 输入目录数量: ${#INPUT_DIRS[@]}
- 专业领域: $DOMAIN
- 批处理大小: $BATCH_SIZE
- 质量阈值: $QUALITY_THRESHOLD
- 并行任务数: $PARALLEL_JOBS

处理结果:
EOF

    local total_qa_pairs=0
    local total_files=0
    
    for report_file in "${pipeline_reports[@]}"; do
        if [ -f "$report_file" ]; then
            local dir_name=$(basename "$(dirname "$(dirname "$report_file")")")
            echo "- $dir_name: 处理完成" >> "$summary_file"
            
            # 提取统计信息（简化处理）
            if command -v jq &> /dev/null; then
                local qa_count=$(jq -r '.statistics.qa_generated.data_count // 0' "$report_file" 2>/dev/null || echo 0)
                total_qa_pairs=$((total_qa_pairs + qa_count))
                ((total_files++))
                echo "  QA对数量: $qa_count" >> "$summary_file"
            fi
        fi
    done
    
    cat >> "$summary_file" << EOF

总体统计:
- 处理成功的目录: $total_files
- 总QA对数量: $total_qa_pairs
- 平均每目录QA对: $((total_files > 0 ? total_qa_pairs / total_files : 0))

详细报告位置:
- 批量处理日志: $OUTPUT_BASE/logs/
- 各目录结果: $OUTPUT_BASE/*/
EOF

    print_success "批量处理报告已生成: $summary_file"
}

# 主函数
main() {
    print_info "智能QA生成系统 - 批量处理脚本"
    print_info "版本: 1.0"
    
    # 解析参数
    parse_args "$@"
    
    # 显示配置信息
    print_info "处理配置:"
    print_info "- 输入目录: ${INPUT_DIRS[*]}"
    print_info "- 输出基础目录: $OUTPUT_BASE"
    print_info "- 专业领域: $DOMAIN"
    print_info "- 批处理大小: $BATCH_SIZE"
    print_info "- 质量阈值: $QUALITY_THRESHOLD"
    print_info "- 并行任务数: $PARALLEL_JOBS"
    print_info "- 跳过数据召回: $SKIP_RETRIEVAL"
    print_info "- 禁用质量控制: $NO_QUALITY_CONTROL"
    
    if [ "$DRY_RUN" = true ]; then
        print_warning "试运行模式 - 不会执行实际处理"
    fi
    
    # 开始处理
    local start_time=$(date +%s)
    
    if parallel_process; then
        local end_time=$(date +%s)
        local total_duration=$((end_time - start_time))
        
        print_success "批量处理全部完成！总耗时: ${total_duration}秒"
        
        # 生成汇总报告
        if [ "$DRY_RUN" != true ]; then
            generate_batch_report
        fi
        
        exit 0
    else
        print_error "批量处理过程中出现错误"
        exit 1
    fi
}

# 脚本入口
if [ "${BASH_SOURCE[0]}" == "${0}" ]; then
    main "$@"
fi