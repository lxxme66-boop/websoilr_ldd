"""
Utilis模块 - 纯文本版本

提供文本处理和分析的工具函数
"""

try:
    from .utilis import (
        clean_text_content,
        extract_text_sections,
        generate_sections_range,
        extract_key_terms,
        calculate_text_complexity,
        validate_text_quality,
        format_text_for_processing,
        create_text_metadata,
        save_processed_text
    )
    
    __all__ = [
        'clean_text_content',
        'extract_text_sections',
        'generate_sections_range',
        'extract_key_terms',
        'calculate_text_complexity',
        'validate_text_quality',
        'format_text_for_processing',
        'create_text_metadata',
        'save_processed_text'
    ]
except ImportError as e:
    print(f"Warning: Utilis module import error: {e}")
    __all__ = []