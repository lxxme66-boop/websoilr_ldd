from Qwen.dataargument import get_total_responses_txt, check_data_quality_txt
import asyncio
import json
import pandas as pd
import argparse
import os

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate QA pairs from text data")
    parser.add_argument("--index", type=int, default=343, help="index for the qa generation task")
    parser.add_argument("--file_path", type=str, default="/workspace/data/txt_output/total_response.json", help="path to the input json file")
    parser.add_argument("--txt_folder", type=str, default="/workspace/data/txt_files", help="path to the text folder")
    parser.add_argument("--pool_size", type=int, default=100, help="number of parallel tasks")
    parser.add_argument("--output_file", type=str, default="/workspace/data/txt_output", help="path to the output json file")
    parser.add_argument("--ark_url", type=str, default="http://0.0.0.0:8080/v1", help="ARK API URL")
    parser.add_argument("--api_key", type=str, default="ae37bba4-73be-4c22-b1a7-c6b1f5ec3a4b", help="ARK API key")
    parser.add_argument("--model", type=str, default="/mnt/storage/models/Skywork/Skywork-R1V3-38B", help="Model to use for checking data quality")
    parser.add_argument("--check_times", type=int, default=9, help="Number of times to check data quality")
    parser.add_argument("--check_task", type=bool, default=False, help="Whether to check data quality or not")
    parser.add_argument("--check_indexes", type=tuple, default=(40,37,38), help="Indexes to check data quality for")
    parser.add_argument("--user_stream", default=False, type=bool)
    args = parser.parse_args()
    
    file_path = args.file_path
    output_file = os.path.join(args.output_file, f"results_{args.index}.json")
    txt_folder = args.txt_folder
    pool_size = args.pool_size
    
    if not args.check_task:
        index = args.index
        stream = args.user_stream
        results = asyncio.run(get_total_responses_txt(index, file_path, txt_folder, pool_size, stream=stream))
        with open(output_file, 'w') as f:
            json.dump(results, f, ensure_ascii=False, indent=4)
    else:
        ark_url = args.ark_url
        api_key = args.api_key
        model = args.model
        check_indexes = args.check_indexes
        check_times = args.check_times
        # apply different model to check the data quality
        asyncio.run(check_data_quality_txt(ark_url, api_key, model, output_file, check_indexes, pool_size=pool_size, check_times=check_times, stream=args.user_stream))