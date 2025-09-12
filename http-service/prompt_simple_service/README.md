## **学生 B - Prompt 构建与 API 服务模块（prompt_builder.py+prompt_server.py）**

**具体职责：**

- 接收用户输入（问答问题或学习目标）；
- 调用知识库检索接口（学生 A），获取相关语义段落；
- 使用 prompt_builder.py 定义并管理不同类型的 Prompt 模板：
    - 问答模板 (QA Template)
    - 学习计划生成模板 (Plan Template)
- 提供明确的 HTTP 接口供 Dify 工作流调用，返回完整的 Prompt；

**接口定义：**

- 问答 Prompt 接口：POST /ask，返回格式化后的问答 Prompt；
- 学习计划 Prompt 接口：POST /plan，返回格式化后的学习计划 Prompt；

## **使用说明**

### 安装依赖
```bash
pip install -r requirements.txt
```

### 启动服务
```bash
python prompt_server.py
```

服务将在 `http://localhost:8001` 启动

### API 接口

#### 1. 健康检查
- **GET** `/health`
- 返回服务状态

#### 2. 问答 Prompt 接口
- **POST** `/ask`
- 请求体：
```json
{
    "query": "用户问题",
    "top_k": 5
}
```
- 返回格式化的问答 Prompt

#### 3. 学习计划 Prompt 接口
- **POST** `/plan`
- 请求体：
```json
{
    "goal": "学习目标",
    "time_range": "时间范围",
    "learning_background": "学习背景",
    "top_k": 5
}
```
- 返回格式化的学习计划 Prompt

### 演示
运行演示脚本：
```bash
python demo.py
```

### API 文档
访问 `http://localhost:8001/docs` 查看完整的 API 文档