# Prompt 服务

## 概述
Prompt 服务负责生成结构化的提示词模板，结合 RAG 模块的检索结果，为大语言模型提供上下文增强的提示词。支持问答和学习计划生成两种场景。

## 功能特性
- 智能问答提示词生成
- 个性化学习计划提示词构建
- 统一的模板管理系统
- 与 RAG 模块的无缝集成
- 为 Dify 工作流提供标准化接口
- 支持直接调用和 HTTP 调用两种模式

## 架构设计

### 文件结构
```
prompt-service/
├── prompt_server.py   # FastAPI HTTP 服务器
├── requirements.txt   # 依赖包
└── README.md         # 说明文档
```

### 技术栈
- **FastAPI**: Web 框架
- **Requests**: HTTP 客户端
- **Pydantic**: 数据验证
- **RAG Service**: 文档检索服务

### 代码逻辑

#### 1. 问答流程
```python
用户问题 → RAG检索 → 上下文整合 → 问答Prompt → 返回给大模型
```

#### 2. 学习计划生成流程
```python
学习目标+时间 → RAG检索 → 知识整合 → 计划Prompt → 返回给大模型
```

#### 3. 核心组件

**PromptTemplate 类**：
- 管理各种提示词模板
- 支持动态参数注入
- 模板类型：qa（问答）、study_plan（学习计划）

**RAG 集成模式**：
- `query_rag_service_direct()`: 直接调用 RAG 服务类
- `query_rag_service_http()`: 通过 HTTP API 调用

**API 接口层**：
- 标准接口：面向通用场景
- Dify 接口：面向工作流集成

## 安装和运行

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 确保 RAG 服务运行
RAG 服务需要在 `http://localhost:5000` 运行

### 3. 启动服务
```bash
python prompt_server.py
```
服务将在 `http://localhost:5001` 启动

## API 接口

### 1. 问答接口
```http
POST /qa
Content-Type: application/json

{
  "question": "什么是人工智能？",
  "limit": 5
}
```

响应示例：
```json
{
  "prompt": "基于以下相关文档内容，请回答用户的问题...",
  "context_sources": [
    {
      "filename": "ai_book.pdf",
      "text": "人工智能是...",
      "score": 0.85
    }
  ]
}
```

### 2. 学习计划生成接口
```http
POST /study-plan
Content-Type: application/json

{
  "goal": "学习机器学习",
  "timeframe": "3个月",
  "limit": 10
}
```

响应示例：
```json
{
  "prompt": "基于以下知识内容，为用户制定学习计划...",
  "learning_materials": [
    {
      "filename": "ml_guide.pdf",
      "text": "机器学习基础...",
      "score": 0.90
    }
  ]
}
```

### 3. Dify 专用接口

#### 问答接口
```http
POST /dify-qa
Content-Type: application/json

{
  "question": "深度学习的原理是什么？"
}
```

响应示例：
```json
{
  "success": true,
  "prompt": "生成的提示词内容",
  "context_count": 5,
  "timestamp": "2024-01-01T12:00:00"
}
```

#### 学习计划接口
```http
POST /dify-study-plan
Content-Type: application/json

{
  "goal": "成为数据科学家",
  "timeframe": "6个月"
}
```

### 4. 自定义模板接口
```http
POST /prompt-template
Content-Type: application/json

{
  "type": "qa",
  "parameters": {
    "context": "相关文档内容",
    "question": "用户问题"
  }
}
```

### 5. 工具接口

#### 获取可用模板
```http
GET /templates
```

#### 健康检查
```http
GET /health
```

## 测试方法

### 1. 基本功能测试
```bash
# 健康检查
curl http://localhost:5001/health

# 问答测试
curl -X POST http://localhost:5001/qa \
  -H "Content-Type: application/json" \
  -d '{"question": "什么是机器学习？", "limit": 3}'

# 学习计划测试
curl -X POST http://localhost:5001/study-plan \
  -H "Content-Type: application/json" \
  -d '{"goal": "学习Python", "timeframe": "2个月"}'
```

