"""
Only_TXT - 纯文本问答对处理项目

基于成功的多模态问答对生成案例，完全按照其逻辑和处理流程，
创建的纯文本版本问答对处理系统。

主要模块：
- question_generator_complete: 核心问题生成器
- batch_inference: 批量推理处理
- clean_data: 数据清洗和格式化
- generate_dataset: 数据集生成
- Doubao: Doubao模型集成
- Qwen: Qwen模型集成
- WizardLM: WizardLM模型集成
- Utilis: 工具函数
- checkInfor: 质量检查模块
"""

__version__ = "1.0.0"
__author__ = "AI Assistant"
__description__ = "纯文本问答对处理系统"

# 导入主要类和函数
try:
    from .question_generator_complete import QuestionGenerator
    from .batch_inference import run_text_batch_processing
    from .clean_data import clean_process
    from .generate_dataset import generate_sharegpt_format_text
    from .checkInfor.checkQuestion import QALabeler, TextQualityAnalyzer
    
    __all__ = [
        'QuestionGenerator',
        'run_text_batch_processing', 
        'clean_process',
        'generate_sharegpt_format_text',
        'QALabeler',
        'TextQualityAnalyzer'
    ]
except ImportError as e:
    # 如果导入失败，提供友好的错误信息
    print(f"Warning: Some modules could not be imported: {e}")
    __all__ = []