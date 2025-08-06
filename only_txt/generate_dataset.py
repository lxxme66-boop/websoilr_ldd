import json
import os
import argparse

def judge_answer_correctness(answer, gt, choices):
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
    if not choices or gt >= len(choices):
        return False
        
    correct_answer = choices[gt]
    if answer == correct_answer:
        return True
    else:
        return False

def judge_answer_with_small_model(answer, gt, choices):
    """
    使用小模型判断答案正确性（预留接口）
    """
    # 这里可以集成小模型进行答案判断
    # 目前使用简单的字符串匹配
    return judge_answer_correctness(answer, gt, choices)

def generate_sharegpt_format_text(input_keys, output_keys, reasoning_keys, json_file, 
                                 root_folder="data/texts"):
    """
    生成ShareGPT格式的纯文本问答数据集
    
    Args:
        input_keys: 输入问题的key
        output_keys: 输出答案的key  
        reasoning_keys: 推理过程的key
        json_file: 输入的JSON文件路径
        root_folder: 根目录路径
    """
    with open(json_file, "r", encoding='utf-8') as f:
        data = json.load(f)
    
    datasets = {}
    datasets["conversations"] = []
    
    for sample in data:
        conversation = []
        
        # 用户输入部分
        user_message = {
            "from": "human",
            "value": sample[input_keys]
        }
        conversation.append(user_message)
        
        # 助手回复部分
        output_text = ""
        
        # 添加推理过程
        if reasoning_keys in sample and sample[reasoning_keys]:
            output_text += "<thinking>\n" + sample[reasoning_keys] + "\n</thinking>\n\n"
        
        # 添加答案
        choices = sample.get("choices", [])
        if choices:
            answer = sample[output_keys]
            if isinstance(answer, int) and answer < len(choices):
                answer = choices[answer]
        else:
            answer = sample[output_keys]
        
        output_text += "<answer>\n" + str(answer) + "\n</answer>"
        
        assistant_message = {
            "from": "gpt", 
            "value": output_text
        }
        conversation.append(assistant_message)
        
        # 添加到数据集
        datasets["conversations"].append(conversation)
        
        # 添加元数据
        if "conversations_metadata" not in datasets:
            datasets["conversations_metadata"] = []
        
        metadata = {
            "id": sample.get("id", len(datasets["conversations_metadata"])),
            "source": sample.get("source", "text_analysis"),
            "text_path": sample.get("text_path", ""),
            "difficulty": sample.get("difficulty", "medium"),
            "question_type": sample.get("type", "unknown"),
            "has_reasoning": bool(sample.get(reasoning_keys)),
            "has_choices": bool(sample.get("choices"))
        }
        datasets["conversations_metadata"].append(metadata)
    
    return datasets

def generate_instruction_format_text(input_keys, output_keys, reasoning_keys, json_file):
    """
    生成Instruction格式的纯文本问答数据集
    """
    with open(json_file, "r", encoding='utf-8') as f:
        data = json.load(f)
    
    datasets = []
    
    for sample in data:
        instruction_data = {
            "instruction": sample[input_keys],
            "input": sample.get("context", ""),
            "output": sample[output_keys]
        }
        
        # 添加推理过程
        if reasoning_keys in sample and sample[reasoning_keys]:
            instruction_data["reasoning"] = sample[reasoning_keys]
        
        # 添加选择项
        if "choices" in sample and sample["choices"]:
            instruction_data["choices"] = sample["choices"]
        
        # 添加元数据
        instruction_data["metadata"] = {
            "question_type": sample.get("type", "unknown"),
            "difficulty": sample.get("difficulty", "medium"),
            "source": sample.get("source", "text_analysis"),
            "text_path": sample.get("text_path", "")
        }
        
        datasets.append(instruction_data)
    
    return datasets

def generate_alpaca_format_text(input_keys, output_keys, reasoning_keys, json_file):
    """
    生成Alpaca格式的纯文本问答数据集
    """
    with open(json_file, "r", encoding='utf-8') as f:
        data = json.load(f)
    
    datasets = []
    
    for sample in data:
        alpaca_data = {
            "instruction": sample[input_keys],
            "input": sample.get("context", ""),
            "output": sample[output_keys]
        }
        
        datasets.append(alpaca_data)
    
    return datasets

