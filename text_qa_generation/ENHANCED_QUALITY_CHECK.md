# 增强质量检查功能

## 概述

增强质量检查功能基于 `checkInfor/checkQuestion.py` 的双阶段验证思路，为 `text_qa_generation` 系统提供了更加全面和准确的QA质量评估能力。

## 主要特性

### 1. 双阶段验证机制

**第一阶段：模型回答生成**
- 让模型独立回答原始问题
- 获取模型的自然回答作为参考

**第二阶段：答案正确性验证** 
- 比较模型回答与标准答案
- 基于专业判断标准评估答案质量
- 返回数字化质量标签（0/1）

### 2. 智能质量评估

- **多维度评估**：内容准确性、完整性、逻辑性
- **领域专业性**：针对半导体显示技术领域优化
- **详细反馈**：提供验证过程的详细信息

### 3. 批量处理能力

- **并发控制**：支持可配置的并发处理数量
- **异常处理**：robust的错误处理和恢复机制
- **进度跟踪**：实时显示处理进度

### 4. 多格式支持

- **输入格式**：JSON、CSV、Excel
- **输出格式**：详细结果、高质量数据、质量报告、CSV分析文件
- **数据结构**：兼容现有text_qa_generation格式

## 使用方法

### 1. 命令行使用

```bash
# 使用增强质量检查
python text_qa_generation.py \
    --file_path "data/output/results_343.json" \
    --output_file "data/output" \
    --check_task True \
    --enhanced_quality True \
    --quality_threshold 0.7 \
    --ark_url "http://0.0.0.0:8080/v1" \
    --api_key "your_api_key" \
    --model "/path/to/your/model"

# 使用传统质量检查
python text_qa_generation.py \
    --file_path "data/output/results_343.json" \
    --output_file "data/output" \
    --check_task True \
    --enhanced_quality False \
    --check_indexes "(40, 37, 38)" \
    --check_times 5
```

### 2. 流水线脚本使用

```bash
# 运行完整流水线
bash run_pipeline.sh

# 在质量检查阶段会询问：
# "Do you want to run quality check? (y/n)" - 选择 y
# "Use enhanced quality check? (y/n)" - 选择 y 使用增强版
```

### 3. Python API 使用

```python
import asyncio
from TextQA.enhanced_quality_checker import TextQAQualityIntegrator

# 加载配置
with open('config.json', 'r') as f:
    config = json.load(f)

# 初始化集成器
integrator = TextQAQualityIntegrator(config)

# 执行质量检查
report = await integrator.enhanced_quality_check(
    qa_file_path="data/output/results_343.json",
    output_dir="data/output",
    quality_threshold=0.7
)

print(f"通过率: {report['pass_rate']:.2%}")
```

## 配置说明

### config.json 配置项

```json
{
    "quality_control": {
        "enhanced_quality_check": {
            "enabled": true,
            "parallel_core": 10,
            "activate_stream": false,
            "quality_threshold": 0.7,
            "verification_method": "dual_stage"
        }
    }
}
```

**配置参数说明：**
- `enabled`: 是否启用增强质量检查
- `parallel_core`: 并发处理核心数
- `activate_stream`: 是否使用流式输出
- `quality_threshold`: 质量阈值（0-1之间）
- `verification_method`: 验证方法（目前支持"dual_stage"）

## 输出文件说明

增强质量检查会生成以下文件：

### 1. 详细结果文件 (`*_detailed.json`)
包含每个QA对的完整验证信息：
```json
{
    "question": "原始问题",
    "answer": "标准答案", 
    "quality_label": 1,
    "verification_details": {
        "model_answer": "模型回答",
        "verification_response": "验证响应",
        "question_length": 50,
        "answer_length": 200,
        "model_answer_length": 180
    }
}
```

### 2. 高质量数据文件 (`*_high_quality.json`)
仅包含通过质量检查的QA对，可直接用于训练或应用。

### 3. 质量报告文件 (`*_quality_report.json`)
包含整体质量统计：
```json
{
    "total_qa_pairs": 100,
    "passed_qa_pairs": 85,
    "pass_rate": 0.85,
    "quality_threshold": 0.7,
    "meets_threshold": true,
    "statistics": {
        "avg_question_length": 45.2,
        "avg_answer_length": 156.8,
        "question_types_distribution": {
            "factual": 25,
            "reasoning": 35,
            "comparison": 15,
            "open_ended": 10
        }
    }
}
```

### 4. CSV分析文件 (`*_results.csv`)
便于Excel或其他工具进行进一步分析的表格格式。

## 质量评估标准

### 事实型问题
- 答案必须准确无误
- 数值和参数必须正确
- 不能包含错误信息

### 分析型问题
- 逻辑清晰，要点完整
- 分析过程合理
- 结论有据可依

### 推理型问题
- 推理链条完整
- 因果关系正确
- 机理解释准确

### 开放型问题
- 方案可行性高
- 考虑因素全面
- 具有实际应用价值

## 性能优化

### 1. 并发控制
```python
# 根据系统性能调整并发数
config['quality_control']['enhanced_quality_check']['parallel_core'] = 5  # 较慢系统
config['quality_control']['enhanced_quality_check']['parallel_core'] = 20  # 高性能系统
```

### 2. 批处理大小
系统会自动根据并发核心数进行批处理，无需手动配置。

### 3. 内存管理
对于大型数据集，系统会分批加载和处理，避免内存溢出。

## 故障排除

### 1. API连接问题
```
错误：模型响应获取失败
解决：检查API URL、密钥和网络连接
```

### 2. 模型加载问题
```
错误：模型路径不存在
解决：确认模型路径正确，模型文件完整
```

### 3. 并发过多问题
```
错误：并发任务执行异常
解决：降低parallel_core数值
```

### 4. 内存不足问题
```
错误：内存溢出
解决：减少批处理大小或并发数
```

## 测试验证

运行测试脚本验证功能：

```bash
# 运行增强质量检查专项测试
python test_enhanced_quality.py

# 运行完整测试套件
python test_pipeline.py
```

## 与原有系统的对比

| 特性 | 原有简化版 | 增强版 |
|------|------------|--------|
| 验证方式 | 单阶段评分 | 双阶段验证 |
| 评估深度 | 基础数字评分 | 详细内容分析 |
| 错误处理 | 基本异常处理 | 全面异常恢复 |
| 输出格式 | CSV文件 | 多格式详细报告 |
| 并发控制 | 简单池化 | 智能批处理 |
| 统计分析 | 基础统计 | 全面质量分析 |
| 可扩展性 | 有限 | 高度可配置 |

## 最佳实践

### 1. 质量阈值设置
- **严格应用**：0.8-0.9（如训练数据）
- **一般应用**：0.6-0.7（如初步筛选）
- **宽松筛选**：0.4-0.5（如数据清洗）

### 2. 并发数配置
- **本地测试**：2-5个并发
- **服务器环境**：10-20个并发
- **高性能集群**：20+个并发

### 3. 数据预处理
- 确保输入数据格式正确
- 预先检查QA对的完整性
- 移除明显的重复或错误数据

### 4. 结果后处理
- 分析质量报告中的统计信息
- 根据问题类型分布调整生成策略
- 对低质量数据进行人工复查

这个增强质量检查系统显著提升了text_qa_generation的数据质量保证能力，为构建高质量QA数据集提供了强有力的工具支持。