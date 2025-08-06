#!/usr/bin/env python3
"""
测试增强质量检查功能
演示如何使用新的增强质量检查器
"""

import asyncio
import json
import os
import sys
from TextQA.enhanced_quality_checker import EnhancedQualityChecker, TextQAQualityIntegrator

def create_sample_qa_data():
    """创建测试用的QA数据"""
    sample_qa_pairs = [
        {
            "question": "IGZO薄膜晶体管的载流子迁移率通常在什么范围内？",
            "answer": "IGZO薄膜晶体管的载流子迁移率通常在10-15 cm²/V·s范围内，这比非晶硅TFT的迁移率（约0.5-1 cm²/V·s）要高得多。",
            "question_type": "factual",
            "source_file": "test_sample.txt"
        },
        {
            "question": "顶栅结构的IGZO TFT相比底栅结构有什么优势？",
            "answer": "顶栅结构的IGZO TFT相比底栅结构主要有以下优势：1）更好的器件性能控制；2）减少背沟道效应；3）更高的开关比；4）更好的稳定性。",
            "question_type": "comparison",
            "source_file": "test_sample.txt"
        },
        {
            "question": "为什么氧空位会影响IGZO的电学性能？",
            "answer": "氧空位是IGZO中的主要载流子来源。氧空位的存在会产生自由电子，增加材料的导电性。氧空位浓度的变化直接影响载流子浓度，从而改变材料的电阻率和迁移率。",
            "question_type": "reasoning",
            "source_file": "test_sample.txt"
        },
        {
            "question": "如何优化IGZO TFT的制造工艺以提高器件稳定性？",
            "answer": "优化IGZO TFT制造工艺可从以下方面入手：1）控制溅射参数优化薄膜质量；2）选择合适的退火条件；3）优化栅介质材料和厚度；4）改进钝化层设计；5）控制制造环境的氧气和湿度。",
            "question_type": "open_ended",
            "source_file": "test_sample.txt"
        }
    ]
    return sample_qa_pairs

def save_test_data(qa_pairs, file_path):
    """保存测试数据到文件"""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    # 保存为text_qa_generation格式
    test_data = [{
        "source_file": "test_sample.txt",
        "qa_pairs": qa_pairs
    }]
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(test_data, f, ensure_ascii=False, indent=2)
    
    print(f"测试数据已保存到: {file_path}")

async def test_enhanced_quality_checker():
    """测试增强质量检查器的核心功能"""
    print("=== 测试增强质量检查器核心功能 ===\n")
    
    # 配置参数
    api_key = "ae37bba4-73be-4c22-b1a7-c6b1f5ec3a4b"
    base_url = "http://0.0.0.0:8080/v1"
    model = "/mnt/storage/models/Skywork/Skywork-R1V3-38B"
    system_prompt = """你是一位半导体和显示技术领域的资深专家，特别擅长IGZO、TFT、OLED等相关技术。
你需要准确回答技术问题，并能够判断答案的正确性和完整性。
请确保你的回答准确、专业、有深度。"""
    
    # 初始化检查器
    checker = EnhancedQualityChecker(
        api_key=api_key,
        base_url=base_url,
        model=model,
        system_prompt=system_prompt,
        parallel_core=2,  # 测试时使用较小的并发数
        activate_stream=False
    )
    
    # 创建测试数据
    test_qa_pairs = create_sample_qa_data()
    
    print(f"创建了 {len(test_qa_pairs)} 个测试QA对")
    print("开始验证QA对质量...\n")
    
    try:
        # 批量验证
        results = await checker.batch_verify_qa_pairs(test_qa_pairs)
        
        print("=== 验证结果 ===")
        for i, result in enumerate(results, 1):
            print(f"\nQA对 {i}:")
            print(f"问题: {result.get('question', '')[:50]}...")
            print(f"质量标签: {result.get('quality_label', 0)}")
            
            details = result.get('verification_details', {})
            if isinstance(details, dict):
                print(f"模型回答长度: {details.get('model_answer_length', 0)} 字符")
                print(f"验证响应: {details.get('verification_response', '')[:30]}...")
        
        # 统计
        passed = sum(1 for r in results if r.get('quality_label', 0) == 1)
        pass_rate = passed / len(results) if results else 0
        print(f"\n总体统计:")
        print(f"通过数量: {passed}/{len(results)}")
        print(f"通过率: {pass_rate:.2%}")
        
        return True
        
    except Exception as e:
        print(f"测试失败: {e}")
        return False

