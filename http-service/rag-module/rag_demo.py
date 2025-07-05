# test_embedding_milvus_demo.py
from openai import OpenAI
from pymilvus import MilvusClient
import os

if __name__ == "__main__":
    # 1. 初始化 OpenAI 客户端
    client = OpenAI(
        api_key="sk-1f0b08f7ee4742c39dbb63254f3db29e",  # 替换为你的 key
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
    )

    # 2. 生成 embedding
    texts = [
        "人工智能正在改变世界。",
        "机器学习是人工智能的核心。",
        "向量数据库可以高效检索相似内容。"
    ]
    response = client.embeddings.create(
        input=texts,
        model="text-embedding-v1"
    )
    embeddings = [item.embedding for item in response.data]
    print("Embedding 生成成功，数量:", len(embeddings), "维度:", len(embeddings[0]))

    # 3. 连接 Milvus Lite
    db_file = os.path.join("db_data", "milvus_lite.db")
    milvus = MilvusClient(db_file)

    # 4. 创建集合（如不存在）
    collection_name = "demo_collection"
    dim = len(embeddings[0])
    if collection_name not in milvus.list_collections():
        milvus.create_collection(
            collection_name=collection_name,
            dimension=dim,
            primary_field_name="id",
            vector_field_name="embedding"
        )
        print("集合已创建")

    # 5. 写入数据
    data = []
    for i, (text, emb) in enumerate(zip(texts, embeddings)):
        data.append({
            "id": i + 1,
            "text": text,
            "embedding": emb
        })
    milvus.insert(
        collection_name=collection_name,
        data=data
    )
    print("数据写入 Milvus 向量库成功！")

    # 6. 查询相似文本
    query_text = "人工智能和机器学习"
    query_emb = client.embeddings.create(
        input=[query_text],
        model="text-embedding-v1"
    ).data[0].embedding

    results = milvus.search(
        collection_name=collection_name,
        data=[query_emb],
        limit=3,
        output_fields=["id", "text"]
    )
    print("\n查询结果：")
    for hit in results[0]:
        text = hit.get('text', '')
        distance = hit.get('distance', 0)
        print(f"id: {hit.get('id')}, text: {text}, distance: {distance:.4f}")