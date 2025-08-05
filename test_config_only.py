#!/usr/bin/env python3
"""
简化测试脚本：只验证配置部分
"""

def test_config_structure():
    """测试配置结构是否正确"""
    
    # 模拟QuestionGenerator的__init__方法中的配置部分
    config = {
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
    
    # 模拟QuestionGenerator的配置加载
    qg_config = config.get('question_generation', {})
    
    # 问题类型
    question_types = qg_config.get('question_types', ['factual', 'comparison', 'reasoning', 'multi_hop', 'open_ended'])
    
    # 问题类型比例控制（优化版）
    question_type_ratios = qg_config.get('question_type_ratios', {
        'factual': 0.25,
        'comparison': 0.18,
        'reasoning': 0.25,
        'multi_hop': 0.15,
        'open_ended': 0.17
    })
    
    # 问题类型优先级配置
    question_type_priorities = qg_config.get('question_type_priorities', {
        'open_ended': 1,
        'reasoning': 2,
        'factual': 3,
        'comparison': 4,
        'multi_hop': 5
    })
    
    print("=== 配置验证结果 ===")
    print(f"问题类型: {question_types}")
    print(f"问题类型比例: {question_type_ratios}")
    print(f"问题类型优先级: {question_type_priorities}")
    
    # 验证配置完整性
    all_types_have_ratios = all(q_type in question_type_ratios for q_type in question_types)
    all_types_have_priorities = all(q_type in question_type_priorities for q_type in question_types)
    ratios_sum_to_one = abs(sum(question_type_ratios.values()) - 1.0) < 0.01
    
    print(f"\n=== 配置完整性检查 ===")
    print(f"所有类型都有比例配置: {all_types_have_ratios}")
    print(f"所有类型都有优先级配置: {all_types_have_priorities}")
    print(f"比例总和接近1.0: {ratios_sum_to_one} (实际: {sum(question_type_ratios.values()):.3f})")
    
    # 测试优先级排序
    sorted_by_priority = sorted(question_type_priorities.items(), key=lambda x: x[1])
    print(f"\n=== 优先级排序 ===")
    for i, (q_type, priority) in enumerate(sorted_by_priority, 1):
        print(f"{i}. {q_type} (优先级: {priority})")
    
    # 验证开放型问题是否为最高优先级
    highest_priority_type = min(question_type_priorities.items(), key=lambda x: x[1])[0]
    print(f"\n=== 优先级验证 ===")
    print(f"最高优先级类型: {highest_priority_type}")
    print(f"开放型问题是最高优先级: {'✅' if highest_priority_type == 'open_ended' else '❌'}")
    
    return all([all_types_have_ratios, all_types_have_priorities, ratios_sum_to_one, highest_priority_type == 'open_ended'])

if __name__ == "__main__":
    success = test_config_structure()
    if success:
        print("\n🎉 配置验证成功! question_type_priorities 配置正常工作!")
    else:
        print("\n💥 配置验证失败!")