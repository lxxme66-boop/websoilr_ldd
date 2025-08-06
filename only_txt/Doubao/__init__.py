"""
Doubao模块 - 纯文本版本

提供Doubao模型的文本分析和问答生成功能
"""

try:
    from .Datageneration import (
        parse_text_content,
        input_TextDoubao, 
        batch_process_text_content,
        extract_parsing_text_result
    )
    from .prompts_conf import system_prompt, user_prompts
    
    __all__ = [
        'parse_text_content',
        'input_TextDoubao',
        'batch_process_text_content', 
        'extract_parsing_text_result',
        'system_prompt',
        'user_prompts'
    ]
except ImportError as e:
    print(f"Warning: Doubao module import error: {e}")
    __all__ = []