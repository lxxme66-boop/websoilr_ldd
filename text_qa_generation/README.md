# 文本问答对生成系统

## 项目概述

本项目基于原多模态问答生成系统修改而来，专门用于处理纯文本数据，生成高质量的问答对。主要用于半导体和显示技术领域的知识问答数据集构建。

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

#### 1.4 Prompt配置（`TextGeneration/prompts_conf.py`）
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

### 3. 保留的功能

1. **异步批量处理架构**
2. **数据清洗和格式化**
3. **QA对生成核心逻辑**
4. **数据质量检查**（简化版）
5. **批量推理优化**

## 运行流程

### 1. 环境准备

```bash
# 安装依赖
pip install -r requirements.txt

# 设置API密钥
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

使用提供的bash脚本运行完整流程：

```bash
bash run_pipeline.sh
```

或分步运行：

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
```

## 输出格式

生成的问答对格式：

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

## 问题类型分布

- **事实型（15%）**：获取指标、数值、性能参数等
  - 示例：JDI开发IGO材料的迁移率、PBTS等参数？制备工艺？

- **比较型（15%）**：比较不同材料、结构或方案等
  - 示例：顶栅结构的IGZO的寄生电容为什么相对于底栅结构的寄生电容要低？

- **推理型（50%）**：机制原理解释，探究某种行为或结果的原因
  - 示例：在IGZO TFT中，环境气氛中的氧气是如何影响TFT的阈值电压的？

- **开放型（20%）**：优化建议，针对问题提出改进方法
  - 示例：怎么实现短沟道的顶栅氧化物TFT器件且同时避免器件失效？

## 实现状态

### 已实现
- ✅ 文本批量处理
- ✅ 异步并发架构
- ✅ 数据清洗和格式化
- ✅ QA对生成
- ✅ 问题类型比例控制
- ✅ 基础质量检查

### 未实现/简化
- ❌ 图片处理（已移除）
- ❌ PDF解析（已移除）
- ❌ 多模态输入（已移除）
- ⚠️ 数据演化（WizardLM）- 暂时移除
- ⚠️ 高级质量检查 - 简化版本
- ⚠️ MPO数据标注 - 暂时移除

## 配置说明

主要配置文件：`config.json`

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
    }
}
```

## 注意事项

1. 确保输入的txt文件编码为UTF-8
2. 每个txt文件应包含完整的技术文档内容
3. API调用有速率限制，建议适当调整`parallel_batch_size`
4. 生成的问答对需要人工审核，特别是开放型问题

## 后续优化建议

1. 添加更多领域特定的prompt模板
2. 实现数据演化功能以增加多样性
3. 加强质量检查机制
4. 添加人工审核和反馈机制

## 快速开始

### 1. 测试系统

首先运行测试脚本确保所有模块正常工作：

```bash
python test_pipeline.py
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
- `results_343_filtered.csv` - 质量检查后的数据（如果运行了质量检查）

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

## 故障排除

### 常见问题

1. **API连接失败**
   - 检查API密钥是否正确
   - 确认网络连接正常
   - 验证API服务地址

2. **内存不足**
   - 减小`batch_size`参数
   - 分批处理大文件
   - 增加系统内存

3. **生成质量问题**
   - 调整temperature参数
   - 优化prompt模板
   - 增加质量检查轮次

## 项目结构

```
text_qa_generation/
├── README.md                          # 项目说明文档
├── requirements.txt                   # Python依赖
├── config.json                       # 配置文件
├── run_pipeline.sh                   # 运行脚本
├── test_pipeline.py                  # 测试脚本
├── text_main_batch_inference.py      # 文本处理主程序
├── clean_text_data.py                # 数据清洗
├── text_qa_generation.py             # QA生成
├── TextGeneration/                   # 文本生成模块
│   ├── __init__.py
│   ├── Datageneration.py
│   └── prompts_conf.py
├── TextQA/                          # QA生成模块
│   ├── __init__.py
│   └── dataargument.py
└── data/                            # 数据目录
    ├── input_texts/                 # 输入文本
    │   └── sample_igzo_tft.txt
    └── output/                      # 输出结果
```

## 贡献指南

欢迎提交Issue和Pull Request来改进本项目。主要改进方向：
- 增加更多领域的prompt模板
- 优化问题生成算法
- 提升数据质量检查机制
- 添加更多的后处理功能

## 许可证

本项目基于原多模态问答生成系统修改，遵循原项目的许可证要求。