import openai
from Utilis.utilis import clean_text_content
from Doubao.prompts_conf import system_prompt
import asyncio
from asyncio import Semaphore, gather
model = "qwen3-32b"
api_key = "sk-85caf631866d4b0fb79eaeeb34f8f96e"
url = "https://dashscope.aliyuncs.com/compatible-mode/v1"

class QALabeler:
    def __init__(self, api_key=api_key, model=model, url=url, activate_stream=True, parallel_core=10,
                 question_key="question", answer_key="answer", system_prompt=system_prompt):
        self.client = openai.AsyncOpenAI(
            api_key=api_key,
            base_url=url if url else None
        )
        self.question_key = question_key
        self.answer_key = answer_key
        self.model = model
        self.activate_stream = activate_stream
        self.parallel_core = parallel_core
        self.system_prompt = system_prompt
    
    def run_check(self, QA_file, use_text_context=False):
        """
        运行问答质量检查（纯文本版本）
        
        Args:
            QA_file: 问答文件路径
            use_text_context: 是否使用文本上下文
        """
        import pandas as pd
        
        if QA_file.endswith('.xlsx'):
            data = pd.read_excel(QA_file)
        elif QA_file.endswith('.csv'):
            data = pd.read_csv(QA_file)
        elif QA_file.endswith('.json'):
            data = pd.read_json(QA_file)
        
        semaphore = Semaphore(self.parallel_core)
        
        async def get_tasks():
            tasks = []
            for index in range(0, len(data), self.parallel_core):
                batch = data.iloc[index:index+self.parallel_core]
                task_batch = []
                for _, row in batch.iterrows():
                    question = row[self.question_key]
                    answer = row[self.answer_key]
                    text_context = row.get("text_content", None) if use_text_context else None
                    task_batch.append(self.get_questions_label({
                        "question": question,
                        "answer": answer,
                        "text_context": text_context
                    }))
                async with semaphore:
                    tasks.extend(await gather(*task_batch))
            return tasks
        
        labels = asyncio.run(get_tasks())
        
        # 保存结果到新的CSV文件
        data['label'] = labels
        data["label_description"] = data["label"].map(
            lambda x: "模型回答正确" if x == 1 else "模型无法回答", 
            na_action='ignore'
        )
        
        output_file = QA_file.replace('.csv', '_labeled.csv').replace('.json', '_labeled.csv')
        data.to_csv(output_file, index=False)
        
        print(f"Quality check completed. Results saved to {output_file}")
        
        # 生成质量报告
        self.generate_quality_report(data, QA_file)
    
    async def get_questions_label(self, QA):
        """获取问题标签"""
        question = QA["question"]
        answer = QA["answer"]
        text_context = QA.get("text_context", "")
        
        # 获取模型回答
        model_answer = await self.get_response(question, answer, text_context)
        
        # 检查答案质量
        label = await self.check_answer(question, answer, model_answer)
        return label
    
    async def get_response(self, question, answer, text_context=None):
        """获取模型响应（纯文本版本）"""
        # 构建提示词
        prompt = f"请回答以下问题，返回内容直接给出答案，不需要给出思考过程：{question}"
        
        if text_context:
            prompt = f"基于以下文本内容：\n{text_context}\n\n{prompt}"
        
        messages = [
            {
                "role": "system",
                "content": [
                    {"type": "text", "text": self.system_prompt}
                ]
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt}
                ]
            }
        ]
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=1,
                max_tokens=4096,
                top_p=0.7,
                stream=self.activate_stream
            )
            
            if self.activate_stream:
                reasoning_content = ""
                answer_content = ""
                async for chunk in response:
                    if not chunk.choices:
                        print("\nUsage:")
                        print(chunk.usage)
                    else:
                        delta = chunk.choices[0].delta
                        if delta.content:
                            answer_content += delta.content
                return answer_content
            else:
                return response.choices[0].message.content
                
        except Exception as e:
            print(f"Error getting response: {e}")
            return ""
    
    async def check_answer(self, question, ground_truth, model_answer):
        """检查答案正确性"""
        if not model_answer.strip():
            return 0
        
        # 使用简单的文本相似度检查
        similarity_score = self.calculate_text_similarity(ground_truth, model_answer)
        
        # 如果相似度高于阈值，认为答案正确
        if similarity_score > 0.6:
            return 1
        
        # 使用模型进行更深入的答案评估
        evaluation_result = await self.evaluate_answer_with_model(question, ground_truth, model_answer)
        return evaluation_result
    
    def calculate_text_similarity(self, text1, text2):
        """计算文本相似度"""
        # 简单的基于词汇重叠的相似度计算
        words1 = set(clean_text_content(text1).split())
        words2 = set(clean_text_content(text2).split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    async def evaluate_answer_with_model(self, question, ground_truth, model_answer):
        """使用模型评估答案质量"""
        evaluation_prompt = f"""
        请评估以下答案的正确性：
        
        问题：{question}
        标准答案：{ground_truth}
        模型答案：{model_answer}
        
        请判断模型答案是否正确，只回答"正确"或"错误"。
        """
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个答案评估专家。"},
                    {"role": "user", "content": evaluation_prompt}
                ],
                temperature=0.3,
                max_tokens=10
            )
            
            result = response.choices[0].message.content.strip()
            return 1 if "正确" in result else 0
            
        except Exception as e:
            print(f"Error in answer evaluation: {e}")
            return 0
    
    def generate_quality_report(self, data, original_file):
        """生成质量报告"""
        report = {
            "total_questions": len(data),
            "correct_answers": sum(data['label']),
            "incorrect_answers": len(data) - sum(data['label']),
            "accuracy": sum(data['label']) / len(data) if len(data) > 0 else 0,
            "question_types": {},
            "difficulty_analysis": {},
            "common_errors": []
        }
        
        # 分析问题类型分布
        if 'type' in data.columns:
            report["question_types"] = data.groupby('type')['label'].agg(['count', 'sum']).to_dict()
        
        # 分析难度分布
        if 'difficulty' in data.columns:
            report["difficulty_analysis"] = data.groupby('difficulty')['label'].agg(['count', 'sum']).to_dict()
        
        # 保存报告
        report_file = original_file.replace('.csv', '_quality_report.json').replace('.json', '_quality_report.json')
        import json
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=4)
        
        print(f"Quality report saved to {report_file}")
        print(f"Overall accuracy: {report['accuracy']:.2%}")
        print(f"Correct answers: {report['correct_answers']}/{report['total_questions']}")

