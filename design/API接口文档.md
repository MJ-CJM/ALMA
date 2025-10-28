# ALMA AI 助手 - API 接口文档

## 📋 接口概述

ALMA AI 助手提供完整的 RESTful API 接口，支持用户管理、对话管理、文件管理等功能。所有接口都基于 HTTP/HTTPS 协议，支持 JSON 格式的数据交换。

## 🔗 基础信息

- **基础 URL**: `http://localhost:8501` (用户前端)
- **管理 URL**: `http://localhost:8502` (管理员前端)
- **数据格式**: JSON
- **字符编码**: UTF-8
- **认证方式**: 会话认证

## 🔐 认证接口

### 1. 用户注册

**接口**: `POST /api/register`

**请求参数**:
```json
{
  "username": "string",      // 用户名，3-50字符，字母数字
  "password": "string",      // 密码，至少6位
  "invite_code": "string"    // 邀请码
}
```

**响应示例**:
```json
{
  "success": true,
  "message": "注册成功",
  "data": {
    "user_id": 123,
    "username": "testuser"
  }
}
```

**错误响应**:
```json
{
  "success": false,
  "message": "邀请码无效或已过期",
  "error_code": "INVALID_INVITE_CODE"
}
```

### 2. 用户登录

**接口**: `POST /api/login`

**请求参数**:
```json
{
  "username": "string",
  "password": "string"
}
```

**响应示例**:
```json
{
  "success": true,
  "message": "登录成功",
  "data": {
    "user_id": 123,
    "username": "testuser",
    "login_time": "2024-12-01T10:30:00Z"
  }
}
```

### 3. 用户登出

**接口**: `POST /api/logout`

**响应示例**:
```json
{
  "success": true,
  "message": "登出成功"
}
```

## 👥 用户管理接口

### 1. 获取用户信息

**接口**: `GET /api/user/info`

**响应示例**:
```json
{
  "success": true,
  "data": {
    "user_id": 123,
    "username": "testuser",
    "created_at": "2024-12-01T10:30:00Z",
    "login_time": "2024-12-01T10:30:00Z"
  }
}
```

### 2. 更新用户信息

**接口**: `PUT /api/user/info`

**请求参数**:
```json
{
  "username": "string",      // 可选，新用户名
  "password": "string"       // 可选，新密码
}
```

**响应示例**:
```json
{
  "success": true,
  "message": "用户信息更新成功"
}
```

## 💬 对话管理接口

### 1. 获取对话列表

**接口**: `GET /api/conversations`

**查询参数**:
- `page`: 页码，默认1
- `limit`: 每页数量，默认20
- `workflow_id`: 工作流ID过滤

**响应示例**:
```json
{
  "success": true,
  "data": {
    "conversations": [
      {
        "id": 1,
        "conversation_name": "新对话",
        "workflow_id": "workflow_1",
        "created_at": "2024-12-01T10:30:00Z",
        "updated_at": "2024-12-01T10:30:00Z",
        "message_count": 5
      }
    ],
    "total": 10,
    "page": 1,
    "limit": 20
  }
}
```

### 2. 创建新对话

**接口**: `POST /api/conversations`

**请求参数**:
```json
{
  "conversation_name": "string",  // 对话名称
  "workflow_id": "string"         // 工作流ID
}
```

**响应示例**:
```json
{
  "success": true,
  "message": "对话创建成功",
  "data": {
    "conversation_id": 123,
    "conversation_name": "新对话",
    "workflow_id": "workflow_1"
  }
}
```

### 3. 获取对话详情

**接口**: `GET /api/conversations/{conversation_id}`

**响应示例**:
```json
{
  "success": true,
  "data": {
    "id": 123,
    "conversation_name": "新对话",
    "workflow_id": "workflow_1",
    "created_at": "2024-12-01T10:30:00Z",
    "updated_at": "2024-12-01T10:30:00Z",
    "messages": [
      {
        "id": 1,
        "role": "user",
        "content": "你好",
        "created_at": "2024-12-01T10:30:00Z"
      },
      {
        "id": 2,
        "role": "assistant",
        "content": "你好！有什么可以帮助你的吗？",
        "created_at": "2024-12-01T10:30:05Z"
      }
    ]
  }
}
```

