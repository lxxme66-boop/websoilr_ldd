import base64
import argparse
import os
# 通过 pip install volcengine-python-sdk[ark] 安装方舟SDK
from volcenginesdkarkruntime import Ark, AsyncArk
from openai import OpenAI,AsyncOpenAI
import os
import re
from .prompts_conf import system_prompt, user_prompts
import asyncio
ark_url = "https://ark.cn-beijing.volces.com/api/v3"
api_key = "ae37bba4-73be-4c22-b1a7-c6b1f5ec3a4b" # my own api
model = "ep-20250707132521-j2q26"
#model = "doubao-lite-128k-240828"
# define logger
ark_url = "http://0.0.0.0:8080/v1"
model = "/mnt/storage/models/Skywork/Skywork-R1V3-38B"

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
os.makedirs("Doubao/logs", exist_ok=True)
current_time = os.path.getmtime(__file__)
file_handler = logging.FileHandler(f"Doubao/logs/doubao_{current_time}.log")

def extract_text_block(prev_idx, next_idx, content, text_content):
    """
    Extract text blocks between two indices (adapted for pure text).
    """
    text_blocks = []
    
    for block in content:
        if block["section_idx"] <= next_idx and block["section_idx"] >= prev_idx:
            if block["type"] == "text":
                text_blocks.append(block["text"])
            elif block["type"] == "section":
                text_blocks.append(f"## {block['title']}")
                if block.get('content'):
                    text_blocks.append(block['content'])
    
    # extract the content in text according to the first and last line in the text_blocks
    if not text_blocks:
        return ""
        
    first_block = text_blocks[0] 
    last_block = text_blocks[-1] 

    start_idx = text_content.find(first_block)
    end_idx = 0
    for last_block in reversed(text_blocks):
        last_idx = text_content.find(last_block, start_idx)
        if last_idx >= end_idx:
            end_idx = last_idx
    if start_idx == -1:
        while start_idx == -1 and text_blocks:
            text_blocks.pop(0)
            first_block = text_blocks[0] if text_blocks else ""
            start_idx = text_content.find(first_block)
    if start_idx == -1:
        logger.warning("No start index found for the first block in text content.")
        start_idx = 0
        return ""
  
    end_idx = end_idx + len(last_block)+1
    # logger.info(f"Extracting content from index {start_idx} to {end_idx} in text content. {prev_idx} {next_idx}")
    extracted_content = text_content[start_idx:end_idx]
    
    return extracted_content

def extract_parsing_text_result(output_dir, section_ranges=None):
    """
    Read the text content and its corresponding sections from the whole text file
    (adapted from PDF parsing to pure text parsing)
    """
    import json
    
    # Find content files
    potential_files = os.listdir(output_dir)
    content_json = None
    text_file = None
    
    for file in potential_files:
        if "_content_list.json" in file:
            content_json = os.path.join(output_dir, file)
        if ".txt" in file or ".md" in file:
            text_file = os.path.join(output_dir, file)

    if not content_json or not text_file:
        logger.error(f"Required files not found in {output_dir}")
        return []

    with open(content_json, "r", encoding='utf-8') as f:
        content = json.load(f)
    with open(text_file, "r", encoding='utf-8') as f:
        text_content = f.read()
        
    if section_ranges is not None:
        final_json_blocks = []
        while len(content):
            block = content.pop(0)
            for section_range in section_ranges:
                start_section, end_section = section_range
                if block["section_idx"] >= start_section-1 and block["section_idx"] <= end_section+1:
                    final_json_blocks.append(block)
                    break
        content = final_json_blocks
    
    # Group content by sections for text analysis
    section_groups = {}
    for block in content:
        section_idx = block.get("section_idx", 0)
        if section_idx not in section_groups:
            section_groups[section_idx] = []
        section_groups[section_idx].append(block)
    
    # Extract text content for each section
    text_analysis_tasks = []
    for section_idx, blocks in section_groups.items():
        # Find the range for this section
        next_section = section_idx + 1
        prev_section = section_idx - 1
        
        # Extract text content for this section
        section_text = extract_text_block(prev_section, next_section, blocks, text_content)
        
        if section_text and len(section_text.strip()) > 50:  # Minimum content length
            task_data = {
                'section_idx': section_idx,
                'text_content': section_text,
                'context': section_text[:500] + "..." if len(section_text) > 500 else section_text,
                'blocks': blocks
            }
            text_analysis_tasks.append(task_data)
    
    logger.info(f"Generated {len(text_analysis_tasks)} text analysis tasks")
    return text_analysis_tasks

