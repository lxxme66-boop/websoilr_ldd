import argparse
import os
import re
import asyncio
import json

# Optional imports with fallbacks
try:
    from volcenginesdkarkruntime import Ark, AsyncArk
    VOLC_AVAILABLE = True
except ImportError:
    VOLC_AVAILABLE = False
    print("Warning: volcenginesdkarkruntime not available")

try:
    from openai import OpenAI, AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("Warning: openai not available")

from .prompts_conf import system_prompt, user_prompts

# API configuration
ark_url = "http://0.0.0.0:8080/v1"
api_key = "ae37bba4-73be-4c22-b1a7-c6b1f5ec3a4b"
model = "/mnt/storage/models/Skywork/Skywork-R1V3-38B"

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
os.makedirs("TextGeneration/logs", exist_ok=True)
current_time = os.path.getmtime(__file__) if os.path.exists(__file__) else 0
file_handler = logging.FileHandler(f"TextGeneration/logs/text_generation_{current_time}.log")


def extract_text_chunks(text_content, chunk_size=2000, overlap=200):
    """
    Extract text chunks from the content for processing.
    """
    chunks = []
    text_length = len(text_content)
    
    if text_length <= chunk_size:
        return [text_content]
    
    start = 0
    while start < text_length:
        end = min(start + chunk_size, text_length)
        
        # Try to find a natural break point (sentence end)
        if end < text_length:
            for sep in ['\n\n', '。\n', '。', '.\n', '.', '\n']:
                last_sep = text_content[start:end].rfind(sep)
                if last_sep != -1:
                    end = start + last_sep + len(sep)
                    break
        
        chunk = text_content[start:end]
        chunks.append(chunk)
        
        # Move start position with overlap
        start = end - overlap if end < text_length else end
    
    return chunks


async def parse_txt(file_path, index=9):
    """
    Parse txt file and create tasks for processing.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        return []
    
    if not content.strip():
        logger.warning(f"Empty file: {file_path}")
        return []
    
    # Extract text chunks
    chunks = extract_text_chunks(content)
    logger.info(f"Extracted {len(chunks)} chunks from {file_path}")
    
    tasks = []
    for i, chunk in enumerate(chunks):
        task = input_text_process(
            chunk, 
            os.path.basename(file_path),
            chunk_index=i,
            total_chunks=len(chunks),
            prompt_index=index
        )
        tasks.append(task)
    
    return tasks


async def input_text_process(text_content, source_file, chunk_index=0, total_chunks=1, prompt_index=9):
    """
    Process text content using the specified prompt.
    """
    # Check if we should use mock mode
    use_mock = os.environ.get('USE_MOCK_API', 'false').lower() == 'true'
    
    if use_mock or not OPENAI_AVAILABLE:
        # Return mock data for testing
        logger.warning("Using mock mode for text processing")
        result = {
            "content": f"Mock QA for {source_file} chunk {chunk_index + 1}/{total_chunks}:\nQ: What is discussed in this text?\nA: The text discusses semiconductor technology and related concepts.",
            "source_file": source_file,
            "chunk_index": chunk_index,
            "total_chunks": total_chunks,
            "text_content": text_content[:500] + "..." if len(text_content) > 500 else text_content,
            "qa_pairs": [
                {
                    "question": "What is the main topic of this text?",
                    "answer": "The text discusses semiconductor technology.",
                    "reasoning": "Based on the content analysis."
                }
            ]
        }
        return result
    
    try:
        client = AsyncOpenAI(
            api_key=api_key,
            base_url=ark_url
        )
    except Exception as e:
        logger.error(f"Failed to create OpenAI client: {e}")
        # Return mock data if client creation fails
        return {
            "content": f"Error creating client, returning mock data for {source_file}",
            "source_file": source_file,
            "chunk_index": chunk_index,
            "total_chunks": total_chunks,
            "text_content": text_content[:500] + "..." if len(text_content) > 500 else text_content
        }
    
    try:
        user_prompt = user_prompts[prompt_index]
        
        # Format the prompt with the text content
        # Check if the prompt expects markdown_content or text_content
        if '{markdown_content}' in user_prompt:
            formatted_prompt = user_prompt.format(
                markdown_content=text_content,
                source_file=source_file,
                chunk_info=f"(Chunk {chunk_index + 1}/{total_chunks})" if total_chunks > 1 else ""
            )
        elif '{text_content}' in user_prompt:
            formatted_prompt = user_prompt.format(
                text_content=text_content,
                source_file=source_file,
                chunk_info=f"(Chunk {chunk_index + 1}/{total_chunks})" if total_chunks > 1 else ""
            )
        else:
            # For prompts that don't have placeholders, just use the prompt as is
            formatted_prompt = user_prompt
        
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user", 
                    "content": formatted_prompt
                }
            ],
            temperature=0.8,
            max_tokens=4096,
            top_p=0.9,
        )
        
        content = response.choices[0].message.content
        
        # Structure the response
        result = {
            "content": content,
            "source_file": source_file,
            "chunk_index": chunk_index,
            "total_chunks": total_chunks,
            "text_content": text_content[:500] + "..." if len(text_content) > 500 else text_content
        }
        
        logger.info(f"Successfully processed chunk {chunk_index + 1}/{total_chunks} from {source_file}")
        return result
        
    except Exception as e:
        logger.error(f"Error processing text from {source_file}: {e}")
        return None


def merge_chunk_responses(responses):
    """
    Merge responses from multiple chunks of the same file.
    """
    if not responses:
        return []
    
    # Group by source file
    file_groups = {}
    for resp in responses:
        if resp and 'source_file' in resp:
            source = resp['source_file']
            if source not in file_groups:
                file_groups[source] = []
            file_groups[source].append(resp)
    
    # Merge chunks for each file
    merged_responses = []
    for source_file, chunks in file_groups.items():
        # Sort by chunk index
        chunks.sort(key=lambda x: x.get('chunk_index', 0))
        
        # Combine content
        combined_content = []
        all_text_content = []
        
        for chunk in chunks:
            combined_content.append(chunk['content'])
            all_text_content.append(chunk.get('text_content', ''))
        
        merged_response = {
            "content": "\n\n".join(combined_content),
            "source_file": source_file,
            "full_text": "\n".join(all_text_content)
        }
        
        merged_responses.append(merged_response)
    
    return merged_responses