#!/bin/bash

# Text QA Generation Pipeline with Enhanced Quality Check
# This script runs the complete pipeline for generating QA pairs from text documents
# Version 2.0 - Enhanced Quality Check Edition

# Color codes for better output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Set default values
INPUT_DIR="${INPUT_DIR:-data/input_texts}"
OUTPUT_DIR="${OUTPUT_DIR:-data/output}"
BATCH_SIZE="${BATCH_SIZE:-50}"
POOL_SIZE="${POOL_SIZE:-100}"
TASK_NUMBER="${TASK_NUMBER:-1000}"
QUALITY_THRESHOLD="${QUALITY_THRESHOLD:-0.7}"
PARALLEL_CORES="${PARALLEL_CORES:-10}"

# API configuration
export ARK_API_KEY="${ARK_API_KEY:-ae37bba4-73be-4c22-b1a7-c6b1f5ec3a4b}"
export ARK_URL="${ARK_URL:-http://0.0.0.0:8080/v1}"
export MODEL_PATH="${MODEL_PATH:-/mnt/storage/models/Skywork/Skywork-R1V3-38B}"

# Function to print colored output
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

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check prerequisites
check_prerequisites() {
    print_info "Checking prerequisites..."
    
    if ! command_exists python; then
        print_error "Python is not installed or not in PATH"
        exit 1
    fi
    
    if ! python -c "import asyncio, json, pandas" 2>/dev/null; then
        print_error "Required Python packages are missing. Please run: pip install -r requirements.txt"
        exit 1
    fi
    
    print_success "Prerequisites check passed"
}

# Function to validate model path
validate_model_path() {
    if [ ! -z "$MODEL_PATH" ] && [ ! -d "$MODEL_PATH" ]; then
        print_warning "Model path does not exist: $MODEL_PATH"
        print_warning "Please ensure the model path is correct"
    fi
}

# Function to display configuration
display_config() {
    echo ""
    echo -e "${BLUE}============================================${NC}"
    echo -e "${BLUE}Text QA Generation Pipeline v2.0${NC}"
    echo -e "${BLUE}Enhanced Quality Check Edition${NC}"
    echo -e "${BLUE}============================================${NC}"
    echo -e "${YELLOW}Configuration:${NC}"
    echo "  Input directory: $INPUT_DIR"
    echo "  Output directory: $OUTPUT_DIR"
    echo "  Batch size: $BATCH_SIZE"
    echo "  Pool size: $POOL_SIZE"
    echo "  Target task number: $TASK_NUMBER"
    echo "  Quality threshold: $QUALITY_THRESHOLD"
    echo "  Parallel cores: $PARALLEL_CORES"
    echo "  API URL: $ARK_URL"
    echo "  Model: $MODEL_PATH"
    echo -e "${BLUE}============================================${NC}"
    echo ""
}

# Function to create directories
create_directories() {
    print_info "Creating directories..."
    mkdir -p "$INPUT_DIR"
    mkdir -p "$OUTPUT_DIR"
    mkdir -p "$OUTPUT_DIR/TEMP"
    print_success "Directories created"
}

