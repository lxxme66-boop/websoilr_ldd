# 可用脚本说明

## 概述
虽然没有找到 `syndata_pipeline_v5.sh`，但系统中有以下几个相关的脚本可以使用：

## 1. quick_start.sh - 主要启动脚本
这是最全面的脚本，提供了完整的功能。

### 使用方法：
```bash
# 查看帮助
./quick_start.sh help

# 初始化环境
./quick_start.sh setup

# 检查系统环境
./quick_start.sh check

# 运行完整流水线
./quick_start.sh full --input data/texts

# 仅运行文本召回
./quick_start.sh retrieval --input data/texts --domain semiconductor

# 批量处理
./quick_start.sh batch --input data/pdfs
```

### 主要功能：
- `setup` - 初始化环境和配置
- `check` - 检查系统环境和依赖
- `full` - 运行完整流水线（召回→清理→生成→质量控制）
- `retrieval` - 仅运行文本召回
- `cleaning` - 仅运行数据清理
- `generation` - 仅运行QA生成
- `quality` - 仅运行质量控制
- `local-models` - 配置和使用本地模型
- `multimodal` - 启用多模态处理
- `batch` - 批量处理多个域
- `test` - 运行测试样例

## 2. batch_process.sh - 批量处理脚本
专门用于批量处理多个文件夹。

### 使用方法：
```bash
# 基本用法
./batch_process.sh data/folder1 data/folder2 data/folder3

# 指定输出目录和领域
./batch_process.sh -o output_dir -d semiconductor data/pdfs

# 并行处理
./batch_process.sh -j 4 data/folder1 data/folder2 data/folder3

# 跳过某些阶段
./batch_process.sh -s -c data/pdfs  # 跳过召回和清理
```

### 选项：
- `-o, --output` - 输出基础目录
- `-d, --domain` - 专业领域
- `-b, --batch-size` - 批处理大小
- `-q, --quality` - 质量阈值
- `-j, --jobs` - 并行任务数
- `-s, --skip-retrieval` - 跳过数据召回
- `-c, --skip-cleaning` - 跳过数据清理

## 3. dataGenerator.sh - 数据生成脚本
较简单的数据生成脚本。

### 使用方法：
```bash
# 使用默认参数
./dataGenerator.sh

# 指定输入输出路径
./dataGenerator.sh /path/to/input /path/to/output
```

## 4. 使用 Python 脚本直接运行

如果你想更精细地控制流程，可以直接使用 Python 脚本：

### 运行完整流水线：
```bash
python3 run_pipeline.py --input data/texts --domain semiconductor
```

### 分步骤运行：
```bash
# 1. 文本召回
python3 text_main_batch_inference.py --txt_path data/texts --storage_folder data/retrieved

# 2. 数据清理
python3 clean_data.py --input_file data/retrieved/total_response.pkl --output_file data/cleaned

# 3. QA生成
python3 text_qa_generation.py --input_file data/cleaned/total_response.json

# 4. 质量检查
python3 TextQA/enhanced_quality_checker.py --input data/qa_results
```

## 推荐使用方式

对于大多数用户，推荐使用 `quick_start.sh`：

1. **首次使用**：
   ```bash
   ./quick_start.sh setup    # 初始化环境
   ./quick_start.sh check    # 检查依赖
   ```

2. **处理文本文件**：
   ```bash
   ./quick_start.sh full --input data/texts --domain semiconductor
   ```

3. **处理PDF文件**（需要PDF支持）：
   ```bash
   ./quick_start.sh full --input data/pdfs --domain semiconductor --enable-multimodal
   ```

4. **批量处理多个领域**：
   ```bash
   ./quick_start.sh batch --input data/texts
   ```

## 注意事项

1. 在运行脚本前，确保：
   - 已安装所有依赖：`pip install -r requirements.txt`
   - 配置文件正确：检查 `config.json`
   - 输入文件放在正确的目录

2. 如果遇到权限问题：
   ```bash
   chmod +x quick_start.sh
   chmod +x batch_process.sh
   ```

3. 查看日志文件以了解处理进度：
   ```bash
   tail -f logs/pipeline.log
   ```