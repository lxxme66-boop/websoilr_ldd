import base64
import argparse
import os
from volcenginesdkarkruntime import Ark, AsyncArk
from openai import OpenAI, AsyncOpenAI
import os
import re
from .prompts_conf import system_prompt, user_prompts
import asyncio
import json
import logging

# API configuration
ark_url = "http://0.0.0.0:8080/v1"
api_key = "ae37bba4-73be-4c22-b1a7-c6b1f5ec3a4b"
model = "/mnt/storage/models/Skywork/Skywork-R1V3-38B"

# Setup logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
os.makedirs("Doubao/logs", exist_ok=True)
current_time = os.path.getmtime(__file__)
file_handler = logging.FileHandler(f"Doubao/logs/doubao_{current_time}.log")


def extract_text_content(txt_file_path):
    """
    Extract text content from a txt file
    """
    try:
        with open(txt_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return content
    except Exception as e:
        logger.error(f"Error reading file {txt_file_path}: {e}")
        return None


def extract_txt_files(folder_path, processed_files=None):
    """
    Extract all txt files from a folder
    """
    if processed_files is None:
        processed_files = []
    
    txt_files = []
    metadata_file = os.path.join(folder_path, "metadata.json")
    
    # Read metadata if exists (optional)
    metadata = {}
    if os.path.exists(metadata_file):
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            logger.info(f"Loaded metadata from {metadata_file}")
        except Exception as e:
            logger.warning(f"Failed to load metadata from {metadata_file}: {e}")
            metadata = {}
    
    # Get all txt files in the folder
    for file in os.listdir(folder_path):
        if file.endswith('.txt') and file not in processed_files:
            file_path = os.path.join(folder_path, file)
            content = extract_text_content(file_path)
            if content:
                txt_info = {
                    "file_path": file_path,
                    "file_name": file,
                    "content": content,
                    "metadata": metadata.get(file, {})
                }
                txt_files.append(txt_info)
    
    return txt_files


async def get_request(input_prompt, text_content, file_path, ark):
    """
    Send request to the model for text processing
    """
    content = [
        {"type": "text", "text": input_prompt},
    ]
    
    try:
        response = await ark.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": [
                        {"type": "text", "text": system_prompt}
                    ]
                },
                {
                    "role": "user",
                    "content": content
                },
            ],
            temperature=1,
            max_tokens=16384,
            top_p=0.7,
            stop=None
        )
    except Exception as e:
        logger.error(f"Error in request: {e}")
        logger.error(f"Input prompt: {input_prompt}")
        return None
    
    content = response.choices[0].message.content
    reason_response = response.choices[0].message.reasoning_content
    
    logger.info(f"seperator: {'-'*50}")
    logger.info(f"Response content: {content}")
    logger.info(f"seperator: {'-'*50}") 
    logger.info(f"Reasoning response: {reason_response}")
    logger.info(f"seperator: {'-'*50}")
    
    return {
        "content": content, 
        "reason_response": reason_response,
        "file_path": file_path,
        "text_content": text_content
    }


async def parse_txt_folder(folder_path, index=5, processed_files=None):
    """
    Parse all txt files in a folder
    """
    inputs = extract_txt_files(folder_path, processed_files)
    
    if not inputs:
        logger.warning(f"No txt files found in {folder_path}")
        return []
    
    ark = AsyncOpenAI(api_key=api_key, base_url=ark_url)
    user_prompt = user_prompts[index]
    
    tasks = []
    for input_json in inputs:
        file_path = input_json["file_path"]
        text_content = input_json["content"]
        metadata = input_json["metadata"]
        
        # Format the prompt with text content
        input_prompt = user_prompt.format(
            text_content=text_content,
            file_path=file_path,
            metadata=json.dumps(metadata, ensure_ascii=False) if metadata else "{}"
        )
        
        if not os.path.exists(file_path):
            continue
            
        task = asyncio.create_task(
            get_request(input_prompt, text_content, file_path, ark)
        )
        tasks.append(task)
    
    return tasks


if __name__ == "__main__":
    folder_path = "/workspace/data/txt_files/sample_folder"
    asyncio.run(parse_txt_folder(folder_path, index=5))