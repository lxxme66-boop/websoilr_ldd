#!/bin/bash

# Run the syndata pipeline
echo "Starting syndata pipeline..."

# Set environment variables if needed
export docstore_path="${docstore_path:-/default/docstore}"
export chroma_db="${chroma_db:-/default/chroma}"
export storage_dir="${storage_dir:-/default/storage}"
export similarity_top_k="${similarity_top_k:-10}"

# Run the Python script
python3 -m utils.syndata_pipeline_v3

echo "Pipeline execution completed"