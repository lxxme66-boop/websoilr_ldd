from Doubao.PPTGeneration import *
import asyncio
import time
import pickle as pkl
import argparse
import json
# calculate tokens
 


async def proccess_folders(temporary_folder,index=9,maximum_tasks = 20):
    for folder in folders:
        folder_path = os.path.join(pdf_path, folder)
        pages = json.load(open(os.path.join(folder_path, "pages.json"), "r"))
        valid_pages = [page for page in pages["pages"]]
        if not os.path.isdir(folder_path):
            continue
        # print(f"Processing folder: {folder_path}")
        
            
        #responses = await parse_pdf(folder_path, inddex=index)
        try:
            print(valid_pages)
            tasks = await parse_pdf(folder_path, inddex=index, page_ranges=valid_pages)
        except Exception as e:
            raise e
            continue
        total_tasks.extend(tasks)
        # Wait for all tasks to complete
    print(f"Total tasks: {len(total_tasks)} initialized for {folder_path}")
    # 
    for i in range(0, len(total_tasks), maximum_tasks):
        # Create a list of tasks for the current batch
        batch_tasks = total_tasks[i:i + maximum_tasks]
        # Use asyncio.gather to run the tasks concurrently
        print(f"Processing {len(batch_tasks)} tasks in batch {i//maximum_tasks + 1}")
        
        batch_responses = await asyncio.gather(*batch_tasks)
        # Filter out None responses
        batch_responses = [response for response in batch_responses if response is not None]
        print(batch_responses)
        total_responses.extend(batch_responses)
        # save to temporary local
        os.makedirs(os.path.join(storage_folder, temporary_folder), exist_ok=True)
        with open(os.path.join(storage_folder, temporary_folder, f"batch_{i//maximum_tasks + 1}.json"), "w",
        encoding="utf-8"
        ) as f:
            json.dump(batch_responses, f, ensure_ascii=False, indent=4)
            print(f"Batch {i//maximum_tasks + 1} responses saved to {storage_folder}/{temporary_folder}/batch_{i//maximum_tasks + 1}.json")
        time.sleep(10)
    return total_responses
# loop = asyncio.get_event_loop()
# loop.run_until_complete(proccess_folders())
# use index 6 for cpt generation， index 9 for sft generation

if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description="Process some integers.")
    parser.add_argument("--index", type=int, default=2123, help="index for the task")
    parser.add_argument("--parallel_batch_size", type=int, default=10, help="number of parallel tasks")
    parser.add_argument("--pdf_path", type=str, default="/Users/Shared/VLReasoningTCL/data/outputppt", help="path to the pdf folder")
    parser.add_argument("--storage_folder", type=str, default="../data/pptoutput", help="path to the storage folder")
    parser.add_argument("--temporary_folder", type=str, default="TEMP", help="path to the temporary folder")
    args = parser.parse_args()
    
    index = args.index
    parallel_batch_size = args.parallel_batch_size
    pdf_path = args.pdf_path
    storage_folder = args.storage_folder
    os.makedirs(storage_folder, exist_ok=True)
    temporary_folder = args.temporary_folder
    folders = os.listdir(pdf_path)
    total_tasks = []
    total_responses = []
    os.makedirs(storage_folder, exist_ok=True)
    final_results = asyncio.run(proccess_folders(temporary_folder, index=index, maximum_tasks=parallel_batch_size))
    with open(storage_folder+"/total_responses.pkl", "wb") as f:
        pkl.dump(final_results, f)