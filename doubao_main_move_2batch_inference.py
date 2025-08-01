from Doubao.Datageneration import *
import asyncio
import time
import pickle as pkl
import argparse
import json
import random
# calculate tokens
 
## this script is not used, use doubao_main_batch_inference.py instead, the code architecture is being rebuilt

async def proccess_folders(temporary_folder,index=9,maximum_tasks = 20,selected_task_number = 500):
    total_tasks = []
    if args.read_hist and os.path.exists(os.path.join(storage_folder, "total_response.json")):
        print(f"Reading history data from {storage_folder}/total_responses.json")
        history_data = json.load(open(os.path.join(storage_folder, "total_response.json"), "r", encoding="utf-8"))
        img_lists = [example["image_path"] for example in history_data if "image_path" in example]
        img_lists = ["/".join(img_list.split("/")[-2:]) for img_list in img_lists]  # remove the first part of the path
        img_lists = list(set(img_lists))  # remove duplicates
        
    else:
        img_lists = None
    print(f"img_lists: {len(img_lists) if img_lists else 'None'}")
    asyncio.sleep(5)
    total_responses = []
    for folder in folders:
        folder_path = os.path.join(pdf_path, folder)
        if not os.path.exists(os.path.join(folder_path, "pages.json")):
            print(f"pages.json not found in {folder_path}, skipping this folder.")
            continue
        pages = json.load(open(os.path.join(folder_path, "pages.json"), "r"))
        valid_pages = [page for page in pages["pages"]]
        if not os.path.isdir(folder_path):
            continue
        # print(f"Processing folder: {folder_path}")
        
            
        #responses = await parse_pdf(folder_path, inddex=index)
        try:
            print(valid_pages)
            tasks = await parse_pdf(folder_path, inddex=index, page_ranges=valid_pages,img_lists=img_lists)
        except Exception as e:
            raise e
            continue
        if len(tasks) == 0:
            print(f"No tasks found in {folder_path}, skipping this folder.")
            continue
        total_tasks.extend(tasks)
        if len(total_tasks) >= maximum_tasks:
            print(f"Total tasks {len(total_tasks)} exceeds the maximum_tasks {maximum_tasks}, waiting for tasks to complete.")
            batch_responses = await asyncio.gather(*total_tasks)
            # Filter out None responses
            batch_responses = [response for response in batch_responses if response is not None]
            total_responses.extend(batch_responses)
            total_tasks = []  # reset the tasks list
            with open(os.path.join(storage_folder, temporary_folder, f"batch_{len(total_responses)//maximum_tasks + 1}.json"), "w",
                encoding="utf-8"
                ) as f:
                json.dump(batch_responses, f, ensure_ascii=False, indent=4)
                print(f"Batch {len(total_responses)//maximum_tasks + 1} responses saved to {storage_folder}/{temporary_folder}/batch_{len(total_responses)//maximum_tasks + 1}.json")
        # Wait for all tasks to complete
        if len(total_responses) >= selected_task_number:
            print(f"Total responses {len(total_responses)} exceeds the selected_task_number {selected_task_number}, stopping the process.")
            break
    # # randomly select tasks if the total number of tasks exceeds the selected_task_number
    # if len(total_tasks) > selected_task_number:
    #     print(f"Total tasks {len(total_tasks)} exceeds the selected_task_number {selected_task_number}, randomly selecting {selected_task_number} tasks.")
    #     total_tasks = random.sample(total_tasks, selected_task_number)
    # print(f"Total tasks: {len(total_tasks)} initialized for {folder_path}") 
    # # remove duplicated tasks
    # from asyncio import Semaphore
    # semaphore = Semaphore(maximum_tasks)
    # async def process_task(task):
    #     async with semaphore:
    #         try:
    #             response = await task
    #             return response
    #         except Exception as e:
    #             print(f"Error processing task: {e}")
    #             return None
    # # Create a list of tasks to run concurrently
    # tasks = [process_task(task) for task in total_tasks]
    # # Use asyncio.gather to run the tasks concurrently
    # print(f"Processing {len(tasks)} tasks concurrently with maximum {maximum_tasks} tasks at a time")
    # responses = await asyncio.gather(*tasks)
    # # Filter out None responses
    # responses = [response for response in responses if response is not None]
    # print(f"Total responses: {len(responses)}")
    # total_responses = responses
    
    # # for i in range(0, len(total_tasks), maximum_tasks):
    # #     # Create a list of tasks for the current batch
    # #     batch_tasks = total_tasks[i:i + maximum_tasks]
    # #     # Use asyncio.gather to run the tasks concurrently
    # #     print(f"Processing {len(batch_tasks)} tasks in batch {i//maximum_tasks + 1}")
        
    # #     batch_responses = await asyncio.gather(*batch_tasks)
    # #     # Filter out None responses
    # #     batch_responses = [response for response in batch_responses if response is not None]
    # #     print(batch_responses)
    # #     total_responses.extend(batch_responses)
    # #     # save to temporary local
    # #     os.makedirs(os.path.join(storage_folder, temporary_folder), exist_ok=True)
    # #     with open(os.path.join(storage_folder, temporary_folder, f"batch_{i//maximum_tasks + 1}.json"), "w",
    # #     encoding="utf-8"
    # #     ) as f:
    # #         json.dump(batch_responses, f, ensure_ascii=False, indent=4)
    # #         print(f"Batch {i//maximum_tasks + 1} responses saved to {storage_folder}/{temporary_folder}/batch_{i//maximum_tasks + 1}.json")
    # #     time.sleep(10)
    return total_responses
# loop = asyncio.get_event_loop()
# loop.run_until_complete(proccess_folders())
# use index 6 for cpt generation， index 9 for sft generation

if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description="Process some integers.")
    parser.add_argument("--index", type=int, default=43, help="index for the task")
    parser.add_argument("--parallel_batch_size", type=int, default=100, help="number of parallel tasks")
    parser.add_argument("--pdf_path", type=str, default="../data/parsed_papers/final_selected_folder", help="path to the pdf folder")
    parser.add_argument("--storage_folder", type=str, default="../data/testoutput", help="path to the storage folder")
    parser.add_argument("--temporary_folder", type=str, default="TEMP", help="path to the temporary folder")
    parser.add_argument("--selected_task_number", type=int, default=1000, help="number of tasks to select")
    parser.add_argument("--read_hist", type=bool, default=True, help="whether to read the historian file")
    args = parser.parse_args()
    
    selected_task_number = args.selected_task_number
    index = args.index
    parallel_batch_size = args.parallel_batch_size
    pdf_path = args.pdf_path
    storage_folder = args.storage_folder
    os.makedirs(storage_folder, exist_ok=True)
    temporary_folder = args.temporary_folder
    folders = os.listdir(pdf_path)
   
    total_responses = []
    os.makedirs(storage_folder, exist_ok=True)
    final_results = asyncio.run(proccess_folders(temporary_folder, index=index, maximum_tasks=parallel_batch_size,\
        selected_task_number=selected_task_number))
    f = open(os.path.join(storage_folder, "total_response.pkl"), "w", encoding="utf-8")
    if args.read_hist:
        history_data = json.load(open(storage_folder+"/total_response.json", "r", encoding="utf-8"))
        
        final_results.extend(history_data)
        pkl.dump(final_results, f)
       
    else:
        pkl.dump(final_results, f)