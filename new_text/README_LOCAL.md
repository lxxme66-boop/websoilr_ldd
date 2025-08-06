# 智能文本QA生成系统 - 本地模型版

## 系统概述

本系统是一个功能完整的智能文本问答生成系统，专门针对半导体、光学等专业领域的文档进行智能处理。系统支持从PDF和文本文件中提取内容，并使用本地大语言模型生成高质量的问答对。

### 主要功能

1. **文本召回与检索**
   - 支持PDF和文本文件的自动识别和处理
   - 智能文本分块和内容提取
   - 支持多种PDF解析方法（PyPDF2、pdfplumber、PyMuPDF）

2. **本地模型支持**
   - 支持Skywork-R1V3-38B本地大模型
   - 支持通过vLLM高效运行大模型
   - 支持Ollama作为备选方案
   - 自动检测和切换可用的模型服务

3. **智能QA生成**
   - 基于专业领域的prompt优化
   - 支持多种QA生成策略
   - 批量异步处理提高效率

4. **质量控制**
   - 自动评估生成的QA质量
   - 支持数据改写和增强
   - 去重和格式化处理

## 安装要求

### 系统要求
- Python 3.8+
- CUDA 11.8+ (用于GPU加速)
- 至少24GB GPU显存（运行38B模型）
- 64GB+ 系统内存

### 依赖安装

```bash
# 安装基础依赖
pip install -r requirements.txt

# 安装vLLM（用于运行Skywork模型）
pip install vllm

# 可选：安装Ollama作为备选
curl -fsSL https://ollama.com/install.sh | sh
```

## 快速开始

### 1. 启动本地模型服务

#### 方式一：使用Skywork模型（推荐）
```bash
# 赋予执行权限
chmod +x start_skywork_server.sh

# 启动Skywork vLLM服务器
./start_skywork_server.sh
```

#### 方式二：使用Ollama（备选）
```bash
# 启动Ollama服务
ollama serve

# 在另一个终端拉取模型
ollama pull qwen:14b
```

### 2. 准备数据

```bash
# 创建数据目录
mkdir -p data/pdfs data/texts

# 将PDF文件放入 data/pdfs/
# 将文本文件放入 data/texts/
```

### 3. 运行系统

#### 一键运行所有阶段
```bash
python run_pipeline.py
```

#### 分步运行
```bash
# 阶段1：文本召回
python run_pipeline.py --stage text_retrieval

# 阶段2：QA生成
python run_pipeline.py --stage qa_generation

# 阶段3：质量检查
python run_pipeline.py --stage quality_check

# 阶段4：数据改写
python run_pipeline.py --stage rewrite_enhancement
```

## 配置说明

系统配置文件为 `config.json`，主要配置项：

```json
{
  "api": {
    "use_local_models": true,  // 启用本地模型
    "local_model_priority": ["skywork", "ollama"]  // 模型优先级
  },
  "models": {
    "local_models": {
      "skywork": {
        "enabled": true,
        "base_url": "http://localhost:8000",
        "model_path": "/mnt/storage/models/Skywork/Skywork-R1V3-38B"
      }
    }
  }
}
```

## 运行流程

1. **文本召回阶段**
   - 扫描 `data/pdfs` 和 `data/texts` 目录
   - 提取和处理文本内容
   - 生成结构化的文本块

2. **QA生成阶段**
   - 使用本地模型处理文本块
   - 生成专业领域的问答对
   - 保存到 `output/qa_pairs/` 目录

3. **质量检查阶段**
   - 评估QA对的质量
   - 过滤低质量内容
   - 生成质量报告

4. **数据改写阶段**
   - 对高质量QA进行改写增强
   - 增加数据多样性
   - 输出最终数据集

## 输出文件

- `output/qa_pairs/`: QA对JSON文件
- `output/quality_checked/`: 质量检查后的数据
- `output/rewritten/`: 改写增强后的数据
- `logs/`: 运行日志文件

## 故障排除

### 1. vLLM服务无法启动
- 检查GPU驱动和CUDA版本
- 降低GPU内存使用率：修改 `start_skywork_server.sh` 中的 `GPU_MEMORY_UTILIZATION`
- 使用更小的模型或减少 `max_model_len`

### 2. 连接错误
- 确保本地模型服务已启动
- 检查端口是否被占用
- 查看服务日志排查问题

### 3. 内存不足
- 减少批处理大小：修改 `config.json` 中的 `batch_size`
- 使用量化模型：在vLLM启动时添加 `--dtype half`
- 分批处理文件

## 性能优化建议

1. **使用GPU加速**
   - 确保正确安装CUDA和相关驱动
   - 使用支持的GPU型号（推荐A100、V100）

2. **批处理优化**
   - 根据GPU内存调整批处理大小
   - 使用异步处理提高吞吐量

3. **模型选择**
   - 大文件使用Skywork-38B获得更好质量
   - 小文件可以使用Ollama的轻量级模型

## 联系和支持

如有问题或需要帮助，请查看：
- 日志文件：`logs/` 目录
- 配置模板：`config_templates.json`
- 测试脚本：`test_*.py`