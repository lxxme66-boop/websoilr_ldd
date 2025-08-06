"""
E2HQA Text Generator Usage Example
展示如何使用E2HQA文本问答生成系统的完整示例
"""

import asyncio
import json
import logging
from e2hqa_text_generator import E2HQAGenerator, create_default_config

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_production_config():
    """创建生产环境配置"""
    return {
        'gpt4_config': {
            'api_key': 'your-gpt4-api-key-here',  # 替换为实际的GPT-4 API密钥
            'base_url': 'https://api.openai.com/v1'
        },
        'lrm_config': {
            'api_key': 'your-lrm-api-key-here',   # 替换为实际的LRM API密钥
            'base_url': 'https://api.your-lrm-provider.com/v1'  # 替换为实际的LRM API地址
        },
        'rejection_sampling_n': 5,  # N次拒绝采样
        'quality_threshold': 0.75,  # 提高质量阈值
        'qa_type_ratios': {
            'simple_factual': 0.15,      # 减少简单事实型问题
            'complex_reasoning': 0.35,   # 增加复杂推理型问题
            'multi_hop': 0.25,           # 增加多跳问题
            'analytical': 0.15,          # 分析型问题
            'open_ended': 0.10           # 开放型问题
        },
        'cot_type_ratios': {
            'short_cot': 0.3,   # 30% Short CoT (GPT-4)
            'long_cot': 0.7     # 70% Long CoT (LRMs)
        },
        'trajectory_filter': {
            'format_validation': True,
            'answer_correctness': True,
            'quality_assessment': True,
            'redundancy_check': True,
            'alignment_check': True,
            'reasoning_coherence': True
        }
    }

def create_research_config():
    """创建研究导向配置，重点关注开放性和创新性"""
    return {
        'gpt4_config': {
            'api_key': 'your-gpt4-api-key-here',
            'base_url': 'https://api.openai.com/v1'
        },
        'lrm_config': {
            'api_key': 'your-lrm-api-key-here',
            'base_url': 'https://api.your-lrm-provider.com/v1'
        },
        'rejection_sampling_n': 8,  # 更多候选轨迹
        'quality_threshold': 0.7,
        'qa_type_ratios': {
            'simple_factual': 0.05,      # 最少事实型
            'complex_reasoning': 0.25,   # 复杂推理
            'multi_hop': 0.20,           # 多跳推理
            'analytical': 0.25,          # 分析型（增加）
            'open_ended': 0.25           # 开放型（大幅增加）
        },
        'cot_type_ratios': {
            'short_cot': 0.2,   # 20% Short CoT
            'long_cot': 0.8     # 80% Long CoT（更多深度推理）
        },
        'trajectory_filter': {
            'format_validation': True,
            'answer_correctness': True,
            'quality_assessment': True,
            'redundancy_check': True,
            'alignment_check': True,
            'reasoning_coherence': True
        }
    }

async def basic_usage_example():
    """基础使用示例"""
    logger.info("=== 基础使用示例 ===")
    
    # 创建配置
    config = create_default_config()
    
    # 初始化生成器
    generator = E2HQAGenerator(config)
    
    # 示例文本
    text = """
    深度学习是机器学习的一个分支，它基于人工神经网络的表示学习。深度学习的核心思想是通过多层神经网络来学习数据的表示，
    每一层都能够学习到数据的不同抽象级别的特征。卷积神经网络(CNN)特别适合处理图像数据，而循环神经网络(RNN)则擅长
    处理序列数据。近年来，Transformer架构的出现革命性地改变了自然语言处理领域，GPT和BERT等模型都基于这一架构。
    深度学习在计算机视觉、自然语言处理、语音识别等领域都取得了突破性进展。
    """
    
    try:
        # 生成QA轨迹
        trajectories = await generator.generate_qa_from_text(text, num_questions=3)
        
        # 保存结果
        generator.save_trajectories(trajectories, 'basic_example_trajectories.json')
        
        # 生成质量报告
        report = generator.generate_quality_report(trajectories)
        
        logger.info(f"生成了 {len(trajectories)} 个QA轨迹")
        logger.info(f"平均质量分数: {report['quality_distribution']['average_score']:.3f}")
        
        # 展示一个示例轨迹
        if trajectories:
            example = trajectories[0]
            print(f"\n示例轨迹 (ID: {example.trajectory_id}):")
            print(f"问题: {example.question}")
            print(f"答案: {example.answer}")
            print(f"推理步骤:")
            for i, step in enumerate(example.reasoning_steps, 1):
                print(f"  {i}. {step}")
            print(f"质量评分: {example.quality_metrics.get('overall_score', 0):.3f}")
        
    except Exception as e:
        logger.error(f"基础示例执行失败: {e}")

