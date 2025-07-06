# Prompt Service Demo 详细解析

## 概述

本文档详细解析 `prompt_demo.py` 的实现原理，包括代码逐行解析、相关技术知识点和扩展说明。这是一个基于 RAG (Retrieval-Augmented Generation) 架构的简化版问答系统演示。

## 技术架构

```
用户问题 → Embedding 生成 → 向量检索 → 上下文构建 → LLM 生成答案
```

### 核心技术栈
- **OpenAI API**: 用于生成文本 embedding 和 LLM 对话
- **Milvus Lite**: 本地向量数据库，用于存储和检索向量
- **RAG 架构**: 检索增强生成，结合知识库和 LLM

## 代码逐行解析

### 1. 导入依赖

```python
import os
import sys
import requests
import json
from openai import OpenAI
from pymilvus import MilvusClient
```

**知识点解析：**
- `openai`: OpenAI 官方 Python SDK，用于调用 GPT 和 Embedding 模型
- `pymilvus`: Milvus 向量数据库的 Python 客户端
- `os`, `sys`: 系统操作和路径管理
- `requests`, `json`: HTTP 请求和 JSON 数据处理

### 2. SimplePromptDemo 类初始化

```python
class SimplePromptDemo:
    def __init__(self):
        # 初始化 OpenAI 客户端
        self.client = OpenAI(
            api_key="sk-1f0b08f7ee4742c39dbb63254f3db29e",
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )
```

**知识点解析：**

#### OpenAI 客户端配置
- `api_key`: 访问 OpenAI API 的密钥
- `base_url`: 自定义 API 端点，这里使用的是阿里云 DashScope 的兼容模式
- 支持多种 embedding 模型：`text-embedding-v1`, `text-embedding-3-small`, `text-embedding-3-large`

#### Embedding 模型详解
```python
# 生成 embedding 的核心代码
response = self.client.embeddings.create(
    input=texts,
    model="text-embedding-v1"
)
embeddings = [item.embedding for item in response.data]
```

**Embedding 技术要点：**
1. **向量化原理**: 将文本转换为高维数值向量，保持语义相似性
2. **维度**: 通常为 1536 维（text-embedding-v1）或 3072 维（text-embedding-3-large）
3. **相似度计算**: 使用余弦相似度或欧氏距离
4. **语义理解**: 相似含义的文本在向量空间中距离较近

### 3. Milvus 向量数据库连接

```python
# 连接 Milvus
self.db_file = os.path.join("..", "rag-module", "db_data", "milvus_lite.db")
self.milvus = MilvusClient(self.db_file)
self.collection_name = "prompt_demo_collection"
```

**知识点解析：**

#### Milvus Lite 特性
- **本地存储**: 使用 SQLite 作为底层存储，无需额外服务
- **轻量级**: 适合开发测试和小规模应用
- **向量索引**: 支持多种索引类型（IVF, HNSW, FLAT）
- **实时搜索**: 支持实时向量相似度搜索

#### 集合（Collection）概念
```python
# 创建集合
self.milvus.create_collection(
    collection_name=self.collection_name,
    dimension=len(embeddings[0]),  # 向量维度
    primary_field_name="id",        # 主键字段
    vector_field_name="embedding"   # 向量字段
)
```

**集合结构说明：**
- `id`: 主键，唯一标识每条记录
- `text`: 原始文本内容
- `embedding`: 向量数据
- `filename`: 文件来源标识
- `file_hash`: 文件哈希值，用于增量更新

### 4. 知识库设置

```python
def setup_knowledge_base(self):
    """设置知识库"""
    # 生成 embedding
    response = self.client.embeddings.create(
        input=self.knowledge_texts,
        model="text-embedding-v1"
    )
    embeddings = [item.embedding for item in response.data]
```

**知识点解析：**

#### 批量 Embedding 生成
- **批量处理**: 一次 API 调用处理多个文本，提高效率
- **错误处理**: 需要处理 API 调用失败的情况
- **维度一致性**: 确保所有文本的 embedding 维度相同

#### 数据插入优化
```python
# 准备插入数据
data = []
for i, (text, emb) in enumerate(zip(self.knowledge_texts, embeddings)):
    data.append({
        "id": i + 1,
        "text": text,
        "embedding": emb,
        "filename": "knowledge_base.txt",
        "file_hash": "kb_hash_123"
    })

# 批量插入
self.milvus.insert(
    collection_name=self.collection_name,
    data=data
)
```

**插入策略：**
1. **批量插入**: 一次性插入多条数据，提高性能
2. **ID 管理**: 确保 ID 唯一性，避免冲突
3. **元数据**: 添加文件名和哈希值，便于管理

### 5. 相似文本搜索

```python
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
```

**知识点解析：**