def validate_dataset_quality(datasets, format_type="sharegpt"):
    """
    验证数据集质量
    """
    quality_report = {
        "total_samples": 0,
        "valid_samples": 0,
        "invalid_samples": 0,
        "empty_questions": 0,
        "empty_answers": 0,
        "has_reasoning": 0,
        "has_choices": 0,
        "question_types": {},
        "difficulties": {},
        "average_question_length": 0,
        "average_answer_length": 0
    }
    
    if format_type == "sharegpt":
        conversations = datasets.get("conversations", [])
        metadata = datasets.get("conversations_metadata", [])
        
        quality_report["total_samples"] = len(conversations)
        
        total_q_len = 0
        total_a_len = 0
        
        for i, conv in enumerate(conversations):
            if len(conv) >= 2:
                question = conv[0].get("value", "")
                answer = conv[1].get("value", "")
                
                if not question.strip():
                    quality_report["empty_questions"] += 1
                if not answer.strip():
                    quality_report["empty_answers"] += 1
                
                if question.strip() and answer.strip():
                    quality_report["valid_samples"] += 1
                else:
                    quality_report["invalid_samples"] += 1
                
                total_q_len += len(question)
                total_a_len += len(answer)
                
                # 检查推理过程
                if "<thinking>" in answer:
                    quality_report["has_reasoning"] += 1
                
                # 统计元数据
                if i < len(metadata):
                    meta = metadata[i]
                    q_type = meta.get("question_type", "unknown")
                    difficulty = meta.get("difficulty", "unknown")
                    
                    quality_report["question_types"][q_type] = quality_report["question_types"].get(q_type, 0) + 1
                    quality_report["difficulties"][difficulty] = quality_report["difficulties"].get(difficulty, 0) + 1
                    
                    if meta.get("has_choices"):
                        quality_report["has_choices"] += 1
        
        if quality_report["total_samples"] > 0:
            quality_report["average_question_length"] = total_q_len / quality_report["total_samples"]
            quality_report["average_answer_length"] = total_a_len / quality_report["total_samples"]
    
    return quality_report

def save_quality_report(quality_report, output_file):
    """
    保存质量报告
    """
    report_file = output_file.replace(".json", "_quality_report.json")
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(quality_report, f, ensure_ascii=False, indent=4)
    
    print(f"Quality report saved to {report_file}")
    print(f"Total samples: {quality_report['total_samples']}")
    print(f"Valid samples: {quality_report['valid_samples']}")
    print(f"Invalid samples: {quality_report['invalid_samples']}")
    print(f"Samples with reasoning: {quality_report['has_reasoning']}")

