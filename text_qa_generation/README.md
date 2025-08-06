# 文本问答对生成系统

## 项目概述

本项目基于原多模态问答生成系统修改而来，专门用于处理纯文本数据，生成高质量的问答对。主要用于半导体和显示技术领域的知识问答数据集构建。

**最新更新**：集成了增强质量检查功能，采用双阶段验证机制，显著提升了QA数据质量评估能力。

## 主要特性

### 🚀 增强质量检查系统（新功能）
- **双阶段验证机制**：模型独立回答 + 答案正确性验证
- **智能质量评估**：多维度专业评估，针对半导体显示技术领域优化
- **批量并发处理**：支持可配置的并发数量和智能批处理
- **多格式输出**：详细报告、高质量数据、质量分析、CSV导出
- **完善的异常处理**：robust的错误恢复机制

### 📊 核心功能
- **纯文本处理**：专为文本文档优化的处理流程
- **异步批量架构**：高效的并发处理能力
- **智能问题生成**：支持4种问题类型，比例可配置
- **专业领域适配**：针对半导体和显示技术领域优化
- **全面的数据清洗**：确保输出数据的一致性和质量

## 主要修改内容

### 1. 核心模块修改

#### 1.1 文本召回模块（`text_main_batch_inference.py`）
- **原版**：`doubao_main_batch_inference.py` - 处理PDF文档，提取图片并进行文本召回
- **修改后**：
  - 移除所有图片处理相关代码
  - 直接读取txt文件内容
  - 保留异步批量处理架构
  - 移除`parse_pdf`函数，替换为`parse_txt`函数
  - 移除图片路径和页面范围处理

#### 1.2 数据清洗模块（`clean_text_data.py`）
- **原版**：`clean_data.py` - 清洗包含图片路径的数据
- **修改后**：
  - 移除图片路径处理逻辑
  - 保留JSON提取和格式化功能
  - 简化数据结构，只保留文本相关字段

#### 1.3 QA生成模块（`text_qa_generation.py`）
- **原版**：`qwen_argument.py` - 生成多模态问答对
- **修改后**：
  - 移除图片输入相关代码
  - 调整问题类型比例：
    - 事实型：15%（原25%）
    - 比较型：15%（原18%）
    - 推理型：50%（原25%）
    - 开放型：20%（原17%）
  - 移除多跳型问题（原15%）
  - **新增**：集成增强质量检查功能

#### 1.4 增强质量检查模块（`TextQA/enhanced_quality_checker.py`）**【新增】**
- **EnhancedQualityChecker**：核心质量检查引擎
- **TextQAQualityIntegrator**：与现有系统的集成适配器
- **双阶段验证流程**：
  1. 让模型独立回答原始问题
  2. 比较模型回答与标准答案，判断正确性
  3. 生成详细的验证报告和质量标签

#### 1.5 Prompt配置（`TextGeneration/prompts_conf.py`）
- **原版**：`Doubao/prompts_conf.py` - 包含图片分析的prompt
- **修改后**：
  - 移除所有图片相关的prompt
  - 新增针对文本分析的prompt模板
  - 调整系统prompt为半导体领域专家

### 2. 移除的功能

1. **图片处理功能**：
   - PDF解析和图片提取
   - 图片base64编码
   - 图片描述生成
   - 多模态输入处理

2. **PPT处理模块**：
   - `doubao_ppt_main.py`及相关功能

3. **预处理模块**：
   - `preprocessing.py` - PDF文件选择和页面范围生成

4. **WizardLM数据演化**：
   - 暂时移除，可后续根据需要添加

### 3. 保留并增强的功能

1. **异步批量处理架构** ✅
2. **数据清洗和格式化** ✅
3. **QA对生成核心逻辑** ✅
4. **数据质量检查** ✅ **（显著增强）**
5. **批量推理优化** ✅
6. **多格式输出支持** ✅ **（新增）**

## 🎯 增强质量检查功能详解

### 双阶段验证机制

**第一阶段：模型回答生成**
- 让模型独立回答原始问题
- 获取模型的自然回答作为参考

