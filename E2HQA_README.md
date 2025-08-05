# E2HQA Text-Only QA Generation System

## 概述

E2HQA (Easy-to-Hard Question Answering) 是一个基于文本的问答生成系统，实现了从简单QA到复杂QA的转换。该系统专门针对**纯文本场景**（非多模态），通过轨迹生成、拒绝采样和质量过滤机制，生成高质量的问答对和推理轨迹。

## 核心特性

### 1. E2HQA 生成方法
- **从简单到复杂**：基于SimpleQA类型的问答，构造复杂QA
- **双模型架构**：
  - Short CoT：使用GPT-4生成简洁推理链
  - Long CoT：使用LRMs（如QwQ-Plus）生成详细推理链
- **N次拒绝采样**：为每个QA生成多个候选轨迹，确保质量

### 2. 轨迹过滤系统
- **格式验证**：检查问题和答案的基本格式要求
- **答案正确性验证**：确保答案与问题相关且合理
- **质量评估**：多维度评估轨迹质量
  - 复杂度评分
  - 推理质量评分
  - 内容丰富度评分
  - 语言质量评分
  - 创新性评分

### 3. 多类型QA支持
- **事实型问题** (Simple Factual)
- **复杂推理问题** (Complex Reasoning)
- **多跳问题** (Multi-hop)
- **分析型问题** (Analytical)
- **开放型问题** (Open-ended)

## 系统架构

```
文本输入 → 简单QA生成 → 轨迹候选生成 → 质量过滤 → 最佳轨迹选择 → 输出
                ↓              ↓           ↓
            GPT-4生成      拒绝采样(N=5)   多维度评估
                         Short/Long CoT   格式/正确性/合理性检查
```

## 安装和配置

### 依赖包安装
```bash
pip install openai numpy asyncio dataclasses enum typing datetime hashlib
```

### 配置文件设置
```python
config = {
    'gpt4_config': {
        'api_key': 'your-gpt4-api-key',
        'base_url': 'https://api.openai.com/v1'
    },
    'lrm_config': {
        'api_key': 'your-lrm-api-key',
        'base_url': 'https://api.your-lrm-provider.com/v1'
    },
    'rejection_sampling_n': 5,
    'quality_threshold': 0.7,
    # ... 其他配置
}
```

## 使用方法

### 基础使用
```python
from e2hqa_text_generator import E2HQAGenerator, create_default_config

# 创建生成器
config = create_default_config()
generator = E2HQAGenerator(config)

# 生成QA轨迹
text = "你的文本内容..."
trajectories = await generator.generate_qa_from_text(text, num_questions=5)

# 保存结果
generator.save_trajectories(trajectories, 'output.json')
```

### 高级配置示例
```python
# 生产环境配置
production_config = {
    'rejection_sampling_n': 8,
    'quality_threshold': 0.8,
    'qa_type_ratios': {
        'simple_factual': 0.1,
        'complex_reasoning': 0.4,
        'multi_hop': 0.3,
        'analytical': 0.15,
        'open_ended': 0.05
    }
}
```

## 质量评估标准

### 1. 常识性检查
- ✅ **符合常识**：生成的问答内容应当符合基本常识和逻辑
- ✅ **无原理错误**：避免违背科学原理或基本事实的内容
- ✅ **逻辑通顺**：问题和答案之间逻辑关系清晰

### 2. 问题质量标准
- **相关性**：问题必须与输入文本高度相关
- **复杂性**：从简单问题演化为需要深度思考的复杂问题
- **多样性**：涵盖不同类型的问题（事实、推理、分析、开放等）

### 3. 答案质量标准
- **准确性**：答案内容准确，不包含错误信息
- **完整性**：答案完整回应问题，不遗漏关键信息
- **非冗余性**：避免重复和无关内容
- **非泛泛而谈**：提供具体、有针对性的回答

### 4. 推理轨迹质量
- **连贯性**：推理步骤逻辑连贯，前后呼应
- **合理性**：每个推理步骤都有合理依据
- **完整性**：推理链条完整，从前提到结论清晰可循

## 质量过滤机制

### 格式验证
```python
def _validate_format(self, trajectory):
    # 检查问题长度 (10-500字符)
    # 检查答案长度 (20-2000字符)
    # 检查推理步骤数量 (≥2步)
    return validation_result
```

### 答案正确性验证
```python
def _validate_answer_correctness(self, trajectory):
    # 关键词重叠度检查 (≥10%)
    # 问答相关性验证
    return validation_result
```

### 冗余检查
```python
def _check_redundancy(self, trajectory):
    # 重复词汇比例检查 (≤60%)
    # 内容重复度分析
    return is_redundant
```

### 目标对齐检查
```python
def _check_alignment(self, trajectory):
    # "如何"类问题 → 包含方法/步骤
    # "为什么"类问题 → 包含原因/解释
    # "什么"类问题 → 包含定义/描述
    return is_aligned
```

### 推理合理性检查
```python
def _check_reasoning_coherence(self, trajectory):
    # 逻辑连接词使用检查
    # 推理步骤内容充实度
    # 推理链条完整性
    return is_coherent
```

## 评分系统

### 五维度质量评估