async def parse_text_content(folder_path, index=9, section_ranges=None, processed_sections=None):
    """
    Parse text content and generate analysis tasks
    (adapted from parse_pdf for pure text processing)
    """
    if processed_sections is None:
        processed_sections = []
    
    try:
        text_tasks = extract_parsing_text_result(folder_path, section_ranges=section_ranges)
        
        if not text_tasks:
            logger.warning(f"No text tasks found in {folder_path}")
            return []
        
        # Filter out already processed sections
        filtered_tasks = []
        for task in text_tasks:
            section_key = f"{folder_path}/section_{task['section_idx']}"
            if section_key not in processed_sections:
                filtered_tasks.append(task)
        
        if not filtered_tasks:
            logger.info(f"All sections already processed in {folder_path}")
            return []
        
        # Generate async tasks for text analysis
        async_tasks = []
        for task_data in filtered_tasks:
            async_task = input_TextDoubao(
                text_content=task_data['text_content'],
                context=task_data['context'],
                section_path=f"{folder_path}/section_{task_data['section_idx']}",
                index=index
            )
            async_tasks.append(async_task)
        
        logger.info(f"Created {len(async_tasks)} async text analysis tasks")
        return async_tasks
        
    except Exception as e:
        logger.error(f"Error parsing text content in {folder_path}: {e}")
        return []

async def input_TextDoubao(text_content, context, section_path, index=9):
    """
    Process text content using Doubao API
    (adapted from input_ImgDoubao for pure text processing)
    """
    try:
        # Select appropriate prompt based on index
        if index in user_prompts:
            user_prompt = user_prompts[index]
        else:
            user_prompt = user_prompts[4]  # Default prompt
        
        # Prepare the prompt for text analysis
        analysis_prompt = f"""
        基于以下文本内容，进行深度分析：
        
        文本内容：
        {text_content}
        
        请分析并提供：
        1. 文本中的关键知识点
        2. 重要概念和技术术语
        3. 文本的主要内容描述
        4. 相关的技术背景和应用场景
        
        {user_prompt}
        """
        
        # Create async client
        client = AsyncOpenAI(
            api_key=api_key,
            base_url=ark_url if ark_url != "http://0.0.0.0:8080/v1" else ark_url
        )
        
        messages = [
            {
                "role": "system",
                "content": [
                    {"type": "text", "text": system_prompt}
                ]
            },
            {
                "role": "user", 
                "content": [
                    {"type": "text", "text": analysis_prompt}
                ]
            }
        ]
        
        # Make API call
        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.7,
            max_tokens=4096,
            top_p=0.9
        )
        
        # Extract response content
        content = response.choices[0].message.content if response.choices else ""
        
        result = {
            'section_path': section_path,
            'text_content': text_content,
            'context': context,
            'content': content,
            'analysis_result': content,
            'processing_index': index,
            'timestamp': asyncio.get_event_loop().time()
        }
        
        logger.info(f"Successfully processed text section: {section_path}")
        return result
        
    except Exception as e:
        logger.error(f"Error processing text content {section_path}: {e}")
        return None

async def batch_process_text_content(text_tasks, max_concurrent=10):
    """
    Process multiple text analysis tasks concurrently
    """
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def process_with_semaphore(task):
        async with semaphore:
            return await task
    
    # Process all tasks concurrently with semaphore
    results = await asyncio.gather(
        *[process_with_semaphore(task) for task in text_tasks],
        return_exceptions=True
    )
    
    # Filter out None results and exceptions
    valid_results = []
    for result in results:
        if result is not None and not isinstance(result, Exception):
            valid_results.append(result)
        elif isinstance(result, Exception):
            logger.error(f"Task failed with exception: {result}")
    
    logger.info(f"Completed {len(valid_results)} out of {len(text_tasks)} text analysis tasks")
    return valid_results

def save_text_analysis_results(results, output_file):
    """
    Save text analysis results to file
    """
    import json
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved {len(results)} text analysis results to {output_file}")
    except Exception as e:
        logger.error(f"Failed to save results to {output_file}: {e}")

# Utility functions for text processing
def clean_text_content(text):
    """Clean and normalize text content"""
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove special characters that might interfere with processing
    text = re.sub(r'[^\w\s\u4e00-\u9fff.,!?;:()[\]{}"-]', '', text)
    return text.strip()

def extract_key_terms(text):
    """Extract key technical terms from text"""
    # Technical terms related to semiconductor display
    tech_terms = [
        'TFT', 'OLED', '薄膜晶体管', '显示器', '背板', '栅极', 
        '介电层', '残影', '可靠性', '器件', '工艺', '制造'
    ]
    
    found_terms = []
    for term in tech_terms:
        if term in text:
            found_terms.append(term)
    
    return found_terms

def segment_long_text(text, max_length=2000):
    """Segment long text into smaller chunks for processing"""
    if len(text) <= max_length:
        return [text]
    
    segments = []
    sentences = text.split('。')
    current_segment = ""
    
    for sentence in sentences:
        if len(current_segment + sentence + '。') <= max_length:
            current_segment += sentence + '。'
        else:
            if current_segment:
                segments.append(current_segment)
            current_segment = sentence + '。'
    
    if current_segment:
        segments.append(current_segment)
    
    return segments