async def advanced_usage_example():
    """高级使用示例 - 使用生产配置"""
    logger.info("=== 高级使用示例 ===")
    
    # 使用生产配置
    config = create_production_config()
    generator = E2HQAGenerator(config)
    
    # 更复杂的文本
    text = """
    量子计算是一种遵循量子力学规律调控量子信息单元进行计算的新型计算模式。与经典计算机使用比特作为信息的基本单位不同，
    量子计算机使用量子比特(qubit)。量子比特具有叠加态的特性，可以同时处于0和1的状态，这使得量子计算机在理论上能够
    并行处理大量信息。量子纠缠是量子计算的另一个重要特性，它允许量子比特之间建立强关联，即使它们在空间上分离。
    
    量子算法如Shor算法和Grover算法展示了量子计算在特定问题上的指数级加速能力。Shor算法能够高效分解大整数，
    这对现有的RSA加密体系构成了潜在威胁。Grover算法则能够在无序数据库中进行快速搜索。
    
    然而，量子计算机的实现面临着巨大的技术挑战。量子退相干是最主要的障碍之一，环境噪声会破坏量子态的相干性。
    此外，量子纠错、量子门的精确控制、以及可扩展的量子系统架构都是需要解决的关键问题。
    
    目前，IBM、Google、Microsoft等公司都在积极研发量子计算机。Google在2019年声称实现了"量子优势"，
    其53量子比特的处理器Sycamore在特定问题上超越了经典超级计算机。
    """
    
    try:
        # 生成更多QA轨迹
        trajectories = await generator.generate_qa_from_text(text, num_questions=6)
        
        # 保存结果
        generator.save_trajectories(trajectories, 'advanced_example_trajectories.json')
        
        # 生成详细报告
        report = generator.generate_quality_report(trajectories)
        
        logger.info(f"生成了 {len(trajectories)} 个高质量QA轨迹")
        
        # 详细分析
        print("\n=== 详细质量报告 ===")
        print(f"总轨迹数: {report['total_trajectories']}")
        print(f"质量分布:")
        print(f"  优秀 (≥0.9): {report['quality_distribution']['excellent']}")
        print(f"  良好 (0.7-0.9): {report['quality_distribution']['good']}")
        print(f"  一般 (0.5-0.7): {report['quality_distribution']['fair']}")
        print(f"  较差 (<0.5): {report['quality_distribution']['poor']}")
        print(f"  平均分数: {report['quality_distribution']['average_score']:.3f}")
        
        print(f"\nQA类型分布:")
        for qa_type, count in report['type_distribution'].items():
            print(f"  {qa_type}: {count}")
        
        print(f"\nCoT类型分布:")
        for cot_type, count in report['cot_distribution'].items():
            print(f"  {cot_type}: {count}")
        
        print(f"\n平均质量指标:")
        for metric, score in report['average_metrics'].items():
            print(f"  {metric}: {score:.3f}")
        
        # 展示最佳轨迹
        best_trajectory = max(trajectories, key=lambda t: t.quality_metrics.get('overall_score', 0))
        print(f"\n=== 最佳轨迹示例 ===")
        print(f"轨迹ID: {best_trajectory.trajectory_id}")
        print(f"QA类型: {best_trajectory.qa_type.value}")
        print(f"CoT类型: {best_trajectory.cot_type.value}")
        print(f"问题: {best_trajectory.question}")
        print(f"答案: {best_trajectory.answer[:200]}...")  # 截取前200字符
        print(f"推理步骤数: {len(best_trajectory.reasoning_steps)}")
        print(f"质量评分: {best_trajectory.quality_metrics.get('overall_score', 0):.3f}")
        
    except Exception as e:
        logger.error(f"高级示例执行失败: {e}")

