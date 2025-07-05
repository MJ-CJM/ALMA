# RAG模块

基于阿里云API的PDF文档检索和向量化服务。

## 功能特性

- PDF文档自动处理和文本提取
- 使用阿里云text-embedding-v4模型生成向量嵌入
- 基于Milvus Lite的本地向量数据库存储
- 提供语义搜索API接口
- 支持TopK查询和相关性阈值过滤
- 内存占用低（~100-200MB）

## 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 设置API密钥
```bash
export ALIYUN_API_KEY="your-api-key"
```

### 3. 启动服务
```bash
python rag_server.py
```

### 4. 处理PDF文档
```bash
curl -X POST http://localhost:8000/process \
  -H "Content-Type: application/json" \
  -d '{"batch_size": 5}'
```

### 5. 搜索文档
```bash
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "搜索关键词", "limit": 5}'
```

## API接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/search` | POST | 搜索相关文档 |
| `/process` | POST | 处理PDF文档 |
| `/health` | GET | 服务状态检查 |
| `/memory` | GET | 内存使用情况 |
| `/stats` | GET | 数据库统计 |
| `/api-test` | GET | 测试API连接 |

## 配置参数

- `chunk_size`: 400字符（文本分片大小）
- `overlap`: 50字符（分片重叠）
- `min_length`: 30字符（最小文本长度）
- `batch_size`: 5（API调用批次大小）

## 性能特点

- **内存占用**: ~100-200MB
- **启动时间**: 5-10秒
- **批处理大小**: 5-10个文本
- **向量维度**: 1024维

## 注意事项

1. 需要稳定的网络连接
2. API调用会产生费用
3. 数据会发送到云端处理
4. 建议定期备份向量数据库

## 故障排除

### API密钥错误
```bash
export ALIYUN_API_KEY="your-api-key"
```

### 内存不足
```bash
curl http://localhost:8000/memory
```

### 网络连接失败
检查网络连接和API密钥是否正确。