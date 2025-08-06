import pickle as pkl
import random
import argparse
import os
import re
import json

pattern = re.compile(r"```json\s*(\{[\s\S]*?\})\s*```", re.DOTALL)

def clean_process(input_file, output_file, copy_parsed_text=False):
    """
    清理和处理文本分析结果数据（纯文本版本）
    
    Args:
        input_file: 输入的pickle文件路径
        output_file: 输出目录路径
        copy_parsed_text: 是否复制解析的文本文件
    """
    with open(input_file, "rb") as f:
        data = pkl.load(f)
    
    output_json = []
    
    for i in range(len(data)):
        try:
            content = data[i]['content']
            matches = pattern.findall(content)
            if matches:
                json_dict_str = matches[-1]
                response = eval(json_dict_str)
            else:
                # 如果没有找到JSON格式，尝试直接解析内容
                try:
                    # 尝试从内容中提取结构化信息
                    response = extract_structured_info(content)
                except:
                    continue
        except Exception as e:
            print(f"Error parsing content for index {i}: {e}")
            continue
        
        # 处理文本路径（替代原来的图像路径处理）
        text_path = data[i].get('section_path', data[i].get('text_path', ''))
        if text_path:
            # 标准化文本路径
            path_parts = text_path.split("/")[-3:] if "/" in text_path else [text_path]
            text_path = "/".join(path_parts)
            text_path = "./" + text_path if not text_path.startswith("./") else text_path
            response['text_path'] = text_path
        
        # 添加文本内容信息
        if 'text_content' in data[i]:
            response['text_content'] = data[i]['text_content'][:500] + "..." if len(data[i]['text_content']) > 500 else data[i]['text_content']
        
        # 添加处理时间戳
        if 'timestamp' in data[i]:
            response['timestamp'] = data[i]['timestamp']
        
        # 添加处理索引
        if 'processing_index' in data[i]:
            response['processing_index'] = data[i]['processing_index']
        
        output_json.append(response)
        
        # 复制解析的文本文件（如果需要）
        if copy_parsed_text and text_path:
            try:
                copy_text_files(data[i], output_file, i)
            except Exception as e:
                print(f"Error copying text files for index {i}: {e}")
    
    # 保存清理后的数据
    output_json_file = os.path.join(output_file, "total_response.json")
    with open(output_json_file, "w", encoding='utf-8') as f:
        json.dump(output_json, f, ensure_ascii=False, indent=4)
    
    print(f"The number of responses is {len(output_json)}")
    print(f"Cleaned data saved to {output_json_file}")
    
    # 生成数据统计报告
    generate_statistics_report(output_json, output_file)

def extract_structured_info(content):
    """
    从非JSON格式的内容中提取结构化信息
    """
    response = {}
    
    # 尝试提取关键信息
    lines = content.split('\n')
    current_section = None
    current_content = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # 检查是否是标题行
        if any(keyword in line for keyword in ['知识点', '分析', '描述', '概念', '术语']):
            if current_section and current_content:
                response[current_section] = '\n'.join(current_content)
            current_section = extract_section_name(line)
            current_content = []
        else:
            current_content.append(line)
    
    # 添加最后一个section
    if current_section and current_content:
        response[current_section] = '\n'.join(current_content)
    
    # 如果没有提取到结构化信息，使用默认结构
    if not response:
        response = {
            'related_knowledge': '文本相关知识点',
            'analysisResults': content[:200] + "..." if len(content) > 200 else content,
            'textDescription': '文本内容描述'
        }
    
    return response

def extract_section_name(line):
    """
    从标题行提取section名称
    """
    if '知识点' in line:
        return 'related_knowledge'
    elif '分析' in line:
        return 'analysisResults'
    elif '描述' in line:
        return 'textDescription'
    elif '概念' in line:
        return 'concepts'
    elif '术语' in line:
        return 'terminology'
    else:
        return 'other_info'

