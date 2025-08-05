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
            'template_ratio': 0.2,  # 20% 使用模板
            'llm_ratio': 0.8,       # 80% 使用LLM
            'min_context_entities': 3,  # LLM生成的最小上下文实体数
            'question_cache': {},   # 问题缓存，避免重复
            'similarity_threshold': 0.85  # 问题相似度阈值
        }
        
        # 问题指纹集合，用于去重
        self.question_fingerprints = set()
        
        logger.info("初始化20%-80%混合问题生成策略")
        
        # 调整生成参数
        self.generation_params = {
            'temperature': 0.8,  # 提高创造性
            'max_new_tokens': 150,  # 增加生成长度
            'top_p': 0.9,
            'do_sample': True
        }
        
    def _load_qa_generator(self):
        """加载QA生成模型"""
        model_config = self.config['models']['qa_generator_model']
        model_path = model_config['path']
        
        logger.info(f"加载QA生成模型: {model_path}")
        
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
            self.model = AutoModelForCausalLM.from_pretrained(
                model_path,
                torch_dtype=torch.float16,
                device_map="auto",
                trust_remote_code=True
            )
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            
            # 设置pad_token
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
                
            logger.info(f"模型加载成功，设备: {self.device}")
            
        except Exception as e:
            logger.error(f"模型加载失败: {e}")
            raise
    
    def _init_question_templates(self):
        """初始化问题模板"""
        self.question_templates = {
            'factual': {
                'zh': [
                    "{entity}的{attribute}是什么？",
                    "请描述{entity}的{property}特征。",
                    "{entity}具有哪些{category}属性？",
                    "关于{entity}的{aspect}信息，你了解多少？"
                ],
                'en': [
                    "What is the {attribute} of {entity}?",
                    "Describe the {property} characteristics of {entity}.",
                    "What {category} attributes does {entity} have?",
                    "What do you know about the {aspect} information of {entity}?"
                ]
            },
            'comparison': {
                'zh': [
                    "{entity1}和{entity2}在{aspect}方面有什么区别？",
                    "比较{entity1}与{entity2}的{property}特性。",
                    "{entity1}相比{entity2}在{dimension}上的优势是什么？",
                    "从{perspective}角度，{entity1}和{entity2}哪个更好？"
                ],
                'en': [
                    "What are the differences between {entity1} and {entity2} in terms of {aspect}?",
                    "Compare the {property} characteristics of {entity1} and {entity2}.",
                    "What advantages does {entity1} have over {entity2} in {dimension}?",
                    "From a {perspective} perspective, which is better: {entity1} or {entity2}?"
                ]
            },
            'reasoning': {
                'zh': [
                    "为什么{entity}会{action}？",
                    "如果{condition}，{entity}会如何{response}？",
                    "基于{evidence}，可以推断出{entity}的什么特征？",
                    "{entity}的{behavior}背后的原因是什么？"
                ],
                'en': [
                    "Why does {entity} {action}?",
                    "If {condition}, how would {entity} {response}?",
                    "Based on {evidence}, what characteristics of {entity} can be inferred?",
                    "What is the reason behind {entity}'s {behavior}?"
                ]
            },
            'multi_hop': {
                'zh': [
                    "通过{intermediate}，{source}如何影响{target}？",
                    "从{start}到{end}的路径中，{middle}起什么作用？",
                    "{entity1}通过哪些中介与{entity2}产生联系？",
                    "在{context}中，{path}路径的意义是什么？"
                ],
                'en': [
                    "How does {source} influence {target} through {intermediate}?",
                    "What role does {middle} play in the path from {start} to {end}?",
                    "Through which intermediaries does {entity1} connect with {entity2}?",
                    "What is the significance of the {path} path in {context}?"
                ]
            },
            'open_ended': {
                'zh': [
                    "请分析{entity}在{domain}领域的发展趋势。",
                    "如何评价{entity}对{field}的影响？",
                    "从多个角度讨论{entity}的{aspect}问题。",
                    "探讨{entity}在{context}中的作用和意义。",
                    "你认为{entity}的{future_aspect}会如何发展？"
                ],
                'en': [
                    "Please analyze the development trends of {entity} in the {domain} field.",
                    "How do you evaluate the impact of {entity} on {field}?",
                    "Discuss the {aspect} issues of {entity} from multiple perspectives.",
                    "Explore the role and significance of {entity} in {context}.",
                    "How do you think the {future_aspect} of {entity} will develop?"
                ]
            }
        }
        
        logger.info("问题模板初始化完成")
    
    def generate_questions(self, subgraphs: List[dict]) -> List[Dict[str, str]]:
        """
        基于子图生成问题
        优化版：增加比例控制和开放型问题
        """
        all_qa_pairs = []
        question_type_counters = {qtype: 0 for qtype in self.question_types}
        
        logger.info(f"开始生成问题，子图数量: {len(subgraphs)}")
        
        # 计算总问题数和各类型目标数量
        total_questions = sum(self._determine_question_count(
            len(sg.get('nodes', [])), len(sg.get('edges', []))
        ) for sg in subgraphs)
        
        type_targets = self._calculate_question_type_targets(total_questions)
        logger.info(f"问题类型分配目标: {type_targets}")
        
        for subgraph in tqdm(subgraphs, desc="生成问题"):
            try:
                # 转换为NetworkX图
                nx_graph = self._convert_dict_to_nx(subgraph)
                if nx_graph.number_of_nodes() == 0:
                    continue
                
                # 分析子图特征
                features = self._analyze_subgraph(nx_graph)
                
                # 确定该子图的问题数量
                num_questions = self._determine_question_count(
                    nx_graph.number_of_nodes(), 
                    nx_graph.number_of_edges()
                )
                
                # 根据比例选择问题类型
                selected_types = self._select_question_types_by_ratio(
                    question_type_counters, type_targets, num_questions
                )
                
                # 为每种类型生成问题
                for q_type in selected_types:
                    if q_type == 'open_ended':
                        # 生成开放型问题
                        open_qa_pairs = self._generate_open_ended_questions(
                            nx_graph, features, 'zh'
                        )
                        all_qa_pairs.extend(open_qa_pairs)
                        question_type_counters[q_type] += len(open_qa_pairs)
                    else:
                        # 生成其他类型问题
                        qa_pairs = self._generate_questions_by_type(
                            nx_graph, features, q_type, 'zh'
                        )
                        all_qa_pairs.extend(qa_pairs)
                        question_type_counters[q_type] += len(qa_pairs)
                
            except Exception as e:
                logger.error(f"子图问题生成失败: {e}")
                continue
        
        # 过滤和优化
        filtered_qa_pairs = self._filter_qa_pairs(all_qa_pairs)
        
        logger.info(f"问题生成完成，总数: {len(filtered_qa_pairs)}")
        logger.info(f"最终问题类型统计: {question_type_counters}")
        
        return filtered_qa_pairs
    
    def _calculate_question_type_targets(self, total_questions: int) -> Dict[str, int]:
        """计算各问题类型的目标数量"""
        targets = {}
        remaining = total_questions
        
        # 按比例分配
        for q_type, ratio in self.question_type_ratios.items():
            if q_type in self.question_types:
                target = int(total_questions * ratio)
                targets[q_type] = target
                remaining -= target
        
        # 将剩余的分配给第一个类型
        if remaining > 0 and self.question_types:
            targets[self.question_types[0]] += remaining
            
        return targets
    
    def _select_question_types_by_ratio(self, current_counters: Dict[str, int], 
                                      targets: Dict[str, int], 
                                      num_questions: int) -> List[str]:
        """根据比例选择问题类型"""
        selected_types = []
        
        # 计算每种类型还需要的数量
        needed = {}
        for q_type in self.question_types:
            current = current_counters.get(q_type, 0)
            target = targets.get(q_type, 0)
            needed[q_type] = max(0, target - current)
        
        # 按需求优先级选择
        sorted_types = sorted(needed.items(), key=lambda x: x[1], reverse=True)
        
        questions_to_assign = num_questions
        for q_type, need_count in sorted_types:
            if questions_to_assign <= 0:
                break
            if need_count > 0:
                # 分配问题数量（不超过需求和剩余数量）
                assign_count = min(need_count, questions_to_assign, 2)  # 每个类型最多2个
                selected_types.extend([q_type] * assign_count)
                questions_to_assign -= assign_count
        
        # 如果还有剩余，随机分配
        while questions_to_assign > 0:
            q_type = random.choice(self.question_types)
            selected_types.append(q_type)
            questions_to_assign -= 1
            
        return selected_types
    
    def _generate_open_ended_questions(self, subgraph: nx.DiGraph, 
                                     features: Dict, lang: str) -> List[Dict]:
        """生成开放型问题"""
        qa_pairs = []
        
        try:
            # 获取关键实体
            key_entities = self._identify_key_entities(subgraph)
            if not key_entities:
                return qa_pairs
            
            # 提取技术上下文
            tech_context = self._extract_technical_context(subgraph)
            
            # 生成多个开放型问题
            for entity in key_entities[:2]:  # 限制为前2个关键实体
                # 使用LLM生成复杂开放问题
                if random.random() < self.generation_strategy['llm_ratio']:
                    question = self._generate_complex_open_question_with_llm(
                        subgraph, entity, tech_context, lang
                    )
                    if question:
                        answer = self._generate_comprehensive_open_answer_with_llm(
                            question, subgraph, tech_context, lang
                        )
                        if answer:
                            qa_pairs.append({
                                'question': question,
                                'answer': answer,
                                'type': 'open_ended',
                                'language': lang,
                                'generation_method': 'llm',
                                'complexity': 'high',
                                'entity': entity
                            })
                
                # 使用模板生成
                else:
                    templates = self.question_templates['open_ended'][lang]
                    template = random.choice(templates)
                    
                    # 上下文化模板
                    question = self._contextualize_open_question(
                        template, subgraph, entity, tech_context
                    )
                    
                    if question and len(question) >= self.min_question_length:
                        answer = self._generate_open_ended_answer_with_llm(
                            question, subgraph, tech_context, lang
                        )
                        if answer:
                            qa_pairs.append({
                                'question': question,
                                'answer': answer,
                                'type': 'open_ended',
                                'language': lang,
                                'generation_method': 'template',
                                'complexity': 'medium',
                                'entity': entity
                            })
                            
        except Exception as e:
            logger.error(f"开放型问题生成失败: {e}")
            
        return qa_pairs
    
    def _extract_technical_context(self, subgraph: nx.DiGraph) -> Dict:
        """提取技术上下文信息"""
        context = {
            'domains': set(),
            'technologies': set(),
            'concepts': set(),
            'relationships': set(),
            'key_terms': set()
        }
        
        # 从节点提取上下文
        for node, data in subgraph.nodes(data=True):
            node_str = str(node).lower()
            
            # 识别技术领域
            tech_keywords = ['ai', 'ml', 'deep', 'neural', 'algorithm', 'model', 
                           'system', 'framework', 'platform', 'service']
            for keyword in tech_keywords:
                if keyword in node_str:
                    context['technologies'].add(keyword)
                    
            # 识别概念
            concept_keywords = ['concept', 'theory', 'principle', 'method', 'approach']
            for keyword in concept_keywords:
                if keyword in node_str:
                    context['concepts'].add(keyword)
                    
            context['key_terms'].add(node)
        
        # 从边提取关系类型
        for source, target, data in subgraph.edges(data=True):
            if 'type' in data:
                context['relationships'].add(data['type'])
                
        return {k: list(v) for k, v in context.items()}
    
    def _contextualize_open_question(self, base_question: str, subgraph: nx.DiGraph,
                                   focus_entity: str, tech_context: Dict) -> str:
        """为开放型问题添加上下文"""
        try:
            # 收集上下文信息
            context_info = self._collect_open_question_context(
                subgraph, focus_entity, tech_context
            )
            
            # 替换模板变量
            question = base_question.format(
                entity=focus_entity,
                domain=context_info.get('domain', '相关领域'),
                field=context_info.get('field', '该领域'),
                aspect=context_info.get('aspect', '发展'),
                context=context_info.get('context', '当前环境'),
                future_aspect=context_info.get('future_aspect', '未来发展')
            )
            
            return question
            
        except Exception as e:
            logger.error(f"开放问题上下文化失败: {e}")
            return None
    
    def _collect_open_question_context(self, subgraph: nx.DiGraph, 
                                     focus_entity: str, tech_context: Dict) -> Dict:
        """收集开放问题的上下文信息"""
        context_info = {}
        
        # 确定领域
        if tech_context['technologies']:
            context_info['domain'] = f"{tech_context['technologies'][0]}技术"
            context_info['field'] = f"{tech_context['technologies'][0]}领域"
        else:
            context_info['domain'] = "技术"
            context_info['field'] = "相关领域"
        
        # 确定方面
        aspects = ['发展趋势', '应用前景', '技术特点', '创新价值', '实际应用']
        context_info['aspect'] = random.choice(aspects)
        
        # 确定上下文
        contexts = ['当前技术环境', '行业发展背景', '实际应用场景', '技术生态系统']
        context_info['context'] = random.choice(contexts)
        
        # 确定未来方面
        future_aspects = ['技术发展', '应用拓展', '创新方向', '市场前景']
        context_info['future_aspect'] = random.choice(future_aspects)
        
        return context_info
    
    def _generate_complex_open_question_with_llm(self, subgraph: nx.DiGraph,
                                               focus_entity: str, tech_context: Dict,
                                               lang: str) -> str:
        """使用LLM生成复杂的开放型问题"""
        try:
            # 构建上下文提示
            nodes_info = list(subgraph.nodes())[:5]  # 限制节点数量
            edges_info = [(u, v) for u, v in list(subgraph.edges())[:5]]
            
            prompt = f"""基于以下技术图谱信息，生成一个深入的开放型问题：

核心实体: {focus_entity}
相关节点: {', '.join(map(str, nodes_info))}
关键关系: {', '.join([f"{u}->{v}" for u, v in edges_info])}
技术领域: {', '.join(tech_context.get('technologies', []))}

请生成一个需要深入分析和多角度思考的开放型问题，问题应该：
1. 围绕核心实体 {focus_entity}
2. 结合相关技术上下文
3. 鼓励批判性思维和深入分析
4. 长度在60-120字之间
5. 避免简单的是非题

问题："""

            # 生成问题
            inputs = self.tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512)
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    **self.generation_params,
                    pad_token_id=self.tokenizer.pad_token_id
                )
            
            generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            question = generated_text[len(prompt):].strip()
            
            # 清理和验证问题
            question = self._clean_generated_question(question)
            
            if (question and 
                self.min_question_length <= len(question) <= self.max_question_length and
                self._is_question_unique(question)):
                return question
                
        except Exception as e:
            logger.error(f"LLM开放问题生成失败: {e}")
            
        return None
    
    def _generate_open_ended_answer_with_llm(self, question: str, subgraph: nx.DiGraph,
                                           tech_context: Dict, lang: str) -> str:
        """使用LLM生成开放型问题的答案"""
        try:
            # 构建答案生成提示
            nodes_info = list(subgraph.nodes())[:5]
            edges_info = [(u, v) for u, v in list(subgraph.edges())[:5]]
            
            prompt = f"""基于以下技术图谱信息，为开放型问题提供全面的答案：

问题: {question}

技术图谱信息:
- 相关节点: {', '.join(map(str, nodes_info))}
- 关键关系: {', '.join([f"{u}->{v}" for u, v in edges_info])}
- 技术领域: {', '.join(tech_context.get('technologies', []))}

请提供一个全面、深入的答案，包括：
1. 多角度分析
2. 具体技术细节
3. 实际应用场景
4. 发展趋势预测
5. 客观评价

答案："""

            inputs = self.tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512)
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=200,
                    temperature=0.7,
                    top_p=0.9,
                    do_sample=True,
                    pad_token_id=self.tokenizer.pad_token_id
                )
            
            generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            answer = generated_text[len(prompt):].strip()
            
            # 清理答案
            answer = self._clean_generated_answer(answer)
            
            if answer and len(answer) >= 100:  # 确保答案足够详细
                return answer
                
        except Exception as e:
            logger.error(f"开放型答案生成失败: {e}")
            
        return None
    
    def _generate_comprehensive_open_answer_with_llm(self, question: str, subgraph: nx.DiGraph,
                                                   tech_context: Dict, lang: str) -> str:
        """生成更全面的开放型答案"""
        return self._generate_open_ended_answer_with_llm(question, subgraph, tech_context, lang)
    
    def _determine_question_count(self, num_nodes: int, num_edges: int) -> int:
        """根据子图大小确定问题数量"""
        if num_nodes <= 3:
            return 1
        elif num_nodes <= 6:
            return 2
        elif num_nodes <= 10:
            return 3
        else:
            return min(4, num_nodes // 3)
    
    def _is_question_type_suitable(self, q_type: str, num_nodes: int, num_edges: int) -> bool:
        """判断问题类型是否适合当前子图"""
        if q_type == 'multi_hop' and num_nodes < 3:
            return False
        if q_type == 'comparison' and num_nodes < 2:
            return False
        if q_type == 'open_ended' and num_nodes < 2:
            return False
        return True
    
    def _validate_qa(self, qa: Dict) -> bool:
        """验证QA对的质量"""
        question = qa.get('question', '')
        answer = qa.get('answer', '')
        
        # 基本验证
        if not question or not answer:
            return False
        
        # 长度验证
        if len(question) < 10 or len(answer) < 20:
            return False
        
        # 重复验证
        if not self._is_question_unique(question):
            return False
            
        return True
    
    def _analyze_subgraph(self, subgraph) -> Dict:
        """分析子图特征"""
        features = {
            'num_nodes': subgraph.number_of_nodes(),
            'num_edges': subgraph.number_of_edges(),
            'density': nx.density(subgraph) if subgraph.number_of_nodes() > 1 else 0,
            'key_entities': self._identify_key_entities(subgraph),
            'path_patterns': self._identify_path_patterns(subgraph)
        }
        
        return features
    
    def _convert_dict_to_nx(self, subgraph_dict: dict) -> nx.DiGraph:
        """将字典格式的子图转换为NetworkX图"""
        G = nx.DiGraph()
        
        # 添加节点
        nodes = subgraph_dict.get('nodes', [])
        for node in nodes:
            if isinstance(node, dict):
                node_id = node.get('id', node.get('name', str(node)))
                G.add_node(node_id, **node)
            else:
                G.add_node(node)
        
        # 添加边
        edges = subgraph_dict.get('edges', [])
        for edge in edges:
            if isinstance(edge, dict):
                source = edge.get('source', edge.get('from'))
                target = edge.get('target', edge.get('to'))
                if source and target:
                    G.add_edge(source, target, **edge)
            elif isinstance(edge, (list, tuple)) and len(edge) >= 2:
                G.add_edge(edge[0], edge[1])
                
        return G
    
    def _identify_key_entities(self, subgraph):
        """识别子图中的关键实体"""
        if subgraph.number_of_nodes() == 0:
            return []
        
        # 计算节点重要性
        centrality_scores = {}
        
        # 度中心性
        degree_centrality = nx.degree_centrality(subgraph)
        
        # 如果图连通，计算其他中心性
        if nx.is_weakly_connected(subgraph):
            try:
                betweenness_centrality = nx.betweenness_centrality(subgraph)
                closeness_centrality = nx.closeness_centrality(subgraph)
            except:
                betweenness_centrality = {node: 0 for node in subgraph.nodes()}
                closeness_centrality = {node: 0 for node in subgraph.nodes()}
        else:
            betweenness_centrality = {node: 0 for node in subgraph.nodes()}
            closeness_centrality = {node: 0 for node in subgraph.nodes()}
        
        # 综合评分
        for node in subgraph.nodes():
            score = (degree_centrality.get(node, 0) * 0.4 + 
                    betweenness_centrality.get(node, 0) * 0.3 + 
                    closeness_centrality.get(node, 0) * 0.3)
            centrality_scores[node] = score
        
        # 返回前3个关键实体
        sorted_entities = sorted(centrality_scores.items(), key=lambda x: x[1], reverse=True)
        return [entity for entity, score in sorted_entities[:3]]
    
    def _identify_path_patterns(self, subgraph: nx.DiGraph) -> List[Dict]:
        """识别子图中的路径模式"""
        patterns = []
        
        try:
            # 寻找简单路径
            nodes = list(subgraph.nodes())
            for i, source in enumerate(nodes):
                for target in nodes[i+1:]:
                    try:
                        paths = list(nx.all_simple_paths(subgraph, source, target, cutoff=3))
                        for path in paths[:2]:  # 限制路径数量
                            if len(path) >= 3:  # 至少3个节点的路径
                                patterns.append({
                                    'type': 'path',
                                    'nodes': path,
                                    'length': len(path)
                                })
                    except:
                        continue
                        
        except Exception as e:
            logger.debug(f"路径模式识别失败: {e}")
            
        return patterns[:5]  # 限制模式数量
    
    def _clean_generated_question(self, question):
        """清理生成的问题"""
        if not question:
            return None
            
        # 移除多余的空白
        question = ' '.join(question.split())
        
        # 确保以问号结尾
        if not question.endswith('？') and not question.endswith('?'):
            question += '？'
            
        # 移除重复的标点
        question = question.replace('？？', '？').replace('??', '?')
        
        return question
    
    def _clean_generated_answer(self, answer):
        """清理生成的答案"""
        if not answer:
            return None
            
        # 移除多余的空白
        answer = ' '.join(answer.split())
        
        # 确保以句号结尾
        if not answer.endswith('。') and not answer.endswith('.'):
            answer += '。'
            
        return answer
    
    def _is_question_unique(self, question):
        """检查问题是否唯一"""
        # 生成问题指纹
        fingerprint = hash(question.lower().replace(' ', ''))
        
        if fingerprint in self.question_fingerprints:
            return False
            
        self.question_fingerprints.add(fingerprint)
        return True
    
    def _filter_qa_pairs(self, qa_pairs: List[Dict]) -> List[Dict]:
        """过滤和优化QA对"""
        filtered_pairs = []
        
        for qa in qa_pairs:
            if self._validate_qa(qa):
                # 计算质量分数
                quality_score = self._calculate_question_quality_score(qa)
                qa['quality_score'] = quality_score
                
                if quality_score >= self.validity_threshold:
                    filtered_pairs.append(qa)
        
        # 按质量分数排序
        filtered_pairs.sort(key=lambda x: x.get('quality_score', 0), reverse=True)
        
        # 平衡问题类型
        balanced_pairs = self._balance_question_types(filtered_pairs)
        
        return balanced_pairs
    
    def _calculate_question_quality_score(self, qa: Dict) -> float:
        """计算问题质量分数"""
        score = 0.0
        question = qa.get('question', '')
        answer = qa.get('answer', '')
        
        # 长度分数 (0.3)
        q_len = len(question)
        if self.min_question_length <= q_len <= self.max_question_length:
            score += 0.3
        elif q_len > self.max_question_length:
            score += 0.2
        else:
            score += 0.1
            
        # 答案质量分数 (0.3)
        a_len = len(answer)
        if a_len >= 50:
            score += 0.3
        elif a_len >= 30:
            score += 0.2
        else:
            score += 0.1
            
        # 复杂性分数 (0.2)
        complexity = qa.get('complexity', 'medium')
        if complexity == 'high':
            score += 0.2
        elif complexity == 'medium':
            score += 0.15
        else:
            score += 0.1
            
        # 类型多样性分数 (0.2)
        q_type = qa.get('type', '')
        if q_type in ['open_ended', 'reasoning', 'multi_hop']:
            score += 0.2
        elif q_type in ['comparison']:
            score += 0.15
        else:
            score += 0.1
            
        return min(score, 1.0)
    
    def _balance_question_types(self, qa_pairs: List[Dict]) -> List[Dict]:
        """平衡问题类型分布"""
        if not qa_pairs:
            return qa_pairs
            
        # 按类型分组
        type_groups = {}
        for qa in qa_pairs:
            q_type = qa.get('type', 'factual')
            if q_type not in type_groups:
                type_groups[q_type] = []
            type_groups[q_type].append(qa)
        
        # 计算目标分布
        total_questions = len(qa_pairs)
        balanced_pairs = []
        
        for q_type in self.question_types:
            if q_type in type_groups:
                target_count = int(total_questions * self.question_type_ratios.get(q_type, 0.2))
                # 选择质量最高的问题
                type_questions = sorted(type_groups[q_type], 
                                      key=lambda x: x.get('quality_score', 0), 
                                      reverse=True)
                balanced_pairs.extend(type_questions[:target_count])
        
        return balanced_pairs
    
    def _generate_questions_by_type(self, subgraph: nx.DiGraph, features: Dict, 
                                  q_type: str, lang: str) -> List[Dict]:
        """根据类型生成问题"""
        if q_type == 'factual':
            return self._generate_factual_questions(subgraph, features, lang)
        elif q_type == 'comparison':
            return self._generate_comparison_questions(subgraph, features, lang)
        elif q_type == 'reasoning':
            return self._generate_reasoning_questions(subgraph, features, lang)
        elif q_type == 'multi_hop':
            return self._generate_multihop_questions(subgraph, features, lang)
        else:
            return []
    
    def _generate_factual_questions(self, subgraph: nx.DiGraph, features: Dict, lang: str) -> List[Dict]:
        """生成事实型问题"""
        qa_pairs = []
        key_entities = features.get('key_entities', [])
        
        for entity in key_entities[:2]:
            templates = self.question_templates['factual'][lang]
            template = random.choice(templates)
            
            question = template.format(
                entity=entity,
                attribute="属性",
                property="特性",
                category="类别",
                aspect="方面"
            )
            
            answer = f"{entity}是一个重要的实体，具有多种特征和属性。"
            
            qa_pairs.append({
                'question': question,
                'answer': answer,
                'type': 'factual',
                'language': lang,
                'generation_method': 'template'
            })
        
        return qa_pairs
    
    def _generate_comparison_questions(self, subgraph: nx.DiGraph, features: Dict, lang: str) -> List[Dict]:
        """生成比较型问题"""
        qa_pairs = []
        key_entities = features.get('key_entities', [])
        
        if len(key_entities) >= 2:
            entity1, entity2 = key_entities[0], key_entities[1]
            templates = self.question_templates['comparison'][lang]
            template = random.choice(templates)
            
            question = template.format(
                entity1=entity1,
                entity2=entity2,
                aspect="功能",
                property="特性",
                dimension="性能",
                perspective="技术"
            )
            
            answer = f"{entity1}和{entity2}在多个方面存在差异，各有其特点和优势。"
            
            qa_pairs.append({
                'question': question,
                'answer': answer,
                'type': 'comparison',
                'language': lang,
                'generation_method': 'template'
            })
        
        return qa_pairs
    
    def _generate_reasoning_questions(self, subgraph: nx.DiGraph, features: Dict, lang: str) -> List[Dict]:
        """生成推理型问题"""
        qa_pairs = []
        key_entities = features.get('key_entities', [])
        
        for entity in key_entities[:1]:
            templates = self.question_templates['reasoning'][lang]
            template = random.choice(templates)
            
            question = template.format(
                entity=entity,
                action="发挥作用",
                condition="特定条件下",
                response="响应",
                evidence="现有证据",
                behavior="行为"
            )
            
            answer = f"基于分析，{entity}的行为和特征可以通过多种因素来解释。"
            
            qa_pairs.append({
                'question': question,
                'answer': answer,
                'type': 'reasoning',
                'language': lang,
                'generation_method': 'template'
            })
        
        return qa_pairs
    
    def _generate_multihop_questions(self, subgraph: nx.DiGraph, features: Dict, lang: str) -> List[Dict]:
        """生成多跳型问题"""
        qa_pairs = []
        path_patterns = features.get('path_patterns', [])
        
        for pattern in path_patterns[:1]:
            if pattern['type'] == 'path' and len(pattern['nodes']) >= 3:
                path = pattern['nodes']
                templates = self.question_templates['multi_hop'][lang]
                template = random.choice(templates)
                
                question = template.format(
                    source=path[0],
                    target=path[-1],
                    intermediate=path[1],
                    start=path[0],
                    end=path[-1],
                    middle=path[1],
                    entity1=path[0],
                    entity2=path[-1],
                    context="技术关系",
                    path="传递路径"
                )
                
                answer = f"在从{path[0]}到{path[-1]}的路径中，{path[1]}作为中介节点发挥关键作用。"
                
                qa_pairs.append({
                    'question': question,
                    'answer': answer,
                    'type': 'multi_hop',
                    'language': lang,
                    'generation_method': 'template'
                })
        
        return qa_pairs