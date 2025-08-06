# 智能文本QA生成系统 - 整合版

一个功能完整的智能文本问答生成系统，整合了文本召回、数据处理、QA生成和质量控制功能，专注于半导体、光学等专业领域。

## 🌟 核心特性

### 📊 完整数据流水线
- **文本召回**：从PDF文档中智能提取和召回相关文本内容
- **数据清理**：使用正则表达式和AI技术进行数据后处理
- **QA生成**：基于专业领域知识生成高质量问答对
- **质量控制**：多维度质量检查和自动改进

### 🔬 专业领域支持
- **半导体物理**：IGZO、TFT、OLED、能带理论等
- **光学与光电子**：光谱分析、器件特性、光子吸收等
- **材料科学**：材料特性、制备工艺等
- **36+专业Prompt模板**：覆盖各种专业场景

### 🤖 多模型支持
- **云端API模型**：豆包、Qwen、GPT等
- **本地模型**：Ollama、vLLM、Transformers
- **智能切换**：根据任务自动选择最佳模型

### 🚀 高性能处理
- **异步批处理**：支持大规模并发处理
- **多进程架构**：充分利用多核CPU资源
- **内存优化**：智能内存管理和缓存机制

## 📦 项目结构

```
├── README.md                           # 项目说明文档
├── requirements.txt                    # 依赖包列表
├── run_pipeline.py                     # 统一流水线脚本
├── config.json                         # 统一配置文件
│
├── data_retrieval/                     # 数据召回模块
│   ├── doubao_main_batch_inference.py  # 主批处理推理
│   ├── clean_data.py                   # 数据清理
│   └── qwen_argument.py                # QA构造
│
├── text_qa_generation/                 # QA生成模块
│   ├── text_qa_generation.py           # 主QA生成
│   ├── TextQA/                         # QA处理核心
│   ├── TextGeneration/                 # 文本生成
│   └── model_rewrite/                  # 数据改写
│
├── Doubao/                            # 豆包模型集成
│   ├── Datageneration.py              # 数据生成
│   └── prompts_conf.py                 # Prompt配置
│
├── Qwen/                              # Qwen模型集成
├── WizardLM/                          # WizardLM模型集成
└── Utilis/                            # 工具函数
```

## 🚀 快速开始

### 1. 环境安装

```bash
# 克隆项目
git clone <repository-url>
cd intelligent-qa-generation

# 安装基础依赖
pip install -r requirements.txt

# 可选：安装多模态支持
pip install PyMuPDF Pillow

# 可选：安装本地模型支持
pip install ollama transformers torch
```

### 2. 配置设置

```bash
# 复制配置模板
cp config_templates.json config.json

# 编辑配置文件，设置API密钥和模型路径
nano config.json
```

### 3. 基础使用

#### 完整流水线处理
```bash
# 一键运行完整流水线
python run_pipeline.py \
    --mode full_pipeline \
    --input_path data/pdfs/research_papers \
    --output_path data/results \
    --domain semiconductor
```

#### 分步骤处理

**步骤1：文本召回**
```bash
python doubao_main_batch_inference.py \
    --pdf_path data/pdfs \
    --storage_folder data/retrieved \
    --selected_task_number 1000
```

**步骤2：数据清理**
```bash
python clean_data.py \
    --input_file data/retrieved/total_response.pkl \
    --output_file data/cleaned
```

**步骤3：QA生成**
```bash
python text_qa_generation/text_qa_generation.py \
    --file_path data/cleaned/total_response.json \
    --output_file data/qa_results \
    --index 343
```

**步骤4：质量检查**
```bash
python text_qa_generation/text_qa_generation.py \
    --check_task true \
    --enhanced_quality true \
    --quality_threshold 0.7
```

## ⚙️ 配置说明

### 基础配置
```json
{
  "api": {
    "ark_url": "http://0.0.0.0:8080/v1",
    "api_key": "your-api-key-here"
  },
  "models": {
    "default_model": "/mnt/storage/models/Skywork/Skywork-R1V3-38B",
    "qa_generator_model": {
      "path": "/mnt/storage/models/Skywork/Skywork-R1V3-38B",
      "type": "api"
    }
  },
  "processing": {
    "batch_size": 100,
    "max_concurrent": 20,
    "quality_threshold": 0.7
  }
}
```

### 专业领域配置
```json
{
  "domains": {
    "semiconductor": {
      "prompts": [343, 3431, 3432],
      "keywords": ["IGZO", "TFT", "OLED", "半导体"],
      "quality_criteria": "high"
    },
    "optics": {
      "prompts": [343, 3431, 3432],
      "keywords": ["光谱", "光学", "激光"],
      "quality_criteria": "high"
    }
  }
}
```

## 📖 详细使用指南

### 数据召回阶段

**功能**：从PDF文档中提取和召回相关文本内容
**主要脚本**：`doubao_main_batch_inference.py`

```bash
python doubao_main_batch_inference.py \
    --index 43 \
    --parallel_batch_size 100 \
    --pdf_path /path/to/pdfs \
    --storage_folder /path/to/output \
    --selected_task_number 1000 \
    --read_hist false
```

**参数说明**：
- `--index`: 任务索引，对应不同的处理策略
- `--parallel_batch_size`: 并行批处理大小
- `--pdf_path`: PDF文件夹路径
- `--storage_folder`: 输出存储文件夹
- `--selected_task_number`: 选择处理的任务数量
- `--read_hist`: 是否读取历史数据

### 数据清理阶段

**功能**：对召回的数据进行清理和格式化
**主要脚本**：`clean_data.py`

