# 文件加载问题修复说明

## 问题描述
原始代码在处理文件时存在以下问题：
1. `text_main_batch_inference_enhanced.py` 只能处理 `.txt` 文件
2. 当输入路径是 `data/pdfs` 时，代码无法正确加载PDF文件
3. 文件类型检查是硬编码的，不够灵活

## 修复内容

### 1. 添加PDF支持检测
```python
# Try to import PDF processing capabilities
PDF_SUPPORT = False
try:
    from MultiModal.pdf_processor import PDFProcessor
    from Doubao.Datageneration import parse_pdf
    PDF_SUPPORT = True
    print("PDF processing support available")
except ImportError:
    print("Warning: PDF processing not available")
```

### 2. 修改文件类型检查
在 `process_folders` 函数中：
- 原来：只检查 `.txt` 文件
- 现在：同时检查 `.txt` 和 `.pdf` 文件

```python
# 修改前
if not folder.endswith('.txt'):
    continue

# 修改后
if not (folder.endswith('.txt') or folder.endswith('.pdf')):
    continue
```

### 3. 根据文件类型调用不同的处理函数
```python
if folder.endswith('.txt'):
    tasks = await parse_txt(file_path, index=index)
elif folder.endswith('.pdf') and PDF_SUPPORT:
    tasks = await parse_pdf(file_path, inddex=index)
```

### 4. 改进文件获取逻辑
在 `main` 函数中，现在会自动检测并加载目录中的所有txt和pdf文件：
```python
# 获取目录中的所有txt和pdf文件
all_files = os.listdir(pdf_path)
txt_files = [f for f in all_files if f.endswith('.txt')]
pdf_files = [f for f in all_files if f.endswith('.pdf')]
files = txt_files + pdf_files
```

## 使用说明

### 文件存放位置
根据文件类型，建议将文件放在以下位置：

1. **TXT文件**: `/workspace/new_text/data/texts/`
   - 这是专门存放文本文件的目录
   - 示例文件：`sample_optics.txt`, `sample_semiconductor.txt`

2. **PDF文件**: `/workspace/new_text/data/pdfs/`
   - 这是专门存放PDF文件的目录
   - 注意：需要安装PDF处理依赖才能处理PDF文件

3. **混合文件**: 任何目录都可以
   - 修复后的代码可以自动识别并处理txt和pdf文件

### 运行示例
```bash
# 处理texts目录中的文本文件
python3 run_pipeline.py --input data/texts --domain semiconductor

# 处理pdfs目录中的PDF文件（需要PDF支持）
python3 run_pipeline.py --input data/pdfs --domain semiconductor

# 处理任意目录中的混合文件
python3 run_pipeline.py --input /path/to/mixed/files --domain semiconductor
```

## 注意事项

1. **PDF支持**: 如果看到 "Warning: PDF processing not available"，说明PDF处理模块未正确安装。需要安装相关依赖：
   ```bash
   pip install pymupdf
   ```

2. **文件扩展名**: 文件必须有正确的扩展名（`.txt` 或 `.pdf`），否则会被忽略

3. **错误处理**: 如果文件处理失败，程序会跳过该文件并继续处理其他文件

## 测试验证
使用 `test_file_loading.py` 脚本可以验证文件加载功能：
```bash
python3 test_file_loading.py
```

该脚本会测试不同目录的文件加载情况，并显示处理结果。