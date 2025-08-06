# 智能QA生成系统 - 使用示例

本文档提供详细的使用示例，帮助您快速上手智能QA生成系统。

## 🚀 快速开始

### 1. 最简单的使用方式

```bash
# 使用交互式快速开始脚本
chmod +x quick_start.sh
./quick_start.sh
```

这将启动一个交互式菜单，引导您完成整个流程。

### 2. 一键完整流水线

```bash
# 处理单个PDF文件夹
python run_pipeline.py \
    --mode full_pipeline \
    --input_path data/semiconductor_papers \
    --output_path data/results \
    --domain semiconductor
```

## 📋 详细使用案例

### 案例1：半导体论文QA生成

假设您有一批关于IGZO材料的研究论文：

```bash
# 第一步：准备数据
mkdir -p data/semiconductor_papers
# 将PDF文件放入该目录

# 第二步：执行完整流水线
python run_pipeline.py \
    --mode full_pipeline \
    --input_path data/semiconductor_papers \
    --output_path data/semiconductor_results \
    --domain semiconductor \
    --batch_size 50 \
    --quality_threshold 0.8 \
    --enhanced_quality \
    --verbose

# 结果将保存在 data/semiconductor_results/pipeline_YYYYMMDD_HHMMSS/ 中
```

**预期输出结构：**
```
data/semiconductor_results/pipeline_20241220_143022/
├── 01_retrieved/          # 数据召回结果
├── 02_cleaned/            # 清理后的数据
├── 03_qa_generated/       # 生成的QA对
├── 04_quality_checked/    # 质量检查后的数据
└── 05_final/             # 最终报告和统计
```

### 案例2：光学领域批量处理

处理多个光学相关的PDF文件夹：

```bash
# 准备多个文件夹
mkdir -p data/optics/{laser_papers,spectroscopy_papers,photonics_papers}

# 批量处理
./batch_process.sh \
    --output data/optics_results \
    --domain optics \
    --batch-size 100 \
    --quality 0.75 \
    --jobs 3 \
    data/optics/laser_papers \
    data/optics/spectroscopy_papers \
    data/optics/photonics_papers
```

### 案例3：分步骤处理（适合大数据量）

当数据量很大时，建议分步骤处理：

```bash
# 步骤1：数据召回
python run_pipeline.py \
    --mode retrieval \
    --input_path data/large_dataset \
    --output_path data/retrieved \
    --selected_task_number 5000 \
    --batch_size 200

# 步骤2：数据清理
python run_pipeline.py \
    --mode cleaning \
    --input_path data/retrieved/total_response.pkl \
    --output_path data/cleaned

# 步骤3：QA生成
python run_pipeline.py \
    --mode qa_generation \
    --input_path data/cleaned/total_response.json \
    --output_path data/qa_results \
    --domain semiconductor \
    --pool_size 150

# 步骤4：质量控制
python run_pipeline.py \
    --mode quality_control \
    --input_path data/qa_results/results_343.json \
    --output_path data/final_results
```

## 🔧 高级配置示例

### 自定义配置文件

创建专门的配置文件 `my_config.json`：

```json
{
  "api": {
    "ark_url": "http://your-api-server:8080/v1",
    "api_key": "your-api-key"
  },
  "processing": {
    "batch_size": 150,
    "quality_threshold": 0.8,
    "selected_task_number": 2000
  },
  "domains": {
    "my_domain": {
      "prompts": [3431, 3432],
      "keywords": ["自定义关键词1", "自定义关键词2"],
      "quality_criteria": "high"
    }
  }
}
```

使用自定义配置：

```bash
python run_pipeline.py \
    --config my_config.json \
    --mode full_pipeline \
    --input_path data/input \
    --output_path data/output \
    --domain my_domain
```

### 性能优化配置

针对高性能服务器的配置：

```bash
python run_pipeline.py \
    --mode full_pipeline \
    --input_path data/input \
    --output_path data/output \
    --batch_size 300 \
    --pool_size 200 \
    --selected_task_number 10000 \
    --domain semiconductor
```

## 🔍 质量控制示例

### 基础质量检查

```bash
# 对现有QA数据进行质量检查
python run_pipeline.py \
    --mode quality_control \
    --input_path data/qa_results/results_343.json \
    --output_path data/quality_checked \
    --verbose
```

### 增强质量检查

```bash
# 使用增强质量检查
python text_qa_generation/text_qa_generation.py \
    --check_task true \
    --enhanced_quality true \
    --quality_threshold 0.8 \
    --file_path data/qa_results/results_343.json
```

## 📊 结果分析示例

### 查看生成统计

```python
import json
import matplotlib.pyplot as plt

# 加载结果数据
with open('data/results/pipeline_20241220_143022/05_final/pipeline_report.json', 'r') as f:
    report = json.load(f)

# 查看统计信息
print("处理统计:")
for stage, stats in report['statistics'].items():
    print(f"- {stage}: {stats['data_count']} 条数据")

# 可视化质量分布（需要安装matplotlib）
# qa_data = json.load(open('data/results/final_qa.json'))
# quality_scores = [item.get('quality_score', 0) for item in qa_data]
# plt.hist(quality_scores, bins=20)
# plt.xlabel('质量分数')
# plt.ylabel('数量')
# plt.title('QA质量分布')
# plt.show()
```

