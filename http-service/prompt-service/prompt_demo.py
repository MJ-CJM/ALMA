#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prompt Service 简化版 Demo
直接调用 embedding API 和向量数据库，实现问答功能
"""

import os
import sys
import requests
import json
from openai import OpenAI
from pymilvus import MilvusClient

class SimplePromptDemo:
    def __init__(self):
        # 初始化 OpenAI 客户端
        self.client = OpenAI(
            api_key="sk-1f0b08f7ee4742c39dbb63254f3db29e",
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )
        
        # 连接 Milvus
        self.db_file = os.path.join("..", "rag-module", "db_data", "milvus_lite.db")
        self.milvus = MilvusClient(self.db_file)
        self.collection_name = "prompt_demo_collection"  # 使用独立的集合名
        
        # 知识库文本
        self.knowledge_texts = [
            "人工智能是计算机科学的一个分支，致力于创建能够执行通常需要人类智能的任务的系统。",
            "机器学习是人工智能的一个子集，它使计算机能够在没有明确编程的情况下学习和改进。",
            "深度学习是机器学习的一个分支，使用多层神经网络来模拟人脑的学习过程。",
            "自然语言处理是人工智能的一个领域，专注于计算机理解和生成人类语言的能力。",
            "计算机视觉是人工智能的一个分支，使计算机能够从数字图像或视频中获取高层次理解。",
            "强化学习通过奖励机制来训练智能体，使其能够自主学习和决策。",
            "知识图谱是结构化的知识表示方法，用于组织和连接实体之间的关系。",
            "语义分析是自然语言处理的重要任务，用于理解文本的深层含义。"
        ]
    
    def setup_knowledge_base(self):
        """设置知识库"""
        print("=" * 50)
        print("设置知识库")
        print("=" * 50)
        
        # 生成 embedding
        print("生成知识库文本的 embedding...")
        response = self.client.embeddings.create(
            input=self.knowledge_texts,
            model="text-embedding-v1"
        )
        embeddings = [item.embedding for item in response.data]
        
        # 检查集合是否存在
        collections = self.milvus.list_collections()
        if self.collection_name not in collections:
            # 创建集合
            self.milvus.create_collection(
                collection_name=self.collection_name,
                dimension=len(embeddings[0]),
                primary_field_name="id",
                vector_field_name="embedding"
            )
            print(f"创建集合: {self.collection_name}")
        
        # 插入知识库数据
        data = []
        for i, (text, emb) in enumerate(zip(self.knowledge_texts, embeddings)):
            data.append({
                "id": i + 1,
                "text": text,
                "embedding": emb,
                "filename": "knowledge_base.txt",
                "file_hash": "kb_hash_123"
            })
        
        self.milvus.insert(
            collection_name=self.collection_name,
            data=data
        )
        print(f"成功插入 {len(data)} 条知识库数据")
    
    def search_similar_texts(self, query: str, top_k: int = 3):
        """搜索相似文本"""
        # 生成查询的 embedding
        response = self.client.embeddings.create(
            input=[query],
            model="text-embedding-v1"
        )
        query_embedding = response.data[0].embedding
        
        # 搜索相似文本
        results = self.milvus.search(
            collection_name=self.collection_name,
            data=[query_embedding],
            limit=top_k,
            output_fields=["id", "text"]
        )
        
        return results[0] if results else []
    
    def generate_answer(self, query: str, context: str):
        """生成答案"""
        prompt = f"""基于以下知识库内容，回答用户的问题。

知识库内容：
{context}

用户问题：{query}

请提供准确、详细的回答："""
        
        response = self.client.chat.completions.create(
            model="qwen-turbo",
            messages=[
                {"role": "system", "content": "你是一个专业的AI助手，基于提供的知识库内容回答问题。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        return response.choices[0].message.content
    
    def qa_demo(self):
        """问答演示"""
        print("\n" + "=" * 50)
        print("问答演示")
        print("=" * 50)
        
        # 示例问题
        questions = [
            "什么是人工智能？",
            "机器学习和深度学习有什么区别？",
            "自然语言处理有哪些应用？",
            "强化学习是如何工作的？"
        ]
        
        for i, question in enumerate(questions, 1):
            print(f"\n问题 {i}: {question}")
            print("-" * 40)
            
            # 搜索相关文本
            similar_texts = self.search_similar_texts(question, top_k=3)
            
            if similar_texts:
                # 构建上下文
                context = "\n".join([hit.get('text', '') for hit in similar_texts])
                print(f"找到 {len(similar_texts)} 个相关文本片段")
                
                # 生成答案
                answer = self.generate_answer(question, context)
                print(f"答案: {answer}")
            else:
                print("未找到相关文本")
    
    def interactive_qa(self):
        """交互式问答"""
        print("\n" + "=" * 50)
        print("交互式问答 (输入 'quit' 退出)")
        print("=" * 50)
        
        while True:
            try:
                question = input("\n请输入您的问题: ").strip()
                if question.lower() in ['quit', 'exit', '退出']:
                    break
                
                if not question:
                    continue
                
                print("正在搜索相关知识...")
                similar_texts = self.search_similar_texts(question, top_k=3)
                
                if similar_texts:
                    context = "\n".join([hit.get('text', '') for hit in similar_texts])
                    print("正在生成答案...")
                    answer = self.generate_answer(question, context)
                    print(f"\n答案: {answer}")
                else:
                    print("抱歉，未找到相关知识来回答您的问题。")
                    
            except KeyboardInterrupt:
                print("\n\n退出交互式问答")
                break
            except Exception as e:
                print(f"发生错误: {e}")

def main():
    """主函数"""
    print("Prompt Service 简化版 Demo")
    print("=" * 60)
    
    demo = SimplePromptDemo()
    
    # 设置知识库
    demo.setup_knowledge_base()
    
    # 运行问答演示
    demo.qa_demo()
    
    # 交互式问答
    demo.interactive_qa()
    
    print("\nDemo 结束")

if __name__ == "__main__":
    main() 