### 4. 更新对话名称

**接口**: `PUT /api/conversations/{conversation_id}`

**请求参数**:
```json
{
  "conversation_name": "string"
}
```

**响应示例**:
```json
{
  "success": true,
  "message": "对话名称更新成功"
}
```

### 5. 删除对话

**接口**: `DELETE /api/conversations/{conversation_id}`

**响应示例**:
```json
{
  "success": true,
  "message": "对话删除成功"
}
```

## 🤖 AI 对话接口

### 1. 发送消息

**接口**: `POST /api/conversations/{conversation_id}/messages`

**请求参数**:
```json
{
  "content": "string",        // 消息内容
  "workflow_id": "string"     // 工作流ID
}
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "message_id": 123,
    "role": "assistant",
    "content": "AI回复内容",
    "created_at": "2024-12-01T10:30:00Z"
  }
}
```

### 2. 获取消息列表

**接口**: `GET /api/conversations/{conversation_id}/messages`

**查询参数**:
- `page`: 页码，默认1
- `limit`: 每页数量，默认50

**响应示例**:
```json
{
  "success": true,
  "data": {
    "messages": [
      {
        "id": 1,
        "role": "user",
        "content": "你好",
        "created_at": "2024-12-01T10:30:00Z"
      },
      {
        "id": 2,
        "role": "assistant",
        "content": "你好！有什么可以帮助你的吗？",
        "created_at": "2024-12-01T10:30:05Z"
      }
    ],
    "total": 2,
    "page": 1,
    "limit": 50
  }
}
```

## 📁 文件管理接口

### 1. 上传文件

**接口**: `POST /api/files/upload`

**请求参数**:
- `file`: 文件数据 (multipart/form-data)
- `description`: 文件描述 (可选)

**支持的文件类型**:
- 文本文件: .txt, .md
- PDF文件: .pdf
- Office文档: .doc, .docx, .xls, .xlsx, .ppt, .pptx

**响应示例**:
```json
{
  "success": true,
  "message": "文件上传成功，等待管理员审批",
  "data": {
    "file_id": 123,
    "filename": "document.pdf",
    "filepath": "uploads/abc123.pdf",
    "status": "pending",
    "upload_at": "2024-12-01T10:30:00Z"
  }
}
```

### 2. 获取用户文件列表

**接口**: `GET /api/files`

**查询参数**:
- `status`: 文件状态过滤 (pending, approved, rejected)
- `page`: 页码，默认1
- `limit`: 每页数量，默认20

**响应示例**:
```json
{
  "success": true,
  "data": {
    "files": [
      {
        "id": 123,
        "filename": "document.pdf",
        "filepath": "uploads/abc123.pdf",
        "status": "approved",
        "upload_at": "2024-12-01T10:30:00Z",
        "reviewed_at": "2024-12-01T10:35:00Z"
      }
    ],
    "total": 5,
    "page": 1,
    "limit": 20
  }
}
```

### 3. 下载文件

**接口**: `GET /api/files/{file_id}/download`

**响应**: 文件二进制数据

**响应头**:
```
Content-Type: application/octet-stream
Content-Disposition: attachment; filename="document.pdf"
```

## 🔧 工作流管理接口

### 1. 获取工作流列表

**接口**: `GET /api/workflows`

**响应示例**:
```json
{
  "success": true,
  "data": [
    {
      "id": "workflow_1",
      "name": "通用助手",
      "description": "适用于一般性问答和对话",
      "status": "active"
    },
    {
      "id": "workflow_2",
      "name": "专业咨询",
      "description": "提供特定领域的专业知识咨询",
      "status": "active"
    }
  ]
}
```

