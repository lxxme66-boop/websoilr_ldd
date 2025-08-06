"""
问题生成器 - WebSailor核心模块（纯文本优化版）
基于文本内容，设计QA问题
覆盖多种问题类型：事实型、比较型、推理型、多跳型、开放型等
增加了问题合理性验证和优化机制
新增：开放型问题生成和比例控制功能
"""
import uuid
import json
import logging
import random
from typing import List, Dict, Tuple, Optional
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
from tqdm import tqdm
import networkx as nx

logger = logging.getLogger(__name__)

class QuestionGenerator:
    """
    WebSailor核心：问题生成器（纯文本优化版）
    基于文本内容生成多样化的问题，覆盖不同难度和类型
    包含问题合理性验证和优化机制
    新增：开放型问题生成和比例控制
    """
    
    def __init__(self, config: dict):
        self.config = config
        self.qg_config = config.get('question_generation', {})
        
        # 问题类型（新增开放型）
        self.question_types = self.qg_config.get('question_types', ['factual', 'comparison', 'reasoning', 'multi_hop', 'open_ended'])
        self.complexity_levels = self.qg_config.get('complexity_levels', {})
        self.language_patterns = self.qg_config.get('language_patterns', {})
        
        # 新增：问题类型比例控制（优化版）
        self.question_type_ratios = self.qg_config.get('question_type_ratios', {
            'factual': 0.25,      # 25% 事实型
            'comparison': 0.18,   # 18% 比较型  
            'reasoning': 0.25,    # 25% 推理型
            'multi_hop': 0.15,    # 15% 多跳型
            'open_ended': 0.17    # 17% 开放型（提高开放型问题比例）
        })
        
        # 新增：问题类型优先级配置
        self.question_type_priorities = self.qg_config.get('question_type_priorities', {
            'open_ended': 1,      # 最高优先级：开放型问题
            'reasoning': 2,       # 高优先级：推理型问题
            'factual': 3,         # 中等优先级：事实型问题
            'comparison': 4,      # 较低优先级：比较型问题
            'multi_hop': 5        # 最低优先级：多跳型问题
        })
        
        # 新增：动态比例调整参数
        self.dynamic_ratio_adjustment = {
            'enable': True,               # 启用动态调整
            'adjustment_factor': 0.1,     # 调整因子
            'min_ratio_threshold': 0.05,  # 最小比例阈值
            'max_ratio_threshold': 0.4    # 最大比例阈值
        }
        
        # 加载QA生成模型
        self._load_qa_generator()
        
        # TCL特定配置
        self.tcl_config = config.get('tcl_specific', {})
        
        # 问题模板（包含开放型）
        self._init_question_templates()
        
        # 合理性阈值
        self.validity_threshold = 0.7
        self.max_optimization_attempts = 2
        self.validation_cache = {}
        self.min_question_length = 60
        self.max_question_length = 120
        self.prefer_complex_questions = True
        
        # 生成策略配置
        self.generation_strategy = {
            'template_ratio': 0.2,  # 20% 使用模板
            'llm_ratio': 0.8,       # 80% 使用LLM
            'min_context_entities': 3,
            'question_cache': {},
            'similarity_threshold': 0.85
        }
        
        # 问题指纹集合，用于去重
        self.question_fingerprints = set()
        
        logger.info("初始化增强版问题生成器（纯文本），支持开放型问题和比例控制")
        
        # 调整生成参数
        self.generation_params = {
            'temperature': 0.8,
            'max_new_tokens': 150,
            'top_p': 0.9,
            'do_sample': True
        }

    def _load_qa_generator(self):
        """加载QA生成模型"""
        try:
            model_config = self.config.get('models', {}).get('qa_generator_model', {})
            model_path = model_config.get('path', '/mnt/storage/models/Qwen/Qwen2.5-14B-Instruct')
            
            logger.info(f"加载QA生成模型: {model_path}")
            
            self.tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
            self.qa_model = AutoModelForCausalLM.from_pretrained(
                model_path, 
                torch_dtype=torch.float16,
                device_map="auto",
                trust_remote_code=True
            )
            
            logger.info("QA生成模型加载成功")
            
        except Exception as e:
            logger.warning(f"QA生成模型加载失败: {e}")
            self.tokenizer = None
            self.qa_model = None

    def _init_question_templates(self):
        """初始化问题模板（包含开放型）"""
        self.question_templates = {
            'factual': [
                "根据文本内容，{entity}的{attribute}是什么？",
                "文本中提到的{entity}具有什么特征？",
                "关于{concept}，文本中给出了哪些具体信息？",
                "在{context}中，{entity}的作用是什么？",
                "文本描述的{process}包含哪些步骤？"
            ],
            'comparison': [
                "比较文本中{entity1}和{entity2}的{attribute}有什么不同？",
                "在{aspect}方面，{entity1}与{entity2}相比有何优势？",
                "文本中{concept1}和{concept2}的主要区别是什么？",
                "对比{method1}和{method2}，哪种更适合{scenario}？",
                "分析{entity1}和{entity2}在{context}中的不同表现。"
            ],
            'reasoning': [
                "基于文本内容，为什么{entity}会{behavior}？",
                "根据文本分析，{phenomenon}产生的原因是什么？",
                "文本中{condition}如何导致{result}？",
                "从文本可以推断出{entity}的{future_state}会如何变化？",
                "基于{evidence}，可以得出什么结论？"
            ],
            'multi_hop': [
                "结合文本中{entity1}的{attribute1}和{entity2}的{attribute2}，可以得出什么结论？",
                "如果{condition1}成立，并且{condition2}也满足，那么{target}会如何？",
                "通过{step1}然后{step2}，最终{goal}能够实现吗？",
                "考虑{factor1}、{factor2}和{factor3}的综合影响，{outcome}会是什么？",
                "从{perspective1}到{perspective2}再到{perspective3}，整个{process}的逻辑是什么？"
            ],
            'open_ended': [
                # 用户指定的核心问题（TCL特定）
                "怎么实现短沟道的顶栅氧化物TFT器件且同时避免器件失效？",
                "金属氧化物背板在短时间内驱动OLED显示时会出现残影，请问如何在TFT方面改善残影问题？",
                
                # 新增的TCL特定问题
                "在薄膜晶体管制造过程中，如何优化栅极介电层的厚度和材料选择以提高器件可靠性？",
                "面对显示面板功耗和亮度的矛盾需求，应该从哪些技术路径寻求突破？",
                "在大尺寸OLED面板生产中，如何解决均匀性和良率之间的平衡问题？",
                "针对柔性显示技术，在保持显示性能的同时如何提高机械可靠性？",
                "在高分辨率显示驱动中，如何解决信号完整性和EMI问题？",
                
                # 通用开放型模板
                "基于文本内容，如何解决{problem}这一技术挑战？",
                "考虑到{constraint}，有哪些创新方法可以改善{target}？",
                "在{scenario}场景下，如何平衡{factor1}和{factor2}之间的矛盾？",
                "针对{challenge}，从{perspective}角度应该采取什么策略？",
                "如何在保证{requirement1}的前提下优化{requirement2}？"
            ]
        }

    def generate_questions(self, text_content: str, num_questions: int = 10) -> List[Dict]:
        """
        基于文本内容生成多样化问题
        
        Args:
            text_content: 输入文本内容
            num_questions: 生成问题数量
            
        Returns:
            List[Dict]: 生成的问题列表
        """
        logger.info(f"开始生成 {num_questions} 个问题，基于文本内容")
        
        # 分析文本内容
        text_analysis = self._analyze_text_content(text_content)
        
        # 计算各类型问题数量
        type_distribution = self._calculate_question_distribution(num_questions)
        
        questions = []
        
        for question_type, count in type_distribution.items():
            if count > 0:
                type_questions = self._generate_questions_by_type(
                    text_analysis, question_type, count
                )
                questions.extend(type_questions)
        
        # 问题去重和优化
        questions = self._deduplicate_and_optimize_questions(questions)
        
        # 质量验证
        validated_questions = []
        for question in questions:
            if self._validate_question_quality(question, text_content):
                validated_questions.append(question)
        
        logger.info(f"成功生成 {len(validated_questions)} 个高质量问题")
        return validated_questions[:num_questions]

    def _analyze_text_content(self, text_content: str) -> Dict:
        """分析文本内容，提取关键信息"""
        analysis = {
            'entities': [],
            'concepts': [],
            'relationships': [],
            'processes': [],
            'attributes': [],
            'context': text_content[:200] + "..." if len(text_content) > 200 else text_content,
            'length': len(text_content),
            'complexity': self._assess_text_complexity(text_content)
        }
        
        # 简单的关键词提取（可以用更复杂的NLP工具替换）
        import re
        
        # 提取可能的实体（专有名词、技术术语）
        entities = re.findall(r'[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*', text_content)
        analysis['entities'] = list(set(entities))[:10]
        
        # 提取技术概念
        tech_patterns = [
            r'TFT', r'OLED', r'显示', r'器件', r'薄膜', r'晶体管',
            r'栅极', r'介电层', r'背板', r'残影', r'可靠性'
        ]
        concepts = []
        for pattern in tech_patterns:
            if re.search(pattern, text_content, re.IGNORECASE):
                concepts.append(pattern)
        analysis['concepts'] = concepts
        
        return analysis

    def _assess_text_complexity(self, text: str) -> str:
        """评估文本复杂度"""
        if len(text) < 100:
            return 'simple'
        elif len(text) < 500:
            return 'medium'
        else:
            return 'complex'

    def _calculate_question_distribution(self, total_questions: int) -> Dict[str, int]:
        """计算各类型问题的分布数量"""
        distribution = {}
        
        # 按比例计算
        for q_type, ratio in self.question_type_ratios.items():
            count = int(total_questions * ratio)
            distribution[q_type] = count
        
        # 调整余数
        assigned = sum(distribution.values())
        remaining = total_questions - assigned
        
        # 按优先级分配剩余问题
        priority_sorted = sorted(
            self.question_type_priorities.items(), 
            key=lambda x: x[1]
        )
        
        for q_type, _ in priority_sorted:
            if remaining <= 0:
                break
            distribution[q_type] += 1
            remaining -= 1
        
        logger.info(f"问题类型分布: {distribution}")
        return distribution

    def _generate_questions_by_type(self, text_analysis: Dict, question_type: str, count: int) -> List[Dict]:
        """根据类型生成指定数量的问题"""
        questions = []
        templates = self.question_templates.get(question_type, [])
        
        for i in range(count):
            if question_type == 'open_ended':
                # 开放型问题特殊处理
                question = self._generate_open_ended_question(text_analysis, templates)
            else:
                # 其他类型问题
                question = self._generate_typed_question(text_analysis, question_type, templates)
            
            if question:
                questions.append({
                    'id': str(uuid.uuid4()),
                    'type': question_type,
                    'question': question,
                    'complexity': text_analysis.get('complexity', 'medium'),
                    'context_length': text_analysis.get('length', 0),
                    'generated_method': 'template' if random.random() < self.generation_strategy['template_ratio'] else 'llm'
                })
        
        return questions

    def _generate_open_ended_question(self, text_analysis: Dict, templates: List[str]) -> str:
        """生成开放型问题"""
        # 优先使用固定的专业问题
        fixed_questions = [
            "怎么实现短沟道的顶栅氧化物TFT器件且同时避免器件失效？",
            "金属氧化物背板在短时间内驱动OLED显示时会出现残影，请问如何在TFT方面改善残影问题？",
            "在薄膜晶体管制造过程中，如何优化栅极介电层的厚度和材料选择以提高器件可靠性？",
            "面对显示面板功耗和亮度的矛盾需求，应该从哪些技术路径寻求突破？",
            "在大尺寸OLED面板生产中，如何解决均匀性和良率之间的平衡问题？"
        ]
        
        if random.random() < 0.6:  # 60%概率使用固定问题
            return random.choice(fixed_questions)
        
        # 否则使用模板生成
        template = random.choice(templates)
        entities = text_analysis.get('entities', ['系统', '设备', '工艺'])
        concepts = text_analysis.get('concepts', ['技术', '方法', '性能'])
        
        # 填充模板
        try:
            question = template.format(
                problem=random.choice(concepts) if concepts else '技术挑战',
                constraint=random.choice(entities) if entities else '现有条件',
                target='性能优化',
                scenario='实际应用',
                factor1='成本',
                factor2='效率',
                challenge='技术难题',
                perspective='工程',
                requirement1='质量',
                requirement2='效率'
            )
            return question
        except:
            return random.choice(fixed_questions)

    def _generate_typed_question(self, text_analysis: Dict, question_type: str, templates: List[str]) -> str:
        """生成指定类型的问题"""
        if not templates:
            return None
        
        template = random.choice(templates)
        entities = text_analysis.get('entities', ['对象', '系统'])
        concepts = text_analysis.get('concepts', ['概念', '技术'])
        
        # 填充模板
        try:
            question = template.format(
                entity=random.choice(entities) if entities else '对象',
                entity1=random.choice(entities) if entities else '对象1',
                entity2=random.choice(entities[1:]) if len(entities) > 1 else '对象2',
                attribute='特性',
                concept=random.choice(concepts) if concepts else '概念',
                concept1=random.choice(concepts) if concepts else '概念1',
                concept2=random.choice(concepts[1:]) if len(concepts) > 1 else '概念2',
                context='文本描述的场景',
                process='处理过程',
                behavior='表现',
                phenomenon='现象',
                condition='条件',
                result='结果',
                evidence='证据',
                aspect='方面',
                method1='方法1',
                method2='方法2',
                scenario='场景'
            )
            return question
        except:
            return f"关于{random.choice(entities) if entities else '内容'}的问题是什么？"

    def _deduplicate_and_optimize_questions(self, questions: List[Dict]) -> List[Dict]:
        """问题去重和优化"""
        unique_questions = []
        seen_fingerprints = set()
        
        for question in questions:
            fingerprint = self._get_question_fingerprint(question['question'])
            if fingerprint not in seen_fingerprints:
                seen_fingerprints.add(fingerprint)
                unique_questions.append(question)
        
        return unique_questions

    def _get_question_fingerprint(self, question: str) -> str:
        """生成问题指纹用于去重"""
        import hashlib
        # 简单的文本指纹
        normalized = question.lower().strip()
        return hashlib.md5(normalized.encode()).hexdigest()

    def _validate_question_quality(self, question: Dict, text_content: str) -> bool:
        """验证问题质量"""
        q_text = question['question']
        
        # 基本长度检查
        if len(q_text) < self.min_question_length or len(q_text) > self.max_question_length:
            return False
        
        # 检查是否包含问号
        if '？' not in q_text and '?' not in q_text:
            return False
        
        # 检查是否与文本内容相关
        relevance_score = self._calculate_relevance(q_text, text_content)
        if relevance_score < 0.3:
            return False
        
        return True

    def _calculate_relevance(self, question: str, text_content: str) -> float:
        """计算问题与文本的相关性"""
        # 简单的关键词重叠计算
        q_words = set(question.lower().split())
        t_words = set(text_content.lower().split())
        
        if len(q_words) == 0:
            return 0.0
        
        overlap = len(q_words.intersection(t_words))
        return overlap / len(q_words)

    def generate_answers(self, questions: List[Dict], text_content: str) -> List[Dict]:
        """为问题生成答案"""
        logger.info(f"开始为 {len(questions)} 个问题生成答案")
        
        answered_questions = []
        
        for question in questions:
            try:
                answer = self._generate_single_answer(question, text_content)
                question['answer'] = answer
                question['reasoning'] = self._generate_reasoning(question, text_content)
                answered_questions.append(question)
            except Exception as e:
                logger.warning(f"答案生成失败: {e}")
                continue
        
        logger.info(f"成功生成 {len(answered_questions)} 个问答对")
        return answered_questions

    def _generate_single_answer(self, question: Dict, text_content: str) -> str:
        """生成单个问题的答案"""
        if not self.qa_model or not self.tokenizer:
            return "基于文本内容的相关答案。"
        
        prompt = f"""基于以下文本内容，回答问题：

文本内容：
{text_content[:1000]}...

问题：{question['question']}

请提供准确、简洁的答案："""

        try:
            inputs = self.tokenizer(prompt, return_tensors="pt", truncation=True, max_length=2048)
            
            with torch.no_grad():
                outputs = self.qa_model.generate(
                    inputs.input_ids,
                    max_new_tokens=self.generation_params['max_new_tokens'],
                    temperature=self.generation_params['temperature'],
                    top_p=self.generation_params['top_p'],
                    do_sample=self.generation_params['do_sample'],
                    pad_token_id=self.tokenizer.eos_token_id
                )
            
            answer = self.tokenizer.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)
            return answer.strip()
        
        except Exception as e:
            logger.warning(f"模型生成答案失败: {e}")
            return "基于文本内容的相关答案。"

    def _generate_reasoning(self, question: Dict, text_content: str) -> str:
        """生成推理过程"""
        reasoning_templates = {
            'factual': "根据文本中的直接描述，可以找到相关信息。",
            'comparison': "通过对比文本中不同部分的描述，可以分析出差异。",
            'reasoning': "基于文本提供的信息和逻辑关系，可以推导出结论。",
            'multi_hop': "需要综合文本中多个相关信息点，进行多步推理。",
            'open_ended': "这是一个开放性问题，需要结合专业知识和文本内容进行综合分析。"
        }
        
        q_type = question.get('type', 'factual')
        return reasoning_templates.get(q_type, "基于文本内容进行分析推理。")

    def get_generation_statistics(self) -> Dict:
        """获取生成统计信息"""
        return {
            'question_type_ratios': self.question_type_ratios,
            'question_type_priorities': self.question_type_priorities,
            'generation_strategy': self.generation_strategy,
            'total_fingerprints': len(self.question_fingerprints),
            'validation_cache_size': len(self.validation_cache)
        }