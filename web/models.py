"""
SQLModel 数据模型定义
最简化的 ORM 实现
"""

from sqlmodel import SQLModel, Field, create_engine, Session, select, or_
from typing import Optional, List, Dict
from datetime import datetime
from sqlalchemy import desc, asc
import json

# ==================== 数据模型 ====================

class User(SQLModel, table=True, extend_existing=True):
    """用户表"""
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True, max_length=50)
    password_hash: str = Field(max_length=255)
    invite_code: str = Field(max_length=20)
    created_at: datetime = Field(default_factory=datetime.now)
    last_login: Optional[datetime] = Field(default=None)  # 最后登录时间

class InviteCode(SQLModel, table=True, extend_existing=True):
    """邀请码表"""
    id: Optional[int] = Field(default=None, primary_key=True)
    code: str = Field(unique=True, index=True, max_length=20)
    max_uses: int = Field(default=1)
    used_count: int = Field(default=0)
    status: str = Field(default="active", max_length=20)  # active, inactive
    expires_at: Optional[datetime] = Field(default=None)
    description: Optional[str] = Field(default="")
    created_at: datetime = Field(default_factory=datetime.now)

class Conversation(SQLModel, table=True, extend_existing=True):
    """对话表"""
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    conversation_name: str = Field(max_length=100)
    workflow_id: str = Field(max_length=50)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class Message(SQLModel, table=True, extend_existing=True):
    """消息表"""
    id: Optional[int] = Field(default=None, primary_key=True)
    conversation_id: int = Field(foreign_key="conversation.id")
    role: str = Field(max_length=20)  # user, assistant
    content: str = Field()
    created_at: datetime = Field(default_factory=datetime.now)

class UploadedFile(SQLModel, table=True, extend_existing=True):
    """上传文件表"""
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    filename: str = Field(max_length=255)
    filepath: str = Field(max_length=500)
    status: str = Field(default="pending", max_length=20)  # pending, approved, rejected
    upload_at: datetime = Field(default_factory=datetime.now)
    reviewed_at: Optional[datetime] = Field(default=None)

# 新增小火人数据模型
class FireCharacter(SQLModel, table=True, extend_existing=True):
    """小火人角色表"""
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", unique=True)
    level: int = Field(default=1)  # 等级
    experience: int = Field(default=0)  # 当前经验值
    total_messages: int = Field(default=0)  # 总对话消息数
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class Workflow(SQLModel, table=True, extend_existing=True):
    """工作流配置表"""
    id: Optional[int] = Field(default=None, primary_key=True)
    workflow_id: str = Field(unique=True, index=True, max_length=50)  # 唯一标识符
    name: str = Field(max_length=100)
    description: str = Field(default="", max_length=500)
    api_base: str = Field(max_length=500)
    api_key: str = Field(max_length=500)
    status: str = Field(default="active", max_length=20)  # active, inactive
    is_global: bool = Field(default=True)  # 是否全局可见
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class WorkflowUserPermission(SQLModel, table=True, extend_existing=True):
    """工作流用户权限表（白名单）"""
    id: Optional[int] = Field(default=None, primary_key=True)
    workflow_id: int = Field(foreign_key="workflow.id")
    user_id: int = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.now)

# ==================== 数据库管理类 ====================