def split_dataset(datasets, train_ratio=0.8, val_ratio=0.1, test_ratio=0.1):
    """
    分割数据集为训练、验证和测试集
    """
    import random
    
    if abs(train_ratio + val_ratio + test_ratio - 1.0) > 1e-6:
        raise ValueError("Ratios must sum to 1.0")
    
    if "conversations" in datasets:
        # ShareGPT format
        conversations = datasets["conversations"]
        metadata = datasets.get("conversations_metadata", [])
        
        total_size = len(conversations)
        indices = list(range(total_size))
        random.shuffle(indices)
        
        train_size = int(total_size * train_ratio)
        val_size = int(total_size * val_ratio)
        
        train_indices = indices[:train_size]
        val_indices = indices[train_size:train_size + val_size]
        test_indices = indices[train_size + val_size:]
        
        train_data = {
            "conversations": [conversations[i] for i in train_indices],
            "conversations_metadata": [metadata[i] for i in train_indices] if metadata else []
        }
        val_data = {
            "conversations": [conversations[i] for i in val_indices],
            "conversations_metadata": [metadata[i] for i in val_indices] if metadata else []
        }
        test_data = {
            "conversations": [conversations[i] for i in test_indices],
            "conversations_metadata": [metadata[i] for i in test_indices] if metadata else []
        }
        
        return train_data, val_data, test_data
    
    else:
        # Instruction format
        total_size = len(datasets)
        indices = list(range(total_size))
        random.shuffle(indices)
        
        train_size = int(total_size * train_ratio)
        val_size = int(total_size * val_ratio)
        
        train_indices = indices[:train_size]
        val_indices = indices[train_size:train_size + val_size]
        test_indices = indices[train_size + val_size:]
        
        train_data = [datasets[i] for i in train_indices]
        val_data = [datasets[i] for i in val_indices]
        test_data = [datasets[i] for i in test_indices]
        
        return train_data, val_data, test_data

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate text-based QA datasets")
    parser.add_argument("--input_file", type=str,
                        default="data/cleaned_output/total_response.json",
                        help="path to the input json file")
    parser.add_argument("--output_file", type=str, 
                        default="data/final_text_dataset.json", 
                        help="path to the output file")
    parser.add_argument("--input_keys", type=str, 
                        default="question", 
                        help="keys for the input question")
    parser.add_argument("--output_keys", type=str, 
                        default="answer", 
                        help="keys for the output answer")
    parser.add_argument("--reasoning_keys", type=str, 
                        default="reasoning", 
                        help="keys for the reasoning")
    parser.add_argument("--root_folder", type=str, 
                        default="data/texts", 
                        help="root folder for the texts")
    parser.add_argument("--format", type=str, 
                        choices=["sharegpt", "instruction", "alpaca"],
                        default="sharegpt",
                        help="output format")
    parser.add_argument("--split", action="store_true",
                        help="split dataset into train/val/test")
    parser.add_argument("--validate", action="store_true",
                        help="validate dataset quality")
    
    args = parser.parse_args()
    
    print(f"Generating {args.format} format dataset...")
    print(f"Input file: {args.input_file}")
    print(f"Output file: {args.output_file}")
    
    # 生成数据集
    if args.format == "sharegpt":
        datasets = generate_sharegpt_format_text(
            input_keys=args.input_keys,
            output_keys=args.output_keys,
            reasoning_keys=args.reasoning_keys,
            json_file=args.input_file,
            root_folder=args.root_folder
        )
    elif args.format == "instruction":
        datasets = generate_instruction_format_text(
            input_keys=args.input_keys,
            output_keys=args.output_keys,
            reasoning_keys=args.reasoning_keys,
            json_file=args.input_file
        )
    elif args.format == "alpaca":
        datasets = generate_alpaca_format_text(
            input_keys=args.input_keys,
            output_keys=args.output_keys,
            reasoning_keys=args.reasoning_keys,
            json_file=args.input_file
        )
    
    # 分割数据集
    if args.split:
        train_data, val_data, test_data = split_dataset(datasets)
        
        # 保存分割后的数据集
        base_name = args.output_file.replace(".json", "")
        
        train_file = f"{base_name}_train.json"
        val_file = f"{base_name}_val.json"
        test_file = f"{base_name}_test.json"
        
        with open(train_file, "w", encoding='utf-8') as f:
            json.dump(train_data, f, ensure_ascii=False, indent=2)
        with open(val_file, "w", encoding='utf-8') as f:
            json.dump(val_data, f, ensure_ascii=False, indent=2)
        with open(test_file, "w", encoding='utf-8') as f:
            json.dump(test_data, f, ensure_ascii=False, indent=2)
        
        print(f"Dataset split saved:")
        print(f"  Train: {train_file}")
        print(f"  Validation: {val_file}")
        print(f"  Test: {test_file}")
    else:
        # 保存完整数据集
        with open(args.output_file, "w", encoding='utf-8') as f:
            json.dump(datasets, f, ensure_ascii=False, indent=2)
        print(f"Generated dataset saved to {args.output_file}")
    
    # 验证数据集质量
    if args.validate:
        print("Validating dataset quality...")
        quality_report = validate_dataset_quality(datasets, args.format)
        save_quality_report(quality_report, args.output_file)
    
    print("Dataset generation completed successfully!")