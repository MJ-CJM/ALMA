# RAG 文档检索服务

## 📋 项目概述

RAG (Retrieval-Augmented Generation) 文档检索服务是一个基于向量数据库的智能文档检索系统。该系统能够自动处理 PDF 文档，提取文本内容，生成向量嵌入，并提供语义搜索功能。

## 🏗️ 系统架构

### 核心组件

```
RAG 系统架构
├── 数据层 (Data Layer)
│   ├── PDF 文档存储 (data/pdf/)
│   └── 向量数据库 (db_data/milvus_lite.db)
├── 业务层 (Business Layer)
│   ├── PDF 文本提取 (PyMuPDF)
│   ├── 向量嵌入生成 (Qwen3-Embedding)
│   └── 相似度搜索 (Milvus Lite)
├── API 层 (API Layer)
│   ├── FastAPI 服务器
│   └── RESTful API 接口
└── 客户端 (Client)
    └── HTTP 客户端
```

### 技术栈

| 组件 | 技术 | 版本 | 说明 |
|------|------|------|------|
| Web 框架 | FastAPI | 0.104.1 | 高性能异步 Web 框架 |
| 向量数据库 | Milvus Lite | 2.5.12 | 本地向量存储 |
| PDF 处理 | PyMuPDF | 1.23.8 | PDF 文本提取 |
| 向量嵌入 | Qwen3-Embedding | - | 阿里云百炼服务 |
| HTTP 服务器 | Uvicorn | 0.24.0 | ASGI 服务器 |

## 🔧 技术实现

### 1. 文档处理流程

```python
# 文档处理流程
PDF 文件 → 文本提取 → 段落切分 → 向量嵌入 → 向量存储
```

**详细步骤：**
1. **PDF 文本提取**：使用 PyMuPDF 提取 PDF 文件中的文本内容
2. **段落切分**：按段落分割文本，过滤过短内容
3. **向量嵌入**：使用 Qwen3-Embedding 生成 1024 维向量
4. **数据存储**：将文本和向量存储到 Milvus Lite 数据库

### 2. 向量搜索机制

```python
# 搜索流程
查询文本 → 向量嵌入 → 相似度计算 → 结果排序 → 返回匹配内容
```

**搜索算法：**
- **相似度度量**：余弦相似度 (Cosine Similarity)
- **搜索策略**：向量最近邻搜索
- **结果排序**：按相似度分数降序排列

### 3. 文件管理机制

- **增量更新**：使用 MD5 哈希检测文件变化
- **去重处理**：避免重复处理相同文件
- **自动加载**：服务启动时自动扫描并处理新文件

## 🚀 快速开始

### 环境要求

- Python 3.8+
- 阿里云百炼 API Key

### 安装依赖

```bash
pip install -r requirements.txt
```

### 启动服务

```bash
python rag_server.py
```

服务将在 `http://localhost:8000` 启动

## 📚 API 接口文档

### 基础接口

#### 1. 健康检查
```http
GET /health
```

**响应：**
```json
{
  "status": "healthy",
  "service": "RAG API Server"
}
```

#### 2. 获取服务状态
```http
GET /
```

**响应：**
```json
{
  "message": "RAG API Server 正在运行",
  "status": "ready"
}
```

### 搜索接口

#### 3. 语义搜索
```http
POST /search
```

