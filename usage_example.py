"""
增强版问题生成器使用示例
展示如何配置和使用支持开放型问题和比例控制的问题生成器
"""

import json
import logging
from question_generator_complete import QuestionGenerator

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_enhanced_config():
    """创建增强版配置"""
    config = {
        # 模型配置
        'models': {
            'qa_generator_model': {
                'path': '/path/to/your/model',  # 替换为实际模型路径
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
            }
        },
        
        # 数据集质量控制
        'dataset_synthesis': {
            'quality_checks': {
                'min_question_length': 50,
                'max_question_length': 500,
                'min_answer_length': 30
            }
        },
        
        # TCL特定配置
        'tcl_specific': {
            'domain': 'electronics_manufacturing',
            'focus_areas': ['display_technology', 'semiconductor', 'manufacturing_process']
        },
        
        # 数据源
        'source': 'tcl_knowledge_graph'
    }
    
    return config

def create_sample_subgraphs():
    """创建示例子图数据"""
    subgraphs = [
        {
            'nodes': [
                {'id': 'TFT器件', 'type': 'technology', 'properties': {'domain': 'semiconductor'}},
                {'id': '顶栅氧化物', 'type': 'material', 'properties': {'application': 'gate_oxide'}},
                {'id': '短沟道', 'type': 'structure', 'properties': {'dimension': 'nanoscale'}},
                {'id': '器件失效', 'type': 'problem', 'properties': {'severity': 'critical'}}
            ],
            'edges': [
                {'source': 'TFT器件', 'target': '顶栅氧化物', 'relation': '使用'},
                {'source': '短沟道', 'target': 'TFT器件', 'relation': '影响'},
                {'source': '器件失效', 'target': 'TFT器件', 'relation': '威胁'}
            ],
            'topology': 'star',
            'center': 'TFT器件'
        },
        {
            'nodes': [
                {'id': 'OLED显示', 'type': 'application', 'properties': {'domain': 'display'}},
                {'id': '金属氧化物背板', 'type': 'component', 'properties': {'material': 'oxide'}},
                {'id': '残影问题', 'type': 'problem', 'properties': {'type': 'image_retention'}},
                {'id': '驱动时间', 'type': 'parameter', 'properties': {'unit': 'milliseconds'}}
            ],
            'edges': [
                {'source': '金属氧化物背板', 'target': 'OLED显示', 'relation': '驱动'},
                {'source': '驱动时间', 'target': '残影问题', 'relation': '导致'},
                {'source': '残影问题', 'target': 'OLED显示', 'relation': '影响'}
            ],
            'topology': 'chain',
            'path': ['金属氧化物背板', '驱动时间', '残影问题', 'OLED显示']
        },
        {
            'nodes': [
                {'id': 'SMT工艺', 'type': 'process', 'properties': {'domain': 'manufacturing'}},
                {'id': 'PCB基板', 'type': 'component', 'properties': {'material': 'substrate'}},
                {'id': '焊膏印刷', 'type': 'process', 'properties': {'step': 'assembly'}},
                {'id': '温度控制', 'type': 'parameter', 'properties': {'critical': True}}
            ],
            'edges': [
                {'source': 'SMT工艺', 'target': 'PCB基板', 'relation': '处理'},
                {'source': '焊膏印刷', 'target': 'PCB基板', 'relation': '应用于'},
                {'source': '温度控制', 'target': 'SMT工艺', 'relation': '控制'}
            ],
            'topology': 'tree'
        }
    ]
    
    return subgraphs

