 #!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAG 核心功能测试
验证 embedding 模型转换、写入和查询 Milvus 向量数据库
"""

import os
import sys
import time
from typing import List

# 添加当前目录到 Python 路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from rag_service import RAGService

def test_embedding_generation():
    print("=" * 40)
    print("测试 1: Embedding 生成")
    print("=" * 40)
    try:
        rag_service = RAGService()
        test_texts = [
            "人工智能是计算机科学的一个分支。",
            "机器学习是人工智能的一个子集。",
            "深度学习使用多层神经网络。"
        ]
        print(f"生成 {len(test_texts)} 个文本的 embedding...")
        embeddings = rag_service.get_embeddings(test_texts)
        if embeddings and len(embeddings) == len(test_texts):
            print("✓ Embedding 生成成功")
            print(f"  - 维度: {len(embeddings[0])}")
            print(f"  - 数据类型: {type(embeddings[0][0])}")
            return True
        else:
            print("✗ Embedding 生成失败")
            return False
    except Exception as e:
        print(f"✗ Embedding 生成测试失败: {e}")
        return False

def test_milvus_connection():
    print("\n" + "=" * 40)
    print("测试 2: Milvus 连接")
    print("=" * 40)
    try:
        rag_service = RAGService()
        collection_info = rag_service.get_collection_info()
        print("✓ Milvus 连接成功")
        print(f"  - 集合名称: {collection_info.get('collection_name')}")
        print(f"  - 向量维度: {collection_info.get('dimension')}")
        print(f"  - 文档数量: {collection_info.get('document_count')}")
        return True
    except Exception as e:
        print(f"✗ Milvus 连接测试失败: {e}")
        return False

def test_data_insertion_and_query():
    print("\n" + "=" * 40)
    print("测试 3: 数据插入和查询")
    print("=" * 40)
    try:
        rag_service = RAGService()
        test_texts = [
            "人工智能是计算机科学的一个分支，致力于创建智能系统。",
            "机器学习使计算机能够在没有明确编程的情况下学习。",
            "深度学习使用神经网络模拟人脑的学习过程。",
            "自然语言处理专注于计算机理解和生成人类语言。",
            "计算机视觉使计算机能够从图像中获取理解。"
        ]
        print("生成 embedding...")
        embeddings = rag_service.get_embeddings(test_texts)
        if not embeddings:
            print("✗ Embedding 生成失败")
            return False
        data = []
        for i, (text, embedding) in enumerate(zip(test_texts, embeddings)):
            data.append({
                "id": i + 2000,
                "text": text,
                "embedding": embedding,
                "filename": "test_core.txt",
                "file_hash": "test_core_hash"
            })
        print(f"插入 {len(data)} 条测试数据...")
        rag_service.milvus_client.insert(
            collection_name=rag_service.collection_name,
            data=data
        )
        print("✓ 数据插入成功")
        time.sleep(1)
        query = "人工智能和机器学习"
        print(f"查询: {query}")
        results = rag_service.search_similar_texts(query, top_k=3)
        if results:
            print("✓ 相似文本搜索成功")
            print(f"  - 返回结果数量: {len(results)}")
            for i, result in enumerate(results, 1):
                text = result.get('text', '')[:80]
                score = result.get('score', 0)
                print(f"  结果 {i}: {text}... (相似度: {score:.4f})")
        else:
            print("✗ 相似文本搜索失败")
            return False
        return True
    except Exception as e:
        print(f"✗ 数据插入和查询测试失败: {e}")
        return False

def main():
    print("RAG 核心功能测试")
    print("=" * 50)
    tests = [
        ("Embedding 生成", test_embedding_generation),
        ("Milvus 连接", test_milvus_connection),
        ("数据插入和查询", test_data_insertion_and_query)
    ]
    passed = 0
    total = len(tests)
    for test_name, test_func in tests:
        try:
            result = test_func()
            if result:
                passed += 1
        except Exception as e:
            print(f"测试 {test_name} 发生异常: {e}")
    print("\n" + "=" * 50)
    print("测试结果总结")
    print("=" * 50)
    print(f"通过: {passed}/{total}")
    if passed == total:
        print("🎉 所有测试通过！RAG 核心功能正常")
    else:
        print("⚠️  部分测试失败，请检查相关功能")
    return 0 if passed == total else 1

if __name__ == "__main__":
    exit(main())