**请求参数：**
```json
{
  "query": "搜索关键词",
  "top_k": 5,
  "filename": "FixAgent.pdf"
}
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| query | string | 是 | 搜索关键词 |
| top_k | integer | 否 | 返回结果数量 (1-20，默认5) |
| filename | string | 否 | 指定文件名过滤 |

**响应：**
```json
{
  "results": [
    {
      "text": "匹配的文本内容",
      "filename": "FixAgent.pdf",
      "score": 0.85,
      "id": 123
    }
  ],
  "query": "搜索关键词",
  "top_k": 5,
  "filename": "FixAgent.pdf"
}
```

#### 4. 按文件名搜索
```http
GET /search/file/{filename}?top_k=10
```

**路径参数：**
- `filename`: 文件名

**查询参数：**
- `top_k`: 返回结果数量 (1-50，默认10)

**响应：**
```json
{
  "results": [
    {
      "text": "文档内容",
      "filename": "FixAgent.pdf"
    }
  ],
  "filename": "FixAgent.pdf",
  "count": 10
}
```

### 管理接口

#### 5. 重新扫描文档
```http
POST /rescan
```

**请求参数：**
```json
{
  "pdf_dir": "data/pdf"
}
```

**响应：**
```json
{
  "message": "重新扫描完成",
  "new_files": ["FixAgent.pdf"],
  "total_files": ["FixAgent.pdf"]
}
```

#### 6. 获取文件列表
```http
GET /files
```

**响应：**
```json
[
  "FixAgent.pdf",
  "NewDocument.pdf"
]
```

#### 7. 获取集合信息
```http
GET /collection-info
```

**响应：**
```json
{
  "collection_name": "rag_documents",
  "num_entities": 150,
  "available_files": ["FixAgent.pdf"],
  "processed_files_count": 1,
  "db_path": "db_data/milvus_lite.db",
  "stats": {
    "row_count": 150
  }
}
```

## 💡 使用示例

### 示例 1：搜索特定文档
```bash
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "agent 工作原理",
    "top_k": 3,
    "filename": "FixAgent.pdf"
  }'
```

### 示例 2：全局搜索
```bash
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "人工智能",
    "top_k": 10
  }'
```

### 示例 3：获取文档内容
```bash
curl "http://localhost:8000/search/file/FixAgent.pdf?top_k=20"
```

### 示例 4：添加新文档
```bash
# 1. 将 PDF 文件放入 data/pdf 目录
# 2. 重新扫描
curl -X POST "http://localhost:8000/rescan" \
  -H "Content-Type: application/json" \
  -d '{"pdf_dir": "data/pdf"}'
```

## 🔍 API 文档访问

启动服务后，访问以下地址查看完整的 Swagger API 文档：

```
http://localhost:8000/docs
```

## 📁 目录结构

```
rag-module/
├── data/
│   └── pdf/                 # PDF 文档存储目录
├── db_data/                 # 向量数据库存储目录
├── rag_service.py           # 业务逻辑层
├── rag_server.py            # API 服务器
├── requirements.txt          # 依赖包列表
└── README.md               # 项目文档
```

## ⚙️ 配置说明

### 环境变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| API_KEY | sk-1f0b08f7ee4742c39dbb63254f3db29e | 阿里云百炼 API Key |
| BASE_URL | https://dashscope.aliyuncs.com/compatible-mode/v1 | API 基础地址 |
| DIMENSION | 1024 | 向量维度 |
| COLLECTION_NAME | rag_documents | 集合名称 |

### 性能参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| 最大输入长度 | 8192 | 单个文本的最大字符数 |
| 最大批量大小 | 10 | 单次处理的文本数量 |
| 搜索限制 | 20 | 单次搜索的最大结果数 |

## 🛠️ 故障排除

### 常见问题

1. **连接失败**
   ```
   错误：Open local milvus failed
   解决：检查 db_data 目录权限，重启服务
   ```

2. **API Key 错误**
   ```
   错误：生成 embedding 失败
   解决：检查 API Key 配置和网络连接
   ```

3. **文件锁定**
   ```
   错误：数据库文件被锁定
   解决：停止所有服务进程，删除数据库文件重新启动
   ```

### 调试模式

启用调试输出：
```python
# 在 rag_service.py 中设置
DEBUG = True
```

## 📈 性能优化

### 建议配置

1. **内存优化**：增加 Python 堆内存
2. **并发处理**：使用异步处理大量文档
3. **缓存机制**：对频繁查询的结果进行缓存
4. **索引优化**：定期重建向量索引

### 监控指标

- 文档处理速度
- 搜索响应时间
- 向量数据库大小
- API 调用频率

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证。

## 📞 联系方式

如有问题或建议，请通过以下方式联系：

- 提交 Issue
- 发送邮件
- 在线讨论

---

**版本**: 1.0.0  
**更新时间**: 2025-07-05  
**维护者**: RAG 开发团队