### 2. Dify 接口测试
```bash
# Dify 问答测试
curl -X POST http://localhost:5001/dify-qa \
  -H "Content-Type: application/json" \
  -d '{"question": "深度学习是什么？"}'

# Dify 学习计划测试
curl -X POST http://localhost:5001/dify-study-plan \
  -H "Content-Type: application/json" \
  -d '{"goal": "AI工程师", "timeframe": "1年"}'
```

### 3. 使用 Python 测试
```python
import requests

# 问答测试
response = requests.post(
    "http://localhost:5001/qa",
    json={
        "question": "什么是自然语言处理？",
        "limit": 5
    }
)
print("Prompt:", response.json()["prompt"])

# 学习计划测试
response = requests.post(
    "http://localhost:5001/study-plan",
    json={
        "goal": "掌握深度学习",
        "timeframe": "4个月"
    }
)
print("Study Plan Prompt:", response.json()["prompt"])
```

### 4. 集成测试
```python
# 完整流程测试：问题 → RAG检索 → Prompt生成 → 大模型调用
import requests

def test_qa_pipeline():
    # 1. 调用问答接口获取 Prompt
    prompt_response = requests.post(
        "http://localhost:5001/dify-qa",
        json={"question": "什么是神经网络？"}
    )
    
    if prompt_response.json()["success"]:
        prompt = prompt_response.json()["prompt"]
        print("Generated Prompt:", prompt)
        
        # 2. 将 Prompt 发送给大模型（示例）
        # llm_response = call_llm_api(prompt)
        # print("LLM Response:", llm_response)

test_qa_pipeline()
```

### 5. 性能测试
```bash
# 并发请求测试
ab -n 50 -c 5 -T 'application/json' \
  -p qa_data.json \
  http://localhost:5001/dify-qa

# 创建测试数据文件
echo '{"question": "什么是人工智能？"}' > qa_data.json
```

## 提示词模板

### 1. 问答模板 (qa)
```
基于以下相关文档内容，请回答用户的问题。如果文档内容不足以回答问题，请说明需要更多信息。

相关文档：
{context}

用户问题：{question}

请提供详细、准确的回答：
```

### 2. 学习计划模板 (study_plan)
```
基于以下知识内容，为用户制定学习计划。

相关知识内容：
{context}

学习目标：{goal}
时间范围：{timeframe}

请制定一个详细的学习计划，包括：
1. 学习阶段划分
2. 每个阶段的具体内容
3. 建议的学习方法
4. 时间安排
5. 评估方式

学习计划：
```

## 配置说明

### RAG 服务配置
- 默认 RAG 服务地址：`http://localhost:5000`
- 可通过环境变量 `RAG_SERVICE_URL` 修改

### 调用模式配置
- 支持直接调用和HTTP调用两种模式
- 默认使用直接调用模式（性能更好）
- HTTP模式用于分布式部署

## 与 Dify 集成

### 1. 在 Dify 中配置 HTTP 节点
- URL: `http://localhost:5001/dify-qa`
- 方法: POST
- 请求体: `{"question": "{{question}}"}`

### 2. 获取生成的 Prompt
```json
{
  "success": true,
  "prompt": "{{生成的提示词}}",
  "context_count": 5,
  "timestamp": "2024-01-01T12:00:00"
}
```

### 3. 将 Prompt 传递给 LLM 节点
使用 `{{dify-qa.prompt}}` 作为 LLM 的输入

## 故障排除

### 常见问题
1. **RAG 服务连接失败**：检查 RAG 服务是否正常运行
2. **上下文为空**：确认 RAG 服务中有相关文档
3. **模板渲染错误**：检查参数是否完整

### 日志查看
服务运行时输出详细日志：
- RAG 服务调用状态
- 模板渲染过程
- 错误详细信息

## 扩展功能
- 支持更多提示词模板类型
- 添加模板版本管理
- 集成更多外部知识源
- 支持多语言提示词生成