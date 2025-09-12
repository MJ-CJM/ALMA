## **学生 A - 知识库构建模块（rag_service.py+rag_server.py）**

**具体职责：**

- 使用 Python 提取 PDF 文件内容，并进行文本段落切分；
- 初始化 Qwen3-Embedding 模型（推荐使用 HuggingFace transformers）；
- 将提取的文本段落批量嵌入为向量，并存储至本地 Milvus Lite 数据库；
- 提供关键词检索 API，基于语义相似性返回相关知识段落；

**接口定义：**

- 提供向量插入接口；
- 提供查询接口：GET /search?keyword={keyword}&top_k={top_k}

## **使用说明**

### 安装依赖
```bash
pip install -r requirements.txt
```

### 准备数据
将 PDF 文件放在 `data/pdf/` 目录中，服务启动时会自动处理这些文件。

### 启动服务
```bash
python rag_server.py
```

服务将在 `http://localhost:8000` 启动

### API 接口

#### 1. 健康检查
- **GET** `/health`
- 返回服务状态

#### 2. 搜索接口
- **GET** `/search?keyword={keyword}&top_k={top_k}`
- 参数：
  - `keyword`: 搜索关键词（必需）
  - `top_k`: 返回结果数量，默认5，最大20
- 返回基于语义相似性的搜索结果

### 演示
运行演示脚本：
```bash
python demo.py
```

### 清空数据库
如果需要重新开始，可以清空 Milvus 数据库：
```bash
# 清空默认集合
python clear_milvus.py

# 清空指定集合
python clear_milvus.py <collection_name>

# 清空所有集合
python clear_milvus.py all
```

### API 文档
访问 `http://localhost:8000/docs` 查看完整的 API 文档

## **功能特点**

- ✅ **PDF 文本提取**: 使用 PyMuPDF 提取 PDF 文件内容
- ✅ **文本段落切分**: 自动将文本分割为有意义的段落
- ✅ **向量嵌入**: 使用 Qwen3-Embedding 模型生成文本向量
- ✅ **向量存储**: 将向量存储到 Milvus 数据库中
- ✅ **语义搜索**: 基于向量相似性进行语义搜索
- ✅ **简化接口**: 只提供核心的搜索功能