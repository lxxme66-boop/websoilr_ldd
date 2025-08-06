# 🚀 Text QA Generation 快速启动指南

## v2.0 增强质量检查版本

欢迎使用 Text QA Generation v2.0！本版本引入了强大的增强质量检查系统，采用双阶段验证机制，显著提升QA数据质量。

## 📋 前置条件

### 系统要求
- Python 3.7+
- 8GB+ 内存（推荐16GB+）
- 可访问的API服务或本地模型

### 依赖安装
```bash
pip install -r requirements.txt
```

## 🎯 5分钟快速体验

### 1. 测试系统环境
```bash
# 验证系统设置
bash run_pipeline.sh --test
```

### 2. 准备示例数据
```bash
# 系统已包含示例文件，直接使用
ls data/input_texts/sample_igzo_tft.txt
```

### 3. 运行完整流程
```bash
# 一键运行（推荐）
bash run_pipeline.sh

# 当询问质量检查时，选择 3（增强质量检查）
```

### 4. 查看结果
```bash
# 查看生成的文件
ls data/output/results_343*

# 主要输出文件：
# - results_343.json              # 原始QA对
# - results_343_high_quality.json # 高质量QA对
# - results_343_quality_report.json # 质量分析报告
```

## 🔧 配置说明

### 基础配置 (`config.json`)
```json
{
    "quality_control": {
        "enhanced_quality_check": {
            "enabled": true,
            "parallel_core": 10,        // 并发数：本地2-5，服务器10-20
            "quality_threshold": 0.7,   // 质量阈值：0.6-0.8
            "verification_method": "dual_stage"
        }
    }
}
```

### 环境变量配置
```bash
# API配置
export ARK_API_KEY="your-api-key"
export ARK_URL="http://your-api-url:8080/v1"
export MODEL_PATH="/path/to/your/model"

# 性能配置
export BATCH_SIZE=50          # 批处理大小
export POOL_SIZE=100         # 并发池大小
export QUALITY_THRESHOLD=0.7 # 质量阈值
export PARALLEL_CORES=10     # 并发核心数
```

## 📊 增强质量检查详解

### 双阶段验证流程
```
输入QA对 → 模型独立回答 → 比较验证 → 质量标签 → 详细报告
```

### 质量评估维度
- ✅ **内容准确性**：技术事实和数值的准确性
- ✅ **逻辑完整性**：推理链条和因果关系
- ✅ **专业深度**：技术解释的专业程度
- ✅ **实用价值**：解决方案的可行性

### 输出文件说明
| 文件 | 说明 | 用途 |
|------|------|------|
| `*_detailed.json` | 详细验证信息 | 调试和分析 |
| `*_high_quality.json` | 高质量数据 | 直接使用 |
| `*_quality_report.json` | 质量统计报告 | 质量评估 |
| `*_results.csv` | CSV格式数据 | Excel分析 |

## 🎮 使用场景

### 场景1：快速生成高质量数据
```bash
# 使用默认高质量阈值
QUALITY_THRESHOLD=0.8 bash run_pipeline.sh
```

### 场景2：大批量处理
```bash
# 提高并发数和批处理大小
BATCH_SIZE=100 POOL_SIZE=200 PARALLEL_CORES=20 bash run_pipeline.sh
```

### 场景3：仅运行质量检查
```bash
# 对已有数据运行质量检查
python text_qa_generation.py \
    --file_path "data/output/results_343.json" \
    --check_task True \
    --enhanced_quality True \
    --quality_threshold 0.7
```

### 场景4：Python API调用
```python
import asyncio
from TextQA.enhanced_quality_checker import TextQAQualityIntegrator

async def run_quality_check():
    # 加载配置
    with open('config.json', 'r') as f:
        config = json.load(f)
    
    # 初始化
    integrator = TextQAQualityIntegrator(config)
    
    # 执行检查
    report = await integrator.enhanced_quality_check(
        qa_file_path="data/output/results_343.json",
        output_dir="data/output",
        quality_threshold=0.7
    )
    
    print(f"通过率: {report['pass_rate']:.2%}")
    return report

# 运行
report = asyncio.run(run_quality_check())
```

## 📈 性能优化指南

