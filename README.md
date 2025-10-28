# ALMA - AI Learning Multi-Agent

基于 Streamlit 和 SQLModel 的 AI 聊天助手系统，支持多工作流、文件上传审批和用户管理。

## 📚 设计文档

完整的项目设计文档位于 `design/` 目录，包含：

- 🏗️ [项目架构设计文档](design/项目架构设计文档.md) - 整体架构和设计理念
- 🚀 [快速上手指南](design/快速上手指南.md) - 5分钟快速启动
- 🔧 [技术实现细节](design/技术实现细节.md) - 深度技术分析
- 📡 [API接口文档](design/API接口文档.md) - 完整接口规范
- 📖 [设计文档索引](design/README.md) - 文档导航指南

**推荐阅读顺序**：快速上手指南 → 项目架构设计文档 → 技术实现细节

## 🚀 快速开始

### 1. 安装依赖
```bash
pip install -r web/requirements.txt
```

### 2. 配置数据库
修改 `web/config.json` 中的数据库连接信息：
```json
{
  "database": {
    "host": "101.34.214.7",
    "port": 3306,
    "database": "alma_db",
    "user": "root",
    "password": "wenhantop123"
  }
}
```

### 3. 初始化数据库
```bash
cd web
python init_database_sqlmodel.py
```

### 4. 启动应用

#### 方式一：命令行参数启动（推荐）
```bash
# 用户前端
python start.py -u

# 管理员前端  
python start.py -m

# 初始化数据库
python start.py -i

# 显示帮助
python start.py -h
```

#### 方式二：直接启动脚本
```bash
# 用户前端
python start_user.py

# 管理员前端
python start_manager.py

# 同时启动两个前端
python start_both.py

# 初始化数据库
python init_db.py
```

#### 方式三：交互式启动
```bash
python start.py
```

#### 方式四：直接启动
```bash
streamlit run front.py --server.port 8501        # 用户前端
streamlit run manager_front.py --server.port 8502 # 管理员前端
```

## 📁 项目结构

```
web/
├── models.py                    # SQLModel 数据模型
├── init_database_sqlmodel.py   # 数据库初始化
├── front.py                     # 用户前端
├── manager_front.py             # 管理员前端
├── auth.py                      # 认证系统
├── backend.py                   # Dify 后端连接
├── config.json                  # 配置文件
├── config_local.json            # 本地配置模板
├── start.py                     # 启动脚本
├── requirements.txt             # 依赖包
└── uploads/                     # 文件上传目录
```

## 🔧 核心功能

### 用户功能
- 邀请码注册登录
- 多工作流选择
- 对话管理 (最多12个)
- 文件上传审批
- 个人资料设置

### 管理员功能
- 文件审批管理
- 邀请码管理
- 工作流状态监控
- 系统概览

## 🔑 默认配置

- **邀请码**: ALMA2024001, ALMA2024002, ALMA2024003
- **管理员密码**: admin123456
- **工作流**: 通用助手、专业咨询

## 🛠️ 技术栈

- **前端**: Streamlit
- **后端**: SQLModel + PyMySQL
- **数据库**: MySQL
- **AI**: Dify 工作流
- **认证**: 邀请码 + 密码

## 📞 访问地址

- 用户前端: http://localhost:8501
- 管理员前端: http://localhost:8502