### 导出特定格式

```python
import json

# 加载QA数据
with open('data/results/qa_generated/results_343.json', 'r') as f:
    qa_data = json.load(f)

# 导出为训练格式
training_data = []
for item in qa_data:
    if 'qa_pairs' in item:
        for qa in item['qa_pairs']:
            training_data.append({
                'instruction': qa['question'],
                'output': qa['answer'],
                'reasoning': qa.get('reasoning', ''),
                'domain': 'semiconductor'
            })

# 保存训练数据
with open('data/training_format.json', 'w', encoding='utf-8') as f:
    json.dump(training_data, f, ensure_ascii=False, indent=2)
```

## 🛠️ 故障排除示例

### 内存不足问题

```bash
# 减少批处理大小
python run_pipeline.py \
    --mode full_pipeline \
    --input_path data/input \
    --output_path data/output \
    --batch_size 50 \
    --pool_size 50
```

### API调用失败

```bash
# 检查API连接
curl -I http://0.0.0.0:8080/v1

# 使用试运行模式检查配置
python run_pipeline.py \
    --mode full_pipeline \
    --input_path data/input \
    --output_path data/output \
    --dry_run
```

### 数据格式问题

```bash
# 验证输入数据
python check_file.py --input data/input.json

# 重新清理数据
python run_pipeline.py \
    --mode cleaning \
    --input_path data/raw/total_response.pkl \
    --output_path data/recleaned
```

## 📈 性能监控示例

### 监控处理进度

```bash
# 在另一个终端中监控日志
tail -f logs/pipeline.log

# 监控系统资源
htop
# 或
watch -n 1 'ps aux | grep python'
```

### 性能分析

```python
import json
import time
from datetime import datetime

def analyze_performance(log_file):
    """分析处理性能"""
    with open(log_file, 'r') as f:
        logs = f.readlines()
    
    # 提取时间戳和阶段信息
    stages = []
    for line in logs:
        if '开始' in line or '完成' in line:
            # 解析时间戳和阶段
            # 这里可以添加具体的日志解析逻辑
            pass
    
    return stages

# 使用示例
# performance_data = analyze_performance('logs/pipeline.log')
```

## 🔄 自动化示例

### 定时处理脚本

```bash
#!/bin/bash
# auto_process.sh - 自动化处理脚本

# 设置路径
INPUT_DIR="/data/incoming_pdfs"
OUTPUT_DIR="/data/processed_results"
ARCHIVE_DIR="/data/archive"

# 检查是否有新文件
if [ "$(ls -A $INPUT_DIR)" ]; then
    echo "发现新文件，开始处理..."
    
    # 创建时间戳目录
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    CURRENT_OUTPUT="$OUTPUT_DIR/$TIMESTAMP"
    
    # 执行处理
    python run_pipeline.py \
        --mode full_pipeline \
        --input_path "$INPUT_DIR" \
        --output_path "$CURRENT_OUTPUT" \
        --domain semiconductor \
        --batch_size 100
    
    # 归档原文件
    mv "$INPUT_DIR"/* "$ARCHIVE_DIR/"
    
    echo "处理完成，结果保存在: $CURRENT_OUTPUT"
else
    echo "没有新文件需要处理"
fi
```

### 监控和报警

```python
import smtplib
from email.mime.text import MIMEText
import json
import os

def send_completion_email(report_file):
    """处理完成后发送邮件通知"""
    with open(report_file, 'r') as f:
        report = json.load(f)
    
    # 构造邮件内容
    subject = "QA生成任务完成"
    body = f"""
    任务执行完成！
    
    处理统计：
    {json.dumps(report['statistics'], indent=2, ensure_ascii=False)}
    
    详细报告：{report_file}
    """
    
    # 发送邮件（需要配置SMTP服务器）
    # msg = MIMEText(body)
    # msg['Subject'] = subject
    # ... 邮件发送逻辑
    
    print("任务完成通知已发送")

# 在流水线完成后调用
# send_completion_email('data/results/pipeline_report.json')
```

## 🎯 最佳实践

### 1. 数据准备
- 确保PDF文件质量良好，文字清晰
- 按专业领域分类组织文件
- 定期清理临时文件和缓存

### 2. 参数调优
- 根据硬件性能调整 `batch_size` 和 `pool_size`
- 根据质量要求设置 `quality_threshold`
- 大数据量时使用分步处理

### 3. 质量控制
- 始终启用质量检查
- 定期人工抽检结果质量
- 根据反馈调整prompt和参数

### 4. 性能优化
- 使用SSD存储提高I/O性能
- 合理设置并发数量避免过载
- 定期清理日志和临时文件

### 5. 监控和维护
- 设置日志轮转避免日志文件过大
- 监控系统资源使用情况
- 备份重要的配置和结果文件

---

**需要更多帮助？** 请查看 `README.md` 或使用 `./quick_start.sh` 获取交互式帮助。