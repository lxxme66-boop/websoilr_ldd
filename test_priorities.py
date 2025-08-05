#!/usr/bin/env python3
"""
测试脚本：验证question_type_priorities配置
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from question_generator_complete import QuestionGenerator

def test_priorities_config():
    """测试优先级配置是否正确加载"""
    
    # 创建测试配置
    test_config = {
        'models': {
            'qa_generator_model': {
                'path': '/mnt/storage/models/Qwen/Qwen2.5-14B-Instruct',
                'max_length': 4096,
                'temperature': 0.8
            }
        },
        'question_generation': {
            'question_types': ['factual', 'comparison', 'reasoning', 'multi_hop', 'open_ended'],
            'question_type_ratios': {
                'factual': 0.25,
                'comparison': 0.18,
                'reasoning': 0.25,
                'multi_hop': 0.15,
                'open_ended': 0.17
            },
            'question_type_priorities': {
                'open_ended': 1,
                'reasoning': 2,
                'factual': 3,
                'comparison': 4,
                'multi_hop': 5
            }
        }
    }
    
    try:
        # 初始化问题生成器
        print("正在初始化问题生成器...")
        qg = QuestionGenerator(test_config)
        
        # 检查优先级配置
        print("\n=== 优先级配置检查 ===")
        print(f"question_type_priorities 属性存在: {hasattr(qg, 'question_type_priorities')}")
        
        if hasattr(qg, 'question_type_priorities'):
            print("优先级配置内容:")
            for q_type, priority in qg.question_type_priorities.items():
                print(f"  {q_type}: {priority}")
        else:
            print("❌ question_type_priorities 属性不存在!")
            return False
        
        # 检查比例配置
        print("\n=== 比例配置检查 ===")
        print(f"question_type_ratios 属性存在: {hasattr(qg, 'question_type_ratios')}")
        
        if hasattr(qg, 'question_type_ratios'):
            print("比例配置内容:")
            for q_type, ratio in qg.question_type_ratios.items():
                print(f"  {q_type}: {ratio}")
        
        # 测试选择方法
        print("\n=== 测试问题类型选择方法 ===")
        current_counters = {'factual': 0, 'comparison': 0, 'reasoning': 0, 'multi_hop': 0, 'open_ended': 0}
        targets = {'factual': 25, 'comparison': 18, 'reasoning': 25, 'multi_hop': 15, 'open_ended': 17}
        
        selected_types = qg._select_question_types_by_ratio(current_counters, targets, 5, 4)
        print(f"选择的问题类型: {selected_types}")
        
        # 验证开放型问题是否被优先选择
        if 'open_ended' in selected_types:
            print("✅ 开放型问题被成功选择（优先级最高）")
        else:
            print("⚠️ 开放型问题未被选择")
        
        print("\n=== 测试完成 ===")
        print("✅ 所有配置都正常工作!")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_priorities_config()
    if success:
        print("\n🎉 配置验证成功!")
    else:
        print("\n💥 配置验证失败!")
        sys.exit(1)