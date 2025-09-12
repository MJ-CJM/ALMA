#!/usr/bin/env python3
"""
Prompt Simple Service 演示脚本

演示如何使用简化的 Prompt 构建服务
"""

import requests
import json

# 服务地址
BASE_URL = "http://localhost:8001"

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

def test_qa_prompt():
    """测试问答 Prompt 接口"""
    print("=== 问答 Prompt 接口测试 ===")
    
    # 测试数据
    test_data = {
        "query": "什么是机器学习？",
        "top_k": 3
    }
    
    try:
        response = requests.post(f"{BASE_URL}/ask", json=test_data)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Prompt 类型: {result['prompt_type']}")
            print(f"查询: {result['query']}")
            print(f"搜索结果数量: {result['search_results_count']}")
            print(f"生成的 Prompt:\n{result['prompt']}")
        else:
            print(f"错误: {response.text}")
    except Exception as e:
        print(f"测试失败: {e}")
    print()

def test_learning_plan_prompt():
    """测试学习计划 Prompt 接口"""
    print("=== 学习计划 Prompt 接口测试 ===")
    
    # 测试数据
    test_data = {
        "goal": "学习 Python 编程",
        "time_range": "3个月",
        "learning_background": "有基础编程经验",
        "top_k": 3
    }
    
    try:
        response = requests.post(f"{BASE_URL}/plan", json=test_data)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Prompt 类型: {result['prompt_type']}")
            print(f"学习目标: {result['query']}")
            print(f"搜索结果数量: {result['search_results_count']}")
            print(f"生成的 Prompt:\n{result['prompt']}")
        else:
            print(f"错误: {response.text}")
    except Exception as e:
        print(f"测试失败: {e}")
    print()

def test_error_cases():
    """测试错误情况"""
    print("=== 错误情况测试 ===")
    
    # 测试空查询
    print("1. 测试空查询:")
    try:
        response = requests.post(f"{BASE_URL}/ask", json={"query": "", "top_k": 5})
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
    except Exception as e:
        print(f"测试失败: {e}")
    print()
    
    # 测试无效的 top_k
    print("2. 测试无效的 top_k:")
    try:
        response = requests.post(f"{BASE_URL}/ask", json={"query": "测试", "top_k": 0})
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
    except Exception as e:
        print(f"测试失败: {e}")
    print()

if __name__ == "__main__":
    print("Prompt Simple Service 演示")
    print("=" * 50)
    
    # 运行测试
    test_health_check()
    test_qa_prompt()
    test_learning_plan_prompt()
    test_error_cases()
    
    print("演示完成！")
    print("\n使用说明:")
    print("1. 启动服务: python prompt_server.py")
    print("2. 服务将在 http://localhost:8001 运行")
    print("3. 访问 http://localhost:8001/docs 查看 API 文档")
    print("4. 使用 /ask 接口进行问答")
    print("5. 使用 /plan 接口生成学习计划") 