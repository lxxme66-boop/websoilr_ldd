# 智能文本QA生成系统 - 整合版

一个功能完整的智能文本问答生成系统，整合了文本召回、数据处理、QA生成、质量控制、多模态处理、本地模型支持和数据改写增强功能，专注于半导体、光学等专业领域。

## 🌟 核心特性

### 📊 完整数据流水线
- **文本召回**：从PDF文档中智能提取和召回相关文本内容
- **数据清理**：使用正则表达式和AI技术进行数据后处理
- **QA生成**：基于专业领域知识生成高质量问答对
- **质量控制**：多维度质量检查和自动改进
- **数据改写增强**：智能改写提升内容质量和多样性
- **最终整理**：生成完整的报告和统计信息

### 🔬 专业领域支持
- **半导体物理**：IGZO、TFT、OLED、能带理论等
- **光学与光电子**：光谱分析、器件特性、光子吸收等
- **材料科学**：材料特性、制备工艺等
- **36+专业Prompt模板**：覆盖各种专业场景
- **领域特定质量检查**：针对不同领域的专业准确性验证

### 🤖 多模型支持
- **云端API模型**：豆包、Qwen、GPT等OpenAI兼容接口
- **本地模型支持**：
  - Ollama集成（llama2, codellama, mistral, qwen等）
  - vLLM高性能推理服务
  - Transformers本地加载
- **智能模型切换**：根据任务自动选择最佳模型
- **混合部署**：支持云端和本地模型混合使用

### 📚 多模态处理
- **PDF文档处理**：自动提取文本和图像，支持复杂学术论文
- **图文结合问答**：基于图片和文本内容生成高质量问答对
- **专业图表分析**：支持半导体、光学等专业领域的图表分析
- **多格式支持**：PNG、JPG、JPEG、WebP等图像格式

### 🚀 高性能处理
- **异步批处理**：支持大规模并发处理
- **多进程架构**：充分利用多核CPU资源
- **内存优化**：智能内存管理和缓存机制
- **自适应调度**：根据系统负载动态调整处理策略

### 🔍 增强质量控制
- **多维度检查**：推理有效性、问题清晰度、答案正确性、图片依赖性
- **双阶段验证**：初步筛选 + 深度质量检查
- **自动改进**：基于质量反馈自动优化生成结果
- **质量报告**：详细的质量分析和统计报告

### ✨ 数据改写增强
- **智能改写**：保持核心内容不变，提升表达质量
- **多样化生成**：生成不同风格的问答对
- **质量提升**：自动优化问题和答案的专业性
- **批量处理**：高效处理大规模数据改写

## 📦 项目结构

```
new_text/
├── README.md                           # 项目说明文档
├── requirements.txt                    # 完整依赖包列表
├── config.json                         # 统一配置文件
├── run_pipeline.py                     # 统一流水线脚本
├── text_qa_generation.py               # 主要QA生成脚本
├── text_qa_generation_enhanced.py      # 增强版QA生成脚本
├── text_main_batch_inference.py        # 批量推理脚本
├── text_main_batch_inference_enhanced.py # 增强批量推理脚本
├── clean_text_data.py                  # 数据清理脚本
├── clean_data.py                       # 基础数据清理
├── argument_data.py                    # 数据参数处理
├── batch_inference.py                  # 批量推理工具
│
├── TextQA/                            # QA处理核心模块
│   ├── dataargument.py                # 数据处理和QA生成
│   └── enhanced_quality_checker.py     # 增强质量检查
│
├── TextGeneration/                    # 文本生成模块
│   ├── Datageneration.py             # 数据生成逻辑
│   └── prompts_conf.py                # 36+专业Prompt配置
│
├── LocalModels/                       # 本地模型支持
│   └── ollama_client.py               # Ollama客户端
│
├── MultiModal/                        # 多模态处理
│   └── pdf_processor.py              # PDF处理器
│
├── model_rewrite/                     # 数据改写增强模块
│   ├── data_generation.py            # 数据生成和改写
│   ├── data_label.py                 # 数据标注和质量检查
│   └── rewrite_templates.py          # 改写模板
│
├── Doubao/                           # 豆包模型集成
├── Qwen/                             # Qwen模型集成  
├── WizardLM/                         # WizardLM模型集成
├── Utilis/                           # 工具函数
│
├── data/                             # 数据目录
│   ├── input/                        # 输入数据
│   ├── output/                       # 输出数据
│   ├── pdfs/                         # PDF文件
│   ├── retrieved/                    # 召回数据
│   ├── cleaned/                      # 清理数据
│   ├── qa_results/                   # QA结果
│   ├── quality_checked/              # 质量检查结果
│   ├── rewritten/                    # 改写结果
│   └── final_output/                 # 最终输出
│
├── temp/                             # 临时文件
├── logs/                             # 日志文件
└── __init__.py                       # Python包初始化
```

