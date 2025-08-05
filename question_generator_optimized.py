"""
问题生成器 - WebSailor核心模块（优化版）
基于子图中节点与关系，设计QA问题
覆盖多种问题类型：事实型、比较型、推理型、多跳型等
增加了问题合理性验证和优化机制
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
    WebSailor核心：问题生成器（优化版）
    基于子图生成多样化的问题，覆盖不同难度和类型
    包含问题合理性验证和优化机制
    """
    
    def __init__(self, config: dict):
        self.config = config
        self.qg_config = config.get('question_generation', {})
        # 问题类型（新增开放型）
        self.question_types = self.qg_config.get('question_types', ['factual', 'comparison', 'reasoning', 'multi_hop', 'open_ended'])
        self.complexity_levels = self.qg_config.get('complexity_levels', {})
        self.language_patterns = self.qg_config.get('language_patterns', {})
        # 添加缺失的属性
        self.question_type_priorities = {
            'factual': 1,
            'comparison': 2,      # 修正名称
            'reasoning': 1,       # 修正名称  
            'multi_hop': 2,       # 修正名称
            'open_ended': 2,      # 保持不变
        }
        # 新增：问题类型比例控制
        self.question_type_ratios = self.qg_config.get('question_type_ratios', {
            'factual': 0.25,      # 25% 事实型
            'comparison': 0.20,   # 20% 比较型  
            'reasoning': 0.25,    # 25% 推理型
            'multi_hop': 0.15,    # 15% 多跳型
            'open_ended': 0.15    # 15% 开放型
        })
        
        # 加载QA生成模型
        self._load_qa_generator()
        
        # TCL特定配置
        self.tcl_config = config.get('tcl_specific', {})
        
        # 问题模板
        self._init_question_templates()
        
        # 合理性阈值
        self.validity_threshold = 0.7
        self.max_optimization_attempts = 2
        self.validation_cache = {}  # 添加验证缓存
        # 添加长度控制参数
        self.min_question_length = 60
        self.max_question_length = 120
        self.prefer_complex_questions = True
        # 新增：生成策略配置
        self.generation_strategy = {
            'template_ratio': 0.2,  # 40% 使用模板
            'llm_ratio': 0.8,       # 60% 使用LLM
            'min_context_entities': 3,  # LLM生成的最小上下文实体数
            'question_cache': {},   # 问题缓存，避免重复
            'similarity_threshold': 0.85  # 问题相似度阈值
        }
        
        # 问题指纹集合，用于去重
        self.question_fingerprints = set()
        
        logger.info("初始化40%-60%混合问题生成策略")
        
        # 调整生成参数
        self.generation_params = {
            'temperature': 0.8,  # 提高创造性
            'max_new_tokens': 150,  # 增加生成长度
            'top_p': 0.9,
            'do_sample': True
        }
        
    def _load_qa_generator(self):
        """加载QA生成模型"""
        model_config = self.qg_config.get('qa_model', {})
        model_name = model_config.get('name', 'microsoft/DialoGPT-medium')
        
        try:
            logger.info(f"加载QA生成模型: {model_name}")
            self.qa_tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.qa_model = AutoModelForCausalLM.from_pretrained(model_name)
            
            # 设置pad_token
            if self.qa_tokenizer.pad_token is None:
                self.qa_tokenizer.pad_token = self.qa_tokenizer.eos_token
                
            # GPU支持
            if torch.cuda.is_available():
                self.qa_model = self.qa_model.cuda()
                logger.info("QA模型已加载到GPU")
            else:
                logger.info("QA模型已加载到CPU")
                
        except Exception as e:
            logger.error(f"加载QA模型失败: {e}")
            self.qa_tokenizer = None
            self.qa_model = None
    
    def _init_question_templates(self):
        """初始化问题模板"""
        self.question_templates = {
            'factual': [
                "什么是{entity}？",
                "{entity}有什么特点？",
                "{entity}的定义是什么？",
                "请描述{entity}的基本信息。",
                "{entity}属于什么类别？"
            ],
            'comparison': [
                "{entity1}和{entity2}有什么区别？",
                "比较{entity1}和{entity2}的特点。",
                "{entity1}与{entity2}哪个更{attribute}？",
                "{entity1}和{entity2}在{aspect}方面有何不同？",
                "分析{entity1}和{entity2}的优缺点。"
            ],
            'reasoning': [
                "为什么{entity1}会{relation}{entity2}？",
                "{entity1}{relation}{entity2}的原因是什么？",
                "如何解释{entity1}和{entity2}之间的{relation}关系？",
                "{entity1}对{entity2}产生什么影响？",
                "分析{entity1}导致{entity2}的机制。"
            ],
            'multi_hop': [
                "通过{entity1}，{entity2}如何与{entity3}产生联系？",
                "从{entity1}到{entity3}，经过{entity2}的路径是什么？",
                "{entity1}、{entity2}和{entity3}之间存在什么复杂关系？",
                "如何从{entity1}推导出{entity3}的结论？",
                "解释{entity1}→{entity2}→{entity3}的逻辑链条。"
            ],
            'open_ended': [
                "如果{entity1}发生变化，会对{entity2}产生什么可能的影响？",
                "在什么情况下，{entity1}和{entity2}的关系可能会改变？",
                "除了{relation}，{entity1}和{entity2}还可能存在什么其他关系？",
                "如何评价{entity1}在{context}中的作用？",
                "对于{entity1}和{entity2}的关系，你有什么看法？"
            ]
        }
        
        # TCL特定模板
        if self.tcl_config.get('enable', False):
            self.question_templates['tcl_specific'] = [
                "{entity}在TCL生态系统中扮演什么角色？",
                "TCL的{entity}技术有什么优势？",
                "{entity}如何支持TCL的智能化战略？",
                "分析{entity}对TCL产业链的影响。"
            ]
    
    def generate_questions_from_subgraph(self, subgraph: nx.Graph, num_questions: int = 10) -> List[Dict]:
        """
        基于子图生成问题
        
        Args:
            subgraph: NetworkX子图对象
            num_questions: 要生成的问题数量
            
        Returns:
            问题列表，每个问题包含问题文本、类型、难度等信息
        """
        logger.info(f"开始从子图生成{num_questions}个问题")
        
        # 分析子图结构
        subgraph_analysis = self._analyze_subgraph(subgraph)
        
        # 根据比例分配问题类型
        question_type_distribution = self._calculate_question_distribution(num_questions)
        
        generated_questions = []
        
        # 按类型生成问题
        for question_type, count in question_type_distribution.items():
            if count > 0:
                questions = self._generate_questions_by_type(
                    subgraph, subgraph_analysis, question_type, count
                )
                generated_questions.extend(questions)
        
        # 问题后处理
        processed_questions = self._post_process_questions(generated_questions)
        
        # 问题验证和优化
        validated_questions = self._validate_and_optimize_questions(processed_questions)
        
        logger.info(f"成功生成{len(validated_questions)}个问题")
        return validated_questions[:num_questions]
    
    def _analyze_subgraph(self, subgraph: nx.Graph) -> Dict:
        """分析子图结构特征"""
        analysis = {
            'nodes': list(subgraph.nodes()),
            'edges': list(subgraph.edges()),
            'node_count': subgraph.number_of_nodes(),
            'edge_count': subgraph.number_of_edges(),
            'entities': [],
            'relations': [],
            'centrality': {},
            'clusters': []
        }
        
        # 提取实体和关系
        for node in subgraph.nodes(data=True):
            entity_info = {
                'id': node[0],
                'type': node[1].get('type', 'unknown'),
                'label': node[1].get('label', str(node[0])),
                'attributes': node[1]
            }
            analysis['entities'].append(entity_info)
        
        for edge in subgraph.edges(data=True):
            relation_info = {
                'source': edge[0],
                'target': edge[1],
                'type': edge[2].get('type', 'unknown'),
                'label': edge[2].get('label', 'related_to'),
                'attributes': edge[2]
            }
            analysis['relations'].append(relation_info)
        
        # 计算中心性
        if analysis['node_count'] > 1:
            try:
                analysis['centrality'] = nx.degree_centrality(subgraph)
            except:
                analysis['centrality'] = {}
        
        # 发现簇
        if analysis['node_count'] > 2:
            try:
                components = list(nx.connected_components(subgraph))
                analysis['clusters'] = [list(comp) for comp in components]
            except:
                analysis['clusters'] = []
        
        return analysis
    
    def _calculate_question_distribution(self, num_questions: int) -> Dict[str, int]:
        """计算问题类型分布"""
        distribution = {}
        
        for q_type, ratio in self.question_type_ratios.items():
            count = max(1, int(num_questions * ratio))
            distribution[q_type] = count
        
        # 调整总数
        total_allocated = sum(distribution.values())
        if total_allocated != num_questions:
            # 按优先级调整
            diff = num_questions - total_allocated
            sorted_types = sorted(self.question_type_priorities.items(), key=lambda x: x[1])
            
            for q_type, _ in sorted_types:
                if diff == 0:
                    break
                if diff > 0:
                    distribution[q_type] += 1
                    diff -= 1
                elif distribution[q_type] > 1:
                    distribution[q_type] -= 1
                    diff += 1
        
        return distribution
    
    def _generate_questions_by_type(self, subgraph: nx.Graph, analysis: Dict, 
                                  question_type: str, count: int) -> List[Dict]:
        """按类型生成问题"""
        questions = []
        
        for _ in range(count):
            # 选择生成策略
            if random.random() < self.generation_strategy['template_ratio']:
                question = self._generate_template_question(analysis, question_type)
            else:
                question = self._generate_llm_question(subgraph, analysis, question_type)
            
            if question and self._is_question_unique(question['text']):
                questions.append(question)
                self._add_question_fingerprint(question['text'])
        
        return questions
    
    def _generate_template_question(self, analysis: Dict, question_type: str) -> Optional[Dict]:
        """基于模板生成问题"""
        templates = self.question_templates.get(question_type, [])
        if not templates:
            return None
        
        template = random.choice(templates)
        entities = analysis['entities']
        relations = analysis['relations']
        
        try:
            if question_type == 'factual':
                if entities:
                    entity = random.choice(entities)
                    question_text = template.format(entity=entity['label'])
                else:
                    return None
            
            elif question_type == 'comparison':
                if len(entities) >= 2:
                    entity1, entity2 = random.sample(entities, 2)
                    question_text = template.format(
                        entity1=entity1['label'],
                        entity2=entity2['label'],
                        attribute=random.choice(['重要', '有效', '复杂']),
                        aspect=random.choice(['功能', '性能', '特点'])
                    )
                else:
                    return None
            
            elif question_type == 'reasoning':
                if relations:
                    relation = random.choice(relations)
                    source_entity = next((e for e in entities if e['id'] == relation['source']), None)
                    target_entity = next((e for e in entities if e['id'] == relation['target']), None)
                    
                    if source_entity and target_entity:
                        question_text = template.format(
                            entity1=source_entity['label'],
                            entity2=target_entity['label'],
                            relation=relation['label']
                        )
                    else:
                        return None
                else:
                    return None
            
            elif question_type == 'multi_hop':
                if len(entities) >= 3:
                    entity1, entity2, entity3 = random.sample(entities, 3)
                    question_text = template.format(
                        entity1=entity1['label'],
                        entity2=entity2['label'],
                        entity3=entity3['label']
                    )
                else:
                    return None
            
            elif question_type == 'open_ended':
                if entities and relations:
                    entity1 = random.choice(entities)
                    entity2 = random.choice(entities)
                    relation = random.choice(relations)
                    question_text = template.format(
                        entity1=entity1['label'],
                        entity2=entity2['label'],
                        relation=relation['label'],
                        context=random.choice(['当前环境', '未来发展', '实际应用'])
                    )
                else:
                    return None
            
            else:
                return None
            
            return {
                'id': str(uuid.uuid4()),
                'text': question_text,
                'type': question_type,
                'generation_method': 'template',
                'difficulty': self._estimate_difficulty(question_text, question_type),
                'entities_involved': [e['id'] for e in entities],
                'relations_involved': [r['type'] for r in relations]
            }
            
        except Exception as e:
            logger.warning(f"模板问题生成失败: {e}")
            return None
    
    def _generate_llm_question(self, subgraph: nx.Graph, analysis: Dict, question_type: str) -> Optional[Dict]:
        """基于LLM生成问题"""
        if not self.qa_model or not self.qa_tokenizer:
            return self._generate_template_question(analysis, question_type)
        
        # 构建上下文
        context = self._build_context_for_llm(analysis, question_type)
        
        # 生成问题
        try:
            inputs = self.qa_tokenizer.encode(context, return_tensors='pt')
            if torch.cuda.is_available():
                inputs = inputs.cuda()
            
            with torch.no_grad():
                outputs = self.qa_model.generate(
                    inputs,
                    **self.generation_params,
                    pad_token_id=self.qa_tokenizer.eos_token_id
                )
            
            generated_text = self.qa_tokenizer.decode(outputs[0], skip_special_tokens=True)
            question_text = self._extract_question_from_generated_text(generated_text, context)
            
            if question_text and self._validate_question_quality(question_text):
                return {
                    'id': str(uuid.uuid4()),
                    'text': question_text,
                    'type': question_type,
                    'generation_method': 'llm',
                    'difficulty': self._estimate_difficulty(question_text, question_type),
                    'entities_involved': [e['id'] for e in analysis['entities']],
                    'relations_involved': [r['type'] for r in analysis['relations']]
                }
            
        except Exception as e:
            logger.warning(f"LLM问题生成失败: {e}")
            return self._generate_template_question(analysis, question_type)
        
        return None
    
    def _build_context_for_llm(self, analysis: Dict, question_type: str) -> str:
        """为LLM构建上下文"""
        entities_text = ", ".join([e['label'] for e in analysis['entities'][:5]])
        relations_text = ", ".join([r['label'] for r in analysis['relations'][:3]])
        
        type_instructions = {
            'factual': "生成一个关于实体基本信息的事实性问题",
            'comparison': "生成一个比较两个实体的问题",
            'reasoning': "生成一个需要推理分析的问题",
            'multi_hop': "生成一个需要多步推理的复杂问题",
            'open_ended': "生成一个开放性的讨论问题"
        }
        
        context = f"""
        实体: {entities_text}
        关系: {relations_text}
        任务: {type_instructions.get(question_type, "生成一个相关问题")}
        
        请生成一个高质量的中文问题:
        """
        
        return context.strip()
    
    def _extract_question_from_generated_text(self, generated_text: str, context: str) -> Optional[str]:
        """从生成的文本中提取问题"""
        # 移除上下文部分
        if context in generated_text:
            question_part = generated_text.replace(context, "").strip()
        else:
            question_part = generated_text.strip()
        
        # 查找问题（以问号结尾的句子）
        sentences = question_part.split('。')
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence.endswith('？') or sentence.endswith('?'):
                # 清理问题文本
                question = sentence.strip()
                if len(question) >= self.min_question_length and len(question) <= self.max_question_length:
                    return question
        
        return None
    
    def _validate_question_quality(self, question_text: str) -> bool:
        """验证问题质量"""
        # 基本长度检查
        if len(question_text) < self.min_question_length or len(question_text) > self.max_question_length:
            return False
        
        # 检查是否以问号结尾
        if not (question_text.endswith('？') or question_text.endswith('?')):
            return False
        
        # 检查是否包含无意义的重复
        words = question_text.split()
        if len(set(words)) / len(words) < 0.5:  # 词汇多样性检查
            return False
        
        return True
    
    def _estimate_difficulty(self, question_text: str, question_type: str) -> str:
        """估算问题难度"""
        difficulty_scores = {
            'factual': 1,
            'comparison': 2,
            'reasoning': 3,
            'multi_hop': 4,
            'open_ended': 3
        }
        
        base_score = difficulty_scores.get(question_type, 2)
        
        # 基于问题长度和复杂性调整
        if len(question_text) > 100:
            base_score += 1
        
        # 检查复杂词汇
        complex_keywords = ['分析', '评价', '比较', '推理', '解释', '机制', '影响']
        for keyword in complex_keywords:
            if keyword in question_text:
                base_score += 0.5
                break
        
        if base_score <= 2:
            return 'easy'
        elif base_score <= 3:
            return 'medium'
        else:
            return 'hard'
    
    def _is_question_unique(self, question_text: str) -> bool:
        """检查问题是否唯一"""
        fingerprint = self._generate_question_fingerprint(question_text)
        return fingerprint not in self.question_fingerprints
    
    def _generate_question_fingerprint(self, question_text: str) -> str:
        """生成问题指纹"""
        # 简化的指纹生成：移除标点符号，转换为小写，排序词汇
        import re
        cleaned = re.sub(r'[^\w\s]', '', question_text.lower())
        words = sorted(cleaned.split())
        return ''.join(words)
    
    def _add_question_fingerprint(self, question_text: str):
        """添加问题指纹"""
        fingerprint = self._generate_question_fingerprint(question_text)
        self.question_fingerprints.add(fingerprint)
    
    def _post_process_questions(self, questions: List[Dict]) -> List[Dict]:
        """问题后处理"""
        processed = []
        
        for question in questions:
            # 文本清理
            question['text'] = self._clean_question_text(question['text'])
            
            # 添加元数据
            question['created_at'] = self._get_timestamp()
            question['version'] = '1.0'
            
            # 添加标签
            question['tags'] = self._generate_question_tags(question)
            
            processed.append(question)
        
        return processed
    
    def _clean_question_text(self, text: str) -> str:
        """清理问题文本"""
        # 移除多余空格
        text = ' '.join(text.split())
        
        # 确保问号正确
        if not text.endswith('？') and not text.endswith('?'):
            text += '？'
        
        return text
    
    def _get_timestamp(self) -> str:
        """获取时间戳"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def _generate_question_tags(self, question: Dict) -> List[str]:
        """生成问题标签"""
        tags = [question['type'], question['difficulty']]
        
        # 基于内容添加标签
        text = question['text'].lower()
        if '比较' in text or '区别' in text:
            tags.append('comparison')
        if '为什么' in text or '原因' in text:
            tags.append('causality')
        if '如何' in text or '怎样' in text:
            tags.append('method')
        if '影响' in text or '作用' in text:
            tags.append('impact')
        
        return list(set(tags))
    
    def _validate_and_optimize_questions(self, questions: List[Dict]) -> List[Dict]:
        """验证和优化问题"""
        validated = []
        
        for question in questions:
            # 基本验证
            if self._basic_question_validation(question):
                # 尝试优化
                optimized = self._optimize_question(question)
                if optimized:
                    validated.append(optimized)
        
        return validated
    
    def _basic_question_validation(self, question: Dict) -> bool:
        """基本问题验证"""
        text = question.get('text', '')
        
        # 长度检查
        if len(text) < self.min_question_length or len(text) > self.max_question_length:
            return False
        
        # 格式检查
        if not (text.endswith('？') or text.endswith('?')):
            return False
        
        # 内容检查
        if not text.strip() or text.count(' ') < 2:
            return False
        
        return True
    
    def _optimize_question(self, question: Dict) -> Optional[Dict]:
        """优化问题"""
        # 如果问题已经很好，直接返回
        if self._calculate_question_score(question) >= self.validity_threshold:
            return question
        
        # 尝试优化
        for attempt in range(self.max_optimization_attempts):
            optimized = self._attempt_question_optimization(question)
            if optimized and self._calculate_question_score(optimized) >= self.validity_threshold:
                return optimized
        
        # 如果优化失败，根据阈值决定是否保留
        if self._calculate_question_score(question) >= 0.5:
            return question
        
        return None
    
    def _calculate_question_score(self, question: Dict) -> float:
        """计算问题质量分数"""
        score = 0.0
        text = question.get('text', '')
        
        # 长度分数 (0.2)
        length_score = min(1.0, len(text) / 80)  # 80字符为满分
        score += length_score * 0.2
        
        # 复杂性分数 (0.3)
        complexity_keywords = ['为什么', '如何', '分析', '比较', '评价', '解释']
        complexity_score = sum(1 for kw in complexity_keywords if kw in text) / len(complexity_keywords)
        score += complexity_score * 0.3
        
        # 语法分数 (0.2)
        grammar_score = 1.0 if (text.endswith('？') or text.endswith('?')) else 0.5
        score += grammar_score * 0.2
        
        # 信息量分数 (0.3)
        unique_words = len(set(text.split()))
        total_words = len(text.split())
        info_score = unique_words / total_words if total_words > 0 else 0
        score += info_score * 0.3
        
        return min(1.0, score)
    
    def _attempt_question_optimization(self, question: Dict) -> Optional[Dict]:
        """尝试优化问题"""
        optimized = question.copy()
        text = question['text']
        
        # 优化策略1：添加修饰词
        if len(text) < 70:
            modifiers = ['具体', '详细', '深入', '全面']
            modifier = random.choice(modifiers)
            if '什么' in text:
                text = text.replace('什么', f'{modifier}什么')
            elif '如何' in text:
                text = text.replace('如何', f'如何{modifier}')
        
        # 优化策略2：改进问题结构
        if not any(kw in text for kw in ['为什么', '如何', '什么']):
            if text.endswith('？'):
                text = '请分析' + text[:-1] + '的原因？'
        
        optimized['text'] = text
        return optimized

    def save_questions_to_file(self, questions: List[Dict], filepath: str):
        """保存问题到文件"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(questions, f, ensure_ascii=False, indent=2)
            logger.info(f"成功保存{len(questions)}个问题到{filepath}")
        except Exception as e:
            logger.error(f"保存问题失败: {e}")
    
    def load_questions_from_file(self, filepath: str) -> List[Dict]:
        """从文件加载问题"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                questions = json.load(f)
            logger.info(f"成功从{filepath}加载{len(questions)}个问题")
            return questions
        except Exception as e:
            logger.error(f"加载问题失败: {e}")
            return []
    
    def get_generation_statistics(self) -> Dict:
        """获取生成统计信息"""
        return {
            'total_fingerprints': len(self.question_fingerprints),
            'cached_validations': len(self.validation_cache),
            'generation_strategy': self.generation_strategy,
            'question_type_ratios': self.question_type_ratios,
            'validity_threshold': self.validity_threshold
        }