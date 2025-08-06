# Text QA Generation - 专业文本问答生成系统

一个功能完整的文本问答生成系统，支持多模态处理、本地大模型、专业领域定制和数据改写增强。

## 🌟 主要特性

### 📚 多模态支持
- **PDF文档处理**：自动提取文本和图像，支持复杂学术论文
- **图文结合问答**：基于图片和文本内容生成高质量问答对
- **专业图表分析**：支持半导体、光学等专业领域的图表分析

### 🤖 多种模型支持
- **云端API模型**：支持OpenAI兼容的API接口
- **本地模型**：
  - Ollama集成（llama2, codellama, mistral, qwen等）
  - vLLM高性能推理服务
  - Transformers本地加载
- **智能模型选择**：根据配置自动选择最佳模型

### 🔬 专业领域定制
- **半导体物理**：IGZO、TFT、OLED等专业内容
- **光学与光电子**：光谱分析、器件特性等
- **材料科学**：材料特性、制备工艺等
- **36个专业Prompt模板**：覆盖各种专业场景

### 🚀 数据改写增强
- **智能改写**：保持核心内容不变，提升表达质量
- **质量提升**：自动优化问题和答案的专业性
- **多样化生成**：生成不同风格的问答对

### 🔍 质量控制系统
- **多维度检查**：推理有效性、问题清晰度、答案正确性
- **自动评分**：基于AI的质量评估和改进建议
- **批量质检**：高效处理大规模数据

## 📦 安装说明

### 基础环境
```bash
# 克隆项目
git clone <repository-url>
cd text_qa_generation

# 安装依赖
pip install -r requirements.txt
```

### 可选依赖

#### 多模态支持
```bash
pip install PyMuPDF  # PDF处理
pip install Pillow   # 图像处理
```

#### 本地模型支持
```bash
# Ollama支持
pip install ollama

# Transformers支持
pip install transformers torch torchvision

# vLLM支持
pip install vllm
```

## 🚀 快速开始

### 1. 基础文本问答生成
```bash
python text_qa_generation.py \
    --file_path data/input_texts/sample.txt \
    --output_file data/output/qa_results.json \
    --index 343
```

### 2. 多模态PDF处理
```bash
# 处理PDF文档
python MultiModal/pdf_processor.py \
    --input data/pdfs/research_paper.pdf \
    --output data/processed \
    --markdown

# 生成多模态问答
python text_main_batch_inference.py \
    --pdf_path data/processed \
    --storage_folder data/output \
    --index 343
```

### 3. 本地模型使用
```bash
# 启动Ollama服务
ollama serve

# 配置使用本地模型
python text_qa_generation.py \
    --file_path data/input.txt \
    --use_local_model ollama \
    --model_name llama2
```

### 4. 数据改写增强
```bash
python model_rewrite/data_generation.py \
    --data-path data/original_qa.json \
    --output-path data/enhanced_qa.json \
    --template-type professional
```

## ⚙️ 配置说明

### 模型配置
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

### 专业领域配置
```json
{
  "professional_domains": {
    "enabled": true,
    "default_domain": "semiconductor",
    "domain_specific_prompts": {
      "semiconductor": [343, 3431, 3432],
      "optics": [343, 3431, 3432]
    }
  }
}
```

## 📖 使用指南

### API Key说明
- **云端模型**：需要API Key用于身份验证和计费
- **本地模型**：无需API Key，完全本地运行
- **混合使用**：可配置优先级，自动切换

### 本地模型 vs 云端模型

| 特性 | 本地模型 | 云端模型 |
|------|----------|----------|
| 成本 | 一次性硬件成本 | 按使用量付费 |
| 隐私 | 完全本地，隐私安全 | 数据上传到云端 |
| 性能 | 取决于硬件配置 | 通常性能更强 |
| 延迟 | 低延迟 | 网络延迟 |
| 可用性 | 24/7本地可用 | 依赖网络连接 |

### 模型选择建议
- **研究环境**：推荐本地模型（数据隐私）
- **生产环境**：推荐云端模型（性能稳定）
- **混合场景**：配置多模型自动切换