## 🚀 快速开始

### 1. 环境安装

```bash
# 克隆项目
git clone <repository-url>
cd new_text

# 安装基础依赖
pip install -r requirements.txt

# 可选：安装多模态支持
pip install PyMuPDF Pillow opencv-python

# 可选：安装本地模型支持
pip install ollama transformers torch torchvision
```

### 2. 配置设置

```bash
# 编辑配置文件，设置API密钥和模型路径
nano config.json
```

**重要配置项**：
```json
{
  "api": {
    "ark_url": "http://your-api-endpoint/v1",
    "api_key": "your-api-key-here"
  },
  "models": {
    "qa_generator_model": {
      "path": "/path/to/your/model"
    }
  },
  "professional_domains": {
    "default_domain": "semiconductor"
  }
}
```

### 3. 一键运行

#### 完整流水线处理
```bash
# 处理PDF文件夹，生成半导体领域QA
python run_pipeline.py \
    --mode full_pipeline \
    --input_path data/pdfs/semiconductor_papers \
    --domain semiconductor

# 处理光学领域文档
python run_pipeline.py \
    --mode full_pipeline \
    --input_path data/pdfs/optics_papers \
    --domain optics \
    --quality_threshold 0.8
```

#### 使用本地模型
```bash
# 启动Ollama服务
ollama serve

# 使用本地模型运行
python run_pipeline.py \
    --mode full_pipeline \
    --input_path data/pdfs \
    --domain semiconductor \
    --use_local_models \
    --enable_multimodal
```

#### 数据改写增强
```bash
# 对现有QA数据进行改写增强
python model_rewrite/data_generation.py \
    --data-path data/qa_results/results_343.json \
    --output-path data/rewritten/enhanced_qa.json \
    --template-type professional
```

### 4. 分步骤运行

**步骤1：文本召回**
```bash
python run_pipeline.py \
    --mode text_retrieval \
    --input_path data/pdfs \
    --domain semiconductor
```

**步骤2：数据清理**
```bash
python run_pipeline.py \
    --mode data_cleaning \
    --input_path data/retrieved/total_response.pkl
```

**步骤3：QA生成**
```bash
python run_pipeline.py \
    --mode qa_generation \
    --input_path data/cleaned/total_response.json \
    --domain semiconductor
```

**步骤4：质量控制**
```bash
python run_pipeline.py \
    --mode quality_control \
    --input_path data/qa_results/results_343.json \
    --quality_threshold 0.7
```

**步骤5：数据改写增强**
```bash
python run_pipeline.py \
    --mode data_rewriting \
    --input_path data/quality_checked/final_qa.json \
    --rewrite_ratio 0.3
```

## ⚙️ 配置说明

### 基础配置
```json
{
  "system_info": {
    "name": "智能文本QA生成系统 - 整合版",
    "version": "3.0.0",
    "features": [
      "文本召回与检索",
      "多模态PDF处理", 
      "智能QA生成",
      "增强质量控制",
      "本地模型支持",
      "专业领域定制",
      "数据改写增强"
    ]
  }
}
```