**第二阶段：答案正确性验证** 
- 比较模型回答与标准答案
- 基于专业判断标准评估答案质量
- 返回数字化质量标签（0/1）

### 质量评估标准

#### 专业领域适配
- **半导体技术**：IGZO、TFT相关问题的专业评估
- **显示技术**：OLED、LCD等显示技术问题
- **制造工艺**：工艺参数、制造流程相关问题

#### 多维度评估
1. **内容准确性**：技术事实、数值参数的准确性
2. **逻辑完整性**：推理链条、因果关系的合理性
3. **专业深度**：技术解释的专业程度和深度
4. **实用价值**：解决方案的可行性和实用性

### 输出文件说明

增强质量检查会生成以下文件：

1. **详细结果文件** (`*_detailed.json`)：包含每个QA对的完整验证信息
2. **高质量数据文件** (`*_high_quality.json`)：仅包含通过质量检查的QA对
3. **质量报告文件** (`*_quality_report.json`)：包含整体质量统计和分析
4. **CSV分析文件** (`*_results.csv`)：便于Excel分析的表格格式

## 运行流程

### 1. 环境准备

```bash
# 安装依赖
pip install -r requirements.txt

# 设置API密钥（如需要）
export ARK_API_KEY="your-api-key"
```

### 2. 准备数据

将txt文件放入指定目录，每个txt文件应包含相关的技术文档内容。

```
data/
├── input_texts/
│   ├── doc1.txt
│   ├── doc2.txt
│   └── ...
```

### 3. 运行流程

#### 方式一：使用流水线脚本（推荐）

```bash
# 运行完整流程
bash run_pipeline.sh

# 在质量检查阶段会询问：
# "Do you want to run quality check? (y/n)" - 选择 y
# "Use enhanced quality check? (y/n)" - 选择 y 使用增强版
```

#### 方式二：分步运行

```bash
# 步骤1：文本召回和初步处理
python text_main_batch_inference.py \
    --txt_path data/input_texts \
    --storage_folder data/output \
    --index 43 \
    --parallel_batch_size 50 \
    --selected_task_number 1000

# 步骤2：数据清洗
python clean_text_data.py \
    --input_file data/output/total_response.pkl \
    --output_file data/output

# 步骤3：QA生成
python text_qa_generation.py \
    --file_path data/output/total_response.json \
    --index 343 \
    --pool_size 100 \
    --output_file data/output

# 步骤4：增强质量检查（可选）
python text_qa_generation.py \
    --file_path data/output/results_343.json \
    --output_file data/output \
    --check_task True \
    --enhanced_quality True \
    --quality_threshold 0.7
```

## 配置说明

### 主要配置文件：`config.json`

