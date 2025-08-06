import os
from openai import OpenAI, AsyncOpenAI
from Doubao.prompts_conf import system_prompt, user_prompts
import asyncio
import json
import pandas as pd
import re

# API configuration
qwen_url = "http://0.0.0.0:8080/v1"
api_key = "ae37bba4-73be-4c22-b1a7-c6b1f5ec3a4b"
model = "/mnt/storage/models/Skywork/Skywork-R1V3-38B"

async def get_response_txt(input_prompt, file_path=None, api_key=api_key, qwen_url=qwen_url, model=model, stream=False):
    """
    Get response from model for text-only input
    """
    client = AsyncOpenAI(
        api_key=api_key,
        base_url=qwen_url if qwen_url != None else None,
    )
    
    reasoning_content = ""
    answer_content = ""

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
                {"type": "text", "text": input_prompt}
            ]
        }
    ]
    
    print(f"Stream mode: {stream}")
    completion = await client.chat.completions.create(
        model=model,
        messages=messages,
        stream=stream,
    )
    
    if stream:
        async for chunk in completion:
            if not chunk.choices:
                print("\nUsage:")
                print(chunk.usage)
            else:
                delta = chunk.choices[0].delta
                if hasattr(delta, 'reasoning_content') and delta.reasoning_content != None:
                    reasoning_content += delta.reasoning_content
                else:
                    answer_content += delta.content
    else:
        if not completion.choices:
            print("\nUsage:")
            print(completion.usage)
            return None
        answer_content = completion.choices[0].message.content
        reasoning_content = getattr(completion.choices[0].message, 'reasoning_content', "")
    
    if reasoning_content is None and answer_content is None:
        print("Error: reasoning_content or answer_content is None")
        return None
    
    return {"content": answer_content, "reasoning": reasoning_content}


async def process_single_txt_response(response, index, txt_folder, stream=False):
    """
    Process a single text response to generate QA
    """
    try:
        # Extract text file path
        file_path = response.get('file_path', '')
        if not file_path:
            return None
            
        # Read the original text content
        text_content = ""
        if 'text_content' in response:
            text_content = response['text_content']
        else:
            # Try to read from file
            full_path = os.path.join(txt_folder, file_path) if not os.path.isabs(file_path) else file_path
            if os.path.exists(full_path):
                with open(full_path, 'r', encoding='utf-8') as f:
                    text_content = f.read()
        
        if not text_content:
            print(f"No text content found for {file_path}")
            return None
        
        # Format prompt
        prompt = user_prompts[index].format(text_content=text_content)
        
        # Get response
        result = await get_response_txt(prompt, file_path, stream=stream)
        if result is None:
            return None
            
        # Parse JSON response
        try:
            content = result['content']
            # Extract JSON from markdown code block if present
            json_pattern = re.compile(r"```json\s*(\{[\s\S]*?\})\s*```", re.DOTALL)
            matches = json_pattern.findall(content)
            if matches:
                qa_data = json.loads(matches[-1])
            else:
                qa_data = json.loads(content)
            
            qa_data['file_path'] = file_path
            qa_data['reasoning_content'] = result.get('reasoning', '')
            return qa_data
            
        except Exception as e:
            print(f"Error parsing response for {file_path}: {e}")
            return None
            
    except Exception as e:
        print(f"Error processing response: {e}")
        return None


async def get_total_responses_txt(index, file_path, txt_folder, pool_size, stream=False):
    """
    Process all text responses to generate QA pairs
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        responses = json.load(f)
    
    results = []
    tasks = []
    
    # Create tasks
    for response in responses:
        task = asyncio.create_task(
            process_single_txt_response(response, index, txt_folder, stream)
        )
        tasks.append(task)
    
    # Process in batches
    for i in range(0, len(tasks), pool_size):
        batch_tasks = tasks[i:i + pool_size]
        batch_results = await asyncio.gather(*batch_tasks)
        
        for result in batch_results:
            if result is not None:
                results.append(result)
        
        print(f"Processed {min(i + pool_size, len(tasks))}/{len(tasks)} responses")
    
    return results


async def check_single_qa(qa_data, check_index, api_key, qwen_url, model, stream=False):
    """
    Check quality of a single QA pair
    """
    prompt = user_prompts[check_index].format(
        question=qa_data.get('question', ''),
        answer=qa_data.get('answer', ''),
        reasoning=qa_data.get('reasoning', ''),
        vqa_data=json.dumps(qa_data, ensure_ascii=False)
    )
    
    result = await get_response_txt(prompt, stream=stream)
    if result is None:
        return None
        
    try:
        content = result['content']
        # Try to parse as number first
        if content.strip() in ['1', '-1']:
            return int(content.strip())
        # Try to parse JSON
        return json.loads(content)
    except:
        return None


async def check_data_quality_txt(ark_url, api_key, model, output_file, check_indexes, pool_size=10, check_times=3, stream=False):
    """
    Check data quality for text QA pairs
    """
    with open(output_file, 'r', encoding='utf-8') as f:
        qa_data_list = json.load(f)
    
    valid_data = []
    
    for qa_data in qa_data_list:
        passed_checks = 0
        
        for check_index in check_indexes:
            check_results = []
            
            # Check multiple times
            for _ in range(check_times):
                result = await check_single_qa(
                    qa_data, check_index, api_key, ark_url, model, stream
                )
                if result is not None:
                    if isinstance(result, int):
                        check_results.append(result)
                    elif isinstance(result, dict) and result.get('useful') == 1:
                        check_results.append(1)
                    else:
                        check_results.append(-1)
            
            # Majority vote
            if check_results.count(1) > len(check_results) / 2:
                passed_checks += 1
        
        # If passed all checks, add to valid data
        if passed_checks == len(check_indexes):
            valid_data.append(qa_data)
    
    # Save valid data
    output_path = output_file.replace('.json', '_checked.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(valid_data, f, ensure_ascii=False, indent=4)
    
    print(f"Data quality check completed. {len(valid_data)}/{len(qa_data_list)} passed.")
    print(f"Valid data saved to {output_path}")