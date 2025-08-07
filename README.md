# 智能文本QA生成系统 - 整合版 v2.0

## 目录
- [系统概述](#系统概述)
- [核心功能](#核心功能)
- [系统架构](#系统架构)
- [安装部署](#安装部署)
- [使用指南](#使用指南)
- [本地模型支持](#本地模型支持)
- [配置说明](#配置说明)
- [API文档](#api文档)
- [故障排除](#故障排除)

## 系统概述

智能文本QA生成系统是一个功能完整的端到端解决方案，用于从各种文档（PDF、文本文件）中自动生成高质量的问答对。系统支持多种大语言模型后端，包括API服务和本地模型部署。

### 主要特性
- 🚀 **高性能处理**: 支持批量并发处理，自动任务调度
- 🤖 **多模型支持**: 支持API和本地模型（vLLM、Transformers、Ollama）
- 📄 **多格式支持**: PDF、TXT、Markdown等文档格式
- 🎯 **专业领域定制**: 半导体、光学、材料等专业领域优化
- 🔍 **智能质量控制**: 多维度质量评估和自动改进
- 📊 **完整的流水线**: 从文档到高质量QA对的全自动化流程

## 核心功能

### 1. 文本召回与检索 (Text Retrieval)
- **功能描述**: 从原始文档中提取和预处理文本内容
- **支持格式**: 
  - PDF文件（支持多种提取引擎：PyMuPDF、pdfplumber、PyPDF2）
  - 文本文件（.txt、.text、.md）
  - 支持中英文混合文档
- **智能分块**: 自动将长文档分割成适合处理的块，保持语义完整性
- **历史记录**: 支持断点续传，避免重复处理

### 2. 数据清理与预处理 (Data Cleaning)
- **文本标准化**: 去除多余空白、统一编码格式
- **格式化处理**: 保持原文档的结构信息（标题、列表、表格等）
- **噪声过滤**: 去除无意义的字符和格式噪声
- **内容验证**: 确保提取的文本质量符合后续处理要求

### 3. 智能QA生成 (QA Generation)
- **多类型问题生成**:
  - 事实性问题 (Factual): 基于文档事实的直接问答
  - 比较性问题 (Comparison): 概念、方法的对比分析
  - 推理性问题 (Reasoning): 需要逻辑推理的深度问题
  - 开放性问题 (Open-ended): 探索性、创造性思考题
- **上下文感知**: 保持问答与原文的语义关联
- **专业领域优化**: 针对特定领域生成专业问题

### 4. 增强质量控制 (Quality Control)
- **多维度评估**:
  - 推理有效性 (Reasoning Validity)
  - 问题清晰度 (Question Clarity)
  - 答案正确性 (Answer Correctness)
  - 领域相关性 (Domain Relevance)
- **自动改进机制**: 低质量QA对的自动重新生成
- **人工审核接口**: 支持人工干预和质量标注

### 5. 多模态处理 (Multimodal Processing)
- **图像理解**: 从PDF中提取图像并生成相关问答
- **图表分析**: 理解图表、流程图等视觉信息
- **文图结合**: 生成需要结合文本和图像的综合性问题

### 6. 本地模型支持 (Local Models)
- **vLLM**: 高性能推理引擎，支持大规模模型部署
- **Transformers**: HuggingFace生态系统，灵活的模型加载
- **Ollama**: 简单易用的本地模型管理工具
- **自动选择**: 根据配置自动选择最优的模型后端

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                        输入层 (Input Layer)                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │  PDF Files  │  │  Text Files │  │   Images    │        │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘        │
└─────────┼─────────────────┼─────────────────┼──────────────┘
          │                 │                 │
┌─────────▼─────────────────▼─────────────────▼──────────────┐
│                    处理层 (Processing Layer)                 │
│  ┌─────────────────────────────────────────────────────┐  │
│  │            文本提取与预处理 (Text Extraction)          │  │
│  │  - PDF解析    - 文本分块    - 格式标准化             │  │
│  └─────────────────────┬───────────────────────────────┘  │
│                        │                                    │
│  ┌─────────────────────▼───────────────────────────────┐  │
│  │              QA生成引擎 (QA Generation Engine)        │  │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐            │  │
│  │  │  Local  │  │   API   │  │ Prompts │            │  │
│  │  │ Models  │  │ Models  │  │ Library │            │  │
│  │  └─────────┘  └─────────┘  └─────────┘            │  │
│  └─────────────────────┬───────────────────────────────┘  │
│                        │                                    │
│  ┌─────────────────────▼───────────────────────────────┐  │
│  │            质量控制系统 (Quality Control)             │  │
│  │  - 多维度评估    - 自动改进    - 人工审核接口        │  │
│  └─────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────┘
          │
┌─────────▼───────────────────────────────────────────────────┐
│                      输出层 (Output Layer)                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │  JSON Files │  │  CSV Files  │  │   Reports   │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

## 安装部署

### 系统要求
- Python 3.8+
- CUDA 11.8+ (用于GPU加速)
- 内存: 建议32GB以上
- 存储: 根据模型大小，建议预留100GB以上

### 安装步骤

1. **克隆仓库**
```bash
git clone <repository_url>
cd text_qa_generation
```

2. **创建虚拟环境**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
```

3. **安装依赖**
```bash
pip install -r requirements.txt
```

4. **安装本地模型支持（可选）**
```bash
# vLLM支持
pip install vllm

# Transformers支持
pip install transformers accelerate bitsandbytes

# Ollama支持
# 访问 https://ollama.ai 下载安装
```

### 快速开始

#### 一键运行
```bash
# 使用默认配置运行完整流水线
bash run_all.sh

# 或使用Python脚本
python run_pipeline.py --config config.json
```

#### 分步运行
```bash
# 步骤1: 文本提取
python run_pipeline.py --stage text_retrieval

# 步骤2: 数据清理
python run_pipeline.py --stage data_cleaning

# 步骤3: QA生成
python run_pipeline.py --stage qa_generation

# 步骤4: 质量控制
python run_pipeline.py --stage quality_control
```

## 本地模型支持

### vLLM配置
vLLM是推荐的本地模型部署方案，提供最佳的推理性能。

1. **启动vLLM服务**
```bash
python -m vllm.entrypoints.openai.api_server \
    --model /mnt/storage/models/Skywork/Skywork-R1V3-38B \
    --port 8000 \
    --gpu-memory-utilization 0.9 \
    --max-model-len 32768
```

2. **配置config.json**
```json
{
  "api": {
    "use_local_models": true,
    "local_model_priority": ["vllm", "transformers", "ollama"]
  },
  "models": {
    "local_models": {
      "vllm": {
        "enabled": true,
        "base_url": "http://localhost:8000",
        "model_name": "/mnt/storage/models/Skywork/Skywork-R1V3-38B"
      }
    }
  }
}
```

### Transformers配置
适合需要更多自定义控制的场景。

```json
{
  "models": {
    "local_models": {
      "transformers": {
        "enabled": true,
        "model_name": "/mnt/storage/models/Skywork/Skywork-R1V3-38B",
        "device": "auto",
        "torch_dtype": "auto",
        "load_in_4bit": false,
        "load_in_8bit": false
      }
    }
  }
}
```

### Ollama配置
最简单的本地模型部署方案。

1. **安装Ollama**
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

2. **下载模型**
```bash
ollama pull qwen:7b
```

3. **配置使用**
```json
{
  "models": {
    "local_models": {
      "ollama": {
        "enabled": true,
        "base_url": "http://localhost:11434",
        "model_name": "qwen:7b"
      }
    }
  }
}
```

## 配置说明

### 核心配置项

#### API配置
```json
{
  "api": {
    "use_local_models": true,  // 是否使用本地模型
    "local_model_priority": ["vllm", "transformers", "ollama"],  // 优先级顺序
    "timeout": 600,  // 请求超时时间（秒）
    "max_retries": 3  // 最大重试次数
  }
}
```

#### 处理配置
```json
{
  "processing": {
    "batch_size": 100,  // 批处理大小
    "max_concurrent": 20,  // 最大并发数
    "chunk_size": 2000,  // 文本分块大小
    "chunk_overlap": 200  // 分块重叠大小
  }
}
```

#### 质量控制配置
```json
{
  "quality_control": {
    "enhanced_quality_check": {
      "enabled": true,
      "quality_threshold": 0.7,  // 质量阈值
      "dimensions": [  // 评估维度
        "reasoning_validity",
        "question_clarity",
        "answer_correctness",
        "domain_relevance"
      ]
    }
  }
}
```

### 专业领域配置

系统支持针对特定专业领域的优化配置：

```json
{
  "professional_domains": {
    "enabled": true,
    "default_domain": "semiconductor",
    "semiconductor": {
      "keywords": ["IGZO", "TFT", "OLED", "半导体", "晶体管"],
      "quality_criteria": "high",
      "specific_checks": ["technical_accuracy", "formula_validity"]
    }
  }
}
```

## 使用示例

### 示例1: 处理PDF文档
```python
from run_pipeline import IntegratedQAPipeline

# 初始化流水线
pipeline = IntegratedQAPipeline("config.json")

# 运行完整流程
results = pipeline.run_pipeline(
    input_dir="data/pdfs",
    stages=["text_retrieval", "qa_generation", "quality_control"]
)

print(f"生成了 {results['total_qa_pairs']} 个QA对")
```

### 示例2: 使用本地模型
```python
from LocalModels import LocalModelManager

# 加载配置
config = json.load(open("config.json"))

# 初始化本地模型管理器
model_manager = LocalModelManager(config)

# 生成文本
response = await model_manager.generate(
    prompt="解释什么是半导体",
    temperature=0.7,
    max_tokens=1024
)
```

### 示例3: 批量处理文本文件
```python
from TextGeneration.Datageneration import process_folder_async

# 处理整个文件夹
results = await process_folder_async(
    folder_path="data/texts",
    prompt_index=43,  # 使用特定的提示模板
    max_concurrent=10,  # 并发处理10个文件
    config=config
)
```

## API文档

### 主要类和函数

#### IntegratedQAPipeline
主流水线类，协调整个处理流程。

```python
class IntegratedQAPipeline:
    def __init__(self, config_path: str = "config.json"):
        """初始化流水线"""
        
    def run_pipeline(self, input_dir: str = None, stages: List[str] = None):
        """运行指定的流水线阶段"""
        
    def run_single_stage(self, stage: str):
        """运行单个阶段"""
```

#### LocalModelManager
本地模型管理器，统一管理不同的模型后端。

```python
class LocalModelManager:
    def __init__(self, config: Dict):
        """初始化模型管理器"""
        
    async def generate(self, prompt: str, **kwargs) -> str:
        """生成文本"""
        
    def is_available(self) -> bool:
        """检查模型是否可用"""
```

#### 文本处理函数
```python
async def parse_txt(file_path: str, index: int = 9, config: Dict = None):
    """解析文本文件并创建处理任务"""
    
async def input_text_process(text_content: str, source_file: str, **kwargs):
    """处理文本内容并生成QA"""
```

## 故障排除

### 常见问题

#### 1. 本地模型加载失败
**错误信息**: `Connection error` 或 `Local models not available`

**解决方案**:
- 检查模型路径是否正确
- 确认vLLM服务是否启动
- 验证GPU驱动和CUDA版本
- 检查内存是否充足

#### 2. PDF提取失败
**错误信息**: `所有PDF提取方法失败`

**解决方案**:
- 安装所需的PDF处理库: `pip install pymupdf pdfplumber pypdf2`
- 检查PDF文件是否损坏
- 尝试不同的提取引擎

#### 3. API连接超时
**错误信息**: `Connection timeout`

**解决方案**:
- 增加timeout配置值
- 检查网络连接
- 启用本地模型作为备选

### 性能优化建议

1. **批处理优化**
   - 根据系统内存调整batch_size
   - 使用适当的max_concurrent值避免过载

2. **模型选择**
   - 大文档使用vLLM获得最佳性能
   - 小批量处理可以使用Transformers
   - 快速原型使用Ollama

3. **内存管理**
   - 启用内存限制和垃圾回收
   - 使用量化技术减少模型内存占用

## 开发指南

### 添加新的模型后端
1. 在`LocalModels`目录创建新的客户端类
2. 实现统一的接口方法（generate、generate_stream等）
3. 在LocalModelManager中注册新后端
4. 更新配置文件模板

### 添加新的专业领域
1. 在config.json中添加领域配置
2. 创建领域特定的提示模板
3. 实现领域特定的质量检查逻辑
4. 更新文档

## 更新日志

### v2.0.0 (2024-12-20)
- ✨ 新增本地模型支持（vLLM、Transformers、Ollama）
- 🔧 优化配置系统，支持动态模型切换
- 📈 提升批处理性能
- 🐛 修复PDF提取相关问题
- 📚 完善文档和示例

### v1.0.0 (2024-12-01)
- 🎉 初始版本发布
- 基础QA生成功能
- 支持PDF和文本文件
- 简单的质量控制

## 许可证
[添加许可证信息]

## 贡献指南
欢迎提交Issue和Pull Request！

## 联系方式
[添加联系信息]