```json
{
    "models": {
        "qa_generator_model": {
            "path": "/path/to/model",
            "max_length": 4096,
            "temperature": 0.8
        }
    },
    "question_generation": {
        "question_types": ["factual", "comparison", "reasoning", "open_ended"],
        "question_type_ratios": {
            "factual": 0.15,
            "comparison": 0.15,
            "reasoning": 0.50,
            "open_ended": 0.20
        }
    },
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

### 增强质量检查配置参数

- `enabled`: 是否启用增强质量检查
- `parallel_core`: 并发处理核心数（建议：本地2-5，服务器10-20）
- `activate_stream`: 是否使用流式输出
- `quality_threshold`: 质量阈值（0-1之间，建议0.6-0.8）
- `verification_method`: 验证方法（目前支持"dual_stage"）

## 输出格式

### 基础QA对格式

```json
{
    "question": "问题内容",
    "answer": "答案内容",
    "question_type": "推理型",
    "reasoning": "推理过程",
    "context": "相关上下文",
    "source_file": "源文件名"
}
```

### 增强质量检查后的格式

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

## 问题类型分布

- **事实型（15%）**：获取指标、数值、性能参数等
  - 示例：JDI开发IGO材料的迁移率、PBTS等参数？制备工艺？

- **比较型（15%）**：比较不同材料、结构或方案等
  - 示例：顶栅结构的IGZO的寄生电容为什么相对于底栅结构的寄生电容要低？

- **推理型（50%）**：机制原理解释，探究某种行为或结果的原因
  - 示例：在IGZO TFT中，环境气氛中的氧气是如何影响TFT的阈值电压的？

- **开放型（20%）**：优化建议，针对问题提出改进方法
  - 示例：怎么实现短沟道的顶栅氧化物TFT器件且同时避免器件失效？

## 质量检查对比

| 特性 | 原有简化版 | 新增强版 |
|------|------------|----------|
| **验证机制** | 单阶段评分 | 双阶段验证 |
| **评估深度** | 基础数字评分 | 详细内容分析 |
| **质量标准** | 简单阈值判断 | 多维度专业评估 |
| **并发处理** | 基本池化 | 智能批处理+异常恢复 |
| **输出格式** | 单一CSV | 多格式详细报告 |
| **错误处理** | 基本异常处理 | 全面异常恢复机制 |
| **统计分析** | 基础计数 | 全面质量分析报告 |
| **可配置性** | 有限参数 | 高度可配置 |

## 实现状态

### 已实现 ✅
- ✅ 文本批量处理
- ✅ 异步并发架构
- ✅ 数据清洗和格式化
- ✅ QA对生成
- ✅ 问题类型比例控制
- ✅ **增强质量检查系统**
- ✅ **双阶段验证机制**
- ✅ **多格式输出支持**
- ✅ **详细质量报告**

### 未实现/简化 ⚠️
- ❌ 图片处理（已移除）
- ❌ PDF解析（已移除）
- ❌ 多模态输入（已移除）
- ⚠️ 数据演化（WizardLM）- 暂时移除
- ⚠️ MPO数据标注 - 暂时移除

## 快速开始

### 1. 测试系统

首先运行测试脚本确保所有模块正常工作：

```bash
# 运行完整测试套件
python test_pipeline.py

# 专门测试增强质量检查功能
python test_enhanced_quality.py
```

### 2. 准备文本数据

将您的技术文档（.txt格式）放入 `data/input_texts/` 目录。系统已包含一个示例文件 `sample_igzo_tft.txt`。

### 3. 运行完整流程

```bash
# 使用默认参数运行
bash run_pipeline.sh

# 或自定义参数
BATCH_SIZE=100 POOL_SIZE=200 bash run_pipeline.sh
```

### 4. 查看结果

生成的问答对将保存在 `data/output/` 目录：
- `results_343.json` - 生成的问答对
- `results_343_stats.json` - 统计信息
- `results_343_detailed.json` - 详细质量检查结果（如果运行了增强质量检查）
- `results_343_high_quality.json` - 高质量数据（如果运行了增强质量检查）
- `results_343_quality_report.json` - 质量分析报告（如果运行了增强质量检查）
- `results_343_results.csv` - CSV格式分析数据（如果运行了增强质量检查）

## 使用示例

### 命令行使用

```bash
# 增强质量检查
python text_qa_generation.py \
    --check_task True \
    --enhanced_quality True \
    --quality_threshold 0.7 \
    --file_path "data/output/results_343.json" \
    --output_file "data/output"

# 传统质量检查（保持兼容）
python text_qa_generation.py \
    --check_task True \
    --enhanced_quality False \
    --check_indexes "(40, 37, 38)"
