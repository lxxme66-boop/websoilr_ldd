import json
import os
import argparse


def generate_sharegpt_format_txt(input_keys, file_keys, output_keys, reasoning_keys, json_file, 
                                root_folder="data/txt_files"):
    """
    Generate ShareGPT format dataset for text-only data
    """
    with open(json_file, "r", encoding='utf-8') as f:
        data = json.load(f)
    
    datasets = {}
    datasets["prompt"] = []
    datasets["files"] = []
    datasets["completions"] = []
    
    for sample in data:
        datasample = {}
        datasample["content"] = []
        datasample["content"].append({"type": "text", "text": sample[input_keys]})
        datasample["role"] = "user"
        
        data_gt = {}
        data_gt["content"] = []
        output_text = "<thinking>\n" + sample[reasoning_keys] + "\n</thinking>\n"
        
        choices = sample.get("choices", [])
        if choices:
            answer = sample[output_keys]
            if isinstance(answer, int):
                answer = choices[answer]
        else:
            answer = sample[output_keys]
        
        output_text += "<answer>\n" + answer + "\n</answer>\n"
        data_gt["content"].append({"type": "text", "text": output_text})
        data_gt["role"] = "assistant"
        
        datasets["prompt"].append([datasample])
        
        # Handle file path
        file_path = sample[file_keys]
        if not os.path.isabs(file_path):
            file_path = os.path.join(root_folder, file_path)
        datasets["files"].append(file_path)
        datasets["completions"].append([data_gt])
    
    return datasets


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate dataset from text QA data")
    parser.add_argument("--input_file", type=str,
                        default="/workspace/data/txt_output/checked_responses_qa.json",
                        help="path to the input json file")
    parser.add_argument("--output_file", type=str, 
                        default="/workspace/data/txt_output/final_data.json", 
                        help="path to the output file")
    parser.add_argument("--input_keys", type=str, default="input", 
                        help="keys for the input question")
    parser.add_argument("--file_keys", type=str, default="file_path", 
                        help="keys for the input file")
    parser.add_argument("--output_keys", type=str, default="output", 
                        help="keys for the output answer")
    parser.add_argument("--reasoning_keys", type=str, default="reasoning", 
                        help="keys for the reasoning")
    parser.add_argument("--root_folder", type=str, default="/workspace/data/txt_files", 
                        help="root folder for the text files")
    
    args = parser.parse_args()
    datasets = generate_sharegpt_format_txt(
        input_keys=args.input_keys,
        file_keys=args.file_keys,
        output_keys=args.output_keys,
        reasoning_keys=args.reasoning_keys,
        json_file=args.input_file,
        root_folder=args.root_folder
    )
    with open(args.output_file, "w", encoding='utf-8') as f:
        json.dump(datasets, f, ensure_ascii=False, indent=4)
    print(f"Generated dataset saved to {args.output_file}")