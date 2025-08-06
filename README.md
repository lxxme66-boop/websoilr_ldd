# WebSoilr LDD - 知识问答数据生成系统

## 项目概述

WebSoilr LDD 是一个专业的知识问答数据生成系统，主要用于半导体和显示技术领域的高质量QA数据集构建。系统支持多种数据源输入，并提供强大的质量检测和数据清洗功能。

## 最新更新

### text_qa_generation 模块 - 增强质量检测系统

`text_qa_generation` 模块已完成重大升级，集成了基于 `checkInfor/checkQuestion.py` 的双阶段验证思路：

- **双阶段验证机制**：先让模型独立回答问题，再比较答案正确性
- **智能质量评估**：多维度评估内容准确性、完整性、逻辑性  
- **批量处理能力**：支持并发处理，提供详细质量报告
- **多格式输出**：生成详细结果、高质量数据、质量报告和CSV分析文件

详细信息请查看 [text_qa_generation README](text_qa_generation/README.md) 和 [增强质量检查文档](text_qa_generation/ENHANCED_QUALITY_CHECK.md)

## 主要模块

### 1. text_qa_generation（文本QA生成）
专门处理纯文本数据，生成高质量的问答对。

```bash
cd text_qa_generation
bash run_pipeline.sh
```

### 2. Doubao（多模态QA生成）
处理PDF、PPT等多模态文档，支持图文混合的QA生成。

### 3. Qwen（模型推理）
基于Qwen模型的推理引擎，提供高质量的答案生成。

### 4. WizardLM（数据演化）
使用WizardLM方法进行数据增强和演化。

### 5. checkInfor（质量检测）
原始的质量检测模块，其核心思想已集成到text_qa_generation中。

## 快速开始

### 环境准备

```bash
# 安装依赖
pip install -r requirements.txt

# 设置API密钥
export ARK_API_KEY="your-api-key"
export ARK_URL="http://0.0.0.0:8080/v1"
```

### 运行文本QA生成

```bash
cd text_qa_generation
bash run_pipeline.sh
```

### 运行质量检测

```bash
# 增强版质量检测（推荐）
python text_qa_generation.py \
    --check_task True \
    --enhanced_quality True \
    --quality_threshold 0.7 \
    --file_path "data/output/results.json"

# 标准质量检测
python text_qa_generation.py \
    --check_task True \
    --enhanced_quality False \
    --check_indexes "(40, 37, 38)"
```

## 项目结构

```
websoilr_ldd/
├── text_qa_generation/     # 文本QA生成模块（已升级）
├── Doubao/                 # 多模态处理模块
├── Qwen/                   # Qwen模型推理
├── WizardLM/              # 数据演化模块
├── checkInfor/            # 原始质量检测模块
├── model_rewrit/          # 模型重写模块
├── Utilis/                # 工具函数
└── EnvoInstruction/       # 环境指令模块
```

## 配置说明

主要配置文件位于各模块的 `config.json` 中，支持以下配置：

- 模型参数（路径、温度、最大长度等）
- 问题类型和比例
- 质量控制参数
- 并发处理参数

## 贡献指南

欢迎提交Issue和Pull Request。主要改进方向：

- 增加更多领域的专业prompt
- 优化质量检测算法
- 提升并发处理性能
- 扩展数据源支持

## 许可证

本项目遵循相应的开源许可证要求。