"""
增强版问题生成器使用示例（纯文本版本）
展示如何配置和使用支持开放型问题和比例控制的纯文本问题生成器
"""

import json
import logging
import os
from question_generator_complete import QuestionGenerator

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_enhanced_config():
    """创建增强版配置（纯文本）"""
    config = {
        # 模型配置
        'models': {
            'qa_generator_model': {
                'path': '/mnt/storage/models/Qwen/Qwen2.5-14B-Instruct',  # 替换为实际模型路径
                'max_length': 4096,
                'temperature': 0.8
            }
        },
        
        # 问题生成配置
        'question_generation': {
            # 问题类型（新增开放型）
            'question_types': ['factual', 'comparison', 'reasoning', 'multi_hop', 'open_ended'],
            
            # 问题类型比例控制（新增功能）
            'question_type_ratios': {
                'factual': 0.25,      # 25% 事实型
                'comparison': 0.20,   # 20% 比较型  
                'reasoning': 0.25,    # 25% 推理型
                'multi_hop': 0.15,    # 15% 多跳型
                'open_ended': 0.15    # 15% 开放型（新增）
            },
            
            # 复杂度级别
            'complexity_levels': {
                'simple': 0.2,
                'medium': 0.5,
                'complex': 0.3
            },
            
            # 语言模式
            'language_patterns': {
                'zh_cn': 0.8,
                'en': 0.2
            },
            
            # 问题类型优先级（新增）
            'question_type_priorities': {
                'open_ended': 1,      # 最高优先级
                'reasoning': 2,       # 高优先级
                'factual': 3,         # 中等优先级
                'comparison': 4,      # 较低优先级
                'multi_hop': 5        # 最低优先级
            }
        },
        
        # 文本处理配置（替代图像处理）
        'text_processing': {
            'max_section_length': 1000,
            'min_text_length': 50,
            'quality_threshold': 0.7,
            'enable_text_cleaning': True,
            'preserve_formatting': False
        },
        
        # TCL特定配置
        'tcl_specific': {
            'domain': 'semiconductor_display',
            'enable_domain_terms': True,
            'technical_focus': True,
            'industry_context': 'TCL显示技术'
        }
    }
    
    return config

def create_sample_text_data():
    """创建示例文本数据"""
    sample_texts = [
        {
            "id": "text_001",
            "content": """
            薄膜晶体管（TFT）是现代显示技术的核心组件。在OLED显示器中，TFT背板负责控制每个像素的开关状态。
            栅极介电层的厚度和材料选择直接影响器件的可靠性和性能。常用的介电材料包括二氧化硅和氮化硅。
            在制造过程中，需要严格控制工艺参数以确保器件的一致性和稳定性。
            """,
            "context": "TFT技术基础",
            "domain": "semiconductor_display"
        },
        {
            "id": "text_002", 
            "content": """
            OLED显示技术具有自发光、高对比度、快速响应等优势。然而，在短时间内驱动时容易出现残影问题。
            这主要是由于有机材料的老化和载流子迁移率的变化导致的。为了改善残影问题，需要从TFT设计、
            驱动算法和材料选择等多个方面进行优化。补偿电路的设计也是关键因素之一。
            """,
            "context": "OLED显示技术",
            "domain": "semiconductor_display"
        },
        {
            "id": "text_003",
            "content": """
            在大尺寸OLED面板生产中，均匀性控制是一个重大挑战。由于基板尺寸较大，
            在蒸镀过程中很难保证有机材料在整个基板上的均匀分布。这会导致不同区域的
            发光效率和色彩表现存在差异。通过优化蒸镀源的设计和工艺参数，可以在一定程度上
            改善均匀性问题，但同时也会影响生产良率和成本。
            """,
            "context": "大尺寸OLED制造",
            "domain": "semiconductor_display"
        }
    ]
    
    return sample_texts

def demonstrate_basic_usage():
    """演示基本使用方法"""
    print("=== 基本使用演示 ===")
    
    # 创建配置
    config = create_enhanced_config()
    
    # 初始化问题生成器
    qg = QuestionGenerator(config)
    
    # 创建示例文本数据
    sample_texts = create_sample_text_data()
    
    # 为每个文本生成问答对
    for text_data in sample_texts:
        print(f"\n处理文本: {text_data['id']}")
        print(f"上下文: {text_data['context']}")
        
        # 生成问题
        questions = qg.generate_questions(
            text_content=text_data['content'],
            num_questions=5
        )
        
        # 生成答案
        qa_pairs = qg.generate_answers(questions, text_data['content'])
        
        # 显示结果
        for i, qa in enumerate(qa_pairs, 1):
            print(f"\n问题 {i} ({qa['type']}):")
            print(f"Q: {qa['question']}")
            print(f"A: {qa['answer']}")
            print(f"推理: {qa['reasoning']}")