### 硬件配置建议
| 环境类型 | CPU核心 | 内存 | 并发数 | 批处理大小 |
|----------|---------|------|--------|------------|
| 本地开发 | 4-8核 | 8GB | 2-5 | 20-50 |
| 服务器 | 8-16核 | 16GB+ | 10-20 | 50-100 |
| 高性能集群 | 16+核 | 32GB+ | 20+ | 100+ |

### 质量阈值建议
| 应用场景 | 阈值 | 说明 |
|----------|------|------|
| 训练数据 | 0.8-0.9 | 严格质量要求 |
| 初步筛选 | 0.6-0.7 | 平衡质量和数量 |
| 数据清洗 | 0.4-0.5 | 宽松筛选 |

### 常见性能问题解决
```bash
# 内存不足
BATCH_SIZE=20 PARALLEL_CORES=5 bash run_pipeline.sh

# API限流
BATCH_SIZE=10 POOL_SIZE=20 bash run_pipeline.sh

# 网络不稳定
# 在config.json中设置较低的并发数
```

## 🔍 质量报告解读

### 示例质量报告
```json
{
    "total_qa_pairs": 100,
    "passed_qa_pairs": 85,
    "pass_rate": 0.85,           // 85%通过率
    "quality_threshold": 0.7,
    "meets_threshold": true,     // 达到质量要求
    "statistics": {
        "avg_question_length": 45.2,
        "avg_answer_length": 156.8,
        "question_types_distribution": {
            "factual": 25,       // 事实型25个
            "reasoning": 35,     // 推理型35个
            "comparison": 15,    // 比较型15个
            "open_ended": 10     // 开放型10个
        }
    }
}
```

### 质量指标含义
- **通过率 > 80%**：优秀质量
- **通过率 60-80%**：良好质量
- **通过率 < 60%**：需要优化

## 🐛 常见问题解决

### 问题1：API连接失败
```bash
# 检查API配置
curl -X POST "$ARK_URL/chat/completions" \
  -H "Authorization: Bearer $ARK_API_KEY" \
  -H "Content-Type: application/json"
```

### 问题2：模型路径错误
```bash
# 验证模型路径
ls "$MODEL_PATH"
```

### 问题3：内存不足
```bash
# 降低并发和批处理大小
BATCH_SIZE=10 PARALLEL_CORES=2 bash run_pipeline.sh
```

### 问题4：质量检查失败
```bash
# 运行专项测试
python test_enhanced_quality.py
```

## 📚 进阶使用

### 自定义质量评估标准
编辑 `TextQA/enhanced_quality_checker.py` 中的评估逻辑：
```python
# 添加领域特定的评估规则
def custom_quality_assessment(self, question, answer, model_answer):
    # 自定义评估逻辑
    pass
```

### 批量文件处理
```bash
# 处理多个目录
for dir in dir1 dir2 dir3; do
    INPUT_DIR="data/$dir" bash run_pipeline.sh
done
```

### 集成到CI/CD
```yaml
# .github/workflows/qa-generation.yml
name: QA Generation
on: [push]
jobs:
  generate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run QA Generation
        run: |
          pip install -r requirements.txt
          bash run_pipeline.sh --test
          QUALITY_THRESHOLD=0.8 bash run_pipeline.sh
```

## 🎉 成功案例

### 半导体技术QA生成
- **数据量**：1000个QA对
- **质量通过率**：87%
- **处理时间**：30分钟
- **应用场景**：技术培训数据集

### 显示技术知识库构建
- **数据量**：2000个QA对
- **质量通过率**：82%
- **处理时间**：45分钟
- **应用场景**：智能客服系统

## 🔗 相关资源

- [详细文档](README.md)
- [增强质量检查说明](ENHANCED_QUALITY_CHECK.md)
- [集成总结](INTEGRATION_SUMMARY.md)
- [测试指南](test_enhanced_quality.py)

## 💬 获得帮助

1. **查看帮助**：`bash run_pipeline.sh --help`
2. **运行测试**：`python test_enhanced_quality.py`
3. **检查配置**：`bash run_pipeline.sh --test`

---

🎊 **恭喜！** 您已掌握 Text QA Generation v2.0 的基本使用方法。现在可以开始生成高质量的问答数据了！