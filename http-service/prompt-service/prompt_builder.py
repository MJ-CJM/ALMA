import json
import requests
from typing import List, Dict, Any, Optional
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

class PromptType(Enum):
    """Prompt 类型枚举"""
    QA = "qa"
    LEARNING_PLAN = "learning_plan"
    SUMMARY = "summary"
    EXPLANATION = "explanation"

@dataclass
class PromptContext:
    """Prompt 上下文数据"""
    query: str
    search_results: List[Dict[str, Any]]
    additional_context: Optional[Dict[str, Any]] = None

class PromptBuilder:
    """Prompt 构建工具"""
    
    def __init__(self, rag_api_base: str = "http://localhost:8000"):
        """
        初始化 Prompt 构建器
        
        Args:
            rag_api_base: RAG 服务的 API 基础地址
        """
        self.rag_api_base = rag_api_base.rstrip('/')
        self.templates = self._load_templates()
    
    def _load_templates(self) -> Dict[str, str]:
        """加载 Prompt 模板"""
        return {
            PromptType.QA.value: self._get_qa_template(),
            PromptType.LEARNING_PLAN.value: self._get_learning_plan_template(),
            PromptType.SUMMARY.value: self._get_summary_template(),
            PromptType.EXPLANATION.value: self._get_explanation_template()
        }
    
    def _get_qa_template(self) -> str:
        """获取问答模板"""
        return """基于以下检索到的相关信息，请回答用户的问题。

检索到的相关信息：
{search_results}

用户问题：{query}

请基于上述信息，给出准确、详细的回答。如果检索到的信息不足以回答问题，请说明需要更多信息。

回答："""
    
    def _get_learning_plan_template(self) -> str:
        """获取学习计划模板"""
        return """基于用户的学习目标和时间范围，结合检索到的相关知识，制定一个详细的学习计划。

用户目标：{query}
时间范围：{time_range}
学习背景：{learning_background}

检索到的相关知识：
{search_results}

请制定一个结构化的学习计划，包括：
1. 学习阶段划分
2. 每个阶段的具体目标
3. 学习方法和资源推荐
4. 时间安排建议
5. 评估和调整机制

学习计划："""
    
    def _get_summary_template(self) -> str:
        """获取总结模板"""
        return """基于检索到的信息，请生成一个结构化的总结。

检索到的信息：
{search_results}

总结要求：{query}

请生成一个包含以下要素的总结：
1. 核心要点
2. 关键概念
3. 重要细节
4. 相关联系

总结："""
    
    def _get_explanation_template(self) -> str:
        """获取解释模板"""
        return """基于检索到的信息，请对用户的问题进行详细解释。

检索到的信息：
{search_results}

解释要求：{query}

请提供：
1. 概念解释
2. 工作原理
3. 应用场景
4. 相关示例

解释："""
    
    def search_knowledge(self, query: str, top_k: int = 5, filename: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        从 RAG 服务搜索相关知识
        
        Args:
            query: 搜索查询
            top_k: 返回结果数量
            filename: 指定文件名过滤
            
        Returns:
            搜索结果列表
        """
        try:
            url = f"{self.rag_api_base}/search"
            payload = {
                "query": query,
                "top_k": top_k
            }
            if filename:
                payload["filename"] = filename
            
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            return result.get("results", [])
        except requests.RequestException as e:
            print(f"搜索知识失败: {e}")
            return []
    
    def build_prompt(self, prompt_type: PromptType, context: PromptContext) -> str:
        """
        构建 Prompt
        
        Args:
            prompt_type: Prompt 类型
            context: Prompt 上下文
            
        Returns:
            构建的 Prompt 文本
        """
        template = self.templates.get(prompt_type.value)
        if not template:
            raise ValueError(f"不支持的 Prompt 类型: {prompt_type}")
        
        # 格式化搜索结果
        formatted_results = self._format_search_results(context.search_results)
        
        # 准备模板变量
        template_vars = {
            "query": context.query,
            "search_results": formatted_results
        }
        
        # 添加额外上下文
        if context.additional_context:
            template_vars.update(context.additional_context)
        
        # 渲染模板
        prompt = template.format(**template_vars)
        return prompt
    
    def _format_search_results(self, results: List[Dict[str, Any]]) -> str:
        """格式化搜索结果"""
        if not results:
            return "未找到相关信息。"
        
        formatted = []
        for i, result in enumerate(results, 1):
            text = result.get("text", "")
            filename = result.get("filename", "")
            score = result.get("score", 0)
            
            formatted.append(f"{i}. 来源文件: {filename}")
            formatted.append(f"   相关度: {score:.3f}")
            formatted.append(f"   内容: {text}")
            formatted.append("")
        
        return "\n".join(formatted)
    
    def build_qa_prompt(self, query: str, top_k: int = 5, filename: Optional[str] = None) -> str:
        """
        构建问答 Prompt
        
        Args:
            query: 用户问题
            top_k: 搜索结果数量
            filename: 指定文件名
            
        Returns:
            问答 Prompt
        """
        # 搜索相关知识
        search_results = self.search_knowledge(query, top_k, filename)
        
        # 构建上下文
        context = PromptContext(
            query=query,
            search_results=search_results
        )
        
        return self.build_prompt(PromptType.QA, context)
    
    def build_learning_plan_prompt(self, goal: str, time_range: str, learning_background: str = "", top_k: int = 5) -> str:
        """
        构建学习计划 Prompt
        
        Args:
            goal: 学习目标
            time_range: 时间范围
            learning_background: 学习背景
            top_k: 搜索结果数量
            
        Returns:
            学习计划 Prompt
        """
        # 搜索相关知识
        search_results = self.search_knowledge(goal, top_k)
        
        # 构建上下文
        context = PromptContext(
            query=goal,
            search_results=search_results,
            additional_context={
                "time_range": time_range,
                "learning_background": learning_background or "无特殊背景要求"
            }
        )
        
        return self.build_prompt(PromptType.LEARNING_PLAN, context)
    
    def build_summary_prompt(self, content: str, summary_requirements: str, top_k: int = 5) -> str:
        """
        构建总结 Prompt
        
        Args:
            content: 要总结的内容
            summary_requirements: 总结要求
            top_k: 搜索结果数量
            
        Returns:
            总结 Prompt
        """
        # 搜索相关知识
        search_results = self.search_knowledge(content, top_k)
        
        # 构建上下文
        context = PromptContext(
            query=summary_requirements,
            search_results=search_results
        )
        
        return self.build_prompt(PromptType.SUMMARY, context)
    
    def build_explanation_prompt(self, concept: str, explanation_requirements: str, top_k: int = 5) -> str:
        """
        构建解释 Prompt
        
        Args:
            concept: 要解释的概念
            explanation_requirements: 解释要求
            top_k: 搜索结果数量
            
        Returns:
            解释 Prompt
        """
        # 搜索相关知识
        search_results = self.search_knowledge(concept, top_k)
        
        # 构建上下文
        context = PromptContext(
            query=explanation_requirements,
            search_results=search_results
        )
        
        return self.build_prompt(PromptType.EXPLANATION, context)
    
    def add_template(self, prompt_type: str, template: str) -> None:
        """
        添加新的 Prompt 模板
        
        Args:
            prompt_type: Prompt 类型
            template: 模板内容
        """
        self.templates[prompt_type] = template
        print(f"已添加新的 Prompt 模板: {prompt_type}")
    
    def get_available_types(self) -> List[str]:
        """获取可用的 Prompt 类型"""
        return list(self.templates.keys())