### 模型配置
```json
{
  "models": {
    "local_models": {
      "ollama": {
        "enabled": true,
        "base_url": "http://localhost:11434",
        "model_name": "qwen:7b"
      },
      "vllm": {
        "enabled": false,
        "base_url": "http://localhost:8000",
        "model_name": "Qwen/Qwen2-7B-Instruct"
      }
    }
  }
}
```

### 专业领域配置
```json
{
  "professional_domains": {
    "semiconductor": {
      "keywords": ["IGZO", "TFT", "OLED", "半导体"],
      "quality_criteria": "high",
      "specific_checks": ["technical_accuracy", "formula_validity"]
    },
    "optics": {
      "keywords": ["光谱", "光学", "激光", "折射"],
      "quality_criteria": "high",
      "specific_checks": ["wavelength_accuracy", "optical_principles"]
    }
  }
}
```

### 数据改写配置
```json
{
  "rewriting": {
    "enabled": true,
    "rewrite_ratio": 0.3,
    "quality_improvement": true,
    "professional_enhancement": true,
    "template_types": ["basic", "advanced", "professional"]
  }
}
```

## 📖 详细使用指南

### 多模态处理
系统支持从PDF文档中提取文本和图像，并基于图文内容生成问答对：

```bash
# 启用多模态处理
python run_pipeline.py \
    --mode full_pipeline \
    --input_path data/pdfs/research_papers \
    --enable_multimodal \
    --domain semiconductor
```

**多模态输出示例**：
```json
{
  "question": "根据图中的I-V特性曲线，判断该器件的类型",
  "answer": "根据曲线的非线性特征和阈值电压，这是一个场效应晶体管",
  "choices": ["二极管", "三极管", "场效应管", "电阻"],
  "reasoning": "从I-V曲线可以看出明显的阈值电压特征...",
  "image_path": "./data/images/iv_curve.png",
  "context": "该图显示了半导体器件的电流-电压特性..."
}
```

### 本地模型使用

#### Ollama集成
```bash
# 1. 安装并启动Ollama
curl -fsSL https://ollama.ai/install.sh | sh
ollama serve

# 2. 下载模型
ollama pull qwen:7b
ollama pull llama2

# 3. 配置使用本地模型
python run_pipeline.py \
    --use_local_models \
    --input_path data/pdfs \
    --domain semiconductor
```

#### 模型选择优先级
系统支持智能模型选择，优先级顺序：
1. Ollama（如果启用且可用）
2. vLLM（如果启用且可用）
3. Transformers（如果启用且可用）
4. 云端API（默认备选）

### 质量控制系统

#### 增强质量检查
```bash
# 启用增强质量检查
python run_pipeline.py \
    --mode quality_control \
    --input_path data/qa_results/results_343.json \
    --quality_threshold 0.8
```

**质量检查维度**：
- **推理有效性**：检查推理逻辑是否合理
- **问题清晰度**：评估问题表述是否清晰
- **答案正确性**：验证答案的准确性
- **图片依赖性**：检查是否正确依赖图片内容
- **领域相关性**：验证内容是否符合专业领域要求

### 数据改写增强

#### 基础改写
```bash
# 基础改写增强
python model_rewrite/data_generation.py \
    --data-path data/qa_results/original.json \
    --output-path data/rewritten/enhanced.json \
    --template-type basic
```

#### 专业增强
```bash
# 专业领域增强
python model_rewrite/data_generation.py \
    --data-path data/qa_results/original.json \
    --output-path data/rewritten/professional.json \
    --template-type professional \
    --domain semiconductor
```

#### 质量标注
```bash
# 质量标注和评估
python model_rewrite/data_label.py \
    --data-path data/rewritten/enhanced.json \
    --output-path data/quality_checked/labeled.json
```

## 📊 输出格式

### 召回阶段输出
```json
{
  "content": "模型返回的原始内容...",
  "image_path": "/path/to/image.png",
  "metadata": {
    "page": 1,
    "confidence": 0.95,
    "processing_time": 2.3
  }
}
```

