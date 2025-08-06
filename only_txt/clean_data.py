import pickle as pkl
import random
import argparse
import os
import re

pattern = re.compile(r"```json\s*(\{[\s\S]*?\})\s*```", re.DOTALL)


def clean_process(input_file, output_file):
    with open(input_file, "rb") as f:
        data = pkl.load(f)
    
    output_json = []
    import json
    for i in range(len(data)):
        try:
            content = data[i]['content']
            matches = pattern.findall(content)
            if matches:
                json_dict_str = matches[-1]
                response = eval(json_dict_str)
            else:
                continue
        except Exception as e:
            print(f"Error parsing content for index {i}: {e}")
            continue
        
        # Add file path information
        file_path = data[i]['file_path']
        response['file_path'] = file_path
        
        # Add text content if available
        if 'text_content' in data[i]:
            response['text_content'] = data[i]['text_content']
        
        output_json.append(response)
    
    with open(os.path.join(output_file, "total_response.json"), "w",
            encoding='utf-8') as f:
        json.dump(output_json, f, ensure_ascii=False, indent=4)
        print("The number of responses is {}".format(len(output_json)))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Clean text processing results")
    parser.add_argument("--input_file", type=str, 
                        default="/workspace/data/txt_output/total_response.pkl",
                        help="path to the input pkl file")
    parser.add_argument("--output_file", type=str, 
                        default="/workspace/data/txt_output", 
                        help="path to the output folder")
    args = parser.parse_args()
    
    new_folder = args.output_file
    input_file = args.input_file
    if not os.path.exists(new_folder):
        os.makedirs(new_folder)
    clean_process(input_file, new_folder)
    print(f"Cleaned data saved to {new_folder}/total_response.json")