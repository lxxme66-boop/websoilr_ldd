#!/bin/bash

# Text QA Generation Pipeline
# This script runs the complete pipeline for generating QA pairs from text documents

# Set default values
INPUT_DIR="${INPUT_DIR:-data/input_texts}"
OUTPUT_DIR="${OUTPUT_DIR:-data/output}"
BATCH_SIZE="${BATCH_SIZE:-50}"
POOL_SIZE="${POOL_SIZE:-100}"
TASK_NUMBER="${TASK_NUMBER:-1000}"

# API configuration
export ARK_API_KEY="${ARK_API_KEY:-ae37bba4-73be-4c22-b1a7-c6b1f5ec3a4b}"
export ARK_URL="${ARK_URL:-http://0.0.0.0:8080/v1}"
export MODEL_PATH="${MODEL_PATH:-/mnt/storage/models/Skywork/Skywork-R1V3-38B}"

echo "==================================="
echo "Text QA Generation Pipeline"
echo "==================================="
echo "Input directory: $INPUT_DIR"
echo "Output directory: $OUTPUT_DIR"
echo "Batch size: $BATCH_SIZE"
echo "Pool size: $POOL_SIZE"
echo "Target task number: $TASK_NUMBER"
echo "==================================="

# Create directories if they don't exist
mkdir -p "$INPUT_DIR"
mkdir -p "$OUTPUT_DIR"
mkdir -p "$OUTPUT_DIR/TEMP"

# Check if input directory has txt files
if [ -z "$(ls -A $INPUT_DIR/*.txt 2>/dev/null)" ]; then
    echo "Error: No .txt files found in $INPUT_DIR"
    echo "Please add text files to process."
    exit 1
fi

# Step 1: Text Processing and Initial Analysis
echo ""
echo "Step 1: Processing text files..."
python text_main_batch_inference.py \
    --txt_path "$INPUT_DIR" \
    --storage_folder "$OUTPUT_DIR" \
    --index 9 \
    --parallel_batch_size "$BATCH_SIZE" \
    --selected_task_number "$TASK_NUMBER"

if [ $? -ne 0 ]; then
    echo "Error in text processing step"
    exit 1
fi

# Step 2: Data Cleaning
echo ""
echo "Step 2: Cleaning and formatting data..."
python clean_text_data.py \
    --input_file "$OUTPUT_DIR/total_response.pkl" \
    --output_file "$OUTPUT_DIR"

if [ $? -ne 0 ]; then
    echo "Error in data cleaning step"
    exit 1
fi

# Step 3: QA Generation
echo ""
echo "Step 3: Generating QA pairs..."
python text_qa_generation.py \
    --file_path "$OUTPUT_DIR/total_response.json" \
    --index 343 \
    --pool_size "$POOL_SIZE" \
    --output_file "$OUTPUT_DIR" \
    --ark_url "$ARK_URL" \
    --api_key "$ARK_API_KEY" \
    --model "$MODEL_PATH"

if [ $? -ne 0 ]; then
    echo "Error in QA generation step"
    exit 1
fi

# Step 4: Generate final report
echo ""
echo "Step 4: Generating final report..."
python -c "
import json
import os

output_dir = '$OUTPUT_DIR'
results_file = os.path.join(output_dir, 'results_343.json')
stats_file = os.path.join(output_dir, 'results_343_stats.json')

if os.path.exists(stats_file):
    with open(stats_file, 'r', encoding='utf-8') as f:
        stats = json.load(f)
    
    print('\\n=== QA Generation Statistics ===')
    print(f'Total QA pairs generated: {stats[\"total_qa_pairs\"]}')
    print('\\nQuestion type distribution:')
    for q_type, percentage in stats['question_type_percentages'].items():
        count = stats['question_types'][q_type]
        print(f'  - {q_type}: {count} ({percentage})')
    print(f'\\nAverage question length: {stats[\"average_question_length\"]:.1f} characters')
    print(f'Average answer length: {stats[\"average_answer_length\"]:.1f} characters')
    print('\\nSource files processed:')
    for source, count in stats['source_files'].items():
        print(f'  - {source}: {count} QA pairs')
"

echo ""
echo "==================================="
echo "Pipeline completed successfully!"
echo "Results saved to: $OUTPUT_DIR"
echo "==================================="

# Optional: Run quality check
echo ""
read -p "Do you want to run quality check? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    read -p "Use enhanced quality check? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Running enhanced quality check..."
        python text_qa_generation.py \
            --file_path "$OUTPUT_DIR/results_343.json" \
            --output_file "$OUTPUT_DIR" \
            --check_task True \
            --enhanced_quality True \
            --quality_threshold 0.7 \
            --ark_url "$ARK_URL" \
            --api_key "$ARK_API_KEY" \
            --model "$MODEL_PATH"
    else
        echo "Running standard quality check..."
        python text_qa_generation.py \
            --file_path "$OUTPUT_DIR/results_343.json" \
            --output_file "$OUTPUT_DIR" \
            --check_task True \
            --enhanced_quality False \
            --check_indexes "(40, 37, 38)" \
            --check_times 5 \
            --ark_url "$ARK_URL" \
            --api_key "$ARK_API_KEY" \
            --model "$MODEL_PATH"
    fi
fi