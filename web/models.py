"""
SQLModel 数据模型定义
最简化的 ORM 实现
"""

from sqlmodel import SQLModel, Field, create_engine, Session, select
from typing import Optional, List
from datetime import datetime
import json

# ==================== 数据模型 ====================

class User(SQLModel, table=True, extend_existing=True):
    """用户表"""
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True, max_length=50)
    password_hash: str = Field(max_length=255)
    invite_code: str = Field(max_length=20)
    created_at: datetime = Field(default_factory=datetime.now)

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
                return session.exec(
                    select(InviteCode).order_by(InviteCode.created_at.desc())
                ).all()
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
        """加载用户的对话列表（最近30天）"""
        try:
            with self.get_session() as session:
                cutoff_date = datetime.now() - timedelta(days=self.config['conversation']['retention_days'])
                
                return session.exec(
                    select(Conversation)
                    .where(Conversation.user_id == user_id)
                    .where(Conversation.created_at >= cutoff_date)
                    .order_by(Conversation.updated_at.desc())
                ).all()
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
                return session.exec(
                    select(Message)
                    .where(Message.conversation_id == conversation_id)
                    .order_by(Message.created_at.asc())
                ).all()
        except Exception as e:
            print(f"加载对话消息失败: {e}")
            return []
    
    def delete_conversation(self, conversation_id: int, user_id: int) -> bool:
        """删除对话（包括所有消息）"""
        try:
            with self.get_session() as session:
                # 先删除所有消息
                session.exec(
                    select(Message).where(Message.conversation_id == conversation_id)
                ).delete()
                
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
                return session.exec(
                    select(UploadedFile)
                    .where(UploadedFile.user_id == user_id)
                    .order_by(UploadedFile.upload_at.desc())
                ).all()
        except Exception as e:
            print(f"获取用户文件列表失败: {e}")
            return []
    
    def get_pending_files(self) -> List[UploadedFile]:
        """获取所有待审批的文件"""
        try:
            with self.get_session() as session:
                return session.exec(
                    select(UploadedFile)
                    .where(UploadedFile.status == 'pending')
                    .order_by(UploadedFile.upload_at.asc())
                ).all()
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

# 导入必要的模块
from datetime import timedelta