# Function to check input files
check_input_files() {
    print_info "Checking input files..."
    
    if [ -z "$(ls -A $INPUT_DIR/*.txt 2>/dev/null)" ]; then
        print_error "No .txt files found in $INPUT_DIR"
        print_info "Please add text files to process."
        print_info "You can use the sample file: data/input_texts/sample_igzo_tft.txt"
        exit 1
    fi
    
    local file_count=$(ls -1 $INPUT_DIR/*.txt 2>/dev/null | wc -l)
    print_success "Found $file_count text file(s) to process"
}

# Function to run a step with error checking
run_step() {
    local step_name="$1"
    local step_number="$2"
    shift 2
    local command="$@"
    
    echo ""
    print_info "Step $step_number: $step_name..."
    
    if eval "$command"; then
        print_success "Step $step_number completed successfully"
        return 0
    else
        print_error "Step $step_number failed: $step_name"
        print_error "Command: $command"
        return 1
    fi
}

# Function to generate final report
generate_final_report() {
    print_info "Generating final report..."
    
    python -c "
import json
import os

output_dir = '$OUTPUT_DIR'
results_file = os.path.join(output_dir, 'results_343.json')
stats_file = os.path.join(output_dir, 'results_343_stats.json')

print()
print('=' * 50)
print('QA Generation Results Summary')
print('=' * 50)

if os.path.exists(results_file):
    with open(results_file, 'r', encoding='utf-8') as f:
        results = json.load(f)
    
    total_qa = len(results) if isinstance(results, list) else len(results.get('qa_pairs', []))
    print(f'📊 Total QA pairs generated: {total_qa}')

if os.path.exists(stats_file):
    with open(stats_file, 'r', encoding='utf-8') as f:
        stats = json.load(f)
    
    print()
    print('📈 Question type distribution:')
    for q_type, percentage in stats.get('question_type_percentages', {}).items():
        count = stats.get('question_types', {}).get(q_type, 0)
        print(f'  • {q_type}: {count} ({percentage})')
    
    avg_q_len = stats.get('average_question_length', 0)
    avg_a_len = stats.get('average_answer_length', 0)
    print(f'📏 Average question length: {avg_q_len:.1f} characters')
    print(f'📏 Average answer length: {avg_a_len:.1f} characters')
    
    print()
    print('📁 Source files processed:')
    for source, count in stats.get('source_files', {}).items():
        print(f'  • {source}: {count} QA pairs')

print()
print('💾 Output files location: $OUTPUT_DIR')
print('=' * 50)
"
}

# Function to run quality check
run_quality_check() {
    local use_enhanced="$1"
    
    if [ "$use_enhanced" = "true" ]; then
        print_info "Running enhanced quality check (dual-stage verification)..."
        print_info "This may take longer but provides more accurate quality assessment"
        
        local cmd="python text_qa_generation.py \
            --file_path '$OUTPUT_DIR/results_343.json' \
            --output_file '$OUTPUT_DIR' \
            --check_task True \
            --enhanced_quality True \
            --quality_threshold $QUALITY_THRESHOLD \
            --ark_url '$ARK_URL' \
            --api_key '$ARK_API_KEY' \
            --model '$MODEL_PATH'"
        
        if eval "$cmd"; then
            print_success "Enhanced quality check completed"
            
            # Display quality check results
            python -c "
import json
import os

output_dir = '$OUTPUT_DIR'
quality_report_file = os.path.join(output_dir, 'results_343_quality_report.json')

if os.path.exists(quality_report_file):
    with open(quality_report_file, 'r', encoding='utf-8') as f:
        report = json.load(f)
    
    print()
    print('🔍 Enhanced Quality Check Results:')
    print('=' * 40)
    print(f'📊 Total QA pairs: {report.get(\"total_qa_pairs\", 0)}')
    print(f'✅ Passed QA pairs: {report.get(\"passed_qa_pairs\", 0)}')
    print(f'📈 Pass rate: {report.get(\"pass_rate\", 0):.2%}')
    print(f'🎯 Quality threshold: {report.get(\"quality_threshold\", 0)}')
    print(f'🏆 Meets threshold: {\"Yes\" if report.get(\"meets_threshold\", False) else \"No\"}')
    
    if 'statistics' in report:
        stats = report['statistics']
        print()
        print('📋 Quality Statistics:')
        print(f'  • Avg question length: {stats.get(\"avg_question_length\", 0):.1f} chars')
        print(f'  • Avg answer length: {stats.get(\"avg_answer_length\", 0):.1f} chars')
        
        dist = stats.get('question_types_distribution', {})
        if dist:
            print('  • Question types distribution:')
            for q_type, count in dist.items():
                print(f'    - {q_type}: {count}')
    
    print()
    print('📄 Generated files:')
    print(f'  • Detailed results: results_343_detailed.json')
    print(f'  • High quality data: results_343_high_quality.json')
    print(f'  • Quality report: results_343_quality_report.json')
    print(f'  • CSV analysis: results_343_results.csv')
    print('=' * 40)
else:
    print('⚠️  Quality report not found. Check if quality check completed successfully.')
"
        else
            print_error "Enhanced quality check failed"
            return 1
        fi
        
    else
        print_info "Running standard quality check..."
        
        local cmd="python text_qa_generation.py \
            --file_path '$OUTPUT_DIR/results_343.json' \
            --output_file '$OUTPUT_DIR' \
            --check_task True \
            --enhanced_quality False \
            --check_indexes '(40, 37, 38)' \
            --check_times 5 \
            --ark_url '$ARK_URL' \
            --api_key '$ARK_API_KEY' \
            --model '$MODEL_PATH'"
        
        if eval "$cmd"; then
            print_success "Standard quality check completed"
        else
            print_error "Standard quality check failed"
            return 1
        fi
    fi
}

# Function to ask user for quality check preferences
ask_quality_check() {
    echo ""
    print_info "Quality Check Options:"
    echo "  1. Skip quality check (faster)"
    echo "  2. Run standard quality check"
    echo "  3. Run enhanced quality check (recommended, but slower)"
    echo ""
    
    while true; do
        read -p "$(echo -e ${YELLOW}Choose an option [1-3]:${NC} )" choice
        case $choice in
            1)
                print_info "Skipping quality check"
                return 0
                ;;
            2)
                run_quality_check "false"
                return $?
                ;;
            3)
                run_quality_check "true"
                return $?
                ;;
            *)
                print_warning "Please enter 1, 2, or 3"
                ;;
        esac
    done
}

# Function to display help
show_help() {
    echo "Text QA Generation Pipeline v2.0"
    echo "Enhanced Quality Check Edition"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Environment Variables:"
    echo "  INPUT_DIR         Input directory for text files (default: data/input_texts)"
    echo "  OUTPUT_DIR        Output directory (default: data/output)"
    echo "  BATCH_SIZE        Batch size for processing (default: 50)"
    echo "  POOL_SIZE         Pool size for QA generation (default: 100)"
    echo "  TASK_NUMBER       Target number of tasks (default: 1000)"
    echo "  QUALITY_THRESHOLD Quality threshold for enhanced check (default: 0.7)"
    echo "  PARALLEL_CORES    Number of parallel cores for quality check (default: 10)"
    echo "  ARK_API_KEY       API key for the service"
    echo "  ARK_URL           API URL (default: http://0.0.0.0:8080/v1)"
    echo "  MODEL_PATH        Path to the model"
    echo ""
    echo "Options:"
    echo "  -h, --help        Show this help message"
    echo "  --test            Run test mode (validate setup only)"
    echo ""
    echo "Examples:"
    echo "  # Run with default settings"
    echo "  bash run_pipeline.sh"
    echo ""
    echo "  # Run with custom batch size and pool size"
    echo "  BATCH_SIZE=100 POOL_SIZE=200 bash run_pipeline.sh"
    echo ""
    echo "  # Run with custom quality threshold"
    echo "  QUALITY_THRESHOLD=0.8 bash run_pipeline.sh"
}

# Function to run test mode
run_test_mode() {
    print_info "Running in test mode - validating setup..."
    
    check_prerequisites
    validate_model_path
    create_directories
    check_input_files
    
    print_success "Test mode completed - setup is valid!"
    print_info "You can now run the full pipeline without --test flag"
    exit 0
}

# Main execution starts here
main() {
    # Parse command line arguments
    case "$1" in
        -h|--help)
            show_help
            exit 0
            ;;
        --test)
            run_test_mode
            ;;
        *)
            # Continue with normal execution
            ;;
    esac
    
    # Run the pipeline
    display_config
    check_prerequisites
    validate_model_path
    create_directories
    check_input_files
    
    # Step 1: Text Processing and Initial Analysis
    if ! run_step "Processing text files" "1" \
        "python text_main_batch_inference.py \
            --txt_path '$INPUT_DIR' \
            --storage_folder '$OUTPUT_DIR' \
            --index 9 \
            --parallel_batch_size '$BATCH_SIZE' \
            --selected_task_number '$TASK_NUMBER'"; then
        exit 1
    fi
    
    # Step 2: Data Cleaning
    if ! run_step "Cleaning and formatting data" "2" \
        "python clean_text_data.py \
            --input_file '$OUTPUT_DIR/total_response.pkl' \
            --output_file '$OUTPUT_DIR'"; then
        exit 1
    fi
    
    # Step 3: QA Generation
    if ! run_step "Generating QA pairs" "3" \
        "python text_qa_generation.py \
            --file_path '$OUTPUT_DIR/total_response.json' \
            --index 343 \
            --pool_size '$POOL_SIZE' \
            --output_file '$OUTPUT_DIR' \
            --ark_url '$ARK_URL' \
            --api_key '$ARK_API_KEY' \
            --model '$MODEL_PATH'"; then
        exit 1
    fi
    
    # Step 4: Generate final report
    generate_final_report
    
    print_success "Pipeline completed successfully!"
    print_info "Results saved to: $OUTPUT_DIR"
    
    # Step 5: Optional Quality Check
    ask_quality_check
    
    echo ""
    echo -e "${GREEN}============================================${NC}"
    echo -e "${GREEN}🎉 All tasks completed successfully!${NC}"
    echo -e "${GREEN}============================================${NC}"
    echo ""
    print_info "Next steps:"
    echo "  • Review the generated QA pairs in $OUTPUT_DIR"
    echo "  • Check quality reports if you ran quality check"
    echo "  • Consider running human review for critical applications"
    echo ""
}

# Run main function with all arguments
main "$@"