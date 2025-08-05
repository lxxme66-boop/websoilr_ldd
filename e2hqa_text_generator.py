"""
E2HQA Text-Only QA Generation System
基于文本的问答生成系统，实现从简单QA到复杂QA的转换
包含轨迹生成、拒绝采样和质量过滤机制
"""

import json
import logging
import random
import asyncio
import re
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum
import openai
from openai import AsyncOpenAI
import numpy as np
from datetime import datetime
import hashlib

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QAType(Enum):
    """问答类型枚举"""
    SIMPLE_FACTUAL = "simple_factual"
    COMPLEX_REASONING = "complex_reasoning" 
    MULTI_HOP = "multi_hop"
    ANALYTICAL = "analytical"
    OPEN_ENDED = "open_ended"

class CoTType(Enum):
    """思维链类型"""
    SHORT_COT = "short_cot"  # GPT-4生成
    LONG_COT = "long_cot"    # LRMs如QwQ-Plus生成

@dataclass
class QATrajectory:
    """QA轨迹数据结构"""
    question: str
    answer: str
    reasoning_steps: List[str]
    cot_type: CoTType
    qa_type: QAType
    confidence_score: float
    quality_metrics: Dict[str, float]
    trajectory_id: str
    source_simple_qa: Optional[Dict] = None

class E2HQAGenerator:
    """E2HQA文本问答生成器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.gpt4_client = None
        self.lrm_client = None
        self._init_clients()
        
        # 拒绝采样参数
        self.rejection_sampling_n = config.get('rejection_sampling_n', 5)
        self.quality_threshold = config.get('quality_threshold', 0.7)
        
        # 轨迹过滤参数
        self.filter_config = config.get('trajectory_filter', {
            'format_validation': True,
            'answer_correctness': True,
            'quality_assessment': True,
            'redundancy_check': True,
            'alignment_check': True,
            'reasoning_coherence': True
        })
        
        # QA类型分布
        self.qa_type_ratios = config.get('qa_type_ratios', {
            'simple_factual': 0.2,
            'complex_reasoning': 0.3,
            'multi_hop': 0.2,
            'analytical': 0.15,
            'open_ended': 0.15
        })
        
        # CoT类型分布
        self.cot_type_ratios = config.get('cot_type_ratios', {
            'short_cot': 0.4,  # GPT-4生成
            'long_cot': 0.6    # LRMs生成
        })
        
        logger.info("E2HQA文本问答生成器初始化完成")
    
    def _init_clients(self):
        """初始化API客户端"""
        # GPT-4客户端 (用于short CoT)
        gpt4_config = self.config.get('gpt4_config', {})
        if gpt4_config:
            self.gpt4_client = AsyncOpenAI(
                api_key=gpt4_config.get('api_key'),
                base_url=gpt4_config.get('base_url', 'https://api.openai.com/v1')
            )
        
        # LRM客户端 (用于long CoT，如QwQ-Plus)
        lrm_config = self.config.get('lrm_config', {})
        if lrm_config:
            self.lrm_client = AsyncOpenAI(
                api_key=lrm_config.get('api_key'),
                base_url=lrm_config.get('base_url')
            )
    
    async def generate_qa_from_text(self, text: str, num_questions: int = 10) -> List[QATrajectory]:
        """从文本生成QA轨迹"""
        logger.info(f"开始从文本生成{num_questions}个QA轨迹")
        
        # 1. 生成简单QA
        simple_qas = await self._generate_simple_qas(text, num_questions)
        
        # 2. 转换为复杂QA轨迹
        trajectories = []
        for simple_qa in simple_qas:
            # 为每个简单QA生成N个候选轨迹
            candidates = await self._generate_trajectory_candidates(simple_qa, text)
            
            # 选择最佳轨迹
            best_trajectory = self._select_best_trajectory(candidates)
            if best_trajectory:
                trajectories.append(best_trajectory)
        
        logger.info(f"成功生成{len(trajectories)}个高质量QA轨迹")
        return trajectories
    
    async def _generate_simple_qas(self, text: str, num_questions: int) -> List[Dict]:
        """生成简单QA作为起点"""
        prompt = f"""
基于以下文本，生成{num_questions}个简单的问答对。要求：
1. 问题应该直接基于文本内容
2. 答案应该准确且简洁
3. 涵盖文本的主要信息点
4. 问题类型多样化（事实型、定义型、关系型等）

文本内容：
{text}