class TextQualityAnalyzer:
    """文本质量分析器"""
    
    def __init__(self):
        self.quality_metrics = [
            "readability",
            "coherence", 
            "technical_accuracy",
            "completeness",
            "relevance"
        ]
    
    def analyze_text_quality(self, text_content):
        """分析文本质量"""
        from Utilis.utilis import validate_text_quality, calculate_text_complexity, extract_key_terms
        
        # 基础质量检查
        basic_quality = validate_text_quality(text_content)
        
        # 复杂度分析
        complexity = calculate_text_complexity(text_content)
        
        # 关键术语分析
        key_terms = extract_key_terms(text_content)
        
        quality_analysis = {
            "basic_quality": basic_quality,
            "complexity": complexity,
            "key_terms_count": len(key_terms),
            "domain_relevance": self.calculate_domain_relevance(key_terms),
            "overall_score": self.calculate_overall_score(basic_quality, complexity, key_terms)
        }
        
        return quality_analysis
    
    def calculate_domain_relevance(self, key_terms):
        """计算领域相关性"""
        domain_terms = ['TFT', 'OLED', '显示', '器件', '薄膜', '晶体管', '栅极', '介电层']
        relevant_terms = [term for term in key_terms if term in domain_terms]
        
        if not key_terms:
            return 0.0
        
        return len(relevant_terms) / len(key_terms)
    
    def calculate_overall_score(self, basic_quality, complexity, key_terms):
        """计算总体质量分数"""
        score = basic_quality.get("quality_score", 0) * 0.4
        score += min(complexity.get("score", 0) * 10, 40) * 0.3
        score += min(len(key_terms) * 2, 20) * 0.3
        
        return min(score, 100)

def batch_quality_check(input_dir, output_dir):
    """批量质量检查"""
    import os
    import json
    
    qa_labeler = QALabeler()
    quality_analyzer = TextQualityAnalyzer()
    
    results = []
    
    for root, dirs, files in os.walk(input_dir):
        for file in files:
            if file.endswith(('.json', '.csv')):
                file_path = os.path.join(root, file)
                print(f"Processing {file_path}...")
                
                try:
                    # 运行QA质量检查
                    qa_labeler.run_check(file_path)
                    
                    # 如果有文本内容，进行文本质量分析
                    if 'text_content' in file:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f) if file.endswith('.json') else None
                        
                        if data and isinstance(data, list):
                            for item in data:
                                if 'text_content' in item:
                                    text_quality = quality_analyzer.analyze_text_quality(item['text_content'])
                                    item['text_quality'] = text_quality
                    
                    results.append({
                        "file": file_path,
                        "status": "completed",
                        "timestamp": asyncio.get_event_loop().time()
                    })
                    
                except Exception as e:
                    print(f"Error processing {file_path}: {e}")
                    results.append({
                        "file": file_path,
                        "status": "error",
                        "error": str(e)
                    })
    
    # 保存批量处理结果
    os.makedirs(output_dir, exist_ok=True)
    results_file = os.path.join(output_dir, "batch_quality_check_results.json")
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=4)
    
    print(f"Batch quality check completed. Results saved to {results_file}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Text QA Quality Checker")
    parser.add_argument("--file", type=str, help="Single file to check")
    parser.add_argument("--input_dir", type=str, help="Input directory for batch processing")
    parser.add_argument("--output_dir", type=str, default="quality_check_results", 
                        help="Output directory for results")
    parser.add_argument("--use_context", action="store_true", 
                        help="Use text context in quality checking")
    
    args = parser.parse_args()
    
    if args.file:
        # 单文件处理
        qa_labeler = QALabeler(activate_stream=True, parallel_core=10,
                               question_key="question", answer_key="answer")
        qa_labeler.run_check(args.file, use_text_context=args.use_context)
    elif args.input_dir:
        # 批量处理
        batch_quality_check(args.input_dir, args.output_dir)
    else:
        print("Please provide either --file or --input_dir")