def demonstrate_batch_processing():
    """演示批量处理功能"""
    print("\n=== 批量处理演示 ===")
    
    # 创建批量文本数据
    sample_texts = create_sample_text_data()
    
    # 保存为JSON文件
    os.makedirs("data", exist_ok=True)
    with open("data/sample_texts.json", "w", encoding='utf-8') as f:
        json.dump(sample_texts, f, ensure_ascii=False, indent=2)
    
    print("示例文本数据已保存到 data/sample_texts.json")
    print("可以使用以下命令进行批量处理:")
    print("python batch_inference.py --workers 2 --concurrency 10")

def demonstrate_different_configs():
    """演示不同配置的使用"""
    print("\n=== 不同配置演示 ===")
    
    # 加载配置模板
    with open("config_templates.json", "r", encoding='utf-8') as f:
        templates = json.load(f)
    
    configs_to_test = [
        ("均衡配置", "balanced_config"),
        ("开放型重点", "open_ended_focused"),
        ("文本分析专用", "text_analysis_focused")
    ]
    
    sample_text = create_sample_text_data()[0]['content']
    
    for config_name, config_key in configs_to_test:
        print(f"\n--- {config_name} ---")
        
        # 创建基础配置
        base_config = create_enhanced_config()
        
        # 应用模板配置
        template = templates['config_templates'][config_key]
        base_config['question_generation']['question_type_ratios'] = template['question_type_ratios']
        
        # 生成问题
        qg = QuestionGenerator(base_config)
        questions = qg.generate_questions(sample_text, num_questions=3)
        
        # 显示问题类型分布
        type_counts = {}
        for q in questions:
            q_type = q['type']
            type_counts[q_type] = type_counts.get(q_type, 0) + 1
        
        print(f"问题类型分布: {type_counts}")

def demonstrate_quality_control():
    """演示质量控制功能"""
    print("\n=== 质量控制演示 ===")
    
    config = create_enhanced_config()
    qg = QuestionGenerator(config)
    
    # 测试不同质量的文本
    test_texts = [
        "这是一个很短的文本。",  # 太短
        "TFT OLED 显示器 栅极 介电层 器件 可靠性 工艺 制造 像素 驱动 电路。" * 10,  # 重复内容
        create_sample_text_data()[0]['content']  # 正常文本
    ]
    
    for i, text in enumerate(test_texts, 1):
        print(f"\n测试文本 {i}:")
        print(f"长度: {len(text)} 字符")
        
        try:
            questions = qg.generate_questions(text, num_questions=2)
            print(f"生成问题数量: {len(questions)}")
            
            if questions:
                print(f"示例问题: {questions[0]['question']}")
        except Exception as e:
            print(f"生成失败: {e}")

def demonstrate_statistics():
    """演示统计功能"""
    print("\n=== 统计信息演示 ===")
    
    config = create_enhanced_config()
    qg = QuestionGenerator(config)
    
    # 获取生成统计
    stats = qg.get_generation_statistics()
    
    print("问题生成器统计信息:")
    print(json.dumps(stats, ensure_ascii=False, indent=2))

def save_configuration_examples():
    """保存配置示例"""
    print("\n=== 保存配置示例 ===")
    
    # 创建不同场景的配置
    configs = {
        "basic_config": create_enhanced_config(),
        "high_quality_config": {
            **create_enhanced_config(),
            "question_generation": {
                **create_enhanced_config()["question_generation"],
                "question_type_ratios": {
                    "factual": 0.20,
                    "comparison": 0.15,
                    "reasoning": 0.30,
                    "multi_hop": 0.20,
                    "open_ended": 0.15
                }
            }
        },
        "fast_processing_config": {
            **create_enhanced_config(),
            "batch_processing": {
                "max_workers": 8,
                "max_concurrency_per_worker": 512,
                "batch_size": 20,
                "timeout_seconds": 180
            }
        }
    }
    
    # 保存配置文件
    os.makedirs("configs", exist_ok=True)
    
    for config_name, config_data in configs.items():
        config_file = f"configs/{config_name}.json"
        with open(config_file, "w", encoding='utf-8') as f:
            json.dump(config_data, f, ensure_ascii=False, indent=2)
        print(f"配置已保存: {config_file}")

def main():
    """主函数"""
    print("纯文本问答对生成系统 - 使用示例")
    print("=" * 50)
    
    try:
        # 基本使用演示
        demonstrate_basic_usage()
        
        # 批量处理演示
        demonstrate_batch_processing()
        
        # 不同配置演示
        demonstrate_different_configs()
        
        # 质量控制演示
        demonstrate_quality_control()
        
        # 统计信息演示
        demonstrate_statistics()
        
        # 保存配置示例
        save_configuration_examples()
        
        print("\n" + "=" * 50)
        print("所有演示完成！")
        print("\n使用建议:")
        print("1. 根据需求选择合适的配置模板")
        print("2. 调整问题类型比例以适应具体场景")
        print("3. 使用批量处理功能提高效率")
        print("4. 启用质量控制确保输出质量")
        
    except Exception as e:
        logger.error(f"演示过程中出现错误: {e}")
        print(f"错误: {e}")

if __name__ == "__main__":
    main()