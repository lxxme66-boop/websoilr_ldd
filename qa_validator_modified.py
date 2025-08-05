#!/usr/bin/env python3
"""
基于本地文档和本地模型的KG问答对验证器
- 从文件夹批量加载txt文档
- 使用本地部署的模型
- 包含进度条显示
"""

import asyncio
import json
import os
import glob
from typing import List, Dict, Tuple
import logging
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
from tqdm import tqdm
import time
from datetime import datetime
import sys  # 新增：确保输出刷新

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LocalKGQAValidator:
    """使用本地模型的问答对验证器"""
    
    def __init__(self, docs_folder: str, model_path: str, config: dict):
        self.config = config
        
        # 确保输出刷新
        sys.stdout.flush()
        
        # 1. 加载文件夹中的所有txt文档
        print("\n正在加载文档...")
        self.reference_content = self._load_docs_from_folder(docs_folder)
        self.doc_chunks = self._chunk_documents(self.reference_content)
        logger.info(f"从 {docs_folder} 加载了 {len(self.reference_content)} 个文档")
        
        # 2. 加载本地模型
        print("\n正在加载模型...")
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        print(f"使用设备: {self.device}")
        self._load_local_model(model_path)
        
        # 领域知识库
        self.domain_knowledge = {
            'semiconductor': ['光刻', '晶圆', '良率', '缺陷', '涂布', '曝光', '显影'],
            'display': ['TFT-LCD', '像素', '显示', '液晶', '背光'],
            'manufacturing': ['生产线', '工艺', '参数', '设备', '质量控制']
        }
    
    def _load_docs_from_folder(self, folder_path: str) -> Dict[str, str]:
        """从文件夹加载所有txt文档"""
        docs = {}
        
        # 支持多种文本文件格式
        patterns = ['*.txt', '*.TXT', '*.md', '*.MD']
        all_files = []
        
        for pattern in patterns:
            files = glob.glob(os.path.join(folder_path, pattern))
            all_files.extend(files)
        
        # 递归查找子文件夹（可选）
        if self.config.get('recursive', False):
            for pattern in patterns:
                files = glob.glob(os.path.join(folder_path, '**', pattern), recursive=True)
                all_files.extend(files)
        
        # 去重
        all_files = list(set(all_files))
        
        if not all_files:
            logger.warning(f"未在 {folder_path} 找到任何文档")
            return docs
        
        # 使用进度条加载文档 - 改进的进度条设置
        with tqdm(total=len(all_files), 
                  desc="加载文档", 
                  unit="文件", 
                  ncols=120,
                  position=0,
                  leave=True) as pbar:
            for file_path in all_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        # 使用相对路径作为文档名
                        doc_name = os.path.relpath(file_path, folder_path)
                        docs[doc_name] = content
                        pbar.set_postfix({'当前': os.path.basename(file_path)[:30]})
                except Exception as e:
                    logger.error(f"加载文档失败 {file_path}: {str(e)}")
                finally:
                    pbar.update(1)
        
        return docs
    
    def _load_local_model(self, model_path: str):
        """加载本地模型"""
        logger.info(f"加载本地模型: {model_path}")
        
        try:
            # 加载tokenizer和模型 - 改进的进度条设置
            with tqdm(total=2, 
                      desc="加载模型组件", 
                      unit="组件", 
                      ncols=120,
                      position=0,
                      leave=True) as pbar:
                # 加载tokenizer
                self.tokenizer = AutoTokenizer.from_pretrained(
                    model_path,
                    trust_remote_code=True,
                    local_files_only=True  # 只使用本地文件
                )
                pbar.update(1)
                pbar.set_postfix({'状态': 'tokenizer加载完成'})
                
                # 加载模型
                self.model = AutoModelForCausalLM.from_pretrained(
                    model_path,
                    torch_dtype=torch.float16,
                    device_map="auto",
                    trust_remote_code=True,
                )
                pbar.update(1)
                pbar.set_postfix({'状态': '模型加载完成'})
            
            self.model.eval()
            logger.info("模型加载成功")
            
        except Exception as e:
            logger.error(f"模型加载失败: {str(e)}")
            raise
    
    async def validate_qa_pairs(self, qa_pairs: List[Dict]) -> Tuple[List[Dict], Dict]:
        """验证问答对（使用本地模型）"""
        validated_results = []
        statistics = {
            'total': len(qa_pairs),
            'passed': 0,
            'failed': 0,  # 修复：添加failed键
            'failed_by_reason': {
                'common_sense': 0,
                'principle': 0,
                'incomplete_question': 0
            },
            'processing_time': 0
        }
        
        start_time = time.time()
        
        # 由于是本地模型，可以适当增加批次大小
        batch_size = self.config.get('batch_size', 10)
        
        print(f"\n开始验证 {len(qa_pairs)} 个问答对...")
        sys.stdout.flush()  # 确保输出
        
        # 创建总进度条 - 这里是你要找的位置！
        with tqdm(total=len(qa_pairs), 
                  desc="验证进度", 
                  unit="QA", 
                  ncols=120,  # 设置宽度
                  position=0,  # 固定位置
                  leave=True) as pbar:  # 完成后保留
            
            for i in range(0, len(qa_pairs), batch_size):
                batch = qa_pairs[i:i+batch_size]
                batch_start = time.time()
                
                # 处理每个QA对
                for j, qa in enumerate(batch):
                    try:
                        # 更新进度条描述
                        pbar.set_description(f"验证进度 [批次 {i//batch_size + 1}/{(len(qa_pairs)-1)//batch_size + 1}]")
                        
                        validated_qa = await self._validate_single_qa(qa)
                        # 【这里是记录每条QA验证结果的最佳位置】
                        # 你可以打印日志
                        logger.info(f"QA ID: {validated_qa.get('id', i+j)} 验证结果: {validated_qa['validation']}")
                        
                        # 或者实时写入文件（追加写），示例如下：
                        with open('qa_validation_log.jsonl', 'a', encoding='utf-8') as logf:
                            logf.write(json.dumps({
                                'id': validated_qa.get('id', i+j),
                                'question': validated_qa.get('question', '')[:100],
                                'validation': validated_qa['validation']
                            }, ensure_ascii=False) + '\n')
                        
                        if self._is_qa_valid(validated_qa):
                            validated_results.append(validated_qa)
                            statistics['passed'] += 1
                        else:
                            statistics['failed'] += 1
                            self._update_failure_stats(validated_qa, statistics)
                        
                        # 更新进度条
                        pbar.update(1)
                        pbar.set_postfix({
                            '通过': statistics['passed'],
                            '失败': statistics['failed'],
                            '通过率': f"{statistics['passed']/(i+j+1)*100:.1f}%"
                        })
                        
                    except Exception as e:
                        logger.error(f"验证QA时出错: {str(e)}")
                        statistics['failed'] += 1
                        statistics['failed_by_reason']['incomplete_question'] += 1
                        pbar.update(1)
                
                # 批次处理时间
                batch_time = time.time() - batch_start
                if len(batch) > 0:
                    avg_time = batch_time / len(batch)
                    remaining_items = len(qa_pairs) - (i + len(batch))
                    eta = remaining_items * avg_time
                    
                    # 更新ETA信息
                    if remaining_items > 0:
                        pbar.set_postfix({
                            '通过': statistics['passed'],
                            '失败': statistics['failed'],
                            '通过率': f"{statistics['passed']/(i+len(batch))*100:.1f}%",
                            'ETA': f"{eta/60:.1f}分钟"
                        })
        
        statistics['processing_time'] = time.time() - start_time
        return validated_results, statistics
    
    async def _validate_single_qa(self, qa_pair: Dict) -> Dict:
        """验证单个问答对（使用本地模型）"""
        # 1. 提取关键信息
        key_info = self._extract_key_information(qa_pair)
        
        # 2. 找到相关文档
        relevant_chunks = self._find_relevant_chunks(qa_pair, key_info)
        
        # 3. 使用本地模型进行验证
        validation_result = await self._validate_with_local_model(
            qa_pair, relevant_chunks, key_info
        )
        
        # 4. 更新结果
        qa_pair['validation'] = validation_result
        qa_pair['relevant_docs'] = [chunk['doc'] for chunk in relevant_chunks]
        qa_pair['key_info'] = key_info
        
        return qa_pair
    
    async def _validate_with_local_model(self, qa_pair: Dict, relevant_chunks: List[Dict], 
                                       key_info: Dict) -> Dict:
        """使用本地模型进行验证"""
        # 构建验证prompt
        prompt = self._create_validation_prompt(qa_pair, relevant_chunks, key_info)
        
        try:
            # 使用本地模型生成
            inputs = self.tokenizer(prompt, return_tensors="pt", truncation=True, 
                                  max_length=2048).to(self.device)
            
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=500,
                    temperature=0.1,  # 低温度确保稳定
                    do_sample=True,
                    top_p=0.8,
                    pad_token_id=self.tokenizer.eos_token_id
                )
            
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            # 去除prompt部分
            response = response[len(prompt):].strip()
            
            return self._parse_validation_response(response)
            
        except Exception as e:
            logger.error(f"本地模型验证失败: {str(e)}")
            return {
                'common_sense': False,
                'principle_correct': False,
                'overall_valid': False,
                'details': {'error': str(e)}
            }
    
    def _create_validation_prompt(self, qa_pair: Dict, relevant_chunks: List[Dict], 
                                key_info: Dict) -> str:
        """创建验证prompt"""
        # 格式化文档内容
        doc_content = ""
        if relevant_chunks:
            doc_content = "\n---\n".join([
                f"[文档: {chunk['doc']}]\n{chunk['content'][:500]}..."
                for chunk in relevant_chunks[:3]
            ])
        else:
            doc_content = "未找到相关文档内容"
        
        # 格式化关键信息
        key_info_str = f"""
关键实体: {', '.join(key_info['entities'][:10])}
技术术语: {', '.join(key_info['technical_terms'][:10])}
领域: {key_info['domain'] or '未识别'}
"""
        
        prompt = f"""你是技术文档验证专家。请基于参考文档验证以下问答对。

参考文档：
{doc_content}

{key_info_str}

待验证问答对：
问题: {qa_pair['question'][:500]}
答案: {qa_pair['answer'][:500]}

请从两个方面验证：
1. 常识验证：问题和答案是否符合技术常识？
2. 原理验证：问题和答案是否符合科学原理？

输出格式：
常识验证: 通过/不通过
理由: xxx

原理验证: 通过/不通过
理由: xxx

总体判断: 通过/不通过（若常识和原理均通过，则判定为通过）
"""
        
        return prompt
    
    def _extract_key_information(self, qa_pair: Dict) -> Dict:
        """提取关键信息"""
        key_info = {
            'entities': [],
            'technical_terms': [],
            'domain': None
        }
        
        # 从子图提取实体
        if 'subgraph' in qa_pair:
            nodes = qa_pair['subgraph'].get('nodes', [])
            key_info['entities'] = [node['id'] for node in nodes]
        
        # 从问题和答案提取技术术语
        question = qa_pair.get('question', '')
        answer = qa_pair.get('answer', '')
        combined_text = question + ' ' + answer
        
        # 识别领域和技术术语
        for domain, terms in self.domain_knowledge.items():
            for term in terms:
                if term in combined_text:
                    key_info['technical_terms'].append(term)
                    if not key_info['domain']:
                        key_info['domain'] = domain
        
        return key_info
    
    def _find_relevant_chunks(self, qa_pair: Dict, key_info: Dict) -> List[Dict]:
        """查找相关文档片段"""
        relevant_chunks = []
        
        for chunk in self.doc_chunks:
            score = 0
            
            # 实体匹配
            for entity in key_info['entities']:
                if entity in chunk['content']:
                    score += 3
            
            # 技术术语匹配
            for term in key_info['technical_terms']:
                if term in chunk['content']:
                    score += 2
            
            if score > 0:
                chunk['relevance_score'] = score
                relevant_chunks.append(chunk)
        
        # 排序返回最相关的
        relevant_chunks.sort(key=lambda x: x['relevance_score'], reverse=True)
        return relevant_chunks[:5]
    
    def _chunk_documents(self, docs: Dict[str, str]) -> List[Dict]:
        """文档分块"""
        chunks = []
        chunk_size = self.config.get('chunk_size', 1000)
        chunk_overlap = self.config.get('chunk_overlap', 200)
        
        if not docs:
            return chunks
        
        # 使用进度条显示分块进度 - 改进的进度条设置
        with tqdm(total=len(docs), 
                  desc="文档分块", 
                  unit="文档", 
                  ncols=120,
                  position=0,
                  leave=True) as pbar:
            for doc_name, content in docs.items():
                # 按段落分割
                paragraphs = content.split('\n\n')
                current_chunk = ""
                
                for para in paragraphs:
                    if len(current_chunk) + len(para) < chunk_size:
                        current_chunk += para + "\n\n"
                    else:
                        if current_chunk:
                            chunks.append({
                                'doc': doc_name,
                                'content': current_chunk.strip()
                            })
                        # 保留部分内容作为重叠
                        if chunk_overlap > 0 and len(current_chunk) > chunk_overlap:
                            current_chunk = current_chunk[-chunk_overlap:] + para + "\n\n"
                        else:
                            current_chunk = para + "\n\n"
                
                # 添加最后一块
                if current_chunk:
                    chunks.append({
                        'doc': doc_name,
                        'content': current_chunk.strip()
                    })
                
                pbar.update(1)
                pbar.set_postfix({'块数': len(chunks)})
        
        logger.info(f"文档分块完成，共 {len(chunks)} 块")
        return chunks
    
    def _parse_validation_response(self, response: str) -> Dict:
        """解析验证响应"""
        result = {
            'common_sense': False,
            'principle_correct': False,
            'overall_valid': False,
            'details': {}
        }
        
        lines = response.strip().split('\n')
        
        for i, line in enumerate(lines):
            line = line.strip()
                    
            if '常识验证' in line:
                result['common_sense'] = '通过' in line and '不通过' not in line
                if i + 1 < len(lines) and '理由' in lines[i + 1]:
                    result['details']['common_sense_reason'] = lines[i + 1].split(':', 1)[-1].strip()
                    
            elif '原理验证' in line:
                result['principle_correct'] = '通过' in line and '不通过' not in line
                if i + 1 < len(lines) and '理由' in lines[i + 1]:
                    result['details']['principle_reason'] = lines[i + 1].split(':', 1)[-1].strip()
                    
            elif '总体判断' in line:
                result['overall_valid'] = '通过' in line and '不通过' not in line
        
        # 如果没有总体判断，基于常识和原理结果
        if not any('总体判断' in line for line in lines):
            result['overall_valid'] = all([
                result['common_sense'],
                result['principle_correct']
            ])
        
        return result
    
    def _is_qa_valid(self, qa_pair: Dict) -> bool:
        """判断QA是否有效"""
        if 'validation' not in qa_pair:
            return False
        return qa_pair['validation'].get('overall_valid', False)
    
    def _update_failure_stats(self, qa_pair: Dict, statistics: Dict):
        """更新失败统计"""
        if 'validation' not in qa_pair:
            statistics['failed_by_reason']['incomplete_question'] += 1
            return
        
        validation = qa_pair['validation']
        if not validation.get('common_sense', False):
            statistics['failed_by_reason']['common_sense'] += 1
        if not validation.get('principle_correct', False):
            statistics['failed_by_reason']['principle'] += 1