1. **复杂度评分** (25%权重)
   - 问题复杂度：词汇数量和结构复杂性
   - 推理步骤数：3-5步(Short CoT)，8-15步(Long CoT)
   - 答案深度：内容丰富程度

2. **推理质量评分** (25%权重)
   - 逻辑连接词密度
   - 推理步骤平均长度
   - 推理链条完整性

3. **内容丰富度评分** (20%权重)
   - 词汇多样性
   - 专业术语使用
   - 信息密度

4. **语言质量评分** (15%权重)
   - 词汇重复度控制
   - 句子完整性
   - 表达清晰度

5. **创新性评分** (15%权重)
   - 创新性词汇使用
   - 开放性问题额外加分
   - 思维独特性

### 质量等级划分
- **优秀** (≥0.9)：高质量轨迹，推理深入，内容丰富
- **良好** (0.7-0.9)：质量良好，符合基本要求
- **一般** (0.5-0.7)：基本合格，存在改进空间
- **较差** (<0.5)：质量不达标，需要重新生成

## 输出格式

### QA轨迹结构
```json
{
  "trajectory_id": "unique_id_12chars",
  "question": "转换后的复杂问题",
  "answer": "详细答案内容",
  "reasoning_steps": [
    "推理步骤1：基于文本内容分析...",
    "推理步骤2：考虑到相关因素...",
    "推理步骤3：因此可以得出..."
  ],
  "qa_type": "complex_reasoning",
  "cot_type": "long_cot",
  "confidence_score": 0.85,
  "quality_metrics": {
    "overall_score": 0.82,
    "complexity": 0.78,
    "reasoning_quality": 0.85,
    "content_richness": 0.80,
    "language_quality": 0.88,
    "novelty": 0.75
  },
  "source_simple_qa": {
    "question": "原始简单问题",
    "answer": "原始简单答案"
  },
  "timestamp": "2024-01-01T12:00:00"
}
```

### 质量报告结构
```json
{
  "total_trajectories": 10,
  "quality_distribution": {
    "excellent": 2,
    "good": 5,
    "fair": 2,
    "poor": 1,
    "average_score": 0.75
  },
  "type_distribution": {
    "complex_reasoning": 4,
    "multi_hop": 3,
    "analytical": 2,
    "open_ended": 1
  },
  "cot_distribution": {
    "short_cot": 4,
    "long_cot": 6
  },
  "average_metrics": {
    "complexity": 0.72,
    "reasoning_quality": 0.78,
    "content_richness": 0.75,
    "language_quality": 0.82,
    "novelty": 0.68
  }
}
```

## 使用场景

### 1. 教育培训
- 生成多层次难度的练习题
- 创建推理训练材料
- 构建知识评估体系

### 2. 研究应用
- 学术文献问答生成
- 研究假设探索
- 创新思维训练

### 3. 内容创作
- 技术文档问答
- 知识库构建
- 互动学习材料

## 最佳实践

### 1. 文本预处理
- 确保输入文本结构清晰
- 去除无关信息和噪声
- 保持文本长度适中（500-2000字）

### 2. 配置优化
- 根据应用场景调整QA类型比例
- 设置合适的质量阈值
- 平衡Short CoT和Long CoT比例

### 3. 质量控制
- 定期检查生成质量
- 根据反馈调整过滤参数
- 建立人工审核机制

### 4. 性能优化
- 使用异步处理提高效率
- 实施批量处理减少API调用
- 缓存机制避免重复生成

## 注意事项

### 1. API配置
- 确保GPT-4和LRM API密钥有效
- 注意API调用频率限制
- 监控API使用成本

### 2. 质量保证
- 设置合理的质量阈值
- 启用所有过滤机制
- 定期评估输出质量

### 3. 资源管理
- 合理设置拒绝采样次数
- 控制并发请求数量
- 监控内存和存储使用

## 故障排除

### 常见问题

1. **API调用失败**
   - 检查API密钥和URL配置
   - 确认网络连接正常
   - 查看API使用限额

2. **质量分数偏低**
   - 降低质量阈值
   - 增加拒绝采样次数
   - 优化输入文本质量

3. **生成速度慢**
   - 减少拒绝采样次数
   - 使用批量处理
   - 优化并发设置

4. **内存占用过高**
   - 分批处理大量文本
   - 清理临时数据
   - 优化数据结构

## 扩展开发

### 自定义质量评估
```python
def custom_quality_scorer(self, trajectory):
    # 实现自定义评分逻辑
    custom_score = your_scoring_logic(trajectory)
    return custom_score
```

### 新增QA类型
```python
class CustomQAType(Enum):
    YOUR_TYPE = "your_custom_type"
    
# 在配置中添加新类型
qa_type_ratios['your_custom_type'] = 0.1
```

### 自定义过滤器
```python
def custom_filter(self, trajectory):
    # 实现自定义过滤逻辑
    return filter_result
```

## 许可证和贡献

本项目遵循MIT许可证。欢迎提交Issue和Pull Request来改进系统。

## 联系方式

如有问题或建议，请通过以下方式联系：
- 提交GitHub Issue
- 发送邮件至项目维护者
- 参与项目讨论区

---

**版本**: 1.0.0  
**更新日期**: 2024年1月  
**作者**: E2HQA开发团队