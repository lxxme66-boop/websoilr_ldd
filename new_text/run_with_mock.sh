#!/bin/bash

# Enable mock API mode to avoid OpenAI connection issues
export USE_MOCK_API=true

# Run the text processing script
echo "Running text processing in mock mode..."
python3 text_main_batch_inference_enhanced.py "$@"