async def research_focused_example():
    """研究导向示例 - 重点关注开放性问题"""
    logger.info("=== 研究导向示例 ===")
    
    config = create_research_config()
    generator = E2HQAGenerator(config)
    
    # 学术研究文本
    text = """
    大语言模型(Large Language Models, LLMs)的涌现能力是指在模型规模达到某个临界点后突然出现的、在小规模模型中不存在的能力。
    这些能力包括少样本学习、思维链推理、代码生成等。研究表明，涌现能力的出现与模型参数量、训练数据规模和计算资源密切相关。
    
    然而，涌现能力的机制仍然不完全清楚。一些研究者认为这是由于模型内部表示的质变，另一些则认为是量变积累的结果。
    理解涌现能力对于预测未来模型的能力边界、指导模型设计和训练策略具有重要意义。
    
    同时，大语言模型也面临着诸多挑战，包括幻觉问题、偏见、对抗攻击的脆弱性、以及巨大的计算成本等。
    如何在保持强大能力的同时解决这些问题，是当前研究的重点方向。
    """
    
    try:
        trajectories = await generator.generate_qa_from_text(text, num_questions=4)
        
        generator.save_trajectories(trajectories, 'research_example_trajectories.json')
        report = generator.generate_quality_report(trajectories)
        
        logger.info(f"生成了 {len(trajectories)} 个研究导向QA轨迹")
        
        # 重点关注开放性和分析性问题
        open_ended_count = sum(1 for t in trajectories if t.qa_type.value == 'open_ended')
        analytical_count = sum(1 for t in trajectories if t.qa_type.value == 'analytical')
        
        print(f"\n=== 研究导向分析 ===")
        print(f"开放性问题数量: {open_ended_count}")
        print(f"分析性问题数量: {analytical_count}")
        print(f"Long CoT轨迹数量: {sum(1 for t in trajectories if t.cot_type.value == 'long_cot')}")
        
        # 展示开放性问题示例
        open_ended_trajectories = [t for t in trajectories if t.qa_type.value == 'open_ended']
        if open_ended_trajectories:
            example = open_ended_trajectories[0]
            print(f"\n=== 开放性问题示例 ===")
            print(f"问题: {example.question}")
            print(f"答案: {example.answer}")
            print(f"推理步骤:")
            for i, step in enumerate(example.reasoning_steps, 1):
                print(f"  {i}. {step}")
        
    except Exception as e:
        logger.error(f"研究示例执行失败: {e}")

async def batch_processing_example():
    """批量处理示例"""
    logger.info("=== 批量处理示例 ===")
    
    config = create_production_config()
    generator = E2HQAGenerator(config)
    
    # 多个文本样本
    text_samples = [
        """
        区块链技术是一种分布式账本技术，通过密码学方法将数据区块按时间顺序链接，形成不可篡改的数据链。
        每个区块包含前一个区块的哈希值，形成链式结构。共识机制确保网络中的所有节点对账本状态达成一致。
        """,
        
        """
        基因编辑技术CRISPR-Cas9允许科学家精确地修改DNA序列。该技术由向导RNA和Cas9核酸酶组成，
        能够在特定位置切割DNA并插入、删除或替换基因片段。这为治疗遗传疾病提供了新的可能性。
        """,
        
        """
        可再生能源包括太阳能、风能、水能、地热能等。这些能源具有可持续性，不会耗尽地球资源。
        太阳能电池板将光能转换为电能，风力发电机利用风能发电。储能技术的发展解决了可再生能源的间歇性问题。
        """
    ]
    
    all_trajectories = []
    
    try:
        for i, text in enumerate(text_samples, 1):
            logger.info(f"处理文本样本 {i}/{len(text_samples)}")
            
            trajectories = await generator.generate_qa_from_text(text, num_questions=2)
            all_trajectories.extend(trajectories)
            
            # 为每个样本保存单独的文件
            generator.save_trajectories(trajectories, f'batch_sample_{i}_trajectories.json')
        
        # 保存所有轨迹
        generator.save_trajectories(all_trajectories, 'batch_all_trajectories.json')
        
        # 综合报告
        overall_report = generator.generate_quality_report(all_trajectories)
        
        print(f"\n=== 批量处理结果 ===")
        print(f"处理文本数: {len(text_samples)}")
        print(f"总轨迹数: {len(all_trajectories)}")
        print(f"平均质量分数: {overall_report['quality_distribution']['average_score']:.3f}")
        
        # 保存综合报告
        with open('batch_processing_report.json', 'w', encoding='utf-8') as f:
            json.dump(overall_report, f, ensure_ascii=False, indent=2)
        
        logger.info("批量处理完成，报告已保存")
        
    except Exception as e:
        logger.error(f"批量处理失败: {e}")

