import os
import json
import re
from typing import List, Dict, Optional, Tuple

def clean_text_content(text: str) -> str:
    """
    清理和标准化文本内容（替代img2base64功能）
    
    Args:
        text: 原始文本内容
        
    Returns:
        str: 清理后的文本内容
    """
    if not text:
        return ""
    
    # 移除多余的空白字符
    text = re.sub(r'\s+', ' ', text)
    
    # 移除特殊字符但保留中文、英文、数字和常用标点
    text = re.sub(r'[^\w\s\u4e00-\u9fff.,!?;:()[\]{}"-]', '', text)
    
    # 移除首尾空白
    text = text.strip()
    
    return text

def extract_text_sections(text_content: str, max_section_length: int = 1000) -> List[Dict]:
    """
    将长文本分割为多个段落（替代generate_pages_range功能）
    
    Args:
        text_content: 输入文本内容
        max_section_length: 每个段落的最大长度
        
    Returns:
        List[Dict]: 段落列表，每个段落包含索引和内容
    """
    if not text_content:
        return []
    
    sections = []
    sentences = text_content.split('。')
    current_section = ""
    section_idx = 0
    
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
            
        # 如果添加当前句子会超过最大长度，则创建新段落
        if len(current_section + sentence + '。') > max_section_length and current_section:
            sections.append({
                "section_idx": section_idx,
                "type": "text",
                "content": current_section.strip(),
                "length": len(current_section),
                "sentence_count": current_section.count('。') + 1
            })
            section_idx += 1
            current_section = sentence + '。'
        else:
            current_section += sentence + '。'
    
    # 添加最后一个段落
    if current_section.strip():
        sections.append({
            "section_idx": section_idx,
            "type": "text", 
            "content": current_section.strip(),
            "length": len(current_section),
            "sentence_count": current_section.count('。') + 1
        })
    
    return sections

def generate_sections_range(content_path: str) -> int:
    """
    生成文本段落范围信息（替代generate_pages_range功能）
    
    Args:
        content_path: 文本内容目录路径
        
    Returns:
        int: 成功返回1，失败返回0
    """
    try:
        # 查找内容文件
        files = os.listdir(content_path)
        content_files = [f for f in files if f.endswith('_content_list.json')]
        
        if not content_files:
            print(f"No valid content list file found in {content_path}.")
            return 0
        
        content_file = content_files[0]
        file_path = os.path.join(content_path, content_file)
        
        if not os.path.exists(file_path):
            print(f"Content file {file_path} not found.")
            return 0
        
        # 读取内容数据
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        sections = []
        start_section = None
        end_section = None
        
        # 分析文本段落
        for item in data:
            if item.get("type") == "text" and len(item.get("content", "")) > 50:
                if start_section is None:
                    start_section = item.get("section_idx", 0)
                end_section = item.get("section_idx", 0)
        
        if start_section is not None and end_section is not None:
            sections_info = {"sections": [[start_section, end_section]]}
            
            # 保存段落信息
            sections_file = os.path.join(content_path, "sections.json")
            with open(sections_file, 'w', encoding='utf-8') as f:
                json.dump(sections_info, f, ensure_ascii=False, indent=4)
            
            print(f"Generated sections range: {start_section} to {end_section}")
            return 1
        else:
            print("No valid text sections found.")
            return 0
            
    except Exception as e:
        print(f"Error generating sections range: {e}")
        return 0

def extract_key_terms(text: str, domain: str = "semiconductor") -> List[str]:
    """
    从文本中提取关键术语
    
    Args:
        text: 输入文本
        domain: 专业领域（默认为半导体）
        
    Returns:
        List[str]: 提取的关键术语列表
    """
    if not text:
        return []
    
    # 半导体显示领域的关键术语
    semiconductor_terms = [
        'TFT', 'OLED', '薄膜晶体管', '显示器', '背板', '栅极', 
        '介电层', '残影', '可靠性', '器件', '工艺', '制造',
        '像素', '驱动', '电路', '基板', '蒸镀', '刻蚀',
        '光刻', '退火', '掺杂', '沉积', '溅射', '等离子',
        '阈值电压', '迁移率', '开关比', '漏电流', '稳定性'
    ]
    
    found_terms = []
    text_lower = text.lower()
    
    for term in semiconductor_terms:
        if term.lower() in text_lower or term in text:
            found_terms.append(term)
    
    # 使用正则表达式提取可能的技术术语
    # 匹配大写字母开头的词组
    tech_pattern = r'[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)*'
    tech_matches = re.findall(tech_pattern, text)
    
    # 匹配中文技术术语模式
    chinese_tech_pattern = r'[\u4e00-\u9fff]{2,}(?:技术|工艺|方法|器件|材料|设备)'
    chinese_matches = re.findall(chinese_tech_pattern, text)
    
    found_terms.extend(tech_matches)
    found_terms.extend(chinese_matches)
    
    # 去重并返回
    return list(set(found_terms))

