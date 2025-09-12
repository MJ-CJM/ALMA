#!/usr/bin/env python3
"""
清空 Milvus 数据库工具

用于清空指定的 Milvus 集合，重新开始数据存储
"""

from pymilvus import MilvusClient
import sys

def clear_milvus_collection(collection_name: str = "rag_simple_collection"):
    """
    清空指定的 Milvus 集合
    
    Args:
        collection_name: 要清空的集合名称
    """
    try:
        # 连接 Milvus
        print(f"正在连接到 Milvus 服务器...")
        milvus_client = MilvusClient(
            uri="http://101.34.214.7:6002"
        )
        
        # 检查集合是否存在
        collections = milvus_client.list_collections()
        print(f"当前存在的集合: {collections}")
        
        if collection_name in collections:
            print(f"找到集合 '{collection_name}'，正在删除...")
            
            # 获取集合信息
            try:
                collection_info = milvus_client.describe_collection(collection_name)
                print(f"集合信息: {collection_info}")
            except Exception as e:
                print(f"获取集合信息失败: {e}")
            
            # 删除集合
            milvus_client.drop_collection(collection_name)
            print(f"✅ 成功删除集合 '{collection_name}'")
            
            # 验证删除
            collections_after = milvus_client.list_collections()
            if collection_name not in collections_after:
                print(f"✅ 验证成功：集合 '{collection_name}' 已从列表中移除")
            else:
                print(f"❌ 警告：集合 '{collection_name}' 可能未完全删除")
                
        else:
            print(f"集合 '{collection_name}' 不存在，无需删除")
            
    except Exception as e:
        print(f"❌ 清空集合时出错: {e}")
        return False
    
    return True

def clear_all_collections():
    """清空所有集合"""
    try:
        print("正在连接到 Milvus 服务器...")
        milvus_client = MilvusClient(
            uri="http://101.34.214.7:6002"
        )
        
        # 获取所有集合
        collections = milvus_client.list_collections()
        print(f"当前存在的集合: {collections}")
        
        if not collections:
            print("没有找到任何集合")
            return True
        
        # 删除所有集合
        for collection_name in collections:
            print(f"正在删除集合 '{collection_name}'...")
            try:
                milvus_client.drop_collection(collection_name)
                print(f"✅ 成功删除集合 '{collection_name}'")
            except Exception as e:
                print(f"❌ 删除集合 '{collection_name}' 时出错: {e}")
        
        # 验证删除
        collections_after = milvus_client.list_collections()
        if not collections_after:
            print("✅ 所有集合已成功删除")
        else:
            print(f"❌ 警告：仍有集合存在: {collections_after}")
            
    except Exception as e:
        print(f"❌ 清空所有集合时出错: {e}")
        return False
    
    return True

def main():
    """主函数"""
    print("=" * 50)
    print("Milvus 数据库清空工具")
    print("=" * 50)
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "all":
            # 清空所有集合
            print("清空所有集合...")
            success = clear_all_collections()
        else:
            # 清空指定集合
            collection_name = command
            print(f"清空集合 '{collection_name}'...")
            success = clear_milvus_collection(collection_name)
    else:
        # 默认清空 rag_simple_collection
        print("清空默认集合 'rag_simple_collection'...")
        success = clear_milvus_collection()
    
    if success:
        print("\n✅ 操作完成！")
        print("\n使用说明:")
        print("1. 清空默认集合: python clear_milvus.py")
        print("2. 清空指定集合: python clear_milvus.py <collection_name>")
        print("3. 清空所有集合: python clear_milvus.py all")
    else:
        print("\n❌ 操作失败！")
        sys.exit(1)

if __name__ == "__main__":
    main() 