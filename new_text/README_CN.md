# 智能文本QA生成系统

## 系统概述

智能文本QA生成系统是一个功能完整的自动化问答对生成平台，专门针对半导体、光学等专业领域的技术文档。系统支持从PDF和文本文件中提取内容，并使用大语言模型（包括本地部署的Skywork模型）自动生成高质量的问答对。

## 主要功能

### 1. 文本召回与检索
- 支持PDF文件自动文本提取（使用多种提取方法）
- 支持纯文本文件处理
- 智能文档分块和重叠处理
- 批量文件并发处理

### 2. 数据清理与预处理
- 自动去除无效字符和格式
- 智能段落重组
- 保留专业术语和公式
- 文本质量评估

### 3. 智能QA生成
- 支持多种本地大模型（Skywork、Qwen等）
- 支持API模型调用
- 自适应prompt模板
- 批量异步生成

### 4. 质量控制
- QA对质量自动评分
- 答案相关性检查
- 专业术语准确性验证
- 低质量内容过滤

### 5. 多模态处理
- PDF图片提取
- 表格数据识别
- 图表内容理解
- 混合内容处理

### 6. 本地模型支持
- **Skywork-R1V3-38B**：支持通过vLLM或Transformers加载
- **Ollama**：支持多种开源模型
- **自定义模型**：可扩展支持其他本地模型

## 系统架构

```
智能文本QA生成系统
├── 数据输入层
│   ├── PDF处理器
│   ├── 文本处理器
│   └── 多模态处理器
├── 处理层
│   ├── 文本清理模块
│   ├── 内容分块模块
│   └── 特征提取模块
├── 生成层
│   ├── 本地模型接口
│   │   ├── Skywork客户端
│   │   ├── Ollama客户端
│   │   └── Transformers客户端
│   └── API模型接口
├── 质量控制层
│   ├── QA评分模块
│   ├── 相关性检查
│   └── 专业性验证
└── 输出层
    ├── JSON格式输出
    ├── 批量导出
    └── 统计报告
```

## 环境要求

### 硬件要求
- GPU：NVIDIA GPU（显存≥24GB，推荐用于Skywork-38B模型）
- CPU：8核以上
- 内存：32GB以上
- 存储：100GB以上可用空间

### 软件要求
- Python 3.8+
- CUDA 11.8+（如使用GPU）
- PyTorch 2.0+

## 安装部署

### 1. 克隆项目
```bash
git clone <repository_url>
cd new_text
```

### 2. 创建虚拟环境
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
```

### 3. 安装依赖
```bash
pip install -r requirements.txt
```

### 4. 配置本地模型

#### 方式一：使用vLLM（推荐用于生产环境）
```bash
# 安装vLLM
pip install vllm

# 启动vLLM服务
python -m vllm.entrypoints.openai.api_server \
    --model /mnt/storage/models/Skywork/Skywork-R1V3-38B \
    --host 0.0.0.0 \
    --port 8000 \
    --tensor-parallel-size 1 \
    --gpu-memory-utilization 0.9
```

#### 方式二：使用Transformers（适合开发测试）
```bash
# 安装额外依赖
pip install transformers accelerate bitsandbytes
```

#### 方式三：使用Ollama（轻量级模型）
```bash
# 安装Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# 启动Ollama服务
ollama serve

# 拉取模型
ollama pull qwen:7b
```

### 5. 配置文件设置

编辑 `config.json` 文件，配置模型路径和参数：

```json
{
  "api": {
    "use_local_models": true,
    "local_model_type": "skywork"
  },
  "models": {
    "skywork": {
      "enabled": true,
      "client_type": "vllm",
      "base_url": "http://localhost:8000",
      "model_path": "/mnt/storage/models/Skywork/Skywork-R1V3-38B",
      "temperature": 0.8,
      "max_tokens": 4096
    }
  }
}
```

## 使用方法

### 1. 准备数据
将PDF或文本文件放入 `data/pdfs` 或 `data/texts` 目录：
```bash
mkdir -p data/pdfs data/texts
cp your_documents.pdf data/pdfs/
cp your_text_files.txt data/texts/
```

### 2. 运行系统

#### 一键运行（推荐）
```bash
./run_all.sh
```

#### 分步运行
```bash
# 步骤1：文本召回
python run_pipeline.py --stage text_retrieval

# 步骤2：数据清理
python run_pipeline.py --stage data_cleaning

# 步骤3：QA生成
python run_pipeline.py --stage qa_generation

# 步骤4：质量控制
python run_pipeline.py --stage quality_control
```

#### 自定义运行
```bash
# 指定配置文件
python run_pipeline.py --config custom_config.json

# 只处理特定文件
python run_pipeline.py --input-dir data/specific_docs

# 调整并发数
python run_pipeline.py --max-concurrent 10

# 使用特定模型
python run_pipeline.py --model-type skywork --model-path /path/to/model
```

### 3. 查看结果
生成的QA对保存在 `data/output/qa_pairs/` 目录：
```bash
ls data/output/qa_pairs/
cat data/output/qa_pairs/generated_qa_*.json
```

## 配置说明

### 主要配置项

1. **模型配置**
   - `use_local_models`: 是否使用本地模型
   - `local_model_type`: 本地模型类型（skywork/ollama）
   - `temperature`: 生成温度（0-1）
   - `max_tokens`: 最大生成长度

2. **处理配置**
   - `batch_size`: 批处理大小
   - `max_concurrent`: 最大并发数
   - `chunk_size`: 文本分块大小
   - `chunk_overlap`: 分块重叠长度

3. **质量控制**
   - `quality_threshold`: 质量阈值（0-1）
   - `min_answer_length`: 最小答案长度
   - `require_reasoning`: 是否需要推理过程

## 性能优化

### 1. GPU加速
- 使用vLLM进行高效推理
- 启用张量并行处理
- 优化显存使用

### 2. 批处理优化
- 动态批大小调整
- 异步并发处理
- 内存池管理

### 3. 缓存机制
- 模型推理缓存
- 文档处理缓存
- 结果增量更新

## 故障排除

### 常见问题

1. **连接错误：Connection error**
   - 检查本地模型服务是否启动
   - 验证端口是否正确
   - 查看防火墙设置

2. **内存不足**
   - 减小batch_size
   - 使用量化模型（8bit/4bit）
   - 增加系统swap空间

3. **PDF提取失败**
   - 安装额外的PDF处理库
   - 检查PDF文件是否损坏
   - 尝试其他提取方法

### 日志查看
```bash
# 查看主日志
tail -f logs/pipeline.log

# 查看生成日志
tail -f TextGeneration/logs/text_generation_*.log

# 查看错误日志
grep ERROR logs/*.log
```

## 扩展开发

### 添加新模型
1. 在 `LocalModels/` 目录创建新的客户端类
2. 实现标准接口（generate、chat方法）
3. 在配置文件中添加模型配置
4. 更新 `Datageneration.py` 添加调用逻辑

### 自定义Prompt
编辑 `TextGeneration/prompts_conf.py` 文件，添加新的prompt模板。

### 质量评估扩展
在 `TextQA/enhanced_quality_checker.py` 中添加新的评估指标。

## 许可证

本项目采用 MIT 许可证。

## 联系方式

如有问题或建议，请提交Issue或联系维护团队。

---

**注意**：本系统设计用于专业技术文档的QA生成，生成内容仅供参考，请人工审核后使用。