### 清理后输出
```json
{
  "imageDescription": "图片描述内容...",
  "analysisResults": "分析结果...",
  "relatedKnowledge": "相关知识...",
  "image_path": "./data/images/sample.png",
  "cleaned_at": "2024-12-20T10:30:00"
}
```

### 最终QA输出
```json
{
  "metadata": {
    "system_name": "智能文本QA生成系统 - 整合版",
    "version": "3.0.0",
    "domain": "semiconductor",
    "generation_time": "20241220_103000",
    "total_qa_pairs": 150,
    "quality_pass_rate": 0.85,
    "rewrite_enhanced": true
  },
  "qa_pairs": [
    {
      "question": "什么是IGZO材料的主要优势？",
      "answer": "IGZO材料具有高迁移率、低功耗和良好的均匀性...",
      "choices": ["选项A", "选项B", "选项C", "选项D"],
      "reasoning": "基于IGZO材料的物理特性分析...",
      "context": "IGZO是铟镓锌氧化物的缩写...",
      "quality_score": 0.85,
      "domain": "semiconductor",
      "source_file": "igzo_research.pdf",
      "question_type": "factual",
      "difficulty": "intermediate",
      "is_rewritten": false,
      "original_version": null
    }
  ],
  "pipeline_stats": {
    "total_duration": 1200.5,
    "stages_completed": [
      "text_retrieval", 
      "data_cleaning", 
      "qa_generation", 
      "quality_control", 
      "data_rewriting",
      "final_processing"
    ]
  }
}
```

### 改写增强输出
```json
{
  "original_qa": {
    "question": "什么是IGZO？",
    "answer": "IGZO是一种材料"
  },
  "rewritten_qa": {
    "question": "请解释IGZO材料的基本概念及其在显示技术中的重要性",
    "answer": "IGZO（铟镓锌氧化物）是一种新型的氧化物半导体材料，具有高载流子迁移率、良好的均匀性和透明性等特点..."
  },
  "rewrite_metadata": {
    "template_type": "professional",
    "improvement_score": 0.92,
    "rewrite_time": "2024-12-20T10:35:00"
  }
}
```

## 🔧 高级功能

### 1. 批量处理脚本

创建自定义批量处理脚本：
```bash
#!/bin/bash
# batch_process_domains.sh

DOMAINS=("semiconductor" "optics" "materials")
INPUT_BASE="data/pdfs"

for domain in "${DOMAINS[@]}"; do
    echo "Processing domain: $domain"
    python run_pipeline.py \
        --mode full_pipeline \
        --input_path "$INPUT_BASE/$domain" \
        --domain "$domain" \
        --quality_threshold 0.7 \
        --batch_size 50 \
        --enable_rewriting
done
```

### 2. 自定义Prompt开发

在 `TextGeneration/prompts_conf.py` 中添加自定义prompt：
```python
# 添加新的专业领域prompt
user_prompts[999] = """
你是一个{domain}领域的专家，请基于以下内容生成高质量的问答对：

内容：{content}

要求：
1. 生成3-5个不同难度的问题
2. 每个问题都要有详细的推理过程
3. 确保答案准确且专业
4. 如果有图片，要充分利用图片信息

请按照以下JSON格式输出：
{{
  "qa_pairs": [
    {{
      "question": "问题内容",
      "answer": "答案内容", 
      "reasoning": "推理过程",
      "difficulty": "easy/medium/hard",
      "question_type": "factual/reasoning/application"
    }}
  ]
}}
"""
```

### 3. 自定义改写模板

在 `model_rewrite/rewrite_templates.py` 中添加新模板：
```python
# 专业领域改写模板
PROFESSIONAL_TEMPLATES = {
    "semiconductor": {
        "question_enhancement": """
        请将以下问题改写为更专业的半导体领域问题：
        原问题：{original_question}
        
        要求：
        1. 使用专业术语
        2. 增加技术深度
        3. 保持原意不变
        """,
        "answer_enhancement": """
        请将以下答案改写为更专业详细的回答：
        原答案：{original_answer}
        
        要求：
        1. 增加技术细节
        2. 使用准确的专业术语
        3. 提供更深入的解释
        """
    }
}
```

