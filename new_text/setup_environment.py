#!/usr/bin/env python3
"""
Environment setup and diagnostics for text processing
"""

import os
import sys
import subprocess

def check_dependencies():
    """Check if required dependencies are installed"""
    dependencies = {
        'openai': False,
        'httpx': False,
        'asyncio': True,  # Built-in
        'json': True,     # Built-in
    }
    
    print("Checking dependencies...")
    for dep, required in dependencies.items():
        try:
            __import__(dep)
            print(f"✓ {dep} is installed")
            dependencies[dep] = True
        except ImportError:
            if required:
                print(f"✗ {dep} is NOT installed (required)")
            else:
                print(f"✗ {dep} is NOT installed (optional)")
    
    return dependencies

def check_api_endpoint():
    """Check if the API endpoint is accessible"""
    api_url = "http://0.0.0.0:8080/v1"
    print(f"\nChecking API endpoint: {api_url}")
    
    try:
        import httpx
        client = httpx.Client(timeout=5.0)
        response = client.get(f"{api_url}/models")
        print(f"✓ API endpoint is accessible (status: {response.status_code})")
        return True
    except Exception as e:
        print(f"✗ API endpoint is NOT accessible: {e}")
        return False

def setup_mock_mode():
    """Set up environment for mock mode"""
    print("\nSetting up mock mode...")
    os.environ['USE_MOCK_API'] = 'true'
    print("✓ Mock mode enabled (USE_MOCK_API=true)")

def install_missing_dependencies():
    """Offer to install missing dependencies"""
    print("\nWould you like to install missing dependencies? (y/n)")
    response = input().strip().lower()
    
    if response == 'y':
        print("Installing dependencies...")
        subprocess.run([sys.executable, "-m", "pip", "install", "openai", "httpx"], check=True)
        print("✓ Dependencies installed")
    else:
        print("Skipping dependency installation")

def main():
    print("=== Text Processing Environment Setup ===\n")
    
    # Check dependencies
    deps = check_dependencies()
    
    # Check API endpoint
    api_available = False
    if deps.get('httpx'):
        api_available = check_api_endpoint()
    
    # Determine mode
    if not deps.get('openai') or not api_available:
        print("\n⚠️  OpenAI library not available or API endpoint not accessible")
        print("   The system will run in MOCK MODE")
        setup_mock_mode()
        
        if not deps.get('openai'):
            install_missing_dependencies()
    else:
        print("\n✓ All dependencies available and API accessible")
        print("   The system can run in PRODUCTION MODE")
    
    print("\n=== Setup Complete ===")
    print("\nTo run the text processing:")
    print("  - With mock mode: ./run_with_mock.sh")
    print("  - Normal mode: python3 text_main_batch_inference_enhanced.py")

if __name__ == "__main__":
    main()