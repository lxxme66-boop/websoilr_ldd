#!/usr/bin/env python3
"""
智能文本QA生成系统 - 统一流水线脚本
整合了数据召回、清理、QA生成和质量控制的完整流程
"""

import os
import sys
import json
import argparse
import asyncio
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Union

# 添加项目路径到系统路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入各模块
from doubao_main_batch_inference import proccess_folders
from clean_data import clean_process
from text_qa_generation.text_qa_generation import main as qa_generation_main
from qwen_argument import main as qwen_argument_main

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/pipeline.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class IntelligentQAPipeline:
    """智能QA生成流水线主类"""
    
    def __init__(self, config_path: str = "config.json"):
        """初始化流水线"""
        self.config = self.load_config(config_path)
        self.setup_directories()
        
    def load_config(self, config_path: str) -> Dict:
        """加载配置文件"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"配置文件 {config_path} 未找到，使用默认配置")
            return self.get_default_config()
    
    def get_default_config(self) -> Dict:
        """获取默认配置"""
        return {
            "api": {
                "ark_url": "http://0.0.0.0:8080/v1",
                "api_key": "ae37bba4-73be-4c22-b1a7-c6b1f5ec3a4b"
            },
            "models": {
                "default_model": "/mnt/storage/models/Skywork/Skywork-R1V3-38B",
                "qa_generator_model": {
                    "path": "/mnt/storage/models/Skywork/Skywork-R1V3-38B",
                    "type": "api"
                }
            },
            "processing": {
                "batch_size": 100,
                "max_concurrent": 20,
                "quality_threshold": 0.7,
                "selected_task_number": 1000
            },
            "domains": {
                "semiconductor": {
                    "prompts": [343, 3431, 3432],
                    "keywords": ["IGZO", "TFT", "OLED", "半导体"],
                    "quality_criteria": "high"
                },
                "optics": {
                    "prompts": [343, 3431, 3432],
                    "keywords": ["光谱", "光学", "激光"],
                    "quality_criteria": "high"
                }
            }
        }
    
    def setup_directories(self):
        """设置必要的目录"""
        directories = [
            "data/input",
            "data/retrieved", 
            "data/cleaned",
            "data/qa_results",
            "data/final_output",
            "logs",
            "temp"
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
            
    async def run_data_retrieval(self, input_path: str, output_path: str, 
                                index: int = 43, **kwargs) -> str:
        """运行数据召回阶段"""
        logger.info("=== 开始数据召回阶段 ===")
        
        try:
            # 设置参数
            folders = os.listdir(input_path) if os.path.isdir(input_path) else [input_path]
            storage_folder = output_path
            temporary_folder = kwargs.get('temporary_folder', 'TEMP')
            maximum_tasks = kwargs.get('batch_size', self.config['processing']['batch_size'])
            selected_task_number = kwargs.get('selected_task_number', 
                                            self.config['processing']['selected_task_number'])
            
            # 执行召回
            results = await proccess_folders(
                folders=folders,
                pdf_path=input_path,
                temporary_folder=temporary_folder,
                index=index,
                maximum_tasks=maximum_tasks,
                selected_task_number=selected_task_number
            )
            
            # 保存结果
            output_file = os.path.join(storage_folder, "total_response.pkl")
            with open(output_file, "wb") as f:
                import pickle
                pickle.dump(results, f)
                
            logger.info(f"数据召回完成，共处理 {len(results)} 条数据")
            logger.info(f"结果保存至: {output_file}")
            
            return output_file
            
        except Exception as e:
            logger.error(f"数据召回阶段出错: {str(e)}")
            raise
    
    def run_data_cleaning(self, input_file: str, output_path: str, **kwargs) -> str:
        """运行数据清理阶段"""
        logger.info("=== 开始数据清理阶段 ===")
        
        try:
            copy_parsed_pdf = kwargs.get('copy_parsed_pdf', False)
            
            # 执行清理
            clean_process(
                input_file=input_file,
                output_file=output_path,
                copy_parsed_pdf=copy_parsed_pdf
            )
            
            cleaned_file = os.path.join(output_path, "total_response.json")
            logger.info(f"数据清理完成，结果保存至: {cleaned_file}")
            
            return cleaned_file
            
        except Exception as e:
            logger.error(f"数据清理阶段出错: {str(e)}")
            raise
    
    async def run_qa_generation(self, input_file: str, output_path: str, 
                               index: int = 343, **kwargs) -> str:
        """运行QA生成阶段"""
        logger.info("=== 开始QA生成阶段 ===")
        
        try:
            # 构造参数
            args_dict = {
                'index': index,
                'file_path': input_file,
                'pool_size': kwargs.get('pool_size', self.config['processing']['batch_size']),
                'output_file': output_path,
                'ark_url': self.config['api']['ark_url'],
                'api_key': self.config['api']['api_key'],
                'model': self.config['models']['default_model'],
                'check_task': False,
                'enhanced_quality': kwargs.get('enhanced_quality', True),
                'quality_threshold': kwargs.get('quality_threshold', 
                                              self.config['processing']['quality_threshold']),
                'user_stream': False
            }
            
            # 创建参数命名空间
            class Args:
                def __init__(self, **kwargs):
                    for key, value in kwargs.items():
                        setattr(self, key, value)
            
            args = Args(**args_dict)
            
            # 执行QA生成（需要修改原函数以支持直接调用）
            results = await self.generate_qa_with_args(args)
            
            output_file = os.path.join(output_path, f"results_{index}.json")
            logger.info(f"QA生成完成，共生成 {len(results)} 个QA对")
            logger.info(f"结果保存至: {output_file}")
            
            return output_file
            
        except Exception as e:
            logger.error(f"QA生成阶段出错: {str(e)}")
            raise
    
    async def generate_qa_with_args(self, args) -> List[Dict]:
        """使用参数生成QA（适配原有函数）"""
        # 这里需要导入并调用text_qa_generation中的核心函数
        from text_qa_generation.TextQA.dataargument import get_total_responses
        
        results = await get_total_responses(
            index=args.index,
            file_path=args.file_path,
            pool_size=args.pool_size,
            stream=args.user_stream
        )
        
        # 保存结果
        output_file = os.path.join(args.output_file, f"results_{args.index}.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=4)
            
        return results
    
    async def run_quality_control(self, input_file: str, output_path: str, **kwargs) -> str:
        """运行质量控制阶段"""
        logger.info("=== 开始质量控制阶段 ===")
        
        try:
            from text_qa_generation.TextQA.dataargument import check_data_quality
            
            # 执行质量检查
            await check_data_quality(
                ark_url=self.config['api']['ark_url'],
                api_key=self.config['api']['api_key'],
                model=self.config['models']['default_model'],
                output_file=input_file,
                check_indexes=kwargs.get('check_indexes', (40, 37, 38)),
                pool_size=kwargs.get('pool_size', self.config['processing']['batch_size']),
                check_times=kwargs.get('check_times', 9),
                stream=False
            )
            
            quality_file = input_file.replace('.json', '_quality_checked.json')
            logger.info(f"质量控制完成，结果保存至: {quality_file}")
            
            return quality_file
            
        except Exception as e:
            logger.error(f"质量控制阶段出错: {str(e)}")
            raise
    
    async def run_full_pipeline(self, input_path: str, output_path: str, 
                               domain: str = "semiconductor", **kwargs) -> Dict[str, str]:
        """运行完整流水线"""
        logger.info("=== 开始完整QA生成流水线 ===")
        logger.info(f"输入路径: {input_path}")
        logger.info(f"输出路径: {output_path}")
        logger.info(f"专业领域: {domain}")
        
        # 创建输出目录结构
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        pipeline_output = os.path.join(output_path, f"pipeline_{timestamp}")
        
        directories = {
            'retrieved': os.path.join(pipeline_output, "01_retrieved"),
            'cleaned': os.path.join(pipeline_output, "02_cleaned"), 
            'qa_generated': os.path.join(pipeline_output, "03_qa_generated"),
            'quality_checked': os.path.join(pipeline_output, "04_quality_checked"),
            'final': os.path.join(pipeline_output, "05_final")
        }
        
        for directory in directories.values():
            Path(directory).mkdir(parents=True, exist_ok=True)
        
        results = {}
        
        try:
            # 阶段1: 数据召回
            if kwargs.get('skip_retrieval', False):
                logger.info("跳过数据召回阶段")
                retrieved_file = kwargs.get('retrieved_file')
            else:
                retrieved_file = await self.run_data_retrieval(
                    input_path=input_path,
                    output_path=directories['retrieved'],
                    index=kwargs.get('retrieval_index', 43),
                    **kwargs
                )
            results['retrieved'] = retrieved_file
            
            # 阶段2: 数据清理
            cleaned_file = self.run_data_cleaning(
                input_file=retrieved_file,
                output_path=directories['cleaned'],
                **kwargs
            )
            results['cleaned'] = cleaned_file
            
            # 阶段3: QA生成
            domain_config = self.config['domains'].get(domain, {})
            qa_index = domain_config.get('prompts', [343])[0]
            
            qa_file = await self.run_qa_generation(
                input_file=cleaned_file,
                output_path=directories['qa_generated'],
                index=qa_index,
                **kwargs
            )
            results['qa_generated'] = qa_file
            
            # 阶段4: 质量控制
            if kwargs.get('enable_quality_control', True):
                quality_file = await self.run_quality_control(
                    input_file=qa_file,
                    output_path=directories['quality_checked'],
                    **kwargs
                )
                results['quality_checked'] = quality_file
            else:
                results['quality_checked'] = qa_file
            
            # 生成最终报告
            final_report = self.generate_pipeline_report(results, directories['final'])
            results['final_report'] = final_report
            
            logger.info("=== 完整流水线执行成功 ===")
            logger.info(f"最终结果保存在: {pipeline_output}")
            
            return results
            
        except Exception as e:
            logger.error(f"流水线执行失败: {str(e)}")
            raise
    
    def generate_pipeline_report(self, results: Dict[str, str], output_dir: str) -> str:
        """生成流水线执行报告"""
        report = {
            "pipeline_execution": {
                "timestamp": datetime.now().isoformat(),
                "status": "completed",
                "stages": {}
            },
            "file_locations": results,
            "statistics": {}
        }
        
        # 统计各阶段数据量
        for stage, file_path in results.items():
            if stage == 'final_report':
                continue
                
            try:
                if file_path.endswith('.json'):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            count = len(data)
                        else:
                            count = 1
                elif file_path.endswith('.pkl'):
                    import pickle
                    with open(file_path, 'rb') as f:
                        data = pickle.load(f)
                        count = len(data) if isinstance(data, list) else 1
                else:
                    count = "unknown"
                    
                report["statistics"][stage] = {
                    "file_path": file_path,
                    "data_count": count,
                    "file_size": os.path.getsize(file_path) if os.path.exists(file_path) else 0
                }
            except Exception as e:
                logger.warning(f"无法统计 {stage} 阶段数据: {str(e)}")
                report["statistics"][stage] = {
                    "file_path": file_path,
                    "data_count": "error",
                    "error": str(e)
                }
        
        # 保存报告
        report_file = os.path.join(output_dir, "pipeline_report.json")
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=4)
        
        # 生成简化版报告
        summary_file = os.path.join(output_dir, "pipeline_summary.txt")
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write("智能QA生成流水线执行报告\n")
            f.write("=" * 40 + "\n\n")
            f.write(f"执行时间: {report['pipeline_execution']['timestamp']}\n")
            f.write(f"执行状态: {report['pipeline_execution']['status']}\n\n")
            
            f.write("各阶段统计:\n")
            f.write("-" * 20 + "\n")
            for stage, stats in report["statistics"].items():
                f.write(f"{stage}: {stats.get('data_count', 'unknown')} 条数据\n")
            
            f.write(f"\n详细报告: {report_file}\n")
        
        logger.info(f"流水线报告已生成: {report_file}")
        return report_file

async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="智能文本QA生成系统 - 统一流水线")
    
    # 基础参数
    parser.add_argument("--mode", type=str, default="full_pipeline",
                      choices=["full_pipeline", "retrieval", "cleaning", "qa_generation", "quality_control"],
                      help="运行模式")
    parser.add_argument("--input_path", type=str, required=True, help="输入路径")
    parser.add_argument("--output_path", type=str, required=True, help="输出路径")
    parser.add_argument("--config", type=str, default="config.json", help="配置文件路径")
    
    # 领域和索引参数
    parser.add_argument("--domain", type=str, default="semiconductor",
                      choices=["semiconductor", "optics"], help="专业领域")
    parser.add_argument("--index", type=int, default=None, help="Prompt索引")
    parser.add_argument("--retrieval_index", type=int, default=43, help="召回阶段索引")
    
    # 处理参数
    parser.add_argument("--batch_size", type=int, default=100, help="批处理大小")
    parser.add_argument("--pool_size", type=int, default=100, help="并发池大小")
    parser.add_argument("--selected_task_number", type=int, default=1000, help="选择处理的任务数")
    parser.add_argument("--quality_threshold", type=float, default=0.7, help="质量阈值")
    
    # 控制参数
    parser.add_argument("--skip_retrieval", action="store_true", help="跳过数据召回")
    parser.add_argument("--retrieved_file", type=str, help="已召回的数据文件")
    parser.add_argument("--enable_quality_control", action="store_true", default=True, 
                      help="启用质量控制")
    parser.add_argument("--enhanced_quality", action="store_true", default=True,
                      help="使用增强质量检查")
    parser.add_argument("--copy_parsed_pdf", action="store_true", help="复制解析的PDF")
    
    # 调试参数
    parser.add_argument("--verbose", action="store_true", help="详细输出")
    parser.add_argument("--dry_run", action="store_true", help="试运行（不执行实际处理）")
    
    args = parser.parse_args()
    
    # 设置日志级别
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # 初始化流水线
    pipeline = IntelligentQAPipeline(args.config)
    
    if args.dry_run:
        logger.info("试运行模式 - 不执行实际处理")
        logger.info(f"配置: {json.dumps(pipeline.config, indent=2, ensure_ascii=False)}")
        return
    
    # 执行相应模式
    try:
        if args.mode == "full_pipeline":
            results = await pipeline.run_full_pipeline(
                input_path=args.input_path,
                output_path=args.output_path,
                domain=args.domain,
                batch_size=args.batch_size,
                pool_size=args.pool_size,
                selected_task_number=args.selected_task_number,
                quality_threshold=args.quality_threshold,
                skip_retrieval=args.skip_retrieval,
                retrieved_file=args.retrieved_file,
                enable_quality_control=args.enable_quality_control,
                enhanced_quality=args.enhanced_quality,
                copy_parsed_pdf=args.copy_parsed_pdf,
                retrieval_index=args.retrieval_index
            )
            print(f"\n✅ 流水线执行成功！")
            print(f"📊 最终报告: {results.get('final_report')}")
            
        elif args.mode == "retrieval":
            result_file = await pipeline.run_data_retrieval(
                input_path=args.input_path,
                output_path=args.output_path,
                index=args.retrieval_index,
                batch_size=args.batch_size,
                selected_task_number=args.selected_task_number
            )
            print(f"\n✅ 数据召回完成！结果文件: {result_file}")
            
        elif args.mode == "cleaning":
            result_file = pipeline.run_data_cleaning(
                input_file=args.input_path,
                output_path=args.output_path,
                copy_parsed_pdf=args.copy_parsed_pdf
            )
            print(f"\n✅ 数据清理完成！结果文件: {result_file}")
            
        elif args.mode == "qa_generation":
            qa_index = args.index or pipeline.config['domains'][args.domain]['prompts'][0]
            result_file = await pipeline.run_qa_generation(
                input_file=args.input_path,
                output_path=args.output_path,
                index=qa_index,
                pool_size=args.pool_size,
                enhanced_quality=args.enhanced_quality,
                quality_threshold=args.quality_threshold
            )
            print(f"\n✅ QA生成完成！结果文件: {result_file}")
            
        elif args.mode == "quality_control":
            result_file = await pipeline.run_quality_control(
                input_file=args.input_path,
                output_path=args.output_path,
                pool_size=args.pool_size
            )
            print(f"\n✅ 质量控制完成！结果文件: {result_file}")
            
    except Exception as e:
        logger.error(f"执行失败: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())