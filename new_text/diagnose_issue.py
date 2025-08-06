#!/usr/bin/env python3
"""
Diagnose the OpenAI retry issue
"""

import os
import sys

print("=== Diagnosing OpenAI Retry Issue ===\n")

# Check Python modules
print("1. Checking Python modules:")
modules = ['openai', 'httpx', 'asyncio']
for module in modules:
    try:
        __import__(module)
        print(f"   ✓ {module} is available")
    except ImportError:
        print(f"   ✗ {module} is NOT available")

# Check environment variables
print("\n2. Environment variables:")
print(f"   USE_MOCK_API: {os.environ.get('USE_MOCK_API', 'Not set')}")
print(f"   ARK_URL: {os.environ.get('ARK_URL', 'Not set')}")

# Check API configuration in code
print("\n3. API Configuration (from code):")
print("   ark_url: http://0.0.0.0:8080/v1")
print("   api_key: ae37bba4-73be-4c22-b1a7-c6b1f5ec3a4b")

print("\n=== Analysis ===")
print("\nThe retry messages occur because:")
print("1. The OpenAI library is trying to connect to http://0.0.0.0:8080/v1")
print("2. This endpoint is not accessible (server not running)")
print("3. OpenAI client retries failed requests automatically")
print("4. Each of the 5 tasks generates retry messages")

print("\n=== Solution ===")
print("\n1. Quick fix - Use mock mode:")
print("   export USE_MOCK_API=true")
print("   python3 text_main_batch_inference_enhanced.py")
print("\n2. Or use the provided script:")
print("   ./run_with_mock.sh")
print("\n3. For production - Start the API server at port 8080")