async def test_file_quality_check():
    """测试文件质量检查功能"""
    print("\n=== 测试文件质量检查功能 ===\n")
    
    # 准备测试文件
    test_file_path = "/workspace/text_qa_generation/data/output/test_qa_sample.json"
    test_qa_pairs = create_sample_qa_data()
    save_test_data(test_qa_pairs, test_file_path)
    
    # 配置参数
    api_key = "ae37bba4-73be-4c22-b1a7-c6b1f5ec3a4b"
    base_url = "http://0.0.0.0:8080/v1"
    model = "/mnt/storage/models/Skywork/Skywork-R1V3-38B"
    system_prompt = """你是一位半导体和显示技术领域的资深专家，特别擅长IGZO、TFT、OLED等相关技术。
你需要准确回答技术问题，并能够判断答案的正确性和完整性。
请确保你的回答准确、专业、有深度。"""
    
    # 初始化检查器
    checker = EnhancedQualityChecker(
        api_key=api_key,
        base_url=base_url,
        model=model,
        system_prompt=system_prompt,
        parallel_core=2,
        activate_stream=False
    )
    
    try:
        # 执行文件质量检查
        output_path = test_file_path.replace('.json', '_quality_checked.json')
        report = await checker.check_qa_file_quality(
            test_file_path,
            output_path,
            quality_threshold=0.6
        )
        
        print("=== 质量检查报告 ===")
        print(f"文件路径: {report['file_path']}")
        print(f"总QA对数: {report['total_qa_pairs']}")
        print(f"通过数量: {report['passed_qa_pairs']}")
        print(f"通过率: {report['pass_rate']:.2%}")
        print(f"达到阈值: {'是' if report['meets_threshold'] else '否'}")
        
        if 'statistics' in report:
            stats = report['statistics']
            print(f"\n统计信息:")
            print(f"平均问题长度: {stats['avg_question_length']:.1f} 字符")
            print(f"平均答案长度: {stats['avg_answer_length']:.1f} 字符")
            
            print(f"问题类型分布:")
            for q_type, count in stats['question_types_distribution'].items():
                print(f"  - {q_type}: {count} 个")
        
        return True
        
    except Exception as e:
        print(f"文件质量检查测试失败: {e}")
        return False

def test_integrator():
    """测试集成器功能"""
    print("\n=== 测试集成器功能 ===\n")
    
    # 加载配置
    config_path = "/workspace/text_qa_generation/config.json"
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 初始化集成器
        integrator = TextQAQualityIntegrator(config)
        checker = integrator.initialize_checker()
        
        print("✓ 集成器初始化成功")
        print(f"✓ API URL: {checker.client.base_url}")
        print(f"✓ 模型: {checker.model}")
        print(f"✓ 并发核心数: {checker.parallel_core}")
        
        return True
        
    except Exception as e:
        print(f"集成器测试失败: {e}")
        return False

async def main():
    """主测试函数"""
    print("增强质量检查功能测试")
    print("=" * 50)
    
    # 测试结果
    test_results = []
    
    # 测试1: 集成器功能
    try:
        result1 = test_integrator()
        test_results.append(("集成器功能", result1))
    except Exception as e:
        print(f"集成器测试异常: {e}")
        test_results.append(("集成器功能", False))
    
    # 测试2: 核心质量检查功能
    try:
        result2 = await test_enhanced_quality_checker()
        test_results.append(("核心质量检查", result2))
    except Exception as e:
        print(f"核心质量检查测试异常: {e}")
        test_results.append(("核心质量检查", False))
    
    # 测试3: 文件质量检查功能
    try:
        result3 = await test_file_quality_check()
        test_results.append(("文件质量检查", result3))
    except Exception as e:
        print(f"文件质量检查测试异常: {e}")
        test_results.append(("文件质量检查", False))
    
    # 汇总结果
    print("\n" + "=" * 50)
    print("测试结果汇总")
    print("=" * 50)
    
    passed = 0
    for test_name, result in test_results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n总计: {passed}/{len(test_results)} 项测试通过")
    
    if passed == len(test_results):
        print("\n🎉 所有测试通过！增强质量检查功能正常工作。")
    else:
        print(f"\n⚠️  有 {len(test_results) - passed} 项测试失败，请检查配置和网络连接。")

if __name__ == "__main__":
    # 运行测试
    asyncio.run(main())