请以JSON格式返回，格式如下：
[
  {{
    "question": "问题内容",
    "answer": "答案内容",
    "question_type": "factual/definition/relationship",
    "difficulty": "simple"
  }}
]
"""
        
        try:
            response = await self.gpt4_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=2000
            )
            
            content = response.choices[0].message.content
            simple_qas = json.loads(content)
            
            logger.info(f"生成了{len(simple_qas)}个简单QA")
            return simple_qas
            
        except Exception as e:
            logger.error(f"生成简单QA失败: {e}")
            return []
    
    async def _generate_trajectory_candidates(self, simple_qa: Dict, context_text: str) -> List[QATrajectory]:
        """为简单QA生成多个轨迹候选"""
        candidates = []
        
        for i in range(self.rejection_sampling_n):
            # 随机选择QA类型和CoT类型
            qa_type = self._sample_qa_type()
            cot_type = self._sample_cot_type()
            
            try:
                trajectory = await self._generate_single_trajectory(
                    simple_qa, context_text, qa_type, cot_type
                )
                if trajectory:
                    candidates.append(trajectory)
            except Exception as e:
                logger.warning(f"生成轨迹候选{i+1}失败: {e}")
                continue
        
        logger.info(f"为简单QA生成了{len(candidates)}个轨迹候选")
        return candidates
    
    async def _generate_single_trajectory(self, simple_qa: Dict, context_text: str, 
                                        qa_type: QAType, cot_type: CoTType) -> Optional[QATrajectory]:
        """生成单个QA轨迹"""
        
        # 构建提示词
        prompt = self._build_trajectory_prompt(simple_qa, context_text, qa_type, cot_type)
        
        # 选择模型客户端
        client = self.gpt4_client if cot_type == CoTType.SHORT_COT else self.lrm_client
        model = "gpt-4" if cot_type == CoTType.SHORT_COT else "qwq-plus"
        
        if not client:
            logger.warning(f"客户端未配置: {cot_type}")
            return None
        
        try:
            response = await client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.8 if cot_type == CoTType.LONG_COT else 0.7,
                max_tokens=3000 if cot_type == CoTType.LONG_COT else 1500
            )
            
            content = response.choices[0].message.content
            
            # 解析响应生成轨迹
            trajectory = self._parse_trajectory_response(
                content, simple_qa, qa_type, cot_type
            )
            
            return trajectory
            
        except Exception as e:
            logger.error(f"生成轨迹失败: {e}")
            return None
    
    def _build_trajectory_prompt(self, simple_qa: Dict, context_text: str, 
                               qa_type: QAType, cot_type: CoTType) -> str:
        """构建轨迹生成提示词"""
        
        base_prompt = f"""
基于以下简单问答对和上下文，生成一个更复杂的问答轨迹。

原始简单QA：
问题: {simple_qa['question']}
答案: {simple_qa['answer']}

上下文文本：
{context_text}

目标要求：
- QA类型: {qa_type.value}
- 推理类型: {cot_type.value}
"""
        
        # 根据QA类型添加特定要求
        if qa_type == QAType.COMPLEX_REASONING:
            base_prompt += """
- 将简单问题转换为需要多步推理的复杂问题
- 答案需要包含清晰的逻辑推理过程
- 涉及因果关系、逻辑推导或复杂分析
"""
        elif qa_type == QAType.MULTI_HOP:
            base_prompt += """
- 创建需要多个信息跳跃的问题
- 答案需要整合文本中的多个相关信息点
- 体现信息之间的关联性和层次性
"""
        elif qa_type == QAType.ANALYTICAL:
            base_prompt += """
- 生成需要分析、评估或比较的问题
- 答案应包含深入的分析和见解
- 体现批判性思维和综合能力
"""
        elif qa_type == QAType.OPEN_ENDED:
            base_prompt += """
- 创建开放性问题，没有标准答案
- 鼓励创新思维和多角度思考
- 答案应提供合理的观点和论证
"""
        
        # 根据CoT类型添加推理要求
        if cot_type == CoTType.SHORT_COT:
            base_prompt += """
推理要求（Short CoT）：
- 提供3-5步清晰的推理步骤
- 每步推理简洁明了
- 逻辑链条完整
"""
        else:  # LONG_COT
            base_prompt += """
推理要求（Long CoT）：
- 提供详细的推理过程（8-15步）
- 包含深入的思考和分析
- 考虑多种可能性和角度
- 体现复杂的推理链条
"""
        
        base_prompt += """
