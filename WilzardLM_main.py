import json
import random
import pandas as pd
from WizardLM.openai_access import call_chatgpt
from WizardLM.depth import createConstraintsPrompt, createDeepenPrompt, createConcretizingPrompt, createReasoningPrompt
from WizardLM.breadth import createBreadthPrompt
import os
import asyncio
from asyncio import Semaphore
fr ="/home/maxzhang/VLReasoningTCL/data/bookoutput/book_checked/merged_data_qa_page30-41_labeled.csv"
all_objs = pd.read_csv(fr)
# convert to list of dicts
all_objs = all_objs.to_dict(orient='records')
folder_path = "/home/maxzhang/VLReasoningTCL/data/bookoutput/book_checked"

pool_size = 20

def generateAnswerResponse(new_prompt, change_content, old_prompt, ori_answer, reasoning_content):
	"""
	Generate a response for the answer and reasoning content
	"""
	prompt="你是一个AI助手， 你现在有两个提示词, #旧提示词#和#新提示词#, #新提示词# 是在#旧提示词#的基础上改写而来 \n"
	prompt += "#新提示词# 通过#改写方法# 在#旧提示词# 的基础上改写而来。\n"
	prompt += "你的任务是参考#旧提示词#,#改写方法#,#旧提示词的答案# 和#旧推理内容#，提供#新提示词#的答案。答案要求简洁直白\n"
	prompt += f"#旧提示词#: {old_prompt}\n"
	prompt += f"#旧提示词的答案#: {ori_answer}\n"
	prompt += f"#改写方法#: {change_content}\n"
	prompt += f"#旧提示词的推理#: {reasoning_content}\n"
	prompt += f"#新提示词#: {new_prompt}\n"
	prompt += f"#新提示词的答案#: "
	return prompt

async def process_single_object(cur_obj):
	"""
	Process a single object
	"""
	try:
		instruction = cur_obj['prompt'].strip()
		image_path = cur_obj['image_path'].strip()
  
		if not image_path:
			image_path = None
		else:
			image_path = os.path.join(folder_path, image_path) 
		ori_answer = cur_obj['answer'].strip()
		ori_content = cur_obj['reasoning'].strip()
		evol_prompts = [
			createConstraintsPrompt(instruction, ori_answer, ori_content),
			createDeepenPrompt(instruction, ori_answer, ori_content),
			createConcretizingPrompt(instruction, ori_answer, ori_content),
			createReasoningPrompt(instruction, ori_answer, ori_content),
			createBreadthPrompt(instruction, ori_answer, ori_content)
		]
	
	
		selected_evol_prompt = random.choice(evol_prompts)
	   
		
		evol_instruction, reasoning_content = await call_chatgpt(selected_evol_prompt, image_path)
		evol_instruction = evol_instruction.strip()
		answer_instruction = generateAnswerResponse(evol_instruction,reasoning_content, instruction, ori_answer, ori_content)

		answer, reasoning_content2 = await call_chatgpt(answer_instruction, image_path)
		print(f"Selected Evolution Prompt: {selected_evol_prompt}")
		print(f"Image Path: {image_path}")
		print("="*20)
		print(f"REASONING CONTENT: {reasoning_content}")
		print("*"*20)
		print(f"Evolution Instruction: {evol_instruction}")
		print("="*20)
		print(f"REASONING CONTENT2: {reasoning_content2}")
		print("*"*20)
		print(f"Answer: {answer}")
		print("="*20)
		
		return {
			"instruction": evol_instruction,
			"new output": answer,
			"reasoning_content": reasoning_content2,
			"original_question": instruction,
			"original_answer": ori_answer,
			"original_reasoning_content": ori_content,
			"image_path": image_path
		}
	except Exception as e:
		raise e

async def process_evolution():
	evol_objs = []
	semaphore = Semaphore(pool_size)  # Control concurrent operations
	
	async def process_with_semaphore(cur_obj):
		async with semaphore:  # Acquire semaphore
			return await process_single_object(cur_obj)
	
	# Create all tasks
	tasks = [
		asyncio.create_task(process_with_semaphore(obj))
		for obj in all_objs
	]
	
	# Process all tasks with progress tracking
	completed = 0
	for coro in asyncio.as_completed(tasks):
		try:
			result = await coro
			if result is not None:
				evol_objs.append(result)
			completed += 1
			
			if completed % 5 == 0:  # Progress update every 5 completions
				print(f"Progress: {completed}/{len(all_objs)} completed")
				
		except Exception as e:
			raise e
			completed += 1
	
	return evol_objs
eval_objs = asyncio.run(process_evolution())

with open(fr.replace("csv","json"), 'w',encoding="utf-8") as f:	
	json.dump(eval_objs, f, indent=4, ensure_ascii=False)