### 2. 测试工作流连接

**接口**: `POST /api/workflows/{workflow_id}/test`

**响应示例**:
```json
{
  "success": true,
  "data": {
    "status": "ok",
    "message": "连接正常",
    "response_time": 1.23
  }
}
```

## 🎫 邀请码管理接口

### 1. 获取邀请码列表

**接口**: `GET /api/invite-codes`

**查询参数**:
- `status`: 状态过滤 (active, inactive)
- `page`: 页码，默认1
- `limit`: 每页数量，默认20

**响应示例**:
```json
{
  "success": true,
  "data": {
    "invite_codes": [
      {
        "id": 1,
        "code": "ALMA2024001",
        "max_uses": 10,
        "used_count": 3,
        "status": "active",
        "expires_at": "2025-12-01T00:00:00Z",
        "description": "测试邀请码",
        "created_at": "2024-12-01T10:30:00Z"
      }
    ],
    "total": 5,
    "page": 1,
    "limit": 20
  }
}
```

### 2. 创建邀请码

**接口**: `POST /api/invite-codes`

**请求参数**:
```json
{
  "code": "string",           // 邀请码
  "max_uses": 10,            // 最大使用次数
  "expires_days": 365,        // 过期天数
  "description": "string"     // 描述
}
```

**响应示例**:
```json
{
  "success": true,
  "message": "邀请码创建成功",
  "data": {
    "id": 123,
    "code": "ALMA2024001",
    "max_uses": 10,
    "used_count": 0,
    "status": "active",
    "expires_at": "2025-12-01T00:00:00Z"
  }
}
```

### 3. 更新邀请码状态

**接口**: `PUT /api/invite-codes/{invite_code_id}`

**请求参数**:
```json
{
  "status": "active|inactive"
}
```

**响应示例**:
```json
{
  "success": true,
  "message": "邀请码状态更新成功"
}
```

## 🔧 管理员接口

### 1. 管理员登录

**接口**: `POST /api/admin/login`

**请求参数**:
```json
{
  "password": "string"
}
```

**响应示例**:
```json
{
  "success": true,
  "message": "管理员登录成功"
}
```

### 2. 获取系统概览

**接口**: `GET /api/admin/overview`

**响应示例**:
```json
{
  "success": true,
  "data": {
    "total_users": 150,
    "total_conversations": 1200,
    "total_messages": 5000,
    "pending_files": 5,
    "active_workflows": 3,
    "system_status": "healthy"
  }
}
```

### 3. 文件审批

**接口**: `PUT /api/admin/files/{file_id}/approve`

**请求参数**:
```json
{
  "action": "approve|reject",
  "reason": "string"  // 可选，拒绝原因
}
```

**响应示例**:
```json
{
  "success": true,
  "message": "文件审批成功"
}
```

### 4. 获取用户列表

**接口**: `GET /api/admin/users`

**查询参数**:
- `page`: 页码，默认1
- `limit`: 每页数量，默认20
- `search`: 搜索关键词

**响应示例**:
```json
{
  "success": true,
  "data": {
    "users": [
      {
        "id": 123,
        "username": "testuser",
        "created_at": "2024-12-01T10:30:00Z",
        "last_login": "2024-12-01T10:30:00Z",
        "conversation_count": 5,
        "file_count": 2
      }
    ],
    "total": 150,
    "page": 1,
    "limit": 20
  }
}
```

## 📊 统计接口

### 1. 获取对话统计

**接口**: `GET /api/stats/conversations`

**查询参数**:
- `start_date`: 开始日期 (YYYY-MM-DD)
- `end_date`: 结束日期 (YYYY-MM-DD)
- `workflow_id`: 工作流ID过滤

