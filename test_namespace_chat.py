#!/usr/bin/env python3
"""
测试 Chat API 的领域参数功能
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_chat_with_namespace():
    """测试带领域参数的聊天请求"""

    # 测试 1: 不指定领域 (自动分类)
    print("\n=== 测试 1: 不指定领域 (自动分类) ===")
    response = requests.get(
        f"{BASE_URL}/api/chat/send",
        params={
            "message": "Python 的装饰器是什么?",
            "use_rag": True,
            "stream": False
        }
    )

    if response.status_code == 200:
        data = response.json()
        print(f"✓ 请求成功")
        print(f"  - 回复: {data.get('message', '')[:100]}...")
        print(f"  - 领域分类: {data.get('domain_classification', {})}")
        print(f"  - 检索统计: {data.get('retrieval_stats', {})}")
    else:
        print(f"✗ 请求失败: {response.status_code}")
        print(f"  错误: {response.text}")

    # 测试 2: 指定 technical_docs 领域
    print("\n=== 测试 2: 指定 technical_docs 领域 ===")
    response = requests.get(
        f"{BASE_URL}/api/chat/send",
        params={
            "message": "什么是装饰器?",
            "use_rag": True,
            "stream": False,
            "namespace": "technical_docs"
        }
    )

    if response.status_code == 200:
        data = response.json()
        print(f"✓ 请求成功")
        print(f"  - 回复: {data.get('message', '')[:100]}...")
        print(f"  - 领域分类: {data.get('domain_classification', {})}")
        print(f"  - 检索统计: {data.get('retrieval_stats', {})}")
    else:
        print(f"✗ 请求失败: {response.status_code}")
        print(f"  错误: {response.text}")

    # 测试 3: POST 请求指定领域
    print("\n=== 测试 3: POST 请求指定 general 领域 ===")
    response = requests.post(
        f"{BASE_URL}/api/chat/send",
        json={
            "message": "天气怎么样?",
            "use_rag": True,
            "stream": False,
            "namespace": "general"
        }
    )

    if response.status_code == 200:
        data = response.json()
        print(f"✓ 请求成功")
        print(f"  - 回复: {data.get('message', '')[:100]}...")
        print(f"  - 领域分类: {data.get('domain_classification', {})}")
        print(f"  - 检索统计: {data.get('retrieval_stats', {})}")
    else:
        print(f"✗ 请求失败: {response.status_code}")
        print(f"  错误: {response.text}")

    # 测试 4: 指定不存在的领域
    print("\n=== 测试 4: 指定不存在的领域 ===")
    response = requests.get(
        f"{BASE_URL}/api/chat/send",
        params={
            "message": "测试消息",
            "use_rag": True,
            "stream": False,
            "namespace": "nonexistent_domain"
        }
    )

    if response.status_code == 200:
        data = response.json()
        print(f"✓ 请求成功")
        print(f"  - 回复: {data.get('message', '')[:100]}...")
        print(f"  - 领域分类: {data.get('domain_classification', {})}")
        print(f"  - 检索统计: {data.get('retrieval_stats', {})}")
        print(f"  - 检索结果数: {len(data.get('sources', []))}")
    else:
        print(f"✗ 请求失败: {response.status_code}")
        print(f"  错误: {response.text}")

if __name__ == "__main__":
    print("开始测试 Chat API 的领域参数功能...")
    print(f"目标服务器: {BASE_URL}")

    try:
        test_chat_with_namespace()
        print("\n=== 测试完成 ===")
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