def calculate_text_complexity(text: str) -> Dict[str, any]:
    """
    计算文本复杂度
    
    Args:
        text: 输入文本
        
    Returns:
        Dict: 包含复杂度指标的字典
    """
    if not text:
        return {"complexity": "simple", "score": 0}
    
    complexity_metrics = {
        "length": len(text),
        "sentence_count": text.count('。') + text.count('.') + text.count('!') + text.count('?'),
        "word_count": len(text.split()),
        "technical_terms": len(extract_key_terms(text)),
        "avg_sentence_length": 0,
        "complexity": "simple",
        "score": 0
    }
    
    # 计算平均句子长度
    if complexity_metrics["sentence_count"] > 0:
        complexity_metrics["avg_sentence_length"] = complexity_metrics["length"] / complexity_metrics["sentence_count"]
    
    # 计算复杂度分数
    score = 0
    
    # 长度因子
    if complexity_metrics["length"] > 1000:
        score += 3
    elif complexity_metrics["length"] > 500:
        score += 2
    elif complexity_metrics["length"] > 200:
        score += 1
    
    # 技术术语因子
    score += min(complexity_metrics["technical_terms"] * 0.5, 3)
    
    # 句子长度因子
    if complexity_metrics["avg_sentence_length"] > 50:
        score += 2
    elif complexity_metrics["avg_sentence_length"] > 30:
        score += 1
    
    complexity_metrics["score"] = score
    
    # 确定复杂度等级
    if score <= 2:
        complexity_metrics["complexity"] = "simple"
    elif score <= 5:
        complexity_metrics["complexity"] = "medium"
    else:
        complexity_metrics["complexity"] = "complex"
    
    return complexity_metrics

def validate_text_quality(text: str, min_length: int = 50) -> Dict[str, any]:
    """
    验证文本质量
    
    Args:
        text: 输入文本
        min_length: 最小长度要求
        
    Returns:
        Dict: 质量验证结果
    """
    if not text:
        return {
            "is_valid": False,
            "issues": ["Empty text"],
            "quality_score": 0
        }
    
    issues = []
    quality_score = 100
    
    # 长度检查
    if len(text) < min_length:
        issues.append(f"Text too short (minimum {min_length} characters)")
        quality_score -= 20
    
    # 内容检查
    if not re.search(r'[\u4e00-\u9fff]', text) and not re.search(r'[a-zA-Z]', text):
        issues.append("No readable content found")
        quality_score -= 30
    
    # 重复内容检查
    sentences = text.split('。')
    unique_sentences = set(sentences)
    if len(sentences) > 1 and len(unique_sentences) / len(sentences) < 0.8:
        issues.append("High repetition detected")
        quality_score -= 15
    
    # 特殊字符过多检查
    special_char_ratio = len(re.findall(r'[^\w\s\u4e00-\u9fff.,!?;:()[\]{}"-]', text)) / len(text)
    if special_char_ratio > 0.1:
        issues.append("Too many special characters")
        quality_score -= 10
    
    return {
        "is_valid": len(issues) == 0,
        "issues": issues,
        "quality_score": max(0, quality_score),
        "text_length": len(text),
        "sentence_count": len(sentences)
    }

def format_text_for_processing(text: str, format_type: str = "standard") -> str:
    """
    格式化文本用于处理
    
    Args:
        text: 输入文本
        format_type: 格式化类型 ("standard", "compact", "detailed")
        
    Returns:
        str: 格式化后的文本
    """
    if not text:
        return ""
    
    if format_type == "compact":
        # 紧凑格式：移除多余空白，保持基本结构
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
    elif format_type == "detailed":
        # 详细格式：保持原有格式，只做基本清理
        text = text.strip()
        
    else:  # standard
        # 标准格式：适度清理
        text = clean_text_content(text)
        
        # 确保句子间有适当的分隔
        text = re.sub(r'([。!?])([^\s])', r'\1 \2', text)
        
        # 移除多余的空行
        text = re.sub(r'\n\s*\n', '\n\n', text)
    
    return text

def create_text_metadata(text: str, source_path: str = "") -> Dict[str, any]:
    """
    创建文本元数据
    
    Args:
        text: 文本内容
        source_path: 源文件路径
        
    Returns:
        Dict: 文本元数据
    """
    complexity = calculate_text_complexity(text)
    quality = validate_text_quality(text)
    key_terms = extract_key_terms(text)
    
    metadata = {
        "source_path": source_path,
        "creation_time": json.dumps({"timestamp": "auto_generated"}),
        "text_stats": {
            "length": len(text),
            "word_count": len(text.split()),
            "sentence_count": text.count('。') + text.count('.'),
            "paragraph_count": text.count('\n\n') + 1
        },
        "complexity": complexity,
        "quality": quality,
        "key_terms": key_terms[:10],  # 只保留前10个关键术语
        "domain": "semiconductor_display",
        "language": "zh-cn" if re.search(r'[\u4e00-\u9fff]', text) else "en"
    }
    
    return metadata

def save_processed_text(text: str, metadata: Dict, output_path: str) -> bool:
    """
    保存处理后的文本和元数据
    
    Args:
        text: 处理后的文本
        metadata: 文本元数据
        output_path: 输出路径
        
    Returns:
        bool: 保存成功返回True
    """
    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # 保存文本内容
        text_file = output_path.replace('.json', '.txt')
        with open(text_file, 'w', encoding='utf-8') as f:
            f.write(text)
        
        # 保存元数据
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=4)
        
        return True
        
    except Exception as e:
        print(f"Error saving processed text: {e}")
        return False