def demonstrate_question_generation():
    """演示问题生成功能"""
    print("=== 增强版问题生成器演示 ===\n")
    
    # 1. 创建配置
    print("1. 创建增强版配置...")
    config = create_enhanced_config()
    print(f"   - 支持问题类型: {config['question_generation']['question_types']}")
    print(f"   - 问题类型比例: {config['question_generation']['question_type_ratios']}")
    print()
    
    # 2. 初始化问题生成器
    print("2. 初始化问题生成器...")
    try:
        generator = QuestionGenerator(config)
        print("   ✓ 问题生成器初始化成功")
    except Exception as e:
        print(f"   ✗ 初始化失败: {str(e)}")
        print("   注意：需要配置正确的模型路径")
        return
    print()
    
    # 3. 创建示例数据
    print("3. 创建示例子图数据...")
    subgraphs = create_sample_subgraphs()
    print(f"   - 创建了 {len(subgraphs)} 个示例子图")
    for i, subgraph in enumerate(subgraphs):
        print(f"   - 子图{i+1}: {len(subgraph['nodes'])}个节点, {len(subgraph['edges'])}条边")
    print()
    
    # 4. 生成问题
    print("4. 开始生成问题...")
    try:
        qa_pairs = generator.generate_questions(subgraphs)
        print(f"   ✓ 成功生成 {len(qa_pairs)} 个QA对")
        
        # 统计问题类型分布
        type_distribution = {}
        for qa in qa_pairs:
            q_type = qa.get('type', 'unknown').split('_')[0]
            type_distribution[q_type] = type_distribution.get(q_type, 0) + 1
        
        print("   - 问题类型分布:")
        for q_type, count in type_distribution.items():
            percentage = (count / len(qa_pairs)) * 100
            print(f"     * {q_type}: {count} 个 ({percentage:.1f}%)")
        
    except Exception as e:
        print(f"   ✗ 问题生成失败: {str(e)}")
        return
    print()
    
    # 5. 展示生成的问题示例
    print("5. 生成的问题示例:")
    print("-" * 60)
    
    # 按类型展示问题
    for q_type in ['factual', 'comparison', 'reasoning', 'multi_hop', 'open_ended']:
        type_questions = [qa for qa in qa_pairs if qa.get('type', '').startswith(q_type)]
        if type_questions:
            print(f"\n【{q_type.upper()}类型问题】")
            for i, qa in enumerate(type_questions[:2]):  # 每种类型最多展示2个
                print(f"\n问题{i+1}: {qa['question']}")
                print(f"答案: {qa['answer'][:100]}...")
                print(f"生成方法: {qa.get('generation_method', 'unknown')}")
                if qa.get('quality_score'):
                    print(f"质量分数: {qa['quality_score']:.2f}")
    
    print("\n" + "=" * 60)
    print("演示完成！")

def demonstrate_ratio_control():
    """演示比例控制功能"""
    print("\n=== 比例控制功能演示 ===\n")
    
    # 创建不同比例配置
    ratio_configs = [
        {
            'name': '均衡配置',
            'ratios': {
                'factual': 0.25, 'comparison': 0.20, 'reasoning': 0.25,
                'multi_hop': 0.15, 'open_ended': 0.15
            }
        },
        {
            'name': '开放型重点配置',
            'ratios': {
                'factual': 0.15, 'comparison': 0.15, 'reasoning': 0.20,
                'multi_hop': 0.10, 'open_ended': 0.40
            }
        },
        {
            'name': '传统型配置',
            'ratios': {
                'factual': 0.40, 'comparison': 0.30, 'reasoning': 0.30,
                'multi_hop': 0.00, 'open_ended': 0.00
            }
        }
    ]
    
    for config_info in ratio_configs:
        print(f"配置: {config_info['name']}")
        print("目标比例:")
        for q_type, ratio in config_info['ratios'].items():
            print(f"  - {q_type}: {ratio*100:.1f}%")
        print()

def show_open_ended_examples():
    """展示开放型问题的特点"""
    print("\n=== 开放型问题特点展示 ===\n")
    
    open_ended_examples = [
        {
            'question': '怎么实现短沟道的顶栅氧化物TFT器件且同时避免器件失效？',
            'features': ['技术实现挑战', '多约束优化', '工程实践导向']
        },
        {
            'question': '金属氧化物背板在短时间内驱动OLED显示时会出现残影，请问如何在TFT方面改善残影问题？',
            'features': ['问题诊断', '解决方案探索', '跨领域思考']
        },
        {
            'question': '在高密度集成电路制造中，如何平衡工艺复杂度、成本控制和良品率之间的关系？',
            'features': ['系统优化', '多目标平衡', '决策支持']
        }
    ]
    
    print("开放型问题的特点：")
    print("1. 没有标准答案，需要创新思维")
    print("2. 涉及多个技术维度和约束条件")
    print("3. 需要系统性分析和综合判断")
    print("4. 贴近实际工程问题和应用场景")
    print()
    
    print("示例问题：")
    for i, example in enumerate(open_ended_examples, 1):
        print(f"\n{i}. {example['question']}")
        print(f"   特点: {', '.join(example['features'])}")

if __name__ == "__main__":
    # 运行演示
    demonstrate_question_generation()
    demonstrate_ratio_control()
    show_open_ended_examples()
    
    print("\n" + "=" * 80)
    print("使用说明：")
    print("1. 修改 create_enhanced_config() 中的模型路径")
    print("2. 根据需要调整问题类型比例")
    print("3. 可以添加更多的开放型问题模板")
    print("4. 质量控制参数可根据实际需求调整")
    print("=" * 80)