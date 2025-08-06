from Utilis.utilis import generate_sections_range
import random
import os
import shutil
import json

def preprocess_text_files():
    """预处理文本文件的主函数"""
    folder_path = input("Enter the folder path: ")
    number_of_files = input("Enter the number of files to process: ")
    
    if os.path.exists(os.path.join(folder_path, "final_selected_folder")):
        print("The folder 'final_selected_folder' already exists. automatically deleting it.")
        shutil.rmtree(os.path.join(folder_path, "final_selected_folder"))

    os.makedirs(os.path.join(folder_path, "final_selected_folder"), exist_ok=True)
    folders = os.listdir(folder_path)
    
    # 筛选包含有效文本内容的文件夹
    sample_lists = []
    for folder in folders:
        folder_full_path = os.path.join(folder_path, folder)
        if os.path.isdir(folder_full_path):
            if generate_sections_range(folder_full_path) == 1:
                sample_lists.append(folder)
    
    if not sample_lists:
        print("No valid text folders found.")
        return
    
    # 随机选择指定数量的文件夹
    selected_count = min(int(number_of_files), len(sample_lists))
    sample_lists = random.sample(sample_lists, selected_count)
    
    # 复制选中的文件夹
    for folder in sample_lists:
        src = os.path.join(folder_path, folder)
        dst = os.path.join(folder_path, "final_selected_folder", folder)
        shutil.copytree(src, dst)
        print(f"Copied {folder} to final_selected_folder.")
    
    print(f"Selected {len(sample_lists)} folders and moved them to 'final_selected_folder'.")
    print("Process completed successfully.")

def create_text_content_structure(text_content, output_dir):
    """
    为文本内容创建结构化的内容列表
    
    Args:
        text_content: 文本内容
        output_dir: 输出目录
    """
    from Utilis.utilis import extract_text_sections, create_text_metadata
    
    # 分割文本为段落
    sections = extract_text_sections(text_content)
    
    # 创建内容列表
    content_list = []
    for section in sections:
        content_list.append({
            "section_idx": section["section_idx"],
            "type": section["type"],
            "content": section["content"],
            "length": section["length"],
            "sentence_count": section["sentence_count"]
        })
    
    # 保存内容列表
    content_file = os.path.join(output_dir, "text_content_list.json")
    with open(content_file, 'w', encoding='utf-8') as f:
        json.dump(content_list, f, ensure_ascii=False, indent=4)
    
    # 保存完整文本
    text_file = os.path.join(output_dir, "full_text.txt")
    with open(text_file, 'w', encoding='utf-8') as f:
        f.write(text_content)
    
    # 创建元数据
    metadata = create_text_metadata(text_content, output_dir)
    metadata_file = os.path.join(output_dir, "metadata.json")
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=4)
    
    print(f"Created structured content for {len(sections)} sections in {output_dir}")
    return len(sections)

def batch_preprocess_text_files(input_dir, output_dir, file_extensions=['.txt', '.md']):
    """
    批量预处理文本文件
    
    Args:
        input_dir: 输入目录
        output_dir: 输出目录
        file_extensions: 支持的文件扩展名
    """
    if not os.path.exists(input_dir):
        print(f"Input directory {input_dir} does not exist.")
        return
    
    os.makedirs(output_dir, exist_ok=True)
    
    processed_count = 0
    total_sections = 0
    
    # 遍历输入目录中的所有文件
    for root, dirs, files in os.walk(input_dir):
        for file in files:
            # 检查文件扩展名
            if any(file.lower().endswith(ext) for ext in file_extensions):
                file_path = os.path.join(root, file)
                
                try:
                    # 读取文本内容
                    with open(file_path, 'r', encoding='utf-8') as f:
                        text_content = f.read()
                    
                    # 检查文本长度
                    if len(text_content.strip()) < 100:
                        print(f"Skipping {file}: too short")
                        continue
                    
                    # 创建输出目录
                    file_name = os.path.splitext(file)[0]
                    file_output_dir = os.path.join(output_dir, file_name)
                    os.makedirs(file_output_dir, exist_ok=True)
                    
                    # 处理文本
                    sections_count = create_text_content_structure(text_content, file_output_dir)
                    
                    processed_count += 1
                    total_sections += sections_count
                    
                    print(f"Processed {file}: {sections_count} sections")
                    
                except Exception as e:
                    print(f"Error processing {file}: {e}")
                    continue
    
    print(f"\nBatch preprocessing completed:")
    print(f"- Processed files: {processed_count}")
    print(f"- Total sections: {total_sections}")
    print(f"- Output directory: {output_dir}")