## 🔧 高级功能

### 1. 批量处理
```bash
# 批量处理PDF文件夹
python run_pipeline.sh --mode batch_pdf \
    --input_dir data/pdfs \
    --output_dir data/results

# 批量质量检查
python model_rewrite/data_label.py \
    --data-path data/qa_pairs.json \
    --output-path data/quality_report.json
```

### 2. 质量控制
```python
from model_rewrite.data_label import DataLabeler

# 初始化质量检查器
labeler = DataLabeler(model_config)

# 执行质量检查
result = await labeler.comprehensive_quality_check(qa_record)
print(f"质量分数: {result['overall_score']}")
```

### 3. 专业领域定制
```python
from TextGeneration.prompts_conf import get_prompt

# 使用半导体专业prompt
prompt = get_prompt(3431)  # 半导体专业prompt
```

## 📊 输出格式

### 标准问答格式
```json
{
  "question": "什么是IGZO材料的主要优势？",
  "answer": "IGZO材料具有高迁移率、低功耗和良好的均匀性...",
  "question_type": "factual",
  "difficulty": "intermediate",
  "reasoning": "基于IGZO材料的物理特性...",
  "domain": "semiconductor",
  "source_file": "igzo_research.pdf"
}
```

### 多模态问答格式
```json
{
  "question": "根据图中的I-V特性曲线，判断器件类型",
  "answer": "A",
  "choices": ["二极管", "三极管", "场效应管"],
  "reasoning": "从曲线形状可以看出...",
  "image_path": "data/images/iv_curve.png",
  "context": "该图显示了半导体器件的电流-电压特性..."
}
```

## 🛠️ 开发指南

### 添加新的Prompt模板
```python
# 在TextGeneration/prompts_conf.py中添加
user_prompts[999] = """
你的自定义prompt模板...
"""
```

### 集成新的本地模型
```python
# 创建新的客户端类
class CustomModelClient:
    def __init__(self, config):
        self.config = config
    
    async def generate(self, prompt):
        # 实现生成逻辑
        pass
```

## 📈 性能优化

### 硬件要求
- **CPU**：8核心以上推荐
- **内存**：16GB以上（本地模型需要更多）
- **GPU**：NVIDIA GPU（支持CUDA，可选）
- **存储**：SSD推荐

### 优化建议
1. **并发控制**：根据硬件调整`pool_size`
2. **批处理**：使用批量处理提高效率
3. **模型缓存**：本地模型支持模型缓存
4. **质量阈值**：调整质量阈值平衡质量和效率

## 🔍 故障排除

### 常见问题

#### 1. Ollama连接失败
```bash
# 检查Ollama服务状态
ollama list

# 启动Ollama服务
ollama serve
```

#### 2. 内存不足
- 调整批处理大小
- 使用量化模型（4bit/8bit）
- 增加虚拟内存

#### 3. API调用失败
- 检查API Key有效性
- 确认网络连接
- 查看错误日志

### 日志配置
```json
{
  "logging": {
    "level": "DEBUG",
    "file": "logs/debug.log"
  }
}
```

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

### 开发流程
1. Fork项目
2. 创建功能分支
3. 提交代码
4. 创建Pull Request

### 代码规范
- 使用Python类型提示
- 遵循PEP 8代码规范
- 添加单元测试
- 更新文档

## 📄 许可证

本项目采用MIT许可证，详见LICENSE文件。

## 🙏 致谢

感谢以下开源项目的支持：
- [Ollama](https://ollama.ai/) - 本地大模型服务
- [vLLM](https://github.com/vllm-project/vllm) - 高性能推理
- [Transformers](https://huggingface.co/transformers/) - 模型库
- [PyMuPDF](https://pymupdf.readthedocs.io/) - PDF处理

## 📞 联系方式

如有问题或建议，请通过以下方式联系：
- 提交GitHub Issue
- 发送邮件至项目维护者

---

**让AI助力专业知识的问答生成！** 🚀