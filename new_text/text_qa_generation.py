from TextQA.dataargument import get_total_responses, check_data_quality
from TextQA.enhanced_quality_checker import TextQAQualityIntegrator
import asyncio
import json
import pandas as pd
import argparse
import os

async def main(index=343, file_path=None, pool_size=100, output_file=None, 
               ark_url="http://0.0.0.0:8080/v1", api_key="ae37bba4-73be-4c22-b1a7-c6b1f5ec3a4b",
               model="/mnt/storage/models/Skywork/Skywork-R1V3-38B", check_task=False,
               user_stream=False, enhanced_quality=True, quality_threshold=0.7):
    """
    Main function for QA generation that can be called by other modules
    
    Args:
        index: Index for the QA generation task
        file_path: Path to the input JSON file
        pool_size: Number of parallel tasks
        output_file: Path to the output folder
        ark_url: ARK API URL
        api_key: ARK API key
        model: Model to use for QA generation
        check_task: Whether to check data quality
        user_stream: Whether to use streaming
        enhanced_quality: Use enhanced quality checking
        quality_threshold: Quality threshold for enhanced checking
        
    Returns:
        List of generated QA pairs
    """
    if file_path is None:
        file_path = "/workspace/text_qa_generation/data/output/total_response.json"
    if output_file is None:
        output_file = "/workspace/text_qa_generation/data/output"
    
    # Ensure output_file is a directory, create the actual output file path
    if os.path.isdir(output_file) or not output_file.endswith('.json'):
        output_file_path = os.path.join(output_file, f"results_{index}.json")
        os.makedirs(output_file, exist_ok=True)
    else:
        output_file_path = output_file
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    if not check_task:
        results = await get_total_responses(index, file_path, pool_size, stream=user_stream)
        
        # Save results
        with open(output_file_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=4)
        print(f"Generated {len(results)} QA pairs, saved to {output_file_path}")
        
        # Generate statistics
        stats = generate_qa_statistics(results)
        stats_file = output_file_path.replace('.json', '_stats.json')
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=4)
        print(f"Statistics saved to {stats_file}")
        
        if enhanced_quality:
            # Use enhanced quality checking
            print("使用增强质量检查...")
            integrator = TextQAQualityIntegrator({
                'api': {'ark_url': ark_url, 'api_key': api_key},
                'models': {'quality_checker_model': {'path': model}}
            })
            
            quality_report = await integrator.enhanced_quality_check(
                qa_file_path=output_file_path,
                output_dir=os.path.dirname(output_file_path),
                quality_threshold=quality_threshold
            )
            print(f"Quality check completed. Pass rate: {quality_report.get('pass_rate', 0):.2%}")
        
        return results
    else:
        # Use original quality checking
        print("使用原有质量检查...")
        check_indexes = (40, 37, 38)
        check_times = 9
        await check_data_quality(ark_url, api_key, model, output_file_path, check_indexes, 
                                pool_size=pool_size, check_times=check_times, stream=user_stream)
        return []


def generate_qa_statistics(qa_data):
    """
    Generate statistics about the QA pairs.
    """
    stats = {
        'total_qa_pairs': 0,
        'question_types': {
            'factual': 0,
            'comparison': 0,
            'reasoning': 0,
            'open_ended': 0
        },
        'source_files': {},
        'average_answer_length': 0,
        'average_question_length': 0
    }
    
    total_answer_length = 0
    total_question_length = 0
    
    for item in qa_data:
        if 'qa_pairs' in item:
            qa_pairs = item['qa_pairs']
            stats['total_qa_pairs'] += len(qa_pairs)
            
            # Count by source file
            source = item.get('source_file', 'unknown')
            if source not in stats['source_files']:
                stats['source_files'][source] = 0
            stats['source_files'][source] += len(qa_pairs)
            
            # Count by question type and calculate lengths
            for qa in qa_pairs:
                q_type = qa.get('question_type', 'unknown')
                if q_type in stats['question_types']:
                    stats['question_types'][q_type] += 1
                    
                total_question_length += len(qa.get('question', ''))
                total_answer_length += len(qa.get('answer', ''))
    
    # Calculate averages
    if stats['total_qa_pairs'] > 0:
        stats['average_question_length'] = total_question_length / stats['total_qa_pairs']
        stats['average_answer_length'] = total_answer_length / stats['total_qa_pairs']
    
    # Calculate percentages
    stats['question_type_percentages'] = {}
    for q_type, count in stats['question_types'].items():
        if stats['total_qa_pairs'] > 0:
            percentage = (count / stats['total_qa_pairs']) * 100
            stats['question_type_percentages'][q_type] = f"{percentage:.1f}%"
    
    return stats

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate QA pairs from text.")
    parser.add_argument("--index", type=int, default=343, help="index for the qa generation task")
    parser.add_argument("--file_path", type=str, 
                        default="/workspace/text_qa_generation/data/output/total_response.json", 
                        help="path to the input json file")
    parser.add_argument("--pool_size", type=int, default=100, help="number of parallel tasks")
    parser.add_argument("--output_file", type=str, 
                        default="/workspace/text_qa_generation/data/output", 
                        help="path to the output folder")
    parser.add_argument("--ark_url", type=str, default="http://0.0.0.0:8080/v1", help="ARK API URL")
    parser.add_argument("--api_key", type=str, default="ae37bba4-73be-4c22-b1a7-c6b1f5ec3a4b", help="ARK API key")
    parser.add_argument("--model", type=str, default="/mnt/storage/models/Skywork/Skywork-R1V3-38B", 
                        help="Model to use for QA generation")
    parser.add_argument("--check_task", type=bool, default=False, help="Whether to check data quality or not")
    parser.add_argument("--user_stream", default=False, type=bool)
    parser.add_argument("--enhanced_quality", type=bool, default=True, help="Use enhanced quality checking")
    parser.add_argument("--quality_threshold", type=float, default=0.7, help="Quality threshold for enhanced checking")
    
    args = parser.parse_args()
    
    # Run the main function with parsed arguments
    results = asyncio.run(main(
        index=args.index,
        file_path=args.file_path,
        pool_size=args.pool_size,
        output_file=args.output_file,
        ark_url=args.ark_url,
        api_key=args.api_key,
        model=args.model,
        check_task=args.check_task,
        user_stream=args.user_stream,
        enhanced_quality=args.enhanced_quality,
        quality_threshold=args.quality_threshold
    ))