import json
import os
import argparse

def judge_answer_correctness(answer,gt,choices):
    """
    Judge the correctness of the answer based on the ground truth and choices.
    :param answer: The answer provided by the model.
    :param gt: The ground truth answer.
    :param choices: The choices available for the question.
    :return: True if the answer is correct, False otherwise.
    accepting the following return values:
    - "A": Correct answer is A
    - "1": Correct answer is 1
    - "A. the answer is A": return the full choice text
    
    """
    correct_answer = choices[gt]
    if answer == correct_answer:
        return True
    else:
        return False
def judge_answer_with_small_model(answer,gt,choices):
    model = "qwen-7b-chat"
    import huggingface_hub
    
    




def generate_sharegpt_format_vl(input_keys, image_keys, output_keys,reasoning_keys,json_file, 
                                root_folder="data/pdfs"):

    with open(json_file, "r", encoding='utf-8') as f:
        data = json.load(f)
    datasets = {}
    datasets["prompt"] = []
    datasets["images"] = []
    datasets["completions"] = []
    for sample in data:
        datasample = {}
        datasample["content"]=[]
        datasample["content"].append({"type": "text", "text": sample[input_keys]})
        datasample["content"].append({"type": "image", "text": None})
        datasample["role"]  = "user"
        data_gt = {}
        data_gt["content"] = []
        output_text = "<thinking>\n" + sample[reasoning_keys] + "\n</thinking>\n"


        choices = sample.get("choices", [])
        if choices:
            answer = sample[output_keys]
            if isinstance(answer, int):
                answer = choices[answer]
        
        output_text += "<answer>\n" + answer + "\n</answer>\n"
        data_gt["content"].append({"type": "text", "text": output_text})
        data_gt["content"].append({"type": "image", "text": None})
        data_gt["role"] = "assistant"
        datasets["prompt"].append([datasample])
        image_ori = sample[image_keys]
        if image_ori.startswith("./"):
            image_ori = image_ori[2:]
        elif image_ori.startswith("/"):
            image_ori = image_ori[1:]
        image_path = os.path.join(root_folder, image_ori)
        datasets["images"].append(image_path)
        datasets["completions"].append([data_gt])


    return datasets


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process some integers.")
    parser.add_argument("--input_file", type=str, \
                        default="/home/maxzhang/VLReasoningTCL/data/pdfs/checked_responses_qa.json",\
                         help="path to the input json file")

    parser.add_argument("--output_file", type=str, default="/home/maxzhang/VLReasoningTCL/data/pdfs/final_data.json", help="path to the output folder")
    parser.add_argument("--input_keys", type=str, default="input", help="keys for the input question")
    parser.add_argument("--image_keys", type=str, default="image_path", help="keys for the input image")
    parser.add_argument("--output_keys", type=str, default="output", help="keys for the output answer")
    parser.add_argument("--reasoning_keys", type=str, default="reasoning", help="keys for the reasoning")
    parser.add_argument("--root_folder", type=str, default="/home/maxzhang/VLReasoningTCL/data/pdfs", help="root folder for the images")
    
    args = parser.parse_args()
    datasets = generate_sharegpt_format_vl(
        input_keys=args.input_keys,
        image_keys=args.image_keys,
        output_keys=args.output_keys,
        reasoning_keys=args.reasoning_keys,
        json_file=args.input_file,
        root_folder=args.root_folder
    )
    with open(args.output_file, "w", encoding='utf-8') as f:
        json.dump(datasets, f, ensure_ascii=False, indent=4)
    print(f"Generated dataset saved to {args.output_file}")