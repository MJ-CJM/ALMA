# Prompt Service 模块

## 📋 项目概述

Prompt Service 是一个面向大模型应用的标准化 Prompt 构建与服务模块。它通过调用 rag-module 的知识检索能力，将用户问题、学习目标等与知识库内容结合，自动生成结构化、高质量的 Prompt，支持问答、学习计划、总结、解释等多种场景，并可灵活扩展。

---

## 🏗️ 系统架构

```
Prompt Service 架构
├── prompt_server.py      # FastAPI HTTP 服务，统一对外接口
├── prompt_builder.py     # Prompt 构建工具，模板与上下文注入
├── rag-module            # 通过 HTTP API 调用知识检索能力
└── Dify/外部系统         # 通过 HTTP 调用 prompt_server
```

- **解耦设计**：Prompt Service 只通过 HTTP API 调用 rag-module，不直接操作底层向量库。
- **模板驱动**：所有 Prompt 通过模板和上下文拼接生成，便于扩展和维护。
- **标准接口**：所有服务接口均为 HTTP RESTful，便于 Dify 等平台集成。

---

## 🔧 技术实现

- **FastAPI**：高性能异步 Web 框架，提供标准化 HTTP 服务。
- **PromptBuilder**：核心工具类，支持多类型 Prompt 模板构建、上下文注入、知识检索。
- **RAG API 调用**：通过 HTTP 请求 rag-module 的 `/search` 接口获取知识片段。
- **模板扩展**：支持动态添加新类型 Prompt 模板，满足未来扩展需求。
- **异常处理**：所有接口均有参数校验和异常处理，保证服务健壮性。

---

## 📚 API 接口说明

### 1. 健康检查
- **GET `/health`**
- 检查服务健康状态

### 2. 问答 Prompt 构建
- **POST `/prompt/qa`**
- 根据用户问题和知识检索结果，生成结构化问答 Prompt
- **请求示例**：
```json
{
  "query": "什么是 FixAgent？",
  "top_k": 3,
  "filename": "FixAgent.pdf"
}
```
- **返回示例**：
```json
{
  "prompt": "...",
  "prompt_type": "qa",
  "query": "什么是 FixAgent？",
  "search_results_count": 3
}
```

### 3. 学习计划 Prompt 构建
- **POST `/prompt/learning-plan`**
- 根据目标、时间范围和知识检索结果，生成学习计划 Prompt
- **请求示例**：
```json
{
  "goal": "掌握大模型原理",
  "time_range": "2024-07-01~2024-08-01",
  "learning_background": "有一定机器学习基础",
  "top_k": 5
}
```

### 4. 总结 Prompt 构建
- **POST `/prompt/summary`**
- 根据内容和总结要求，结合知识检索结果，生成总结 Prompt
- **请求示例**：
```json
{
  "content": "大模型的训练流程...",
  "summary_requirements": "请总结核心流程和关键技术",
  "top_k": 3
}
```

### 5. 解释 Prompt 构建
- **POST `/prompt/explanation`**
- 对某个概念或问题进行详细解释
- **请求示例**：
```json
{
  "concept": "RAG",
  "explanation_requirements": "请详细解释 RAG 的原理和应用场景",
  "top_k": 3
}
```

### 6. 自定义 Prompt 构建
- **POST `/prompt/custom`**
- 支持自定义 Prompt 类型和上下文，适合扩展新类型
- **请求示例**：
```json
{
  "prompt_type": "qa",
  "query": "什么是向量数据库？",
  "top_k": 2,
  "filename": "FixAgent.pdf",
  "additional_context": {"extra_info": "可选的上下文"}
}
```

### 7. 添加新模板
- **POST `/template/add`**
- 动态添加新的 Prompt 模板
- **请求示例**：
```json
{
  "prompt_type": "my_custom_type",
  "template": "自定义模板内容 {query} {search_results}"
}
```

### 8. 获取所有支持的 Prompt 类型
- **GET `/types`**
- 获取当前支持的所有 Prompt 类型

### 9. 检查 RAG 服务健康
- **GET `/rag/health`**
- 检查 rag-module 服务是否可用

---

## 💡 使用建议

- 推荐通过 `/docs` 访问自动生成的 Swagger API 文档，获取所有接口的详细参数和返回示例。
- 可根据业务需求扩展自定义 Prompt 类型和模板。
- 适合 Dify、工作流平台等作为 HTTP 节点直接集成。

---

## 📁 目录结构

```
prompt-service/
├── prompt_server.py      # FastAPI HTTP 服务
├── prompt_builder.py     # Prompt 构建工具
├── requirements.txt      # 依赖包列表
└── README.md             # 项目文档
```

---

**版本**: 1.0.0  
**更新时间**: 2025-07-05  
**维护者**: Prompt Service 开发团队