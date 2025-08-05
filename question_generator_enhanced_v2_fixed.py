"""
问题生成器 - WebSailor核心模块（优化版V2-修正版）
基于子图中节点与关系，设计QA问题
覆盖多种问题类型：事实型、比较型、推理型、多跳型、开放型等
增加了问题合理性验证和优化机制
修正了逻辑不一致的问题
"""
import uuid
import json
import logging
import random
import hashlib
from typing import List, Dict, Tuple, Optional, Set
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
from tqdm import tqdm
import networkx as nx
import numpy as np
from collections import defaultdict, Counter
import re

logger = logging.getLogger(__name__)

class QuestionGenerator:
    """
    WebSailor核心：问题生成器（优化版V2-修正版）
    基于子图生成多样化的问题，覆盖不同难度和类型
    包含问题合理性验证和优化机制
    修正了类型定义、比例配置等逻辑问题
    """
    
    def __init__(self, config: dict):
        self.config = config
        self.qg_config = config.get('question_generation', {})
        
        # 问题类型（统一定义）
        self.question_types = self.qg_config.get('question_types', [
            'factual',      # 事实型
            'comparison',   # 比较型
            'reasoning',    # 推理型
            'multi_hop',    # 多跳型
            'open_ended',   # 开放型
            'analytical',   # 分析型
            'causal',       # 因果型
            'hypothetical'  # 假设型
        ])
        
        self.complexity_levels = self.qg_config.get('complexity_levels', {})
        self.language_patterns = self.qg_config.get('language_patterns', {})
        
        # 问题类型优先级配置（修正版 - 数字越小优先级越高）
        self.question_type_priorities = {
            'reasoning': 1,      # 推理型问题 - 最高优先级
            'factual': 2,        # 事实性问题 - 高优先级
            'analytical': 2,     # 分析性问题 - 高优先级  
            'open_ended': 2,     # 开放性问题 - 高优先级
            'multi_hop': 3,      # 多跳型问题 - 中等优先级
            'comparison': 3,     # 比较型问题 - 中等优先级
            'causal': 4,         # 因果关系问题 - 较低优先级
            'hypothetical': 4    # 假设性问题 - 较低优先级
        }
        
        # 问题类型比例控制（修正版 - 确保总和为1.0）
        self.question_type_ratios = self.qg_config.get('question_type_ratios', {
            'factual': 0.20,        # 20% 事实型
            'comparison': 0.15,     # 15% 比较型  
            'reasoning': 0.25,      # 25% 推理型
            'multi_hop': 0.15,      # 15% 多跳型
            'open_ended': 0.15,     # 15% 开放型
            'analytical': 0.05,     # 5% 分析型
            'causal': 0.03,         # 3% 因果型
            'hypothetical': 0.02    # 2% 假设型
        })
        
        # 验证比例总和
        total_ratio = sum(self.question_type_ratios.values())
        if abs(total_ratio - 1.0) > 0.01:
            logger.warning(f"问题类型比例总和不等于1.0: {total_ratio:.3f}")
            # 自动归一化
            for q_type in self.question_type_ratios:
                self.question_type_ratios[q_type] /= total_ratio
            logger.info("已自动归一化比例配置")
        
        # 验证类型一致性
        self._validate_type_consistency()
        
        # 加载QA生成模型
        self._load_qa_generator()
        
        # TCL特定配置
        self.tcl_config = config.get('tcl_specific', {})
        
        # 问题模板
        self._init_question_templates()
        
        # 合理性阈值和验证配置
        self.validity_threshold = 0.7
        self.max_optimization_attempts = 3
        self.validation_cache = {}
        
        # 长度控制参数（智能调整）
        self.min_question_length = 50
        self.max_question_length = 150
        self.prefer_complex_questions = True
        self.optimal_length_range = (80, 120)  # 最优长度范围
        
        # 生成策略配置（智能混合）
        self.generation_strategy = {
            'template_ratio': 0.3,      # 30% 使用模板
            'llm_ratio': 0.7,           # 70% 使用LLM
            'min_context_entities': 2,   # 最小上下文实体数
            'question_cache': {},        # 问题缓存
            'similarity_threshold': 0.82, # 相似度阈值
            'diversity_boost': True,     # 多样性增强
            'context_awareness': True    # 上下文感知
        }
        
        # 问题指纹集合，用于去重
        self.question_fingerprints = set()
        
        # 质量评估配置
        self.quality_metrics = {
            'clarity_weight': 0.25,      # 清晰度权重
            'complexity_weight': 0.20,   # 复杂度权重
            'relevance_weight': 0.30,    # 相关性权重
            'diversity_weight': 0.15,    # 多样性权重
            'answerable_weight': 0.10    # 可回答性权重
        }
        
        # 调整生成参数（优化版）
        self.generation_params = {
            'temperature': 0.85,         # 提高创造性
            'max_new_tokens': 180,       # 增加生成长度
            'top_p': 0.92,              # 核采样参数
            'top_k': 50,                # Top-K采样
            'do_sample': True,
            'repetition_penalty': 1.1,   # 重复惩罚
            'length_penalty': 1.0,       # 长度惩罚
            'num_beams': 1,             # 束搜索
            'early_stopping': True       # 早停
        }
        
        # 动态调整参数
        self.dynamic_adjustment = {
            'enable': True,
            'learning_rate': 0.1,
            'adaptation_window': 50,     # 适应窗口
            'performance_threshold': 0.75,
            'adjustment_history': []
        }
        
        # 统计信息
        self.generation_stats = {
            'total_generated': 0,
            'type_distribution': defaultdict(int),
            'quality_scores': [],
            'generation_times': [],
            'success_rate': 0.0
        }
        
        logger.info("初始化增强版问题生成器V2（修正版），支持智能生成策略和质量评估")
    
    def _validate_type_consistency(self):
        """验证问题类型配置的一致性"""
        # 检查优先级配置
        priority_types = set(self.question_type_priorities.keys())
        ratio_types = set(self.question_type_ratios.keys())
        defined_types = set(self.question_types)
        
        # 找出不一致的类型
        missing_in_priority = ratio_types - priority_types
        missing_in_ratio = defined_types - ratio_types
        extra_in_priority = priority_types - defined_types
        
        if missing_in_priority:
            logger.warning(f"优先级配置中缺少类型: {missing_in_priority}")
            # 自动添加默认优先级
            for q_type in missing_in_priority:
                self.question_type_priorities[q_type] = 3  # 中等优先级
        
        if missing_in_ratio:
            logger.warning(f"比例配置中缺少类型: {missing_in_ratio}")
            # 自动添加默认比例
            remaining_ratio = 1.0 - sum(self.question_type_ratios.values())
            default_ratio = max(0.01, remaining_ratio / len(missing_in_ratio))
            for q_type in missing_in_ratio:
                self.question_type_ratios[q_type] = default_ratio
        
        if extra_in_priority:
            logger.warning(f"优先级配置中多余类型: {extra_in_priority}")
        
        logger.info("类型一致性验证完成")
        
    def _load_qa_generator(self):
        """加载QA生成模型（优化版）"""
        try:
            model_config = self.config['models']['qa_generator_model']
            model_path = model_config['path']
            
            logger.info(f"加载QA生成模型: {model_path}")
            
            # 优化的模型加载配置
            self.tokenizer = AutoTokenizer.from_pretrained(
                model_path, 
                trust_remote_code=True,
                padding_side='left'  # 优化批处理
            )
            
            # 设置pad_token
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
                
            self.model = AutoModelForCausalLM.from_pretrained(
                model_path,
                torch_dtype=torch.float16,
                device_map="auto",
                trust_remote_code=True,
                low_cpu_mem_usage=True,  # 优化内存使用
            )
            
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            logger.info(f"模型加载成功，使用设备: {self.device}")
            
        except Exception as e:
            logger.warning(f"无法加载指定模型，使用备用配置: {e}")
            # 降级处理
            self._load_fallback_model()
    
    def _load_fallback_model(self):
        """加载备用模型"""
        try:
            # 使用更小的模型作为备用
            fallback_model = "microsoft/DialoGPT-medium"
            self.tokenizer = AutoTokenizer.from_pretrained(fallback_model)
            self.model = AutoModelForCausalLM.from_pretrained(fallback_model)
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            self.model.to(self.device)
            logger.info(f"备用模型加载成功: {fallback_model}")
        except Exception as e:
            logger.error(f"备用模型加载失败: {e}")
            raise
    
    def _init_question_templates(self):
        """初始化问题模板（修正版）"""
        self.question_templates = {
            'factual': [
                "什么是{entity}？",
                "{entity}的定义是什么？",
                "请描述{entity}的基本特征。",
                "{entity}有哪些重要属性？",
                "关于{entity}，我们知道什么？"
            ],
            'comparison': [
                "{entity1}和{entity2}有什么区别？",
                "比较{entity1}与{entity2}的异同点。",
                "{entity1}相比{entity2}有什么优势？",
                "在某个方面，{entity1}和{entity2}如何比较？",
                "{entity1}与{entity2}哪个更好？"
            ],
            'reasoning': [
                "为什么{entity}会这样？",
                "如何解释{entity}的特性？",
                "基于什么原因{entity}具有这种特征？",
                "从逻辑上分析，{entity}为何如此？",
                "可以推断出{entity}的什么特点？"
            ],
            'multi_hop': [
                "通过{entity1}，我们如何理解{entity2}？",
                "{entity1}如何影响{entity2}，进而影响{entity3}？",
                "从{entity1}到{entity2}的关系链是什么？",
                "结合{entity1}和{entity2}，可以得出什么结论？",
                "基于{entity1}的信息，{entity2}会如何变化？"
            ],
            'open_ended': [
                "如果{entity}发生变化，会产生什么影响？",
                "你认为{entity}的未来发展趋势如何？",
                "假设{entity}不存在，会怎样？",
                "从不同角度看，{entity}意味着什么？",
                "如何创新性地运用{entity}？"
            ],
            'analytical': [
                "分析{entity}的内在机制是什么？",
                "从结构上看，{entity}是如何组成的？",
                "解析{entity}的关键要素有哪些？",
                "深入分析{entity}的运作原理。",
                "剖析{entity}的核心特征。"
            ],
            'causal': [
                "{entity1}如何导致{entity2}？",
                "什么因素造成了{entity}的状态？",
                "{entity}的根本原因是什么？",
                "解释{entity1}与{entity2}的因果关系。",
                "{entity}产生的后果是什么？"
            ],
            'hypothetical': [
                "假如{entity}具有某种特性，会怎样？",
                "设想{entity}在某种情况中的表现。",
                "如果改变{entity}的某个方面，结果如何？",
                "想象{entity}的理想状态是什么？",
                "假设{entity}不受限制，会如何？"
            ]
        }
        
        # 验证模板完整性
        missing_templates = set(self.question_types) - set(self.question_templates.keys())
        if missing_templates:
            logger.warning(f"缺少问题模板的类型: {missing_templates}")
            # 为缺少的类型添加基础模板
            for q_type in missing_templates:
                self.question_templates[q_type] = [
                    f"关于{{entity}}的{q_type}问题？",
                    f"请解释{{entity}}的{q_type}特点。"
                ]
        
        # 复杂度模板
        self.complexity_templates = {
            'simple': {
                'patterns': ["什么是", "如何", "为什么"],
                'max_entities': 2,
                'structure': "simple"
            },
            'medium': {
                'patterns': ["比较", "分析", "解释"],
                'max_entities': 3,
                'structure': "compound"
            },
            'complex': {
                'patterns': ["综合考虑", "深入分析", "系统评估"],
                'max_entities': 4,
                'structure': "complex"
            }
        }
    
    def generate_questions_from_subgraph(self, subgraph: nx.Graph, 
                                       target_count: int = 10,
                                       quality_threshold: float = 0.7) -> List[Dict]:
        """
        从子图生成问题（智能优化版）
        
        Args:
            subgraph: 输入子图
            target_count: 目标问题数量
            quality_threshold: 质量阈值
            
        Returns:
            生成的QA对列表
        """
        logger.info(f"开始从子图生成 {target_count} 个问题，质量阈值: {quality_threshold}")
        
        # 分析子图特征
        subgraph_features = self._analyze_subgraph(subgraph)
        
        # 计算问题类型分布
        type_distribution = self._calculate_type_distribution(target_count, subgraph_features)
        
        # 生成问题
        qa_pairs = []
        generation_attempts = 0
        max_attempts = target_count * 3  # 最大尝试次数
        
        with tqdm(total=target_count, desc="生成问题") as pbar:
            while len(qa_pairs) < target_count and generation_attempts < max_attempts:
                generation_attempts += 1
                
                # 选择问题类型
                question_type = self._select_question_type(type_distribution, qa_pairs)
                
                # 生成单个问题
                qa_pair = self._generate_single_question(
                    subgraph, question_type, subgraph_features
                )
                
                if qa_pair and self._validate_question_quality(qa_pair, quality_threshold):
                    # 去重检查
                    if not self._is_duplicate_question(qa_pair):
                        qa_pairs.append(qa_pair)
                        self._update_generation_stats(qa_pair)
                        pbar.update(1)
        
        # 后处理和优化
        qa_pairs = self._post_process_questions(qa_pairs)
        
        # 生成报告
        self._generate_quality_report(qa_pairs, target_count)
        
        logger.info(f"成功生成 {len(qa_pairs)} 个问题，尝试次数: {generation_attempts}")
        return qa_pairs
    
    def _analyze_subgraph(self, subgraph: nx.Graph) -> Dict:
        """分析子图特征"""
        features = {
            'node_count': subgraph.number_of_nodes(),
            'edge_count': subgraph.number_of_edges(),
            'density': nx.density(subgraph) if subgraph.number_of_nodes() > 1 else 0.0,
            'node_types': defaultdict(int),
            'relation_types': defaultdict(int),
            'centrality_scores': {},
            'complexity_score': 0.0
        }
        
        # 节点类型分析
        for node, data in subgraph.nodes(data=True):
            node_type = data.get('type', 'unknown')
            features['node_types'][node_type] += 1
        
        # 关系类型分析
        for u, v, data in subgraph.edges(data=True):
            relation_type = data.get('relation', 'unknown')
            features['relation_types'][relation_type] += 1
        
        # 中心性分析
        if features['node_count'] > 1:
            features['centrality_scores'] = nx.degree_centrality(subgraph)
        
        # 复杂度评分
        features['complexity_score'] = self._calculate_complexity_score(features)
        
        return features
    
    def _calculate_complexity_score(self, features: Dict) -> float:
        """计算子图复杂度分数"""
        node_score = min(features['node_count'] / 10.0, 1.0)
        edge_score = min(features['edge_count'] / 20.0, 1.0)
        density_score = features['density']
        type_diversity = len(features['node_types']) / max(features['node_count'], 1)
        
        complexity_score = (
            node_score * 0.3 +
            edge_score * 0.3 +
            density_score * 0.2 +
            type_diversity * 0.2
        )
        
        return complexity_score
    
    def _calculate_type_distribution(self, target_count: int, 
                                   subgraph_features: Dict) -> Dict[str, int]:
        """计算问题类型分布（智能调整）"""
        distribution = {}
        
        # 基础分布
        for q_type, ratio in self.question_type_ratios.items():
            distribution[q_type] = max(1, int(target_count * ratio))
        
        # 根据子图特征调整
        complexity = subgraph_features['complexity_score']
        
        if complexity > 0.7:  # 高复杂度
            # 增加复杂问题类型
            distribution['reasoning'] = int(distribution.get('reasoning', 0) * 1.2)
            distribution['multi_hop'] = int(distribution.get('multi_hop', 0) * 1.3)
            distribution['analytical'] = int(distribution.get('analytical', 0) * 1.5)
        elif complexity < 0.3:  # 低复杂度
            # 增加简单问题类型
            distribution['factual'] = int(distribution.get('factual', 0) * 1.2)
            distribution['open_ended'] = int(distribution.get('open_ended', 0) * 1.1)
        
        # 确保总数不超过目标
        total = sum(distribution.values())
        if total > target_count:
            # 按比例缩减
            scale_factor = target_count / total
            for q_type in distribution:
                distribution[q_type] = max(1, int(distribution[q_type] * scale_factor))
        
        return distribution
    
    def _select_question_type(self, type_distribution: Dict[str, int], 
                            current_questions: List[Dict]) -> str:
        """智能选择问题类型"""
        # 统计当前已生成的类型
        current_distribution = defaultdict(int)
        for qa in current_questions:
            current_distribution[qa.get('type', 'unknown')] += 1
        
        # 找出需要补充的类型
        needed_types = []
        for q_type, target in type_distribution.items():
            current = current_distribution[q_type]
            if current < target:
                priority = self.question_type_priorities.get(q_type, 5)
                # 优先级越高（数字越小），权重越大
                weight = max(1, 6 - priority)
                needed_types.extend([q_type] * (target - current) * weight)
        
        if needed_types:
            return random.choice(needed_types)
        else:
            # 随机选择一个类型
            return random.choice(list(self.question_type_ratios.keys()))
    
    def _generate_single_question(self, subgraph: nx.Graph, 
                                question_type: str,
                                subgraph_features: Dict) -> Optional[Dict]:
        """生成单个问题（修正版）"""
        try:
            # 选择生成方法
            use_template = random.random() < self.generation_strategy['template_ratio']
            
            if use_template:
                # 使用模板生成
                qa_pair = self._generate_from_template(subgraph, question_type)
                generation_method = 'template'
            else:
                # 使用LLM生成
                qa_pair = self._generate_with_llm(subgraph, question_type, subgraph_features)
                generation_method = 'llm'
            
            if qa_pair:
                # 添加元数据（修正：使用确定的生成方法）
                qa_pair.update({
                    'id': str(uuid.uuid4()),
                    'type': question_type,
                    'generation_method': generation_method,  # 修正：使用确定的方法
                    'subgraph_complexity': subgraph_features['complexity_score'],
                    'timestamp': self._get_timestamp()
                })
                
                # 计算质量分数
                qa_pair['quality_score'] = self._calculate_quality_score(qa_pair, subgraph)
                
            return qa_pair
            
        except Exception as e:
            logger.warning(f"生成问题失败: {e}")
            return None
    
    def _generate_from_template(self, subgraph: nx.Graph, question_type: str) -> Optional[Dict]:
        """使用模板生成问题"""
        templates = self.question_templates.get(question_type, [])
        if not templates:
            logger.warning(f"没有找到类型 {question_type} 的模板")
            return None
        
        template = random.choice(templates)
        entities = list(subgraph.nodes())
        
        if not entities:
            logger.warning("子图中没有实体节点")
            return None
        
        try:
            # 根据模板需要的实体数量选择实体
            if '{entity}' in template:
                entity = random.choice(entities)
                question = template.format(entity=entity)
                answer = f"关于{entity}的详细回答。"
                used_entities = [entity]
                
            elif '{entity1}' in template and '{entity2}' in template:
                if len(entities) >= 2:
                    entity1, entity2 = random.sample(entities, 2)
                    question = template.format(entity1=entity1, entity2=entity2)
                    answer = f"关于{entity1}和{entity2}的比较分析。"
                    used_entities = [entity1, entity2]
                else:
                    # 实体不足，使用单实体模板
                    entity = entities[0]
                    question = f"请描述{entity}的特点。"
                    answer = f"关于{entity}的详细描述。"
                    used_entities = [entity]
                    
            elif '{entity1}' in template and '{entity2}' in template and '{entity3}' in template:
                if len(entities) >= 3:
                    entity1, entity2, entity3 = random.sample(entities, 3)
                    question = template.format(entity1=entity1, entity2=entity2, entity3=entity3)
                    answer = f"关于{entity1}、{entity2}和{entity3}的综合分析。"
                    used_entities = [entity1, entity2, entity3]
                else:
                    # 实体不足，降级处理
                    return self._generate_fallback_template_question(entities, question_type)
            else:
                # 模板不包含实体占位符，直接使用
                question = template
                answer = f"关于{question_type}类型问题的回答。"
                used_entities = entities[:2]  # 取前两个实体
            
            return {
                'question': question,
                'answer': answer,
                'entities': used_entities,
                'template_used': template
            }
            
        except Exception as e:
            logger.warning(f"模板生成失败: {e}")
            return None
    
    def _generate_fallback_template_question(self, entities: List, question_type: str) -> Optional[Dict]:
        """生成备用模板问题"""
        if not entities:
            return None
        
        entity = entities[0]
        fallback_templates = {
            'factual': f"什么是{entity}？",
            'comparison': f"请描述{entity}的特点。",
            'reasoning': f"为什么{entity}很重要？",
            'multi_hop': f"如何理解{entity}？",
            'open_ended': f"你对{entity}有什么看法？",
            'analytical': f"分析{entity}的特征。",
            'causal': f"{entity}的原因是什么？",
            'hypothetical': f"假如{entity}改变会怎样？"
        }
        
        question = fallback_templates.get(question_type, f"请解释{entity}。")
        answer = f"关于{entity}的{question_type}类型回答。"
        
        return {
            'question': question,
            'answer': answer,
            'entities': [entity],
            'template_used': 'fallback'
        }
    
    def _generate_with_llm(self, subgraph: nx.Graph, question_type: str, 
                          subgraph_features: Dict) -> Optional[Dict]:
        """使用LLM生成问题（优化版）"""
        try:
            # 构建上下文
            context = self._build_context_for_llm(subgraph, question_type, subgraph_features)
            
            # 构建提示词
            prompt = self._build_generation_prompt(context, question_type)
            
            # 生成问题
            inputs = self.tokenizer.encode(prompt, return_tensors='pt').to(self.device)
            
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs,
                    **self.generation_params,
                    pad_token_id=self.tokenizer.eos_token_id
                )
            
            generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # 解析生成的内容
            qa_pair = self._parse_llm_output(generated_text, subgraph)
            
            return qa_pair
            
        except Exception as e:
            logger.warning(f"LLM生成失败: {e}")
            return None
    
    def _build_context_for_llm(self, subgraph: nx.Graph, question_type: str, 
                              subgraph_features: Dict) -> str:
        """为LLM构建上下文"""
        context_parts = []
        
        # 节点信息
        nodes_info = []
        for node, data in subgraph.nodes(data=True):
            node_desc = f"{node}"
            if 'type' in data:
                node_desc += f" (类型: {data['type']})"
            if 'description' in data:
                node_desc += f" - {data['description'][:50]}..."
            nodes_info.append(node_desc)
        
        context_parts.append("实体信息:")
        context_parts.extend(nodes_info[:5])  # 限制实体数量
        
        # 关系信息
        if subgraph.number_of_edges() > 0:
            context_parts.append("\n关系信息:")
            for u, v, data in list(subgraph.edges(data=True))[:5]:  # 限制关系数量
                relation = data.get('relation', '相关')
                context_parts.append(f"{u} {relation} {v}")
        
        return "\n".join(context_parts)
    
    def _build_generation_prompt(self, context: str, question_type: str) -> str:
        """构建生成提示词"""
        type_descriptions = {
            'factual': '事实性问题，询问具体信息',
            'comparison': '比较性问题，对比不同实体',
            'reasoning': '推理性问题，需要逻辑分析',
            'multi_hop': '多跳问题，涉及多个实体关系',
            'open_ended': '开放性问题，允许多种答案',
            'analytical': '分析性问题，深入剖析',
            'causal': '因果关系问题',
            'hypothetical': '假设性问题'
        }
        
        type_desc = type_descriptions.get(question_type, '相关问题')
        
        prompt = f"""基于以下信息，生成一个{type_desc}：

{context}

请生成一个高质量的问题和对应的答案，格式如下：
问题：[你的问题]
答案：[对应的答案]

要求：
1. 问题应该清晰、具体
2. 答案应该准确、完整
3. 符合{type_desc}的特点
4. 长度适中（60-120字）

"""
        return prompt
    
    def _parse_llm_output(self, generated_text: str, subgraph: nx.Graph) -> Optional[Dict]:
        """解析LLM输出"""
        try:
            # 提取问题和答案
            lines = generated_text.split('\n')
            question = None
            answer = None
            
            for line in lines:
                line = line.strip()
                if line.startswith('问题：'):
                    question = line[3:].strip()
                elif line.startswith('答案：'):
                    answer = line[3:].strip()
            
            if question and answer:
                # 提取相关实体
                entities = []
                for node in subgraph.nodes():
                    if str(node).lower() in question.lower() or str(node).lower() in answer.lower():
                        entities.append(node)
                
                return {
                    'question': question,
                    'answer': answer,
                    'entities': entities[:3],  # 限制实体数量
                    'generated_text': generated_text
                }
            
        except Exception as e:
            logger.warning(f"解析LLM输出失败: {e}")
        
        return None
    
    def _validate_question_quality(self, qa_pair: Dict, threshold: float) -> bool:
        """验证问题质量"""
        if not qa_pair or 'question' not in qa_pair or 'answer' not in qa_pair:
            return False
        
        question = qa_pair['question']
        answer = qa_pair['answer']
        
        # 基本检查
        if len(question) < self.min_question_length or len(question) > self.max_question_length:
            return False
        
        if len(answer) < 10:  # 答案太短
            return False
        
        # 质量分数检查
        quality_score = qa_pair.get('quality_score', 0)
        if quality_score < threshold:
            return False
        
        return True
    
    def _calculate_quality_score(self, qa_pair: Dict, subgraph: nx.Graph) -> float:
        """计算问题质量分数"""
        scores = {}
        
        question = qa_pair.get('question', '')
        answer = qa_pair.get('answer', '')
        
        # 清晰度评分
        scores['clarity'] = self._score_clarity(question)
        
        # 复杂度评分
        scores['complexity'] = self._score_complexity(question, answer)
        
        # 相关性评分
        scores['relevance'] = self._score_relevance(qa_pair, subgraph)
        
        # 多样性评分
        scores['diversity'] = self._score_diversity(question)
        
        # 可回答性评分
        scores['answerable'] = self._score_answerability(question, answer)
        
        # 加权计算总分
        total_score = sum(
            scores[metric] * weight 
            for metric, weight in self.quality_metrics.items()
            if metric.replace('_weight', '') in scores
        )
        
        return total_score
    
    def _score_clarity(self, question: str) -> float:
        """评分问题清晰度"""
        score = 0.5  # 基础分
        
        # 长度合理性
        if self.optimal_length_range[0] <= len(question) <= self.optimal_length_range[1]:
            score += 0.2
        
        # 语法结构
        if question.endswith('？') or question.endswith('?'):
            score += 0.1
        
        # 关键词检查
        question_words = ['什么', '如何', '为什么', '哪个', '怎样', '是否']
        if any(word in question for word in question_words):
            score += 0.2
        
        return min(score, 1.0)
    
    def _score_complexity(self, question: str, answer: str) -> float:
        """评分问题复杂度"""
        score = 0.3  # 基础分
        
        # 问题长度
        if len(question) > 80:
            score += 0.2
        
        # 实体数量
        entity_count = len(re.findall(r'[\u4e00-\u9fff]+', question))
        if entity_count >= 3:
            score += 0.3
        elif entity_count >= 2:
            score += 0.2
        
        # 答案复杂度
        if len(answer) > 50:
            score += 0.2
        
        return min(score, 1.0)
    
    def _score_relevance(self, qa_pair: Dict, subgraph: nx.Graph) -> float:
        """评分问题相关性"""
        question = qa_pair.get('question', '')
        entities = qa_pair.get('entities', [])
        
        if not entities:
            return 0.3
        
        # 实体覆盖率
        subgraph_entities = set(subgraph.nodes())
        covered_entities = set(entities) & subgraph_entities
        coverage_ratio = len(covered_entities) / len(subgraph_entities) if subgraph_entities else 0
        
        return min(0.3 + coverage_ratio * 0.7, 1.0)
    
    def _score_diversity(self, question: str) -> float:
        """评分问题多样性"""
        # 计算问题指纹
        fingerprint = self._calculate_question_fingerprint(question)
        
        # 检查与已有问题的相似度
        if fingerprint in self.question_fingerprints:
            return 0.2  # 重复问题
        
        # 简单的多样性评分
        unique_chars = len(set(question))
        diversity_score = min(unique_chars / 50.0, 1.0)
        
        return diversity_score
    
    def _score_answerability(self, question: str, answer: str) -> float:
        """评分问题可回答性"""
        score = 0.4  # 基础分
        
        # 答案长度合理性
        if 20 <= len(answer) <= 200:
            score += 0.3
        
        # 问答匹配度（简单检查）
        question_keywords = set(re.findall(r'[\u4e00-\u9fff]+', question))
        answer_keywords = set(re.findall(r'[\u4e00-\u9fff]+', answer))
        
        if question_keywords & answer_keywords:
            score += 0.3
        
        return min(score, 1.0)
    
    def _is_duplicate_question(self, qa_pair: Dict) -> bool:
        """检查问题是否重复"""
        question = qa_pair.get('question', '')
        fingerprint = self._calculate_question_fingerprint(question)
        
        if fingerprint in self.question_fingerprints:
            return True
        
        # 添加到指纹集合
        self.question_fingerprints.add(fingerprint)
        return False
    
    def _calculate_question_fingerprint(self, question: str) -> str:
        """计算问题指纹"""
        # 简化问题，去除标点和空格
        simplified = re.sub(r'[^\u4e00-\u9fff\w]', '', question.lower())
        return hashlib.md5(simplified.encode()).hexdigest()[:16]
    
    def _update_generation_stats(self, qa_pair: Dict):
        """更新生成统计信息"""
        self.generation_stats['total_generated'] += 1
        
        q_type = qa_pair.get('type', 'unknown')
        self.generation_stats['type_distribution'][q_type] += 1
        
        quality_score = qa_pair.get('quality_score', 0)
        self.generation_stats['quality_scores'].append(quality_score)
    
    def _post_process_questions(self, qa_pairs: List[Dict]) -> List[Dict]:
        """后处理问题列表"""
        # 按质量分数排序
        qa_pairs.sort(key=lambda x: x.get('quality_score', 0), reverse=True)
        
        # 进一步去重
        unique_questions = []
        seen_fingerprints = set()
        
        for qa in qa_pairs:
            fingerprint = self._calculate_question_fingerprint(qa.get('question', ''))
            if fingerprint not in seen_fingerprints:
                unique_questions.append(qa)
                seen_fingerprints.add(fingerprint)
        
        return unique_questions
    
    def _generate_quality_report(self, qa_pairs: List[Dict], target_count: int):
        """生成质量报告"""
        if not qa_pairs:
            logger.warning("没有生成任何问题")
            return
        
        # 基本统计
        actual_count = len(qa_pairs)
        completion_rate = actual_count / target_count
        
        # 质量统计
        quality_scores = [qa.get('quality_score', 0) for qa in qa_pairs]
        avg_quality = np.mean(quality_scores)
        
        # 类型分布
        type_counts = Counter(qa.get('type', 'unknown') for qa in qa_pairs)
        
        logger.info(f"问题生成报告:")
        logger.info(f"  目标数量: {target_count}, 实际生成: {actual_count}")
        logger.info(f"  完成率: {completion_rate:.1%}")
        logger.info(f"  平均质量分数: {avg_quality:.2f}")
        logger.info(f"  类型分布: {dict(type_counts)}")
    
    def _get_timestamp(self) -> str:
        """获取时间戳"""
        import datetime
        return datetime.datetime.now().isoformat()
    
    def get_generation_statistics(self) -> Dict:
        """获取生成统计信息"""
        stats = self.generation_stats.copy()
        
        if stats['quality_scores']:
            stats['avg_quality'] = np.mean(stats['quality_scores'])
            stats['quality_std'] = np.std(stats['quality_scores'])
        
        return stats
    
    def reset_cache(self):
        """重置缓存"""
        self.validation_cache.clear()
        self.question_fingerprints.clear()
        self.generation_strategy['question_cache'].clear()
        logger.info("缓存已重置")
    
    def validate_configuration(self) -> Dict[str, bool]:
        """验证配置的完整性和一致性"""
        validation_results = {
            'type_consistency': True,
            'ratio_sum': True,
            'template_completeness': True,
            'priority_completeness': True
        }
        
        issues = []
        
        # 检查类型一致性
        defined_types = set(self.question_types)
        ratio_types = set(self.question_type_ratios.keys())
        priority_types = set(self.question_type_priorities.keys())
        template_types = set(self.question_templates.keys())
        
        if defined_types != ratio_types:
            validation_results['type_consistency'] = False
            issues.append(f"类型定义与比例配置不一致: {defined_types ^ ratio_types}")
        
        if defined_types != priority_types:
            validation_results['priority_completeness'] = False
            issues.append(f"类型定义与优先级配置不一致: {defined_types ^ priority_types}")
        
        if defined_types != template_types:
            validation_results['template_completeness'] = False
            issues.append(f"类型定义与模板配置不一致: {defined_types ^ template_types}")
        
        # 检查比例总和
        ratio_sum = sum(self.question_type_ratios.values())
        if abs(ratio_sum - 1.0) > 0.01:
            validation_results['ratio_sum'] = False
            issues.append(f"问题类型比例总和不等于1.0: {ratio_sum:.3f}")
        
        if issues:
            logger.warning("配置验证发现问题:")
            for issue in issues:
                logger.warning(f"  - {issue}")
        else:
            logger.info("配置验证通过")
        
        return validation_results