def validate_preprocessed_data(data_dir):
    """
    验证预处理后的数据
    
    Args:
        data_dir: 数据目录
    """
    validation_results = {
        "total_folders": 0,
        "valid_folders": 0,
        "invalid_folders": [],
        "total_sections": 0,
        "average_sections_per_folder": 0
    }
    
    if not os.path.exists(data_dir):
        print(f"Data directory {data_dir} does not exist.")
        return validation_results
    
    folders = [f for f in os.listdir(data_dir) if os.path.isdir(os.path.join(data_dir, f))]
    validation_results["total_folders"] = len(folders)
    
    for folder in folders:
        folder_path = os.path.join(data_dir, folder)
        
        # 检查必需文件
        required_files = ["text_content_list.json", "full_text.txt", "sections.json"]
        missing_files = []
        
        for required_file in required_files:
            file_path = os.path.join(folder_path, required_file)
            if not os.path.exists(file_path):
                missing_files.append(required_file)
        
        if missing_files:
            validation_results["invalid_folders"].append({
                "folder": folder,
                "missing_files": missing_files
            })
        else:
            validation_results["valid_folders"] += 1
            
            # 统计段落数量
            try:
                with open(os.path.join(folder_path, "text_content_list.json"), 'r', encoding='utf-8') as f:
                    content_list = json.load(f)
                    validation_results["total_sections"] += len(content_list)
            except:
                pass
    
    # 计算平均值
    if validation_results["valid_folders"] > 0:
        validation_results["average_sections_per_folder"] = validation_results["total_sections"] / validation_results["valid_folders"]
    
    return validation_results

def print_validation_report(validation_results):
    """打印验证报告"""
    print("\n=== 数据验证报告 ===")
    print(f"总文件夹数: {validation_results['total_folders']}")
    print(f"有效文件夹数: {validation_results['valid_folders']}")
    print(f"无效文件夹数: {len(validation_results['invalid_folders'])}")
    print(f"总段落数: {validation_results['total_sections']}")
    print(f"平均每文件夹段落数: {validation_results['average_sections_per_folder']:.2f}")
    
    if validation_results['invalid_folders']:
        print("\n无效文件夹详情:")
        for invalid in validation_results['invalid_folders']:
            print(f"- {invalid['folder']}: 缺失文件 {invalid['missing_files']}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Text preprocessing utilities")
    parser.add_argument("--mode", choices=["interactive", "batch", "validate"], 
                        default="interactive", help="Processing mode")
    parser.add_argument("--input_dir", type=str, help="Input directory for batch processing")
    parser.add_argument("--output_dir", type=str, help="Output directory")
    parser.add_argument("--extensions", nargs="+", default=['.txt', '.md'], 
                        help="File extensions to process")
    
    args = parser.parse_args()
    
    if args.mode == "interactive":
        preprocess_text_files()
    elif args.mode == "batch":
        if not args.input_dir or not args.output_dir:
            print("Batch mode requires --input_dir and --output_dir")
        else:
            batch_preprocess_text_files(args.input_dir, args.output_dir, args.extensions)
    elif args.mode == "validate":
        if not args.input_dir:
            print("Validate mode requires --input_dir")
        else:
            results = validate_preprocessed_data(args.input_dir)
            print_validation_report(results)