#### 向量搜索原理
1. **查询向量化**: 将用户问题转换为向量
2. **相似度计算**: 计算查询向量与库中所有向量的相似度
3. **排序返回**: 按相似度排序，返回 top-k 结果

#### 搜索参数详解
- `limit`: 返回结果数量限制
- `output_fields`: 指定返回的字段
- `metric_type`: 相似度计算方式（L2, IP, COSINE）

#### 相似度算法
```python
# 余弦相似度计算示例
import numpy as np

def cosine_similarity(vec1, vec2):
    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
```

### 6. 答案生成

```python
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
```

**知识点解析：**

#### Prompt 工程
1. **上下文注入**: 将检索到的相关文本作为上下文
2. **指令明确**: 明确告诉模型基于知识库内容回答
3. **角色设定**: 通过 system message 设定助手角色

#### LLM 参数说明
- `temperature`: 控制输出的随机性（0-1），值越高越随机
- `max_tokens`: 限制输出长度，控制成本
- `model`: 使用的语言模型，这里使用通义千问

#### RAG 架构优势
1. **准确性**: 基于真实知识库，减少幻觉
2. **时效性**: 可以更新知识库，保持信息新鲜
3. **可控性**: 可以控制模型的知识来源

### 7. 问答演示

```python
def qa_demo(self):
    """问答演示"""
    questions = [
        "什么是人工智能？",
        "机器学习和深度学习有什么区别？",
        "自然语言处理有哪些应用？",
        "强化学习是如何工作的？"
    ]
    
    for i, question in enumerate(questions, 1):
        # 搜索相关文本
        similar_texts = self.search_similar_texts(question, top_k=3)
        
        if similar_texts:
            # 构建上下文
            context = "\n".join([hit.get('text', '') for hit in similar_texts])
            # 生成答案
            answer = self.generate_answer(question, context)
```

**知识点解析：**

#### 上下文构建策略
1. **文本拼接**: 将多个相关文本片段拼接
2. **长度控制**: 避免上下文过长，超出模型限制
3. **相关性排序**: 按相似度排序，优先使用最相关的文本

#### 问答流程优化
1. **错误处理**: 处理搜索失败的情况
2. **结果验证**: 验证搜索结果的完整性
3. **性能监控**: 记录搜索和生成时间

## 技术要点总结

### 1. Embedding 技术
- **语义理解**: 将文本转换为数值向量，保持语义关系
- **维度选择**: 根据应用场景选择合适的 embedding 模型
- **批量处理**: 提高 API 调用效率
- **缓存策略**: 避免重复计算 embedding

### 2. 向量数据库
- **索引类型**: 选择合适的向量索引（HNSW, IVF）
- **相似度计算**: 理解不同距离度量方法
- **性能优化**: 批量操作和连接池管理
- **数据一致性**: 确保向量维度匹配

### 3. RAG 架构
- **检索策略**: 选择合适的检索算法和参数
- **上下文管理**: 有效构建和传递上下文
- **答案生成**: 设计合适的 prompt 模板
- **质量评估**: 建立答案质量评估机制

### 4. 系统优化
- **错误处理**: 完善的异常处理机制
- **性能监控**: 关键指标监控和优化
- **扩展性**: 支持知识库动态更新
- **用户体验**: 响应时间和交互设计

## 扩展知识点

### 1. 向量索引算法
- **HNSW (Hierarchical Navigable Small World)**: 适合高维向量，查询速度快
- **IVF (Inverted File Index)**: 适合大规模数据，内存占用低
- **FLAT**: 暴力搜索，精度最高但速度慢

### 2. 相似度计算
- **余弦相似度**: 适合文本 embedding，关注方向而非大小
- **欧氏距离**: 计算向量间的直线距离
- **点积**: 简单快速，但受向量长度影响

### 3. Prompt 工程技巧
- **Few-shot Learning**: 通过示例引导模型行为
- **Chain of Thought**: 引导模型进行推理
- **角色设定**: 通过 system message 设定模型角色

### 4. 性能优化策略
- **向量缓存**: 缓存常用 embedding
- **批量处理**: 减少 API 调用次数
- **异步处理**: 提高并发性能
- **索引优化**: 选择合适的向量索引

## 总结

这个 demo 展示了现代 AI 应用的核心技术栈：**Embedding + 向量数据库 + LLM**。通过 RAG 架构，我们能够构建既准确又可控的智能问答系统。关键技术包括：

1. **文本向量化**: 将非结构化文本转换为可计算的向量
2. **相似度检索**: 在向量空间中快速找到相关内容
3. **上下文增强**: 将检索结果作为 LLM 的输入上下文
4. **智能生成**: 基于上下文生成准确、相关的答案

这种架构为构建企业级 AI 应用提供了可靠的技术基础。 