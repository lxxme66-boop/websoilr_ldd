import base64
import argparse
import os
from volcenginesdkarkruntime import Ark, AsyncArk
import os
import re
from Doubao.prompts_conf import system_prompt, user_prompts
import asyncio
import json

ark_url = "https://ark.cn-beijing.volces.com/api/v3"
api_key = "ecb26efc-05e7-4d58-8d40-0dca61ccb4e9"
model = "doubao-1.5-thinking-pro-m-250428"

async def modify_sft_response(responses, index, prompt_template):
    """
    Modify SFT response for text data
    """
    response = responses[index]
    question = response.get('question', '')
    answer = response.get('answer', '')
    choices = response.get('choices', [])
    reasoning = response.get('reasoning', '')
    lecture = response.get('lecture', '')
    context = response.get('context', '')
    file_path = response.get('file_path', '')
    
    prompt = prompt_template.format(
        question=question,
        answer=answer,
        choices=choices,
        reasoning=reasoning,
        lecture=lecture,
        context=context
    )
    
    ark = AsyncArk(api_key=api_key)
    
    async def get_request(input_prompt):
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
                        "content": [
                            {"type": "text", "text": input_prompt},
                        ]
                    },
                ],
                temperature=1,
                max_tokens=4096,
                top_p=0.7,
                stop=None
            )
            try:
                content = response.choices[0].message.content
                content = eval(content)
                content["choices"] = choices
                content["question"] = question
                content["answer"] = answer
                content["lecture"] = lecture
                content["context"] = context
            except Exception as e:
                print(f"Error in eval: {e}")
                return None
            return content
        except Exception as e:
            if 'ModelAccountTpmRateLimitExceeded' in str(e):
                print("Rate limit exceeded, waiting for 60 seconds...")
                await asyncio.sleep(60)
                return None
            else:
                print(f"Error in request: {e}")
                return None
    
    content = await get_request(prompt)
    if content is None:
        print(f"Response is None for index {index}, skipping...")
        return None
    content["file_path"] = file_path
    print(content)
    return content

async def check_ori_response(responses, prompt_template, batch_size=1):
    """
    Check original responses for quality
    """
    async def check_response(response, prompt_template):
        vqa_data = {}
        vqa_data["input"] = response.get("input", response.get("context", ""))
        vqa_data["instruction"] = response.get("instruction", response.get("question", ""))
        vqa_data["reasoning"] = response.get("reasoning", "")
        vqa_data["output"] = response.get("output", response.get("answer", ""))
        
        check_prompt = prompt_template.format(vqa_data=vqa_data)
        ark = AsyncArk(api_key=api_key)
        content = await ark.chat.completions.create(
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
                    "content": [
                        {"type": "text", "text": check_prompt},
                    ]
                },
            ],
            temperature=1,
            max_tokens=4096,
            top_p=0.7,
            stop=None
        )
        try:
            content = content.choices[0].message.content
            content = eval(content)
            return content, response
        except Exception as e:
            print(f"Error in eval: {e}")
            return None
    
    new_responses = []
    tasks = []
    for response in responses:
        task = asyncio.create_task(check_response(response, prompt_template))
        tasks.append(task)
    
    for i in range(0, len(tasks), batch_size):
        batches = tasks[i:i + batch_size]
        batches = await asyncio.gather(*batches)
        for t, data in enumerate(batches):
            if data is None:
                continue
            response, vqa_data = data
            if response is None:
                print(f"Response is None, skipping...")
                continue
            elif response["useful"]:
                new_responses.append(vqa_data)
            else:
                print(response)
                print(vqa_data)
    
    return new_responses

async def rephrase_response(responses, index, poolSize, CheckQuestion):
    """
    Rephrase responses for text data
    """
    response_index = 0
    tasks = []
    for i in range(len(responses)):
        task = asyncio.create_task(modify_sft_response(responses, i, user_prompts[index]))
        tasks.append(task)
    
    # Use asyncio.gather to run the tasks concurrently
    for i in range(0, len(tasks), poolSize):
        batch_tasks = tasks[i:i + poolSize]
        batch_responses = await asyncio.gather(*batch_tasks)
        for response in batch_responses:
            if response is not None:
                responses[response_index] = response
                response_index += 1
                print(f"Processed response {response_index}/{len(responses)}")
    return responses


if __name__ == "__main__":
    import json
    parser = argparse.ArgumentParser(description="Process text QA data")
    parser.add_argument("--input_file", type=str,
                        default="/workspace/data/txt_output/results_343.json",
                        help="path to the input json file")
    parser.add_argument("--output_file", type=str, 
                        default="/workspace/data/txt_output", 
                        help="path to the output folder")
    parser.add_argument("--indexes", type=int, default=21, 
                        help="indexes for rephrase prompt 21 for sft, 22 for cpt")
    parser.add_argument("--poolSize", type=int, default=8, 
                        help="number of parallel tasks")
    parser.add_argument("--CheckQuestion", type=int, default=22, 
                        help="whether to check the question or not, if not the index will be -1")
    
    args = parser.parse_args()
    
    output_dir = args.output_file
    indexes = args.indexes
    poolsize = args.poolSize
    input_file = args.input_file
    
    with open(input_file, "r") as f:
        input_file = json.load(f)

    responses = asyncio.run(rephrase_response(input_file, indexes, poolSize=poolsize, CheckQuestion=args.CheckQuestion))
    with open(os.path.join(output_dir, "rephrased_responses_qa.json"), "w", encoding='utf-8') as f:
        json.dump(responses, f, ensure_ascii=False, indent=4)
    print(responses)
    
    if args.CheckQuestion != -1:
        file_path = os.path.join(output_dir, f"rephrased_responses_qa.json")
        responses = []
        indexes = args.CheckQuestion
        with open(file_path, "r") as f:
            responses = json.load(f)
        responses = asyncio.run(check_ori_response(responses, user_prompts[indexes], batch_size=poolsize))
        with open(os.path.join(output_dir, "checked_responses_qa.json"), "w", encoding='utf-8') as f:
            json.dump(responses, f, ensure_ascii=False, indent=4)