```

### Python API使用

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

## 示例输出

### 事实型问题示例
```json
{
    "question": "IGZO薄膜的典型电子迁移率范围是多少？",
    "answer": "IGZO薄膜的典型电子迁移率为10-20 cm²/V·s，远高于非晶硅（a-Si:H）的0.5-1 cm²/V·s。",
    "question_type": "factual",
    "context": "IGZO材料特性章节"
}
```

### 推理型问题示例
```json
{
    "question": "为什么SiNx钝化层会导致IGZO薄膜电阻率降低？",
    "answer": "SiNx钝化层在沉积过程中会释放氢原子，这些氢原子扩散到IGZO薄膜中形成施主态，增加了自由载流子浓度，从而导致IGZO薄膜的电阻率降低。这种效应可使电阻率降低1-2个数量级。",
    "question_type": "reasoning",
    "reasoning": "氢原子作为施主提供额外的自由电子，增加了载流子浓度，根据电导率与载流子浓度的正比关系，电阻率相应降低。"
}
```

### 质量报告示例
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

## 性能优化建议

### 1. 并发数配置
- **本地测试**：2-5个并发
- **服务器环境**：10-20个并发
- **高性能集群**：20+个并发

### 2. 质量阈值设置
- **严格应用**：0.8-0.9（如训练数据）
- **一般应用**：0.6-0.7（如初步筛选）
- **宽松筛选**：0.4-0.5（如数据清洗）

### 3. 批处理优化
- 根据系统内存调整batch_size
- 大文件分批处理避免内存溢出
- 合理设置API调用间隔

## 故障排除

### 常见问题

1. **API连接失败**
   - 检查API密钥是否正确
   - 确认网络连接正常
   - 验证API服务地址

2. **内存不足**
   - 减小`batch_size`参数
   - 降低`parallel_core`数值
   - 分批处理大文件

3. **质量检查失败**
   - 检查模型路径是否正确
   - 确认输入数据格式正确
   - 查看详细错误日志

4. **生成质量问题**
   - 调整temperature参数
   - 优化prompt模板
   - 提高质量阈值

## 注意事项

1. 确保输入的txt文件编码为UTF-8
2. 每个txt文件应包含完整的技术文档内容
3. API调用有速率限制，建议适当调整`parallel_batch_size`
4. 生成的问答对建议进行人工审核，特别是开放型问题
5. 增强质量检查需要较多计算资源，建议在服务器环境运行

## 项目结构

```
text_qa_generation/
├── README.md                          # 项目说明文档
├── ENHANCED_QUALITY_CHECK.md          # 增强质量检查详细说明
├── INTEGRATION_SUMMARY.md             # 集成总结文档
├── requirements.txt                   # Python依赖
├── config.json                       # 配置文件
├── run_pipeline.sh                   # 运行脚本
├── test_pipeline.py                  # 完整测试脚本
├── test_enhanced_quality.py          # 增强质量检查专项测试
├── text_main_batch_inference.py      # 文本处理主程序
├── clean_text_data.py                # 数据清洗
├── text_qa_generation.py             # QA生成主程序
├── TextGeneration/                   # 文本生成模块
│   ├── __init__.py
│   ├── Datageneration.py
│   └── prompts_conf.py
├── TextQA/                          # QA生成模块
│   ├── __init__.py
│   ├── dataargument.py
│   └── enhanced_quality_checker.py   # 增强质量检查器
└── data/                            # 数据目录
    ├── input_texts/                 # 输入文本
    │   └── sample_igzo_tft.txt
    └── output/                      # 输出结果
```

## 后续优化建议

1. **增强质量检查**：
   - 添加更多领域特定的评估标准
   - 实现自适应质量阈值调整
   - 增加问题难度评估功能

2. **系统功能**：
   - 添加更多领域的prompt模板
   - 实现数据演化功能以增加多样性
   - 添加人工审核和反馈机制

3. **性能优化**：
   - 实现增量处理支持
   - 添加缓存机制减少重复计算
   - 优化内存使用和并发控制

## 更新日志

### v2.0.0 - 增强质量检查版本
- ✨ 新增增强质量检查系统
- ✨ 实现双阶段验证机制
- ✨ 添加多格式输出支持
- ✨ 增加详细质量报告功能
- 🔧 完善配置系统
- 🔧 优化运行脚本
- 📚 更新文档和测试

### v1.0.0 - 基础版本
- 🎉 初始版本发布
- ✨ 纯文本QA生成功能
- ✨ 异步批量处理
- ✨ 基础质量检查

## 贡献指南

欢迎提交Issue和Pull Request来改进本项目。主要改进方向：
- 增加更多领域的prompt模板
- 优化问题生成算法
- 提升数据质量检查机制
- 添加更多的后处理功能
- 完善测试覆盖率

## 许可证

本项目基于原多模态问答生成系统修改，遵循原项目的许可证要求。