## 🛠️ 故障排除

### 常见问题

#### 1. 本地模型连接失败
```bash
# 检查Ollama服务状态
ollama list

# 重启Ollama服务
pkill ollama
ollama serve

# 检查模型是否已下载
ollama pull qwen:7b
```

#### 2. 内存不足
```bash
# 减少批处理大小
python run_pipeline.py --batch_size 20

# 启用内存优化
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512
```

#### 3. API调用失败
```bash
# 检查网络连接
curl -I http://your-api-endpoint/v1

# 验证API密钥
python -c "
import json
with open('config.json') as f:
    config = json.load(f)
print('API Key:', config['api']['api_key'][:10] + '...')
"
```

#### 4. 多模态处理错误
```bash
# 检查图像处理依赖
pip install PyMuPDF Pillow opencv-python

# 检查PDF文件完整性
python -c "
import fitz
doc = fitz.open('your_file.pdf')
print(f'Pages: {len(doc)}')
doc.close()
"
```

#### 5. 数据改写失败
```bash
# 检查改写模块依赖
pip install textstat wordcloud

# 验证数据格式
python -c "
import json
with open('data/qa_results/sample.json') as f:
    data = json.load(f)
print('Data keys:', list(data.keys()))
"
```

## 📈 系统架构

### 数据流程图
```
PDF文档 → 文本召回 → 数据清理 → QA生成 → 质量控制 → 数据改写 → 最终输出
    ↓         ↓         ↓        ↓        ↓         ↓         ↓
  图像提取   结构化    格式统一   多模态    质量评分   内容增强   报告生成
             数据      JSON     问答对    改进建议   多样化     统计分析
```

### 模块交互
```
run_pipeline.py (主控制器)
    ├── TextQA/ (QA处理)
    ├── TextGeneration/ (文本生成)  
    ├── LocalModels/ (本地模型)
    ├── MultiModal/ (多模态)
    ├── model_rewrite/ (数据改写)
    └── 各领域模块/ (Doubao, Qwen, etc.)
```

## 🚀 整合完成确认

### ✅ 已整合功能
- [x] **文本召回与检索** - 从PDF文档智能提取相关内容
- [x] **数据清理与预处理** - 正则表达式和AI清理技术
- [x] **智能QA生成** - 基于36+专业Prompt模板生成高质量问答
- [x] **增强质量控制** - 多维度质量检查和自动改进
- [x] **多模态处理** - PDF图文结合，支持图像分析问答
- [x] **本地模型支持** - Ollama、vLLM、Transformers集成
- [x] **专业领域定制** - 半导体、光学、材料科学等领域特化
- [x] **数据改写增强** - 智能改写提升内容质量和多样性
- [x] **高性能处理** - 异步批处理、多进程架构、内存优化
- [x] **完整配置系统** - 统一配置文件支持所有功能
- [x] **统一流水线** - 一键运行完整处理流程

### 🎯 核心优势
1. **功能完整性** - 涵盖从原始PDF到最终QA对的完整流程，包括数据改写增强
2. **技术先进性** - 整合最新的AI技术、本地模型支持和数据增强技术
3. **专业领域深度** - 针对半导体、光学等专业领域深度优化
4. **部署灵活性** - 支持云端、本地、混合部署方案
5. **质量保证** - 多层次质量控制确保输出质量
6. **数据增强** - 智能改写技术提升数据质量和多样性
7. **易用性** - 一键运行，配置简单，文档完善

### 🔄 完整工作流程
1. **文档输入** → PDF文件或文本文件
2. **文本召回** → 智能提取相关内容
3. **数据清理** → 格式化和标准化处理
4. **QA生成** → 基于专业模板生成问答对
5. **质量控制** → 多维度质量检查和评分
6. **数据改写** → 智能改写增强内容质量
7. **最终输出** → 生成完整的QA数据集和报告

**让AI助力专业知识的智能问答生成，现在支持数据改写增强！** 🚀

如有问题或建议，请提交Issue或联系项目维护者。