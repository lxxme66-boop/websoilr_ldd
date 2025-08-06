# Only_Txt: 纯文本QA数据生成系统

## 项目概述

本项目是基于原多模态QA数据生成系统修改而来的纯文本版本。核心功能保持不变，只是去除了所有图片相关的处理，专注于从纯文本文档中生成高质量的问答数据集。

## 主要修改内容

### 1. 去除的功能
- **图片处理**：移除了所有图片编码、解码和传输相关代码
- **PDF解析**：改为直接读取txt文件，不再需要PDF解析
- **图片路径管理**：简化为文本文件路径管理
- **多模态prompt**：修改为纯文本处理的prompt

### 2. 保留的核心功能
- **异步并发处理**：保持原有的高效异步架构
- **批量处理能力**：支持大规模文本文件批处理
- **数据质量控制**：保留多轮质量检查机制
- **数据增强**：保留SFT格式转换和数据润色功能
- **灵活的prompt系统**：调整为适合文本处理的prompt模板

### 3. 新增/修改的文件

#### 核心处理文件
- `txt_main_batch_inference.py`：替代原`doubao_main_batch_inference.py`
  - 修改：处理txt文件夹而非PDF文件夹
  - 修改：metadata.json变为可选文件
  - 保留：异步批处理架构

- `clean_data.py`：数据清洗
  - 修改：去除图片路径处理
  - 新增：文本内容字段处理
  - 保留：正则提取和数据过滤逻辑

- `qwen_argument.py`：QA生成
  - 修改：调用`get_total_responses_txt`处理纯文本
  - 修改：`txt_folder`参数替代`image_folder`
  - 保留：并发处理和质量检查功能

#### 模块文件
- `Doubao/Datageneration.py`
  - 新增：`extract_text_content()`读取txt文件
  - 新增：`extract_txt_files()`批量提取文本
  - 修改：`get_request()`去除图片参数
  - 修改：`parse_txt_folder()`替代`parse_pdf()`
  - 修改：metadata.json为可选，不存在时使用空字典

- `Doubao/prompts_conf.py`
  - 修改：所有prompt改为文本分析相关
  - 保留：prompt编号体系（1, 9, 21, 22, 33, 43, 343, 37, 38, 40）
  - 新增：文本专用的知识提取和QA生成prompt

- `Qwen/dataargument.py`
  - 新增：`get_response_txt()`处理纯文本响应
  - 新增：`process_single_txt_response()`单个文本QA生成
  - 修改：`get_total_responses_txt()`批量处理文本
  - 保留：质量检查逻辑

#### 其他文件
- `argument_data.py`：数据增强
  - 修改：去除图片相关字段
  - 保留：SFT格式转换和质量检查
  
- `generate_dataset.py`：最终数据集生成
  - 修改：`files`字段替代`images`
  - 保留：ShareGPT格式输出

## 文件结构要求

### 输入文件结构
```
txt_files/
├── folder1/
│   ├── metadata.json  # 可选：文件夹元信息
│   ├── text1.txt
│   ├── text2.txt
│   └── ...
├── folder2/
│   ├── text1.txt      # 可以没有metadata.json
│   └── ...
└── ...
```

### metadata.json 示例（可选）
如果提供metadata.json，格式如下：
```json
{
  "folder_info": "文档集描述",
  "text1.txt": {
    "title": "文档标题",
    "author": "作者",
    "category": "类别"
  }
}
```
注意：metadata.json是完全可选的。如果不存在，系统会使用空元数据继续处理。

## 运行流程

### 1. 准备数据
将文本文件按文件夹组织。每个文件夹可以选择性地包含一个`metadata.json`文件。

### 2. 运行脚本
```bash
# 使用默认参数
./run_pipeline.sh

# 自定义参数
./run_pipeline.sh /path/to/txt_files /path/to/output [index1] [index2]
```

参数说明：
- 参数1：文本文件路径（默认：/workspace/data/txt_files）
- 参数2：输出路径（默认：/workspace/data/txt_output）
- 参数3：文本提取索引（默认：43）
- 参数4：QA生成索引（默认：343）

### 3. 运行步骤详解

1. **文本提取**（txt_main_batch_inference.py）
   - 读取各文件夹中的txt文件
   - 可选读取metadata.json
   - 使用prompt 43提取文本内容
   - 输出：total_response.pkl

2. **数据清洗**（clean_data.py）
   - 清理提取的JSON响应
   - 标准化文件路径
   - 输出：total_response.json

3. **QA生成**（qwen_argument.py）
   - 使用prompt 343生成问答对
   - 并发处理多个文本
   - 输出：results_343.json

4. **数据增强**（argument_data.py）
   - 使用prompt 21转换为SFT格式
   - 润色和改写内容
   - 输出：rephrased_responses_qa.json

5. **质量检查**（argument_data.py）
   - 使用prompt 22检查数据质量
   - 过滤低质量数据
   - 输出：checked_responses_qa.json

6. **生成数据集**（generate_dataset.py）
   - 转换为ShareGPT格式
   - 整理最终训练数据
   - 输出：final_data.json

## 输出格式

### 中间文件格式

#### total_response.json
```json
[
  {
    "file_path": "folder1/text1.txt",
    "text_content": "文本内容...",
    "main_knowledge": "主要知识点...",
    "key_concepts": "关键概念..."
  }
]
```

#### results_343.json（QA格式）
```json
[
  {
    "file_path": "folder1/text1.txt",
    "question": "问题内容",
    "choices": ["选项A", "选项B", "选项C", "选项D"],
    "answer": "A",
    "reasoning": "推理过程...",
    "lecture": "相关知识点...",
    "context": "背景信息..."
  }
]
```

#### final_data.json（ShareGPT格式）
```json
{
  "prompt": [
    [{
      "role": "user",
      "content": [{"type": "text", "text": "问题和背景"}]
    }]
  ],
  "files": ["folder1/text1.txt"],
  "completions": [
    [{
      "role": "assistant",
      "content": [{"type": "text", "text": "<thinking>推理过程</thinking>\n<answer>答案</answer>"}]
    }]
  ]
}
```

## 未实现的功能

1. **WizardLM集成**：暂未集成指令进化功能
2. **批量推理优化**：未包含batch_inference.py的优化版本
3. **模型改写功能**：model_rewrit目录下的功能未集成
4. **EnvoInstruction**：另一套指令增强系统未集成

## 依赖要求

```python
# 主要依赖
volcenginesdkarkruntime
openai
asyncio
pandas
```

## 注意事项

1. **API配置**：需要在相关文件中配置正确的API密钥和端点
2. **并发控制**：根据API限制调整并发数量
3. **文本编码**：确保所有文本文件使用UTF-8编码
4. **内存管理**：处理大量文件时注意内存使用
5. **metadata.json**：可选文件，不是必需的

## 故障排查

1. **文件读取错误**：检查文件编码和路径
2. **API限流**：降低并发数或增加重试间隔
3. **JSON解析错误**：检查prompt返回格式
4. **质量检查失败**：调整检查标准或增加检查次数
5. **metadata.json缺失**：这是正常的，系统会继续处理