# 使用示例
async def main():
    import argparse
    parser = argparse.ArgumentParser(description='KG问答对验证系统')
    parser.add_argument("--docs_folder", required=True,
                       help="包含参考文档的文件夹路径")
    parser.add_argument("--model_path", required=True,
                       help="本地模型路径，如 /path/to/Qwen2.5-14B-Instruct")
    parser.add_argument("--qa_file", required=True,
                       help="KG生成的问答对JSON文件")
    parser.add_argument("--output_file", required=True,
                       help="验证通过的问答对输出文件")
    parser.add_argument("--batch_size", type=int, default=10,
                       help="批处理大小")
    parser.add_argument("--recursive", action='store_true',
                       help="是否递归搜索子文件夹中的文档")
    parser.add_argument("--max_qa", type=int, default=None,
                       help="最大处理的QA数量（用于测试）")
    
    args = parser.parse_args()
    
    # 配置
    config = {
        'batch_size': args.batch_size,
        'recursive': args.recursive,
        'chunk_size': 1000,
        'chunk_overlap': 200
    }
    
    print("\n" + "="*60)
    print("KG问答对验证系统")
    print("="*60)
    print(f"文档文件夹: {args.docs_folder}")
    print(f"模型路径: {args.model_path}")
    print(f"输入文件: {args.qa_file}")
    print(f"输出文件: {args.output_file}")
    print(f"批处理大小: {args.batch_size}")
    print(f"递归搜索: {'是' if args.recursive else '否'}")
    print("="*60 + "\n")
    
    try:
        # 初始化验证器
        validator = LocalKGQAValidator(
            docs_folder=args.docs_folder,
            model_path=args.model_path,
            config=config
        )
        
        # 加载问答对
        print("\n正在加载问答对...")
        with open(args.qa_file, 'r', encoding='utf-8') as f:
            qa_pairs = json.load(f)
        
        # 如果指定了最大数量，截取
        if args.max_qa:
            qa_pairs = qa_pairs[:args.max_qa]
        
        print(f"加载了 {len(qa_pairs)} 个问答对\n")
        
        # 执行验证
        validated_qa, statistics = await validator.validate_qa_pairs(qa_pairs)
        
        # 保存结果
        os.makedirs(os.path.dirname(args.output_file), exist_ok=True)
        with open(args.output_file, 'w', encoding='utf-8') as f:
            json.dump(validated_qa, f, ensure_ascii=False, indent=2)
        
        # 保存统计报告
        report_file = args.output_file.replace('.json', '_report.json')
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(statistics, f, ensure_ascii=False, indent=2)
        
        # 打印统计
        print("\n" + "="*60)
        print("验证完成！")
        print("="*60)
        print(f"总数: {statistics['total']}")
        print(f"通过: {statistics['passed']} ({statistics['passed']/max(statistics['total'], 1)*100:.1f}%)")
        print(f"失败: {statistics['failed']} ({statistics['failed']/max(statistics['total'], 1)*100:.1f}%)")
        print(f"\n失败原因分布:")
        for reason, count in statistics['failed_by_reason'].items():
            if count > 0:
                print(f"  {reason}: {count}")
        print(f"\n处理时间: {statistics['processing_time']:.2f}秒")
        print(f"平均每个QA: {statistics['processing_time']/max(statistics['total'], 1):.2f}秒")
        print(f"\n结果文件: {args.output_file}")
        print(f"统计报告: {report_file}")
        print("="*60 + "\n")
        
    except Exception as e:
        logger.error(f"程序执行失败: {str(e)}")
        raise

if __name__ == "__main__":
    # 设置环境变量确保输出无缓冲
    os.environ['PYTHONUNBUFFERED'] = '1'
    asyncio.run(main())