请以JSON格式返回，格式如下：
{
  "complex_question": "转换后的复杂问题",
  "detailed_answer": "详细答案",
  "reasoning_steps": ["推理步骤1", "推理步骤2", ...],
  "confidence_score": 0.85,
  "key_concepts": ["关键概念1", "关键概念2", ...],
  "difficulty_level": "medium/hard/expert"
}
"""
        
        return base_prompt
    
    def _parse_trajectory_response(self, response_content: str, simple_qa: Dict, 
                                 qa_type: QAType, cot_type: CoTType) -> Optional[QATrajectory]:
        """解析轨迹生成响应"""
        try:
            # 提取JSON内容
            json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
            if not json_match:
                logger.warning("响应中未找到JSON格式内容")
                return None
            
            data = json.loads(json_match.group())
            
            # 生成轨迹ID
            trajectory_id = hashlib.md5(
                f"{data.get('complex_question', '')}{datetime.now().isoformat()}".encode()
            ).hexdigest()[:12]
            
            # 创建轨迹对象
            trajectory = QATrajectory(
                question=data.get('complex_question', ''),
                answer=data.get('detailed_answer', ''),
                reasoning_steps=data.get('reasoning_steps', []),
                cot_type=cot_type,
                qa_type=qa_type,
                confidence_score=data.get('confidence_score', 0.5),
                quality_metrics={},
                trajectory_id=trajectory_id,
                source_simple_qa=simple_qa
            )
            
            return trajectory
            
        except Exception as e:
            logger.error(f"解析轨迹响应失败: {e}")
            return None
    
    def _sample_qa_type(self) -> QAType:
        """随机采样QA类型"""
        types = list(self.qa_type_ratios.keys())
        weights = list(self.qa_type_ratios.values())
        selected = np.random.choice(types, p=weights)
        return QAType(selected)
    
    def _sample_cot_type(self) -> CoTType:
        """随机采样CoT类型"""
        types = list(self.cot_type_ratios.keys())
        weights = list(self.cot_type_ratios.values())
        selected = np.random.choice(types, p=weights)
        return CoTType(selected)
    
    def _select_best_trajectory(self, candidates: List[QATrajectory]) -> Optional[QATrajectory]:
        """从候选轨迹中选择最佳轨迹"""
        if not candidates:
            return None
        
        # 对每个候选进行质量评估
        scored_candidates = []
        for candidate in candidates:
            # 轨迹过滤
            if not self._filter_trajectory(candidate):
                continue
            
            # 质量评估
            quality_score = self._assess_trajectory_quality(candidate)
            candidate.quality_metrics['overall_score'] = quality_score
            
            if quality_score >= self.quality_threshold:
                scored_candidates.append((candidate, quality_score))
        
        if not scored_candidates:
            logger.warning("没有候选轨迹通过质量过滤")
            return None
        
        # 选择得分最高的轨迹
        best_candidate = max(scored_candidates, key=lambda x: x[1])[0]
        logger.info(f"选择最佳轨迹，质量得分: {best_candidate.quality_metrics['overall_score']:.3f}")
        
        return best_candidate
    
    def _filter_trajectory(self, trajectory: QATrajectory) -> bool:
        """轨迹过滤"""
        
        # 格式验证
        if self.filter_config.get('format_validation', True):
            if not self._validate_format(trajectory):
                logger.debug("轨迹格式验证失败")
                return False
        
        # 答案正确性验证
        if self.filter_config.get('answer_correctness', True):
            if not self._validate_answer_correctness(trajectory):
                logger.debug("答案正确性验证失败")
                return False
        
        # 冗余检查
        if self.filter_config.get('redundancy_check', True):
            if self._check_redundancy(trajectory):
                logger.debug("检测到冗余内容")
                return False
        
        # 目标对齐检查
        if self.filter_config.get('alignment_check', True):
            if not self._check_alignment(trajectory):
                logger.debug("目标对齐检查失败")
                return False
        
        # 推理合理性检查
        if self.filter_config.get('reasoning_coherence', True):
            if not self._check_reasoning_coherence(trajectory):
                logger.debug("推理合理性检查失败")
                return False
        
        return True
    
    def _validate_format(self, trajectory: QATrajectory) -> bool:
        """格式验证"""
        # 检查必要字段
        if not trajectory.question or not trajectory.answer:
            return False
        
        # 检查问题长度
        if len(trajectory.question) < 10 or len(trajectory.question) > 500:
            return False
        
        # 检查答案长度
        if len(trajectory.answer) < 20 or len(trajectory.answer) > 2000:
            return False
        
        # 检查推理步骤
        if not trajectory.reasoning_steps or len(trajectory.reasoning_steps) < 2:
            return False
        
        return True
    
    def _validate_answer_correctness(self, trajectory: QATrajectory) -> bool:
        """答案正确性验证"""
        # 检查答案是否与问题相关
        question_lower = trajectory.question.lower()
        answer_lower = trajectory.answer.lower()
        
        # 简单的关键词匹配检查
        question_keywords = set(re.findall(r'\b\w+\b', question_lower))
        answer_keywords = set(re.findall(r'\b\w+\b', answer_lower))
        
        # 计算关键词重叠度
        if len(question_keywords) > 0:
            overlap_ratio = len(question_keywords & answer_keywords) / len(question_keywords)
            return overlap_ratio > 0.1  # 至少10%的关键词重叠
        
        return True
    
    def _check_redundancy(self, trajectory: QATrajectory) -> bool:
        """检查冗余内容"""
        # 检查推理步骤中的重复内容
        steps_text = ' '.join(trajectory.reasoning_steps)
        words = steps_text.split()
        
        if len(words) == 0:
            return True
        
        # 计算重复词汇比例
        unique_words = set(words)
        redundancy_ratio = 1 - (len(unique_words) / len(words))
        
        return redundancy_ratio > 0.6  # 超过60%重复认为冗余
    
    def _check_alignment(self, trajectory: QATrajectory) -> bool:
        """检查目标对齐"""
        # 检查问题和答案是否对齐
        if "如何" in trajectory.question or "怎样" in trajectory.question:
            # 方法类问题应该包含具体步骤或方法
            return any(word in trajectory.answer for word in ["步骤", "方法", "通过", "可以"])
        
        if "为什么" in trajectory.question or "原因" in trajectory.question:
            # 原因类问题应该包含解释
            return any(word in trajectory.answer for word in ["因为", "由于", "原因", "导致"])
        
        if "什么" in trajectory.question:
            # 定义类问题应该包含定义或描述
            return len(trajectory.answer) > 30  # 至少包含一定长度的描述
        
        return True
    
    def _check_reasoning_coherence(self, trajectory: QATrajectory) -> bool:
        """检查推理合理性"""
        if not trajectory.reasoning_steps:
            return False
        
        # 检查推理步骤的连贯性
        steps = trajectory.reasoning_steps
        
        # 检查每个步骤是否有实际内容
        for step in steps:
            if len(step.strip()) < 10:  # 步骤太短
                return False
        
        # 检查逻辑连接词的使用
        logic_words = ["因此", "所以", "由于", "基于", "根据", "通过", "然后", "接下来", "最后"]
        steps_text = ' '.join(steps)
        logic_word_count = sum(1 for word in logic_words if word in steps_text)
        
        # 推理步骤应该包含一定数量的逻辑连接词
        return logic_word_count >= len(steps) * 0.3
    
    def _assess_trajectory_quality(self, trajectory: QATrajectory) -> float:
        """评估轨迹质量"""
        scores = []
        
        # 1. 复杂度评分
        complexity_score = self._score_complexity(trajectory)
        scores.append(complexity_score)
        trajectory.quality_metrics['complexity'] = complexity_score
        
        # 2. 推理质量评分
        reasoning_score = self._score_reasoning_quality(trajectory)
        scores.append(reasoning_score)
        trajectory.quality_metrics['reasoning_quality'] = reasoning_score
        
        # 3. 内容丰富度评分
        richness_score = self._score_content_richness(trajectory)
        scores.append(richness_score)
        trajectory.quality_metrics['content_richness'] = richness_score
        
        # 4. 语言质量评分
        language_score = self._score_language_quality(trajectory)
        scores.append(language_score)
        trajectory.quality_metrics['language_quality'] = language_score
        
        # 5. 创新性评分
        novelty_score = self._score_novelty(trajectory)
        scores.append(novelty_score)
        trajectory.quality_metrics['novelty'] = novelty_score
        
        # 计算加权平均分
        weights = [0.25, 0.25, 0.2, 0.15, 0.15]  # 各维度权重
        overall_score = sum(score * weight for score, weight in zip(scores, weights))
        
        return min(overall_score, 1.0)  # 确保分数不超过1.0
    
    def _score_complexity(self, trajectory: QATrajectory) -> float:
        """评估复杂度"""
        score = 0.0
        
        # 问题复杂度
        question_words = len(trajectory.question.split())
        if question_words > 15:
            score += 0.3
        elif question_words > 10:
            score += 0.2
        else:
            score += 0.1
        
        # 推理步骤数量
        step_count = len(trajectory.reasoning_steps)
        if step_count >= 8:
            score += 0.4
        elif step_count >= 5:
            score += 0.3
        elif step_count >= 3:
            score += 0.2
        else:
            score += 0.1
        
        # 答案长度和深度
        answer_words = len(trajectory.answer.split())
        if answer_words > 100:
            score += 0.3
        elif answer_words > 50:
            score += 0.2
        else:
            score += 0.1
        
        return min(score, 1.0)
    
    def _score_reasoning_quality(self, trajectory: QATrajectory) -> float:
        """评估推理质量"""
        if not trajectory.reasoning_steps:
            return 0.0
        
        score = 0.0
        
        # 逻辑连接词密度
        logic_words = ["因此", "所以", "由于", "基于", "根据", "通过", "然后", "接下来", "最后", "首先", "其次"]
        steps_text = ' '.join(trajectory.reasoning_steps)
        logic_density = sum(1 for word in logic_words if word in steps_text) / len(trajectory.reasoning_steps)
        score += min(logic_density, 1.0) * 0.4
        
        # 推理步骤平均长度
        avg_step_length = sum(len(step.split()) for step in trajectory.reasoning_steps) / len(trajectory.reasoning_steps)
        if avg_step_length > 15:
            score += 0.3
        elif avg_step_length > 10:
            score += 0.2
        else:
            score += 0.1
        
        # 推理链条完整性（检查是否有明确的结论）
        final_step = trajectory.reasoning_steps[-1].lower()
        if any(word in final_step for word in ["因此", "所以", "综上", "总结", "结论"]):
            score += 0.3
        else:
            score += 0.1
        
        return min(score, 1.0)
    
    def _score_content_richness(self, trajectory: QATrajectory) -> float:
        """评估内容丰富度"""
        score = 0.0
        
        # 词汇多样性
        all_text = f"{trajectory.question} {trajectory.answer} {' '.join(trajectory.reasoning_steps)}"
        words = re.findall(r'\b\w+\b', all_text.lower())
        if len(words) > 0:
            unique_ratio = len(set(words)) / len(words)
            score += unique_ratio * 0.4
        
        # 专业术语使用
        technical_terms = ["技术", "方法", "原理", "机制", "过程", "系统", "结构", "功能", "性能", "效果"]
        term_count = sum(1 for term in technical_terms if term in all_text)
        score += min(term_count / 5, 1.0) * 0.3
        
        # 信息密度
        info_density = len(words) / max(len(all_text), 1)
        score += min(info_density * 10, 1.0) * 0.3
        
        return min(score, 1.0)
    
    def _score_language_quality(self, trajectory: QATrajectory) -> float:
        """评估语言质量"""
        score = 0.8  # 基础分
        
        all_text = f"{trajectory.question} {trajectory.answer} {' '.join(trajectory.reasoning_steps)}"
        
        # 检查重复词汇过多
        words = all_text.split()
        if len(words) > 0:
            unique_ratio = len(set(words)) / len(words)
            if unique_ratio < 0.3:
                score -= 0.3
        
        # 检查句子完整性（简单检查标点符号）
        sentences = re.split(r'[。！？]', all_text)
        complete_sentences = [s for s in sentences if len(s.strip()) > 5]
        if len(complete_sentences) < len(trajectory.reasoning_steps):
            score -= 0.2
        
        return max(score, 0.0)
    
    def _score_novelty(self, trajectory: QATrajectory) -> float:
        """评估创新性"""
        score = 0.5  # 基础分
        
        # 检查是否包含创新性词汇
        innovative_words = ["创新", "新颖", "独特", "突破", "改进", "优化", "革新", "发展"]
        all_text = f"{trajectory.question} {trajectory.answer} {' '.join(trajectory.reasoning_steps)}"
        
        innovation_count = sum(1 for word in innovative_words if word in all_text)
        score += min(innovation_count / 3, 0.5)
        
        # 开放性问题获得额外分数
        if trajectory.qa_type == QAType.OPEN_ENDED:
            score += 0.2
        
        return min(score, 1.0)
    
    def save_trajectories(self, trajectories: List[QATrajectory], output_path: str):
        """保存轨迹到文件"""
        data = []
        for trajectory in trajectories:
            data.append({
                'trajectory_id': trajectory.trajectory_id,
                'question': trajectory.question,
                'answer': trajectory.answer,
                'reasoning_steps': trajectory.reasoning_steps,
                'qa_type': trajectory.qa_type.value,
                'cot_type': trajectory.cot_type.value,
                'confidence_score': trajectory.confidence_score,
                'quality_metrics': trajectory.quality_metrics,
                'source_simple_qa': trajectory.source_simple_qa,
                'timestamp': datetime.now().isoformat()
            })
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"已保存{len(trajectories)}个轨迹到 {output_path}")
    
    def generate_quality_report(self, trajectories: List[QATrajectory]) -> Dict[str, Any]:
        """生成质量报告"""
        if not trajectories:
            return {}
        
        report = {
            'total_trajectories': len(trajectories),
            'timestamp': datetime.now().isoformat(),
            'quality_distribution': {},
            'type_distribution': {},
            'cot_distribution': {},
            'average_metrics': {}
        }
        
        # 质量分布
        quality_scores = [t.quality_metrics.get('overall_score', 0) for t in trajectories]
        report['quality_distribution'] = {
            'excellent': sum(1 for s in quality_scores if s >= 0.9),
            'good': sum(1 for s in quality_scores if 0.7 <= s < 0.9),
            'fair': sum(1 for s in quality_scores if 0.5 <= s < 0.7),
            'poor': sum(1 for s in quality_scores if s < 0.5),
            'average_score': np.mean(quality_scores) if quality_scores else 0
        }
        
        # 类型分布
        qa_types = [t.qa_type.value for t in trajectories]
        for qa_type in set(qa_types):
            report['type_distribution'][qa_type] = qa_types.count(qa_type)
        
        # CoT分布
        cot_types = [t.cot_type.value for t in trajectories]
        for cot_type in set(cot_types):
            report['cot_distribution'][cot_type] = cot_types.count(cot_type)
        
        # 平均指标
        metrics = ['complexity', 'reasoning_quality', 'content_richness', 'language_quality', 'novelty']
        for metric in metrics:
            scores = [t.quality_metrics.get(metric, 0) for t in trajectories]
            report['average_metrics'][metric] = np.mean(scores) if scores else 0
        
        return report

# 使用示例配置
def create_default_config():
    """创建默认配置"""
    return {
        'gpt4_config': {
            'api_key': 'your-gpt4-api-key',
            'base_url': 'https://api.openai.com/v1'
        },
        'lrm_config': {
            'api_key': 'your-lrm-api-key',
            'base_url': 'https://api.your-lrm-provider.com/v1'
        },
        'rejection_sampling_n': 5,
        'quality_threshold': 0.7,
        'qa_type_ratios': {
            'simple_factual': 0.2,
            'complex_reasoning': 0.3,
            'multi_hop': 0.2,
            'analytical': 0.15,
            'open_ended': 0.15
        },
        'cot_type_ratios': {
            'short_cot': 0.4,
            'long_cot': 0.6
        },
        'trajectory_filter': {
            'format_validation': True,
            'answer_correctness': True,
            'quality_assessment': True,
            'redundancy_check': True,
            'alignment_check': True,
            'reasoning_coherence': True
        }
    }

if __name__ == "__main__":
    # 使用示例
    config = create_default_config()
    generator = E2HQAGenerator(config)
    
    # 示例文本
    sample_text = """
人工智能是计算机科学的一个分支，它企图了解智能的实质，并生产出一种新的能以人类智能相似的方式做出反应的智能机器。
该领域的研究包括机器人、语言识别、图像识别、自然语言处理和专家系统等。人工智能从诞生以来，理论和技术日益成熟，
应用领域也不断扩大，可以设想，未来人工智能带来的科技产品，将会是人类智慧的"容器"。
"""
    
    # 异步运行示例
    async def main():
        trajectories = await generator.generate_qa_from_text(sample_text, num_questions=5)
        
        # 保存结果
        generator.save_trajectories(trajectories, 'qa_trajectories.json')
        
        # 生成质量报告
        report = generator.generate_quality_report(trajectories)
        print("质量报告:")
        print(json.dumps(report, ensure_ascii=False, indent=2))
    
    # asyncio.run(main())