def quality_analysis_example():
    """质量分析示例 - 分析已生成的轨迹"""
    logger.info("=== 质量分析示例 ===")
    
    try:
        # 加载之前生成的轨迹
        with open('batch_all_trajectories.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"\n=== 轨迹质量分析 ===")
        print(f"总轨迹数: {len(data)}")
        
        # 质量分布分析
        quality_scores = [item['quality_metrics'].get('overall_score', 0) for item in data]
        
        print(f"质量分数统计:")
        print(f"  最高分: {max(quality_scores):.3f}")
        print(f"  最低分: {min(quality_scores):.3f}")
        print(f"  平均分: {sum(quality_scores) / len(quality_scores):.3f}")
        print(f"  中位数: {sorted(quality_scores)[len(quality_scores)//2]:.3f}")
        
        # 各维度分析
        dimensions = ['complexity', 'reasoning_quality', 'content_richness', 'language_quality', 'novelty']
        
        print(f"\n各维度平均分:")
        for dim in dimensions:
            scores = [item['quality_metrics'].get(dim, 0) for item in data]
            avg_score = sum(scores) / len(scores) if scores else 0
            print(f"  {dim}: {avg_score:.3f}")
        
        # 类型分析
        qa_types = [item['qa_type'] for item in data]
        cot_types = [item['cot_type'] for item in data]
        
        print(f"\nQA类型分布:")
        for qa_type in set(qa_types):
            count = qa_types.count(qa_type)
            avg_quality = sum(item['quality_metrics'].get('overall_score', 0) 
                            for item in data if item['qa_type'] == qa_type) / count
            print(f"  {qa_type}: {count} 个 (平均质量: {avg_quality:.3f})")
        
        print(f"\nCoT类型分布:")
        for cot_type in set(cot_types):
            count = cot_types.count(cot_type)
            avg_quality = sum(item['quality_metrics'].get('overall_score', 0) 
                            for item in data if item['cot_type'] == cot_type) / count
            print(f"  {cot_type}: {count} 个 (平均质量: {avg_quality:.3f})")
        
    except FileNotFoundError:
        logger.warning("未找到轨迹文件，请先运行批量处理示例")
    except Exception as e:
        logger.error(f"质量分析失败: {e}")

async def main():
    """主函数 - 运行所有示例"""
    print("E2HQA Text Generator 使用示例")
    print("=" * 50)
    
    # 运行各种示例
    await basic_usage_example()
    await advanced_usage_example()
    await research_focused_example()
    await batch_processing_example()
    
    # 质量分析（同步函数）
    quality_analysis_example()
    
    print("\n所有示例执行完成！")
    print("生成的文件:")
    print("- basic_example_trajectories.json")
    print("- advanced_example_trajectories.json")  
    print("- research_example_trajectories.json")
    print("- batch_sample_*_trajectories.json")
    print("- batch_all_trajectories.json")
    print("- batch_processing_report.json")

if __name__ == "__main__":
    # 运行示例
    asyncio.run(main())