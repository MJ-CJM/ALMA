#!/usr/bin/env python3
"""
RAG Simple Module 演示脚本

演示如何使用简化的 RAG 服务
"""

import requests
import json

# 服务地址
BASE_URL = "http://localhost:8000"

def test_health_check():
    """测试健康检查"""
    print("=== 健康检查 ===")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
    except Exception as e:
        print(f"健康检查失败: {e}")
    print()

def test_search():
    """测试搜索接口"""
    print("=== 搜索接口测试 ===")
    
    # 测试查询
    test_queries = [
        "机器学习",
        "深度学习",
        "自然语言处理",
        "计算机视觉"
    ]
    
    for query in test_queries:
        print(f"\n搜索关键词: {query}")
        print("-" * 40)
        
        try:
            response = requests.get(f"{BASE_URL}/search", params={
                "keyword": query,
                "top_k": 3
            })
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"查询: {result['query']}")
                print(f"返回数量: {result['top_k']}")
                print(f"找到结果: {len(result['results'])} 条")
                
                for i, item in enumerate(result['results'], 1):
                    print(f"\n结果 {i}:")
                    print(f"  内容: {item.get('content', '')[:100]}...")
                    print(f"  文件名: {item.get('filename', '')}")
                    print(f"  相关度: {item.get('score', 0):.3f}")
            else:
                print(f"错误: {response.text}")
        except Exception as e:
            print(f"搜索失败: {e}")
        print()

def test_error_cases():
    """测试错误情况"""
    print("=== 错误情况测试 ===")
    
    # 测试空关键词
    print("1. 测试空关键词:")
    try:
        response = requests.get(f"{BASE_URL}/search", params={"keyword": "", "top_k": 5})
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
    except Exception as e:
        print(f"测试失败: {e}")
    print()
    
    # 测试无效的 top_k
    print("2. 测试无效的 top_k:")
    try:
        response = requests.get(f"{BASE_URL}/search", params={"keyword": "测试", "top_k": 0})
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
    except Exception as e:
        print(f"测试失败: {e}")
    print()
    
    # 测试过大的 top_k
    print("3. 测试过大的 top_k:")
    try:
        response = requests.get(f"{BASE_URL}/search", params={"keyword": "测试", "top_k": 25})
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
    except Exception as e:
        print(f"测试失败: {e}")
    print()

def test_rag_service_directly():
    """直接测试 RAG 服务"""
    print("=== 直接测试 RAG 服务 ===")
    
    try:
        from rag_service import RAGService
        
        # 初始化服务
        rag_service = RAGService()
        
        # 测试搜索
        query = "人工智能"
        results = rag_service.search_similar_texts(query, top_k=3)
        
        print(f"查询: {query}")
        print(f"找到 {len(results)} 个结果:")
        
        for i, result in enumerate(results, 1):
            print(f"\n结果 {i}:")
            print(f"  内容: {result.get('content', '')[:100]}...")
            print(f"  文件名: {result.get('filename', '')}")
            print(f"  相关度: {result.get('score', 0):.3f}")
            
    except Exception as e:
        print(f"直接测试失败: {e}")
    print()

if __name__ == "__main__":
    print("RAG Simple Module 演示")
    print("=" * 50)
    
    # 运行测试
    test_health_check()
    test_search()
    test_error_cases()
    test_rag_service_directly()
    
    print("演示完成！")
    print("\n使用说明:")
    print("1. 启动服务: python rag_server.py")
    print("2. 服务将在 http://localhost:8000 运行")
    print("3. 访问 http://localhost:8000/docs 查看 API 文档")
    print("4. 使用 GET /search?keyword={keyword}&top_k={top_k} 进行搜索")
    print("5. 将 PDF 文件放在 data/pdf/ 目录中，服务会自动处理") 