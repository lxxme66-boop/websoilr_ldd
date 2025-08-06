#!/usr/bin/env python3
"""
Test script for Text QA Generation Pipeline
Tests each module individually and the complete pipeline
"""

import os
import sys
import json
import asyncio
import logging

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_text_generation_module():
    """Test the TextGeneration module"""
    print("\n=== Testing TextGeneration Module ===")
    try:
        from TextGeneration.Datageneration import extract_text_chunks, parse_txt
        from TextGeneration.prompts_conf import system_prompt, user_prompts
        
        # Test text chunking
        sample_text = "This is a test. " * 200
        chunks = extract_text_chunks(sample_text, chunk_size=500, overlap=50)
        print(f"✓ Text chunking works: {len(chunks)} chunks created")
        
        # Test prompt loading
        print(f"✓ System prompt loaded: {len(system_prompt)} characters")
        print(f"✓ User prompts loaded: {len(user_prompts)} prompts")
        
        return True
    except Exception as e:
        print(f"✗ TextGeneration module test failed: {e}")
        return False


def test_data_cleaning_module():
    """Test the data cleaning module"""
    print("\n=== Testing Data Cleaning Module ===")
    try:
        from clean_text_data import clean_process, merge_chunked_responses
        
        # Test JSON pattern matching
        import re
        pattern = re.compile(r"```json\s*(\{[\s\S]*?\})\s*```", re.DOTALL)
        test_content = '```json\n{"test": "value"}\n```'
        matches = pattern.findall(test_content)
        assert len(matches) == 1
        print("✓ JSON extraction pattern works")
        
        # Test response merging
        test_responses = [
            {'source_file': 'test.txt', 'chunk_index': 0, 'total_chunks': 2, 'qa_pairs': [{'q': '1'}]},
            {'source_file': 'test.txt', 'chunk_index': 1, 'total_chunks': 2, 'qa_pairs': [{'q': '2'}]}
        ]
        merged = merge_chunked_responses(test_responses)
        print(f"✓ Response merging works: {len(merged)} merged responses")
        
        return True
    except Exception as e:
        print(f"✗ Data cleaning module test failed: {e}")
        return False


def test_qa_generation_module():
    """Test the QA generation module"""
    print("\n=== Testing QA Generation Module ===")
    try:
        from TextQA.dataargument import select_question_types
        from text_qa_generation import generate_qa_statistics
        
        # Test question type selection
        target_dist = {'factual': 0.15, 'comparison': 0.15, 'reasoning': 0.50, 'open_ended': 0.20}
        selected = select_question_types(0, 100, target_dist)
        print(f"✓ Question type selection works: {selected}")
        
        # Test statistics generation
        test_data = [{
            'source_file': 'test.txt',
            'qa_pairs': [
                {'question': 'Q1?', 'answer': 'A1', 'question_type': 'factual'},
                {'question': 'Q2?', 'answer': 'A2', 'question_type': 'reasoning'}
            ]
        }]
        stats = generate_qa_statistics(test_data)
        print(f"✓ Statistics generation works: {stats['total_qa_pairs']} QA pairs")
        
        return True
    except Exception as e:
        print(f"✗ QA generation module test failed: {e}")
        return False


def test_enhanced_quality_checker():
    """Test the enhanced quality checker module"""
    print("\n=== Testing Enhanced Quality Checker ===")
    try:
        from TextQA.enhanced_quality_checker import EnhancedQualityChecker, TextQAQualityIntegrator
        
        # Test integrator initialization
        config = {
            'api': {'api_key': 'test', 'ark_url': 'http://test'},
            'models': {'qa_generator_model': {'path': 'test_model'}},
            'quality_control': {'parallel_core': 2, 'activate_stream': False}
        }
        integrator = TextQAQualityIntegrator(config)
        print("✓ Enhanced quality integrator initialization works")
        
        # Test quality checker initialization
        checker = EnhancedQualityChecker(
            api_key='test',
            base_url='http://test',
            model='test_model',
            system_prompt='test prompt',
            parallel_core=2
        )
        print("✓ Enhanced quality checker initialization works")
        
        # Test prompt templates
        assert 'answer_generation' in checker.quality_check_prompts
        assert 'answer_verification' in checker.quality_check_prompts
        print("✓ Quality check prompt templates loaded")
        
        return True
    except Exception as e:
        print(f"✗ Enhanced quality checker test failed: {e}")
        return False


def test_file_structure():
    """Test if all required files and directories exist"""
    print("\n=== Testing File Structure ===")
    
    required_files = [
        'text_main_batch_inference.py',
        'clean_text_data.py',
        'text_qa_generation.py',
        'run_pipeline.sh',
        'config.json',
        'requirements.txt',
        'README.md'
    ]
    
    required_dirs = [
        'TextGeneration',
        'TextQA',
        'data',
        'data/input_texts',
        'data/output'
    ]
    
    all_good = True
    
    for file in required_files:
        if os.path.exists(file):
            print(f"✓ {file} exists")
        else:
            print(f"✗ {file} missing")
            all_good = False
    
    for dir in required_dirs:
        if os.path.isdir(dir):
            print(f"✓ {dir}/ exists")
        else:
            print(f"✗ {dir}/ missing")
            os.makedirs(dir, exist_ok=True)
            print(f"  → Created {dir}/")
    
    return all_good


def test_sample_data():
    """Test if sample data exists"""
    print("\n=== Testing Sample Data ===")
    
    sample_file = 'data/input_texts/sample_igzo_tft.txt'
    if os.path.exists(sample_file):
        with open(sample_file, 'r', encoding='utf-8') as f:
            content = f.read()
        print(f"✓ Sample file exists: {len(content)} characters")
        
        # Check content
        if 'IGZO' in content and 'TFT' in content:
            print("✓ Sample file contains relevant content")
            return True
        else:
            print("✗ Sample file content seems incorrect")
            return False
    else:
        print(f"✗ Sample file {sample_file} not found")
        return False


def test_config_loading():
    """Test configuration loading"""
    print("\n=== Testing Configuration ===")
    
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        # Check key sections
        required_sections = ['models', 'api', 'question_generation', 'processing']
        for section in required_sections:
            if section in config:
                print(f"✓ Config section '{section}' exists")
            else:
                print(f"✗ Config section '{section}' missing")
                return False
        
        # Check question type ratios
        ratios = config['question_generation']['question_type_ratios']
        total = sum(ratios.values())
        print(f"✓ Question type ratios sum to {total:.2f}")
        
        if abs(total - 1.0) < 0.01:
            print("✓ Question type ratios are properly normalized")
        else:
            print("✗ Question type ratios don't sum to 1.0")
            return False
        
        return True
    except Exception as e:
        print(f"✗ Config loading failed: {e}")
        return False


def main():
    """Run all tests"""
    print("Text QA Generation Pipeline Test Suite")
    print("=" * 50)
    
    tests = [
        ("File Structure", test_file_structure),
        ("Configuration", test_config_loading),
        ("Sample Data", test_sample_data),
        ("TextGeneration Module", test_text_generation_module),
        ("Data Cleaning Module", test_data_cleaning_module),
        ("QA Generation Module", test_qa_generation_module),
        ("Enhanced Quality Checker", test_enhanced_quality_checker)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "PASSED" if result else "FAILED"
        symbol = "✓" if result else "✗"
        print(f"{symbol} {test_name}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! The pipeline is ready to use.")
        print("\nTo run the pipeline, use:")
        print("  bash run_pipeline.sh")
    else:
        print("\n⚠️  Some tests failed. Please fix the issues before running the pipeline.")
        sys.exit(1)


if __name__ == "__main__":
    main()