```bash
python clean_data.py \
    --input_file /path/to/raw_data.pkl \
    --output_file /path/to/cleaned_output \
    --copy_parsed_pdf false
```

**处理内容**：
- 正则表达式匹配JSON格式内容
- 图片路径标准化
- 数据结构统一化

### QA生成阶段

**功能**：基于清理后的数据生成高质量问答对
**主要脚本**：`text_qa_generation/text_qa_generation.py`

```bash
python text_qa_generation/text_qa_generation.py \
    --index 343 \
    --file_path /path/to/cleaned_data.json \
    --pool_size 100 \
    --output_file /path/to/qa_output \
    --enhanced_quality true
```

### 质量控制阶段

**功能**：多维度质量检查和改进
**检查维度**：
- 推理有效性检查
- 问题清晰度评估
- 答案正确性验证
- 图片依赖性检查

## 🔧 高级功能

### 1. 批量处理脚本

创建批量处理脚本 `batch_process.sh`：

```bash
#!/bin/bash
# 批量处理多个PDF文件夹

INPUT_DIRS=("data/pdfs1" "data/pdfs2" "data/pdfs3")
OUTPUT_BASE="data/batch_results"

for dir in "${INPUT_DIRS[@]}"; do
    echo "Processing $dir..."
    python run_pipeline.py \
        --mode full_pipeline \
        --input_path "$dir" \
        --output_path "$OUTPUT_BASE/$(basename $dir)" \
        --domain semiconductor
done
```

### 2. 质量监控

```python
# quality_monitor.py
import json
import matplotlib.pyplot as plt

def monitor_quality(results_path):
    with open(results_path, 'r') as f:
        data = json.load(f)
    
    # 计算质量指标
    scores = [item.get('quality_score', 0) for item in data]
    avg_score = sum(scores) / len(scores)
    
    print(f"平均质量分数: {avg_score:.2f}")
    print(f"通过率: {len([s for s in scores if s > 0.7]) / len(scores):.2%}")
    
    # 生成质量分布图
    plt.hist(scores, bins=20)
    plt.xlabel('质量分数')
    plt.ylabel('数量')
    plt.title('QA质量分布')
    plt.savefig('quality_distribution.png')
```

### 3. 自定义Prompt

```python
# 在Doubao/prompts_conf.py中添加自定义prompt
user_prompts[999] = """
你的自定义prompt模板...
专门用于{domain}领域的{task_type}任务
"""
```

## 📊 输出格式

### 召回阶段输出
```json
{
  "content": "模型返回的原始内容...",
  "image_path": "/path/to/image.png",
  "metadata": {
    "page": 1,
    "confidence": 0.95
  }
}
```

### 清理后输出
```json
{
  "imageDescription": "图片描述内容...",
  "analysisResults": "分析结果...",
  "relatedKnowledge": "相关知识...",
  "image_path": "./data/images/sample.png"
}
```

### 最终QA输出
```json
{
  "question": "什么是IGZO材料的主要优势？",
  "answer": "IGZO材料具有高迁移率、低功耗和良好的均匀性...",
  "choices": ["选项A", "选项B", "选项C"],
  "reasoning": "基于IGZO材料的物理特性分析...",
  "context": "IGZO是铟镓锌氧化物的缩写...",
  "quality_score": 0.85,
  "domain": "semiconductor",
  "source_file": "igzo_research.pdf"
}
```

## 🛠️ 故障排除

### 常见问题

1. **内存不足**
   ```bash
   # 减少批处理大小
   --parallel_batch_size 50
   
   # 增加虚拟内存
   sudo swapon -s
   ```

2. **API调用失败**
   ```bash
   # 检查网络连接
   curl -I http://0.0.0.0:8080/v1
   
   # 验证API密钥
   python -c "from config import api_key; print('API Key valid' if api_key else 'Missing API Key')"
   ```

3. **数据格式错误**
   ```bash
   # 验证输入数据格式
   python check_file.py --input data/input.json
   
   # 重新运行清理步骤
   python clean_data.py --input raw_data.pkl --output cleaned_data
   ```

### 日志配置

```json
{
  "logging": {
    "level": "INFO",
    "file": "logs/pipeline.log",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  }
}
```

## 📈 性能优化

### 硬件建议
- **CPU**: 8核心以上
- **内存**: 32GB以上（大批量处理）
- **存储**: SSD，至少100GB可用空间
- **网络**: 稳定的网络连接（API调用）

### 优化参数
```json
{
  "optimization": {
    "batch_size": 100,
    "max_workers": 8,
    "memory_limit": "16GB",
    "cache_enabled": true,
    "parallel_processing": true
  }
}
```

## 🤝 贡献指南

### 开发环境设置
```bash
# 安装开发依赖
pip install -r requirements-dev.txt

# 运行测试
python -m pytest tests/

# 代码格式化
black . --line-length 100
flake8 . --max-line-length 100
```

### 提交规范
- feat: 新功能
- fix: 错误修复
- docs: 文档更新
- refactor: 代码重构
- test: 测试相关

## 📄 许可证

本项目采用MIT许可证，详见LICENSE文件。

## 🙏 致谢

感谢以下技术和项目的支持：
- [豆包大模型](https://www.volcengine.com/product/doubao) - 核心AI能力
- [Qwen](https://github.com/QwenLM/Qwen) - 文本生成模型
- [PyMuPDF](https://pymupdf.readthedocs.io/) - PDF处理
- [Asyncio](https://docs.python.org/3/library/asyncio.html) - 异步处理

---

**让AI助力专业知识的智能问答生成！** 🚀

如有问题或建议，请提交Issue或联系项目维护者。