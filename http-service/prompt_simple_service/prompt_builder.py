import requests
from typing import List, Dict, Any, Optional

class PromptBuilder:
    """简化的 Prompt 构建工具"""
    
    def __init__(self, rag_api_base: str = "http://localhost:8000"):
        """
        初始化 Prompt 构建器
        
        Args:
            rag_api_base: RAG 服务的 API 基础地址
        """
        self.rag_api_base = rag_api_base.rstrip('/')
    
    def search_knowledge(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        调用知识库检索接口获取相关语义段落
        
        Args:
            query: 查询内容
            top_k: 返回结果数量
            
        Returns:
            搜索结果列表
        """
        try:
            # 调用 RAG 服务的搜索接口
            response = requests.post(
                f"{self.rag_api_base}/search",
                json={"query": query, "top_k": top_k},
                timeout=10
            )
            response.raise_for_status()
            return response.json().get("results", [])
        except Exception as e:
            print(f"搜索知识库时出错: {e}")
            return []
    
    def build_qa_prompt(self, query: str, top_k: int = 5) -> str:
        """
        构建问答 Prompt
        
        Args:
            query: 用户问题
            top_k: 检索结果数量
            
        Returns:
            格式化的问答 Prompt
        """
        # 获取相关语义段落
        search_results = self.search_knowledge(query, top_k)
        
        # 格式化搜索结果
        formatted_results = self._format_search_results(search_results)
        
        # 构建问答模板
        prompt = f"""基于以下检索到的相关信息，请回答用户的问题。

检索到的相关信息：
{formatted_results}

用户问题：{query}

请基于上述信息，给出准确、详细的回答。如果检索到的信息不足以回答问题，请说明需要更多信息。

回答："""
        
        return prompt
    
    def build_learning_plan_prompt(self, goal: str, time_range: str = "", learning_background: str = "", top_k: int = 5) -> str:
        """
        构建学习计划 Prompt
        
        Args:
            goal: 学习目标
            time_range: 时间范围
            learning_background: 学习背景
            top_k: 检索结果数量
            
        Returns:
            格式化的学习计划 Prompt
        """
        # 获取相关语义段落
        search_results = self.search_knowledge(goal, top_k)
        
        # 格式化搜索结果
        formatted_results = self._format_search_results(search_results)
        
        # 构建学习计划模板
        prompt = f"""基于用户的学习目标和时间范围，结合检索到的相关知识，制定一个详细的学习计划。

用户目标：{goal}
时间范围：{time_range}
学习背景：{learning_background}

检索到的相关知识：
{formatted_results}

请制定一个结构化的学习计划，包括：
1. 学习阶段划分
2. 每个阶段的具体目标
3. 学习方法和资源推荐
4. 时间安排建议
5. 评估和调整机制

学习计划："""
        
        return prompt
    
    def _format_search_results(self, results: List[Dict[str, Any]]) -> str:
        """
        格式化搜索结果
        
        Args:
            results: 搜索结果列表
            
        Returns:
            格式化后的搜索结果文本
        """
        if not results:
            return "未找到相关信息"
        
        formatted = []
        for i, result in enumerate(results, 1):
            content = result.get("content", "")
            score = result.get("score", 0)
            formatted.append(f"{i}. {content} (相关度: {score:.3f})")
        
        return "\n".join(formatted) 