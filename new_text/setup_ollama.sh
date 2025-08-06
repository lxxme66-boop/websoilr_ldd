#!/bin/bash

echo "Setting up Ollama for local model support..."

# Check if running on Linux
if [[ "$OSTYPE" != "linux-gnu"* ]]; then
    echo "This script is designed for Linux systems."
    exit 1
fi

# Install Ollama
echo "Installing Ollama..."
curl -fsSL https://ollama.ai/install.sh | sh

# Check if installation was successful
if ! command -v ollama &> /dev/null; then
    echo "Ollama installation failed!"
    exit 1
fi

echo "Ollama installed successfully!"

# Start Ollama service
echo "Starting Ollama service..."
ollama serve &
OLLAMA_PID=$!

# Wait for service to start
sleep 5

# Pull the qwen:7b model
echo "Pulling qwen:7b model (this may take a while)..."
ollama pull qwen:7b

# Check if model was pulled successfully
if ollama list | grep -q "qwen:7b"; then
    echo "qwen:7b model pulled successfully!"
else
    echo "Failed to pull qwen:7b model"
    echo "You can try pulling it manually with: ollama pull qwen:7b"
fi

echo ""
echo "Ollama setup complete!"
echo "Ollama is running in the background (PID: $OLLAMA_PID)"
echo ""
echo "To stop Ollama: kill $OLLAMA_PID"
echo "To run Ollama manually: ollama serve"
echo "To pull additional models: ollama pull <model-name>"
echo ""
echo "Available models for Chinese text processing:"
echo "  - qwen:7b (already pulled)"
echo "  - qwen:14b"
echo "  - qwen:32b"
echo "  - yi:6b"
echo "  - yi:34b"