def copy_text_files(data_item, output_dir, index):
    """
    复制相关的文本文件到输出目录
    """
    if 'section_path' in data_item:
        section_path = data_item['section_path']
        # 创建目标目录
        target_dir = os.path.join(output_dir, f"text_sections", f"section_{index}")
        os.makedirs(target_dir, exist_ok=True)
        
        # 保存文本内容
        if 'text_content' in data_item:
            text_file = os.path.join(target_dir, "content.txt")
            with open(text_file, 'w', encoding='utf-8') as f:
                f.write(data_item['text_content'])
        
        # 保存上下文信息
        if 'context' in data_item:
            context_file = os.path.join(target_dir, "context.txt")
            with open(context_file, 'w', encoding='utf-8') as f:
                f.write(data_item['context'])

def generate_statistics_report(data, output_dir):
    """
    生成数据统计报告
    """
    stats = {
        'total_items': len(data),
        'items_with_knowledge': 0,
        'items_with_analysis': 0,
        'items_with_description': 0,
        'processing_indices': {},
        'text_path_count': 0,
        'average_content_length': 0
    }
    
    total_length = 0
    
    for item in data:
        # 统计包含各类信息的条目数
        if 'related_knowledge' in item and item['related_knowledge']:
            stats['items_with_knowledge'] += 1
        if 'analysisResults' in item and item['analysisResults']:
            stats['items_with_analysis'] += 1
        if 'textDescription' in item and item['textDescription']:
            stats['items_with_description'] += 1
        
        # 统计处理索引分布
        if 'processing_index' in item:
            idx = item['processing_index']
            stats['processing_indices'][idx] = stats['processing_indices'].get(idx, 0) + 1
        
        # 统计文本路径
        if 'text_path' in item:
            stats['text_path_count'] += 1
        
        # 统计内容长度
        if 'text_content' in item:
            total_length += len(item['text_content'])
    
    if stats['total_items'] > 0:
        stats['average_content_length'] = total_length / stats['total_items']
    
    # 保存统计报告
    stats_file = os.path.join(output_dir, "statistics_report.json")
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=4)
    
    print(f"Statistics report saved to {stats_file}")
    print(f"Total items: {stats['total_items']}")
    print(f"Items with knowledge: {stats['items_with_knowledge']}")
    print(f"Items with analysis: {stats['items_with_analysis']}")
    print(f"Items with description: {stats['items_with_description']}")

def validate_cleaned_data(output_file):
    """
    验证清理后的数据质量
    """
    json_file = os.path.join(output_file, "total_response.json")
    
    if not os.path.exists(json_file):
        print(f"Error: {json_file} not found")
        return False
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"Validation: Successfully loaded {len(data)} items")
        
        # 检查数据完整性
        incomplete_items = []
        for i, item in enumerate(data):
            if not any(key in item for key in ['related_knowledge', 'analysisResults', 'textDescription']):
                incomplete_items.append(i)
        
        if incomplete_items:
            print(f"Warning: {len(incomplete_items)} items may be incomplete")
        else:
            print("Validation: All items appear to be complete")
        
        return True
        
    except Exception as e:
        print(f"Validation error: {e}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Clean text analysis results")
    parser.add_argument("--input_file", type=str,
                        default="data/text_analysis_results.pkl",
                        help="path to the input pickle file")
    parser.add_argument("--output_file", type=str, 
                        default="data/cleaned_output", 
                        help="path to the output folder")
    parser.add_argument("--copy_parsed_text", type=bool, 
                        default=False,
                        help="copy parsed text from original directory to new folder")
    parser.add_argument("--validate", action="store_true",
                        help="validate cleaned data after processing")
    
    args = parser.parse_args()
    
    output_dir = args.output_file
    input_file = args.input_file
    copy_parsed_text = args.copy_parsed_text
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    print(f"Starting text data cleaning...")
    print(f"Input file: {input_file}")
    print(f"Output directory: {output_dir}")
    
    clean_process(input_file, output_dir, copy_parsed_text=copy_parsed_text)
    
    if args.validate:
        print("Running validation...")
        validate_cleaned_data(output_dir)
    
    print(f"Text data cleaning completed. Results saved to {output_dir}/total_response.json")