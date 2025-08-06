#!/usr/bin/env python3
"""
Only_TXT 完整流水线运行脚本

按照原项目的完整逻辑，运行纯文本问答对生成的完整流水线
"""

import os
import sys
import json
import argparse
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_directories():
    """创建必要的目录结构"""
    directories = [
        "data/input",
        "data/processed", 
        "data/cleaned",
        "data/output",
        "logs",
        "configs",
        "temp"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        logger.info(f"Created directory: {directory}")

def run_preprocessing(input_dir, output_dir):
    """运行数据预处理"""
    logger.info("=== 阶段1：数据预处理 ===")
    
    from preprocessing import batch_preprocess_text_files, validate_preprocessed_data, print_validation_report
    
    # 批量预处理文本文件
    batch_preprocess_text_files(input_dir, output_dir)
    
    # 验证预处理结果
    validation_results = validate_preprocessed_data(output_dir)
    print_validation_report(validation_results)
    
    return validation_results['valid_folders'] > 0

def run_text_analysis(input_dir, output_dir):
    """运行文本分析"""
    logger.info("=== 阶段2：文本内容分析 ===")
    
    from Doubao.Datageneration import parse_text_content, batch_process_text_content
    import asyncio
    
    # 解析文本内容并生成分析任务
    text_tasks = []
    
    for folder_name in os.listdir(input_dir):
        folder_path = os.path.join(input_dir, folder_name)
        if os.path.isdir(folder_path):
            try:
                tasks = asyncio.run(parse_text_content(folder_path))
                text_tasks.extend(tasks)
                logger.info(f"Generated {len(tasks)} analysis tasks for {folder_name}")
            except Exception as e:
                logger.error(f"Error processing {folder_name}: {e}")
    
    if not text_tasks:
        logger.warning("No text analysis tasks generated")
        return False
    
    # 批量处理文本分析任务
    logger.info(f"Starting batch processing of {len(text_tasks)} tasks")
    results = asyncio.run(batch_process_text_content(text_tasks))
    
    # 保存分析结果
    os.makedirs(output_dir, exist_ok=True)
    results_file = os.path.join(output_dir, "text_analysis_results.json")
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    logger.info(f"Text analysis completed. {len(results)} results saved to {results_file}")
    return len(results) > 0

def run_question_generation(text_analysis_results, output_dir, config_name="balanced_config"):
    """运行问题生成"""
    logger.info("=== 阶段3：问题生成 ===")
    
    from question_generator_complete import QuestionGenerator
    from usage_example import create_enhanced_config
    
    # 加载配置
    with open("config_templates.json", "r", encoding='utf-8') as f:
        templates = json.load(f)
    
    config = create_enhanced_config()
    if config_name in templates['config_templates']:
        template = templates['config_templates'][config_name]
        config['question_generation']['question_type_ratios'] = template['question_type_ratios']
        logger.info(f"Using config template: {config_name}")
    
    # 初始化问题生成器
    qg = QuestionGenerator(config)
    
    # 读取文本分析结果
    with open(text_analysis_results, 'r', encoding='utf-8') as f:
        analysis_data = json.load(f)
    
    all_qa_pairs = []
    
    # 为每个文本分析结果生成问答对
    for i, analysis in enumerate(analysis_data):
        if 'text_content' not in analysis:
            continue
            
        try:
            logger.info(f"Generating questions for text {i+1}/{len(analysis_data)}")
            
            # 生成问题
            questions = qg.generate_questions(
                text_content=analysis['text_content'],
                num_questions=5
            )
            
            # 生成答案
            qa_pairs = qg.generate_answers(questions, analysis['text_content'])
            
            # 添加元数据
            for qa in qa_pairs:
                qa['source_analysis'] = analysis.get('section_path', f'analysis_{i}')
                qa['text_content'] = analysis['text_content'][:200] + "..."
            
            all_qa_pairs.extend(qa_pairs)
            
        except Exception as e:
            logger.error(f"Error generating questions for analysis {i}: {e}")
            continue
    
    # 保存问答对
    os.makedirs(output_dir, exist_ok=True)
    qa_file = os.path.join(output_dir, "generated_qa_pairs.json")
    with open(qa_file, 'w', encoding='utf-8') as f:
        json.dump(all_qa_pairs, f, ensure_ascii=False, indent=2)
    
    logger.info(f"Question generation completed. {len(all_qa_pairs)} QA pairs saved to {qa_file}")
    
    # 生成统计报告
    stats = qg.get_generation_statistics()
    stats_file = os.path.join(output_dir, "generation_statistics.json")
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    
    return len(all_qa_pairs) > 0

def run_data_cleaning(input_file, output_dir):
    """运行数据清洗"""
    logger.info("=== 阶段4：数据清洗 ===")
    
    from clean_data import clean_process, validate_cleaned_data
    
    # 由于我们的数据已经是JSON格式，创建一个模拟的pickle文件处理
    # 实际使用中，这里应该处理原始的模型输出
    
    try:
        # 直接处理JSON格式的问答对
        with open(input_file, 'r', encoding='utf-8') as f:
            qa_data = json.load(f)
        
        # 转换为清洗模块期望的格式
        cleaned_data = []
        for qa in qa_data:
            cleaned_item = {
                'question': qa.get('question', ''),
                'answer': qa.get('answer', ''),
                'reasoning': qa.get('reasoning', ''),
                'type': qa.get('type', 'unknown'),
                'difficulty': qa.get('complexity', 'medium'),
                'text_content': qa.get('text_content', ''),
                'source_analysis': qa.get('source_analysis', '')
            }
            cleaned_data.append(cleaned_item)
        
        # 保存清洗后的数据
        os.makedirs(output_dir, exist_ok=True)
        cleaned_file = os.path.join(output_dir, "total_response.json")
        with open(cleaned_file, 'w', encoding='utf-8') as f:
            json.dump(cleaned_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Data cleaning completed. {len(cleaned_data)} items saved to {cleaned_file}")
        
        # 验证清洗后的数据
        if validate_cleaned_data(output_dir):
            logger.info("Data validation passed")
            return True
        else:
            logger.warning("Data validation failed")
            return False
            
    except Exception as e:
        logger.error(f"Error in data cleaning: {e}")
        return False

def run_quality_check(input_file, output_dir):
    """运行质量检查"""
    logger.info("=== 阶段5：质量检查 ===")
    
    from checkInfor.checkQuestion import QALabeler
    
    try:
        # 初始化质量检查器
        qa_labeler = QALabeler(
            activate_stream=True,
            parallel_core=5,  # 减少并发数以避免API限制
            question_key="question",
            answer_key="answer"
        )
        
        # 运行质量检查
        qa_labeler.run_check(input_file, use_text_context=True)
        
        logger.info("Quality check completed")
        return True
        
    except Exception as e:
        logger.error(f"Error in quality check: {e}")
        return False

def run_dataset_generation(input_file, output_dir, format_type="sharegpt"):
    """运行数据集生成"""
    logger.info("=== 阶段6：最终数据集生成 ===")
    
    from generate_dataset import (
        generate_sharegpt_format_text,
        generate_instruction_format_text,
        generate_alpaca_format_text,
        validate_dataset_quality,
        save_quality_report,
        split_dataset
    )
    
    try:
        # 生成数据集
        if format_type == "sharegpt":
            datasets = generate_sharegpt_format_text(
                input_keys="question",
                output_keys="answer", 
                reasoning_keys="reasoning",
                json_file=input_file
            )
        elif format_type == "instruction":
            datasets = generate_instruction_format_text(
                input_keys="question",
                output_keys="answer",
                reasoning_keys="reasoning", 
                json_file=input_file
            )
        elif format_type == "alpaca":
            datasets = generate_alpaca_format_text(
                input_keys="question",
                output_keys="answer",
                reasoning_keys="reasoning",
                json_file=input_file
            )
        
        # 保存数据集
        os.makedirs(output_dir, exist_ok=True)
        dataset_file = os.path.join(output_dir, f"final_dataset_{format_type}.json")
        with open(dataset_file, 'w', encoding='utf-8') as f:
            json.dump(datasets, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Dataset saved to {dataset_file}")
        
        # 分割数据集
        train_data, val_data, test_data = split_dataset(datasets)
        
        train_file = os.path.join(output_dir, f"train_{format_type}.json")
        val_file = os.path.join(output_dir, f"val_{format_type}.json")
        test_file = os.path.join(output_dir, f"test_{format_type}.json")
        
        with open(train_file, 'w', encoding='utf-8') as f:
            json.dump(train_data, f, ensure_ascii=False, indent=2)
        with open(val_file, 'w', encoding='utf-8') as f:
            json.dump(val_data, f, ensure_ascii=False, indent=2)
        with open(test_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Dataset split saved: train({len(train_data) if isinstance(train_data, list) else len(train_data.get('conversations', []))}), val({len(val_data) if isinstance(val_data, list) else len(val_data.get('conversations', []))}), test({len(test_data) if isinstance(test_data, list) else len(test_data.get('conversations', []))})")
        
        # 验证数据集质量
        quality_report = validate_dataset_quality(datasets, format_type)
        save_quality_report(quality_report, dataset_file)
        
        return True
        
    except Exception as e:
        logger.error(f"Error in dataset generation: {e}")
        return False

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="Only_TXT Complete Pipeline")
    parser.add_argument("--input_dir", type=str, default="data/input",
                        help="Input directory containing text files")
    parser.add_argument("--config", type=str, default="balanced_config",
                        choices=["balanced_config", "open_ended_focused", "traditional_qa", "complex_reasoning", "text_analysis_focused"],
                        help="Configuration template to use")
    parser.add_argument("--format", type=str, default="sharegpt",
                        choices=["sharegpt", "instruction", "alpaca"],
                        help="Output dataset format")
    parser.add_argument("--skip_quality_check", action="store_true",
                        help="Skip quality check step (faster but less validation)")
    parser.add_argument("--stages", nargs="+", 
                        choices=["preprocess", "analyze", "generate", "clean", "check", "dataset"],
                        default=["preprocess", "analyze", "generate", "clean", "dataset"],
                        help="Stages to run")
    
    args = parser.parse_args()
    
    # 记录开始时间
    start_time = datetime.now()
    logger.info(f"Starting Only_TXT pipeline at {start_time}")
    logger.info(f"Configuration: {args.config}")
    logger.info(f"Output format: {args.format}")
    logger.info(f"Stages to run: {args.stages}")
    
    # 设置目录
    setup_directories()
    
    # 检查输入目录
    if not os.path.exists(args.input_dir):
        logger.error(f"Input directory {args.input_dir} does not exist")
        return 1
    
    success = True
    current_data_file = None
    
    try:
        # 阶段1：数据预处理
        if "preprocess" in args.stages:
            if not run_preprocessing(args.input_dir, "data/processed"):
                logger.error("Preprocessing failed")
                success = False
            else:
                logger.info("✓ Preprocessing completed successfully")
        
        # 阶段2：文本分析
        if "analyze" in args.stages and success:
            if not run_text_analysis("data/processed", "data/analyzed"):
                logger.error("Text analysis failed")
                success = False
            else:
                current_data_file = "data/analyzed/text_analysis_results.json"
                logger.info("✓ Text analysis completed successfully")
        
        # 阶段3：问题生成
        if "generate" in args.stages and success:
            if current_data_file and os.path.exists(current_data_file):
                if not run_question_generation(current_data_file, "data/generated", args.config):
                    logger.error("Question generation failed")
                    success = False
                else:
                    current_data_file = "data/generated/generated_qa_pairs.json"
                    logger.info("✓ Question generation completed successfully")
            else:
                logger.error("No data file available for question generation")
                success = False
        
        # 阶段4：数据清洗
        if "clean" in args.stages and success:
            if current_data_file and os.path.exists(current_data_file):
                if not run_data_cleaning(current_data_file, "data/cleaned"):
                    logger.error("Data cleaning failed")
                    success = False
                else:
                    current_data_file = "data/cleaned/total_response.json"
                    logger.info("✓ Data cleaning completed successfully")
            else:
                logger.error("No data file available for cleaning")
                success = False
        
        # 阶段5：质量检查（可选）
        if "check" in args.stages and success and not args.skip_quality_check:
            if current_data_file and os.path.exists(current_data_file):
                if not run_quality_check(current_data_file, "data/quality_checked"):
                    logger.warning("Quality check failed, but continuing...")
                else:
                    logger.info("✓ Quality check completed successfully")
            else:
                logger.warning("No data file available for quality check")
        
        # 阶段6：最终数据集生成
        if "dataset" in args.stages and success:
            if current_data_file and os.path.exists(current_data_file):
                if not run_dataset_generation(current_data_file, "data/output", args.format):
                    logger.error("Dataset generation failed")
                    success = False
                else:
                    logger.info("✓ Dataset generation completed successfully")
            else:
                logger.error("No data file available for dataset generation")
                success = False
        
    except KeyboardInterrupt:
        logger.info("Pipeline interrupted by user")
        success = False
    except Exception as e:
        logger.error(f"Unexpected error in pipeline: {e}")
        success = False
    
    # 记录结束时间和结果
    end_time = datetime.now()
    duration = end_time - start_time
    
    if success:
        logger.info(f"🎉 Pipeline completed successfully in {duration}")
        logger.info("Final outputs:")
        logger.info(f"  - Dataset: data/output/final_dataset_{args.format}.json")
        logger.info(f"  - Train set: data/output/train_{args.format}.json")
        logger.info(f"  - Validation set: data/output/val_{args.format}.json") 
        logger.info(f"  - Test set: data/output/test_{args.format}.json")
        return 0
    else:
        logger.error(f"❌ Pipeline failed after {duration}")
        return 1

if __name__ == "__main__":
    sys.exit(main())