class DatabaseManager:
    """基于 SQLModel 的数据库管理类"""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.config = self.load_config()
        self.engine = None
        self._init_engine()
    
    def load_config(self) -> dict:
        """加载配置文件"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"配置文件 {self.config_file} 不存在")
        except json.JSONDecodeError:
            raise ValueError(f"配置文件 {self.config_file} 格式错误")
    
    def _init_engine(self):
        """初始化数据库引擎"""
        db_config = self.config['database']
        
        # 构建数据库 URL
        database_url = (
            f"mysql+pymysql://{db_config['user']}:{db_config['password']}"
            f"@{db_config['host']}:{db_config['port']}/{db_config['database']}"
            f"?charset=utf8mb4"
        )
        
        self.engine = create_engine(
            database_url,
            echo=False,  # 设置为 True 可以看到 SQL 语句
            pool_pre_ping=True,  # 连接池预检查
            pool_recycle=3600,  # 连接回收时间
        )
    
    def create_tables(self):
        """创建所有表"""
        if self.engine:
            SQLModel.metadata.create_all(self.engine)
    
    def get_session(self):
        """获取数据库会话"""
        return Session(self.engine)
    
    # ==================== 用户管理 ====================
    
    def create_user(self, username: str, password: str, invite_code: str) -> bool:
        """创建新用户"""
        try:
            # 验证邀请码
            if not self.validate_invite_code(invite_code):
                return False
            
            # 检查用户名是否已存在
            with self.get_session() as session:
                existing_user = session.exec(
                    select(User).where(User.username == username)
                ).first()
                
                if existing_user:
                    return False
                
                # 直接存储明文密码
                # 创建用户
                user = User(
                    username=username,
                    password_hash=password,  # 直接存储明文密码
                    invite_code=invite_code
                )
                session.add(user)
                session.commit()
                
                # 使用邀请码
                self.use_invite_code(invite_code)
                
                return True
                
        except Exception as e:
            print(f"创建用户失败: {e}")
            return False
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """根据用户名获取用户信息"""
        try:
            with self.get_session() as session:
                return session.exec(
                    select(User).where(User.username == username)
                ).first()
        except Exception as e:
            print(f"获取用户信息失败: {e}")
            return None
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """根据用户ID获取用户信息"""
        try:
            with self.get_session() as session:
                return session.get(User, user_id)
        except Exception as e:
            print(f"获取用户信息失败: {e}")
            return None
    
    def verify_password(self, password: str, password_hash: str) -> bool:
        """验证密码（明文比较）"""
        try:
            return password == password_hash
        except Exception as e:
            print(f"密码验证失败: {e}")
            return False
    
    # ==================== 邀请码管理 ====================
    
    def validate_invite_code(self, code: str) -> bool:
        """验证邀请码是否有效"""
        try:
            with self.get_session() as session:
                invite_code = session.exec(
                    select(InviteCode).where(InviteCode.code == code)
                ).first()
                
                if not invite_code:
                    return False
                
                # 检查状态
                if invite_code.status != 'active':
                    return False
                
                # 检查使用次数
                if invite_code.used_count >= invite_code.max_uses:
                    return False
                
                # 检查过期时间
                if invite_code.expires_at and datetime.now() > invite_code.expires_at:
                    return False
                
                return True
                
        except Exception as e:
            print(f"验证邀请码失败: {e}")
            return False
    
    def use_invite_code(self, code: str) -> bool:
        """使用邀请码（增加使用次数）"""
        try:
            with self.get_session() as session:
                invite_code = session.exec(
                    select(InviteCode).where(InviteCode.code == code)
                ).first()
                
                if invite_code:
                    invite_code.used_count += 1
                    session.add(invite_code)
                    session.commit()
                    return True
                return False
                
        except Exception as e:
            print(f"使用邀请码失败: {e}")
            return False
    
    def create_invite_code(self, code: str, max_uses: int = 1, expires_days: int = 365, description: str = "") -> bool:
        """创建邀请码"""
        try:
            with self.get_session() as session:
                expires_at = datetime.now() + timedelta(days=expires_days)
                
                invite_code = InviteCode(
                    code=code,
                    max_uses=max_uses,
                    expires_at=expires_at,
                    description=description
                )
                session.add(invite_code)
                session.commit()
                return True
                
        except Exception as e:
            print(f"创建邀请码失败: {e}")
            return False
    
    def get_invite_codes(self) -> List[InviteCode]:
        """获取所有邀请码"""
        try:
            with self.get_session() as session:
                return list(session.exec(
                    select(InviteCode).order_by(desc('created_at'))
                ).all())
        except Exception as e:
            print(f"获取邀请码列表失败: {e}")
            return []
    
    # ==================== 对话管理 ====================
    
    def save_conversation(self, user_id: int, conversation_name: str, workflow_id: str) -> Optional[int]:
        """保存对话"""
        try:
            with self.get_session() as session:
                conversation = Conversation(
                    user_id=user_id,
                    conversation_name=conversation_name,
                    workflow_id=workflow_id
                )
                session.add(conversation)
                session.commit()
                session.refresh(conversation)
                return conversation.id
        except Exception as e:
            print(f"保存对话失败: {e}")
            return None
    
    def load_user_conversations(self, user_id: int) -> List[Conversation]:
        """加载用户的对话列表（不限制时间，按更新时间排序）"""
        try:
            with self.get_session() as session:
                # 移除时间限制，加载所有对话
                # 如果需要限制，可以使用 retention_days，但这里改为加载所有对话
                return list(session.exec(
                    select(Conversation)
                    .where(Conversation.user_id == user_id)
                    .order_by(desc('updated_at'))
                ).all())
        except Exception as e:
            print(f"加载对话列表失败: {e}")
            return []
    
    def save_message(self, conversation_id: int, role: str, content: str) -> bool:
        """保存消息"""
        try:
            with self.get_session() as session:
                message = Message(
                    conversation_id=conversation_id,
                    role=role,
                    content=content
                )
                session.add(message)
                
                # 更新对话的更新时间
                conversation = session.get(Conversation, conversation_id)
                if conversation:
                    conversation.updated_at = datetime.now()
                    session.add(conversation)
                
                session.commit()
                return True
                
        except Exception as e:
            print(f"保存消息失败: {e}")
            return False
    
    def load_conversation_messages(self, conversation_id: int) -> List[Message]:
        """加载对话的所有消息"""
        try:
            with self.get_session() as session:
                return list(session.exec(
                    select(Message)
                    .where(Message.conversation_id == conversation_id)
                    .order_by(asc('created_at'))
                ).all())
        except Exception as e:
            print(f"加载对话消息失败: {e}")
            return []
    
    def delete_conversation(self, conversation_id: int, user_id: int) -> bool:
        """删除对话（包括所有消息）"""
        try:
            with self.get_session() as session:
                # 先获取并删除所有消息
                messages = session.exec(
                    select(Message).where(Message.conversation_id == conversation_id)
                ).all()
                
                for msg in messages:
                    session.delete(msg)
                
                # 再删除对话
                conversation = session.get(Conversation, conversation_id)
                if conversation and conversation.user_id == user_id:
                    session.delete(conversation)
                    session.commit()
                    return True
                return False
                
        except Exception as e:
            print(f"删除对话失败: {e}")
            return False
    
    # ==================== 文件管理 ====================
    
    def save_uploaded_file(self, user_id: int, filename: str, filepath: str) -> Optional[int]:
        """保存上传文件记录"""
        try:
            with self.get_session() as session:
                # 兜底：避免重复插入相同待审批记录（同用户、同文件名、同路径且未审核）
                existing = session.exec(
                    select(UploadedFile)
                    .where(UploadedFile.user_id == user_id)
                    .where(UploadedFile.filename == filename)
                    .where(UploadedFile.filepath == filepath)
                    .where(UploadedFile.status == 'pending')
                ).first()
                if existing:
                    return existing.id
                uploaded_file = UploadedFile(
                    user_id=user_id,
                    filename=filename,
                    filepath=filepath
                )
                session.add(uploaded_file)
                session.commit()
                session.refresh(uploaded_file)
                return uploaded_file.id
        except Exception as e:
            print(f"保存文件记录失败: {e}")
            return None
    
    def get_user_uploaded_files(self, user_id: int) -> List[UploadedFile]:
        """获取用户上传的文件列表"""
        try:
            with self.get_session() as session:
                return list(session.exec(
                    select(UploadedFile)
                    .where(UploadedFile.user_id == user_id)
                    .order_by(desc('upload_at'))
                ).all())
        except Exception as e:
            print(f"获取用户文件列表失败: {e}")
            return []
    
    def get_pending_files(self) -> List[UploadedFile]:
        """获取所有待审批的文件"""
        try:
            with self.get_session() as session:
                return list(session.exec(
                    select(UploadedFile)
                    .where(UploadedFile.status == 'pending')
                    .order_by(asc('upload_at'))
                ).all())
        except Exception as e:
            print(f"获取待审批文件失败: {e}")
            return []
    
    def update_file_status(self, file_id: int, status: str) -> bool:
        """更新文件审批状态"""
        try:
            with self.get_session() as session:
                uploaded_file = session.get(UploadedFile, file_id)
                if uploaded_file:
                    uploaded_file.status = status
                    uploaded_file.reviewed_at = datetime.now()
                    session.add(uploaded_file)
                    session.commit()
                    return True
                return False
        except Exception as e:
            print(f"更新文件状态失败: {e}")
            return False
    
    # ==================== 工作流管理 ====================
    
    def create_workflow(self, workflow_id: str, name: str, description: str, api_base: str, 
                       api_key: str, status: str = "active", is_global: bool = True) -> Optional[int]:
        """创建工作流"""
        try:
            with self.get_session() as session:
                # 检查 workflow_id 是否已存在
                existing = session.exec(
                    select(Workflow).where(Workflow.workflow_id == workflow_id)
                ).first()
                if existing:
                    return None
                
                workflow = Workflow(
                    workflow_id=workflow_id,
                    name=name,
                    description=description,
                    api_base=api_base,
                    api_key=api_key,
                    status=status,
                    is_global=is_global
                )
                session.add(workflow)
                session.commit()
                session.refresh(workflow)
                return workflow.id
        except Exception as e:
            print(f"创建工作流失败: {e}")
            return None
    
    def update_workflow(self, workflow_db_id: int, workflow_id: Optional[str] = None, name: Optional[str] = None, 
                       description: Optional[str] = None, api_base: Optional[str] = None, api_key: Optional[str] = None,
                       status: Optional[str] = None, is_global: Optional[bool] = None) -> bool:
        """更新工作流"""
        try:
            with self.get_session() as session:
                workflow = session.get(Workflow, workflow_db_id)
                if not workflow:
                    return False
                
                # 如果更新 workflow_id，检查是否冲突
                if workflow_id and workflow_id != workflow.workflow_id:
                    existing = session.exec(
                        select(Workflow).where(Workflow.workflow_id == workflow_id)
                    ).first()
                    if existing:
                        return False
                    workflow.workflow_id = workflow_id
                
                if name is not None:
                    workflow.name = name
                if description is not None:
                    workflow.description = description
                if api_base is not None:
                    workflow.api_base = api_base
                if api_key is not None:
                    workflow.api_key = api_key
                if status is not None:
                    workflow.status = status
                if is_global is not None:
                    workflow.is_global = is_global
                
                workflow.updated_at = datetime.now()
                session.add(workflow)
                session.commit()
                return True
        except Exception as e:
            print(f"更新工作流失败: {e}")
            return False
    
    def delete_workflow(self, workflow_db_id: int) -> bool:
        """删除工作流（同时删除相关权限）"""
        try:
            with self.get_session() as session:
                workflow = session.get(Workflow, workflow_db_id)
                if not workflow:
                    return False
                
                # 检查是否有对话在使用此工作流
                conversations = session.exec(
                    select(Conversation).where(Conversation.workflow_id == workflow.workflow_id)
                ).all()
                if conversations:
                    return False  # 有对话在使用，不允许删除
                
                # 删除相关权限
                permissions = session.exec(
                    select(WorkflowUserPermission).where(WorkflowUserPermission.workflow_id == workflow_db_id)
                ).all()
                for perm in permissions:
                    session.delete(perm)
                
                # 删除工作流
                session.delete(workflow)
                session.commit()
                return True
        except Exception as e:
            print(f"删除工作流失败: {e}")
            return False
    
    def get_all_workflows(self) -> List[Workflow]:
        """获取所有工作流（管理员用）"""
        try:
            with self.get_session() as session:
                return list(session.exec(
                    select(Workflow).order_by(desc('created_at'))
                ).all())
        except Exception as e:
            print(f"获取工作流列表失败: {e}")
            return []
    
    def get_workflow_by_db_id(self, workflow_db_id: int) -> Optional[Workflow]:
        """根据数据库ID获取工作流"""
        try:
            with self.get_session() as session:
                return session.get(Workflow, workflow_db_id)
        except Exception as e:
            print(f"获取工作流失败: {e}")
            return None
    
    def get_workflow_by_workflow_id(self, workflow_id: str) -> Optional[Workflow]:
        """根据 workflow_id 获取工作流"""
        try:
            with self.get_session() as session:
                return session.exec(
                    select(Workflow).where(Workflow.workflow_id == workflow_id)
                ).first()
        except Exception as e:
            print(f"获取工作流失败: {e}")
            return None
    
    def get_user_accessible_workflows(self, user_id: int) -> List[Workflow]:
        """获取用户可见的工作流（全局可见的 + 在白名单中的）"""
        try:
            with self.get_session() as session:
                # 获取全局可见的启用工作流
                global_workflows = session.exec(
                    select(Workflow)
                    .where(Workflow.is_global == True)
                    .where(Workflow.status == "active")
                ).all()
                
                # 获取用户在白名单中的工作流
                user_permissions = session.exec(
                    select(WorkflowUserPermission)
                    .where(WorkflowUserPermission.user_id == user_id)
                ).all()
                
                workflow_ids = {perm.workflow_id for perm in user_permissions}
                private_workflows = []
                if workflow_ids:
                    # SQLModel 的 in_ 操作需要这样写
                    conditions = [Workflow.id == wid for wid in workflow_ids]
                    if conditions:
                        private_workflows = session.exec(
                            select(Workflow)
                            .where(or_(*conditions))
                            .where(Workflow.status == "active")
                        ).all()
                
                # 合并并去重
                all_workflows = {w.id: w for w in global_workflows}
                for w in private_workflows:
                    all_workflows[w.id] = w
                
                return list(all_workflows.values())
        except Exception as e:
            print(f"获取用户可见工作流失败: {e}")
            return []
    
    def set_workflow_users(self, workflow_db_id: int, user_ids: List[int]) -> bool:
        """设置工作流的用户白名单"""
        try:
            with self.get_session() as session:
                workflow = session.get(Workflow, workflow_db_id)
                if not workflow:
                    return False
                
                # 删除现有权限
                existing_permissions = session.exec(
                    select(WorkflowUserPermission).where(WorkflowUserPermission.workflow_id == workflow_db_id)
                ).all()
                for perm in existing_permissions:
                    session.delete(perm)
                
                # 添加新权限
                for user_id in user_ids:
                    permission = WorkflowUserPermission(
                        workflow_id=workflow_db_id,
                        user_id=user_id
                    )
                    session.add(permission)
                
                session.commit()
                return True
        except Exception as e:
            print(f"设置工作流用户权限失败: {e}")
            return False
    
    def get_workflow_users(self, workflow_db_id: int) -> List[int]:
        """获取工作流的用户白名单"""
        try:
            with self.get_session() as session:
                permissions = session.exec(
                    select(WorkflowUserPermission).where(WorkflowUserPermission.workflow_id == workflow_db_id)
                ).all()
                return [perm.user_id for perm in permissions]
        except Exception as e:
            print(f"获取工作流用户列表失败: {e}")
            return []
    
    def import_workflows_from_config(self, is_global: bool = True) -> int:
        """从 config.json 导入工作流到数据库"""
        try:
            workflows_config = self.config.get('workflows', [])
            imported_count = 0
            
            for wf_config in workflows_config:
                workflow_id = wf_config.get('id')
                if not workflow_id:
                    continue
                
                # 检查是否已存在
                existing = self.get_workflow_by_workflow_id(workflow_id)
                if existing:
                    continue
                
                # 创建新工作流
                result = self.create_workflow(
                    workflow_id=workflow_id,
                    name=wf_config.get('name', ''),
                    description=wf_config.get('description', ''),
                    api_base=wf_config.get('api_base', ''),
                    api_key=wf_config.get('api_key', ''),
                    status='active',
                    is_global=is_global
                )
                
                if result:
                    imported_count += 1
            
            return imported_count
        except Exception as e:
            print(f"导入工作流失败: {e}")
            return 0
    
    def get_all_users(self) -> List[User]:
        """获取所有用户（用于权限管理）"""
        try:
            with self.get_session() as session:
                return list(session.exec(
                    select(User).order_by(desc('created_at'))
                ).all())
        except Exception as e:
            print(f"获取用户列表失败: {e}")
            return []
    
    # ==================== 用户管理 ====================
    
    def update_user_last_login(self, user_id: int) -> bool:
        """更新用户最后登录时间"""
        try:
            with self.get_session() as session:
                user = session.get(User, user_id)
                if user:
                    user.last_login = datetime.now()
                    session.add(user)
                    session.commit()
                    return True
                return False
        except Exception as e:
            print(f"更新用户登录时间失败: {e}")
            return False
    
    def get_user_statistics(self, user_id: int) -> Dict:
        """获取用户统计数据"""
        try:
            with self.get_session() as session:
                # 对话数量
                conversations = session.exec(
                    select(Conversation).where(Conversation.user_id == user_id)
                ).all()
                conversation_count = len(conversations)
                
                # 文件数量
                files = session.exec(
                    select(UploadedFile).where(UploadedFile.user_id == user_id)
                ).all()
                file_count = len(files)
                
                # 最后活动时间（最近对话更新时间或文件上传时间）
                last_activity = None
                if conversations:
                    last_conv_time = max([c.updated_at for c in conversations])
                    if last_activity is None or last_conv_time > last_activity:
                        last_activity = last_conv_time
                
                if files:
                    last_file_time = max([f.upload_at for f in files])
                    if last_activity is None or last_file_time > last_activity:
                        last_activity = last_file_time
                
                return {
                    "conversation_count": conversation_count,
                    "file_count": file_count,
                    "last_activity": last_activity
                }
        except Exception as e:
            print(f"获取用户统计失败: {e}")
            return {
                "conversation_count": 0,
                "file_count": 0,
                "last_activity": None
            }
    
    def get_all_users_with_stats(self) -> List[Dict]:
        """获取所有用户及其统计数据"""
        try:
            users = self.get_all_users()
            result = []
            for user in users:
                if user.id is not None:
                    stats = self.get_user_statistics(user.id)
                else:
                    stats = {"conversation_count": 0, "file_count": 0, "last_activity": None}
                result.append({
                    "user": user,
                    "stats": stats
                })
            return result
        except Exception as e:
            print(f"获取用户统计列表失败: {e}")
            return []
    
    def reset_user_password(self, user_id: int, new_password: str) -> bool:
        """重置用户密码"""
        try:
            with self.get_session() as session:
                user = session.get(User, user_id)
                if user:
                    user.password_hash = new_password
                    session.add(user)
                    session.commit()
                    return True
                return False
        except Exception as e:
            print(f"重置密码失败: {e}")
            return False
    
    def delete_user(self, user_id: int) -> tuple[bool, str]:
        """
        删除用户（硬删除）
        返回: (是否成功, 错误信息)
        """
        try:
            with self.get_session() as session:
                user = session.get(User, user_id)
                if not user:
                    return False, "用户不存在"
                
                # 获取关联数据统计
                conversations = session.exec(
                    select(Conversation).where(Conversation.user_id == user_id)
                ).all()
                files = session.exec(
                    select(UploadedFile).where(UploadedFile.user_id == user_id)
                ).all()
                
                # 删除所有对话的消息
                for conv in conversations:
                    messages = session.exec(
                        select(Message).where(Message.conversation_id == conv.id)
                    ).all()
                    for msg in messages:
                        session.delete(msg)
                    session.commit()  # 先提交消息删除
                
                # 删除所有对话
                for conv in conversations:
                    session.delete(conv)
                
                # 删除所有文件记录
                for file_record in files:
                    session.delete(file_record)
                
                # 删除工作流权限（如果表存在）
                try:
                    permissions = session.exec(
                        select(WorkflowUserPermission).where(WorkflowUserPermission.user_id == user_id)
                    ).all()
                    for perm in permissions:
                        session.delete(perm)
                except Exception as perm_error:
                    # 如果表不存在，跳过权限删除（表可能还未创建）
                    print(f"警告: 无法删除工作流权限（表可能不存在）: {perm_error}")
                
                # 删除用户
                session.delete(user)
                session.commit()
                
                return True, f"用户已删除（包括 {len(conversations)} 个对话、{len(files)} 个文件）"
        except Exception as e:
            print(f"删除用户失败: {e}")
            return False, f"删除失败: {str(e)}"
    
    def get_total_conversation_count(self) -> int:
        """获取总对话数"""
        try:
            with self.get_session() as session:
                conversations = session.exec(select(Conversation)).all()
                return len(conversations)
        except Exception as e:
            print(f"获取对话总数失败: {e}")
            return 0
    
    def get_or_create_fire_character(self, user_id: int) -> Optional[FireCharacter]:
        """获取或创建用户的小火人角色"""
        try:
            with self.get_session() as session:
                # 查找现有的小火人角色
                fire_char = session.exec(
                    select(FireCharacter).where(FireCharacter.user_id == user_id)
                ).first()
                
                # 如果不存在，则创建一个新的
                if not fire_char:
                    fire_char = FireCharacter(user_id=user_id)
                    session.add(fire_char)
                    session.commit()
                    session.refresh(fire_char)
                
                return fire_char
        except Exception as e:
            print(f"获取或创建小火人角色失败: {e}")
            return None
    
    def update_fire_character_exp(self, user_id: int, exp_gained: int = 1) -> Optional[FireCharacter]:
        """更新小火人经验值"""
        try:
            with self.get_session() as session:
                # 获取用户的小火人角色
                fire_char = session.exec(
                    select(FireCharacter).where(FireCharacter.user_id == user_id)
                ).first()
                
                # 如果不存在，则创建一个新的
                if not fire_char:
                    fire_char = FireCharacter(user_id=user_id)
                    session.add(fire_char)
                
                # 更新经验值和消息数
                fire_char.experience += exp_gained
                fire_char.total_messages += 1
                
                # 检查是否升级（每10点经验升一级）
                new_level = fire_char.experience // 10 + 1
                if new_level > fire_char.level:
                    fire_char.level = new_level
                
                fire_char.updated_at = datetime.now()
                session.add(fire_char)
                session.commit()
                session.refresh(fire_char)
                
                return fire_char
        except Exception as e:
            print(f"更新小火人经验值失败: {e}")
            return None

# 导入必要的模块
from datetime import timedelta
