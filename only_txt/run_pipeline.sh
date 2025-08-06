#!/bin/bash

# Text QA Generation Pipeline Script
# This script runs the complete pipeline for generating QA pairs from text files

# Default values
TXT_PATH="${1:-/workspace/data/txt_files}"
OUTPUT_PATH="${2:-/workspace/data/txt_output}"
INDEX1="${3:-43}"
INDEX2="${4:-343}"

echo "==================== Text QA Generation Pipeline ===================="
echo "Input Text Path: $TXT_PATH"
echo "Output Path: $OUTPUT_PATH"
echo "Text Extraction Index: $INDEX1"
echo "QA Generation Index: $INDEX2"
echo "===================================================================="

# Create output directory if not exists
mkdir -p $OUTPUT_PATH

# Step 1: Text extraction and initial processing
echo ""
echo "Step 1: Extracting and processing text files..."
python txt_main_batch_inference.py \
    --txt_path $TXT_PATH \
    --storage_folder $OUTPUT_PATH \
    --index $INDEX1 \
    --parallel_batch_size 50 \
    --selected_task_number 500

# Check if step 1 succeeded
if [ $? -ne 0 ]; then
    echo "Error in Step 1: Text extraction failed"
    exit 1
fi

# Step 2: Clean extracted data
echo ""
echo "Step 2: Cleaning extracted data..."
python clean_data.py \
    --input_file "$OUTPUT_PATH/total_response.pkl" \
    --output_file $OUTPUT_PATH

# Check if step 2 succeeded
if [ $? -ne 0 ]; then
    echo "Error in Step 2: Data cleaning failed"
    exit 1
fi

# Step 3: Generate QA pairs
echo ""
echo "Step 3: Generating QA pairs..."
python qwen_argument.py \
    --file_path "$OUTPUT_PATH/total_response.json" \
    --txt_folder $TXT_PATH \
    --output_file $OUTPUT_PATH \
    --index $INDEX2 \
    --pool_size 50

# Check if step 3 succeeded
if [ $? -ne 0 ]; then
    echo "Error in Step 3: QA generation failed"
    exit 1
fi

# Step 4: Data augmentation (convert to SFT format)
echo ""
echo "Step 4: Converting to SFT format..."
python argument_data.py \
    --input_file "$OUTPUT_PATH/results_${INDEX2}.json" \
    --output_file $OUTPUT_PATH \
    --indexes 21 \
    --poolSize 8 \
    --CheckQuestion -1

# Check if step 4 succeeded
if [ $? -ne 0 ]; then
    echo "Error in Step 4: Data augmentation failed"
    exit 1
fi

# Step 5: Quality check
echo ""
echo "Step 5: Checking data quality..."
python argument_data.py \
    --input_file "$OUTPUT_PATH/rephrased_responses_qa.json" \
    --output_file $OUTPUT_PATH \
    --indexes 22 \
    --poolSize 8 \
    --CheckQuestion 22

# Check if step 5 succeeded
if [ $? -ne 0 ]; then
    echo "Error in Step 5: Quality check failed"
    exit 1
fi

# Step 6: Generate final dataset
echo ""
echo "Step 6: Generating final dataset..."
python generate_dataset.py \
    --input_file "$OUTPUT_PATH/checked_responses_qa.json" \
    --output_file "$OUTPUT_PATH/final_data.json" \
    --root_folder $TXT_PATH

# Check if step 6 succeeded
if [ $? -ne 0 ]; then
    echo "Error in Step 6: Dataset generation failed"
    exit 1
fi

echo ""
echo "==================== Pipeline Completed Successfully ===================="
echo "Final dataset saved to: $OUTPUT_PATH/final_data.json"
echo "========================================================================"