**响应示例**:
```json
{
  "success": true,
  "data": {
    "total_conversations": 1200,
    "daily_conversations": [
      {
        "date": "2024-12-01",
        "count": 50
      },
      {
        "date": "2024-12-02",
        "count": 45
      }
    ],
    "workflow_stats": [
      {
        "workflow_id": "workflow_1",
        "name": "通用助手",
        "count": 800
      },
      {
        "workflow_id": "workflow_2",
        "name": "专业咨询",
        "count": 400
      }
    ]
  }
}
```

### 2. 获取用户活跃度统计

**接口**: `GET /api/stats/users`

**查询参数**:
- `start_date`: 开始日期
- `end_date`: 结束日期

**响应示例**:
```json
{
  "success": true,
  "data": {
    "total_users": 150,
    "active_users": 120,
    "new_users": 15,
    "daily_active_users": [
      {
        "date": "2024-12-01",
        "count": 45
      }
    ]
  }
}
```

## 🚨 错误码说明

| 错误码 | 说明 | 解决方案 |
|--------|------|----------|
| `INVALID_CREDENTIALS` | 用户名或密码错误 | 检查用户名和密码 |
| `INVALID_INVITE_CODE` | 邀请码无效 | 使用有效的邀请码 |
| `USER_EXISTS` | 用户名已存在 | 使用其他用户名 |
| `CONVERSATION_NOT_FOUND` | 对话不存在 | 检查对话ID |
| `FILE_NOT_FOUND` | 文件不存在 | 检查文件ID |
| `WORKFLOW_NOT_FOUND` | 工作流不存在 | 检查工作流ID |
| `PERMISSION_DENIED` | 权限不足 | 检查用户权限 |
| `RATE_LIMIT_EXCEEDED` | 请求频率过高 | 降低请求频率 |
| `INTERNAL_ERROR` | 服务器内部错误 | 联系技术支持 |

## 🔒 安全说明

### 1. 认证机制
- 使用会话认证，登录后获得会话令牌
- 会话令牌存储在 `st.session_state` 中
- 支持自动过期和手动登出

### 2. 权限控制
- 用户只能访问自己的数据
- 管理员可以访问所有数据
- 文件上传需要管理员审批

### 3. 数据验证
- 所有输入参数都进行验证
- 防止 SQL 注入攻击
- 文件类型和大小限制

### 4. 错误处理
- 统一的错误响应格式
- 详细的错误信息
- 安全的错误日志记录

## 📝 使用示例

### 1. 用户注册流程

```bash
# 1. 注册用户
curl -X POST http://localhost:8501/api/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "password123",
    "invite_code": "ALMA2024001"
  }'

# 2. 用户登录
curl -X POST http://localhost:8501/api/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "password123"
  }'
```

### 2. 创建对话并发送消息

```bash
# 1. 创建对话
curl -X POST http://localhost:8501/api/conversations \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_name": "测试对话",
    "workflow_id": "workflow_1"
  }'

# 2. 发送消息
curl -X POST http://localhost:8501/api/conversations/123/messages \
  -H "Content-Type: application/json" \
  -d '{
    "content": "你好，请介绍一下自己",
    "workflow_id": "workflow_1"
  }'
```

### 3. 文件上传

```bash
# 上传文件
curl -X POST http://localhost:8501/api/files/upload \
  -F "file=@document.pdf" \
  -F "description=测试文档"
```

---

## 📋 总结

ALMA AI 助手提供了完整的 RESTful API 接口，支持：

- ✅ **用户管理**: 注册、登录、信息管理
- ✅ **对话管理**: 创建、查询、更新、删除对话
- ✅ **AI 对话**: 发送消息、获取回复
- ✅ **文件管理**: 上传、下载、审批文件
- ✅ **工作流管理**: 工作流列表、状态监控
- ✅ **邀请码管理**: 创建、查询、管理邀请码
- ✅ **管理员功能**: 系统概览、用户管理、文件审批
- ✅ **统计分析**: 对话统计、用户活跃度

所有接口都遵循 RESTful 设计原则，提供统一的错误处理和响应格式，确保系统的稳定性和易用性。
