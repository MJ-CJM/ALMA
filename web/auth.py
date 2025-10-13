import json
import os
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
import streamlit as st

class InviteCodeAuth:
    """邀请码认证管理类"""
    
    def __init__(self, data_file: str = "web/invite_codes.json"):
        self.data_file = data_file
        self.ensure_data_file()
    
    def ensure_data_file(self):
        """确保数据文件存在，如果不存在则创建默认数据"""
        if not os.path.exists(self.data_file):
            default_data = {
                "codes": {
                    "ALMA2024001": {
                        "status": "active",
                        "max_uses": 1,
                        "used_count": 0,
                        "created_at": datetime.now().isoformat(),
                        "expires_at": (datetime.now() + timedelta(days=365)).isoformat(),
                        "description": "默认测试邀请码"
                    }
                },
                "users": {}
            }
            self.save_data(default_data)
    
    def load_data(self) -> Dict:
        """加载邀请码数据"""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.ensure_data_file()
            return self.load_data()
    
    def save_data(self, data: Dict):
        """保存邀请码数据"""
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def validate_invite_code(self, code: str) -> Tuple[bool, str]:
        """
        验证邀请码
        返回: (是否有效, 错误信息)
        """
        if not code or not code.strip():
            return False, "请输入邀请码"
        
        code = code.strip().upper()
        data = self.load_data()
        
        if code not in data["codes"]:
            return False, "邀请码不存在"
        
        code_info = data["codes"][code]
        
        # 检查状态
        if code_info["status"] != "active":
            return False, "邀请码已被禁用"
        
        # 检查使用次数
        if code_info["used_count"] >= code_info["max_uses"]:
            return False, "邀请码使用次数已达上限"
        
        # 检查过期时间
        try:
            expires_at = datetime.fromisoformat(code_info["expires_at"])
            if datetime.now() > expires_at:
                return False, "邀请码已过期"
        except (ValueError, KeyError):
            pass  # 如果没有过期时间或格式错误，忽略检查
        
        return True, "验证成功"
    
    def use_invite_code(self, code: str, session_id: str) -> bool:
        """
        使用邀请码
        返回: 是否成功
        """
        is_valid, error_msg = self.validate_invite_code(code)
        if not is_valid:
            return False
        
        code = code.strip().upper()
        data = self.load_data()
        
        # 更新使用次数
        data["codes"][code]["used_count"] += 1
        
        # 记录用户信息
        data["users"][session_id] = {
            "invite_code": code,
            "login_time": datetime.now().isoformat(),
            "last_activity": datetime.now().isoformat()
        }
        
        self.save_data(data)
        return True
    
    def is_user_logged_in(self, session_id: str) -> bool:
        """检查用户是否已登录"""
        data = self.load_data()
        return session_id in data["users"]
    
    def update_last_activity(self, session_id: str):
        """更新用户最后活动时间"""
        data = self.load_data()
        if session_id in data["users"]:
            data["users"][session_id]["last_activity"] = datetime.now().isoformat()
            self.save_data(data)
    
    def logout_user(self, session_id: str):
        """用户登出"""
        data = self.load_data()
        if session_id in data["users"]:
            del data["users"][session_id]
            self.save_data(data)
    
    def get_user_info(self, session_id: str) -> Optional[Dict]:
        """获取用户信息"""
        data = self.load_data()
        return data["users"].get(session_id)
    
    def generate_invite_code(self, prefix: str = "ALMA", max_uses: int = 1, 
                           expires_days: int = 365, description: str = "") -> str:
        """
        生成新的邀请码
        """
        data = self.load_data()
        
        # 生成唯一的邀请码
        year = datetime.now().year
        counter = 1
        while True:
            code = f"{prefix}{year}{counter:03d}"
            if code not in data["codes"]:
                break
            counter += 1
        
        # 添加邀请码信息
        data["codes"][code] = {
            "status": "active",
            "max_uses": max_uses,
            "used_count": 0,
            "created_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(days=expires_days)).isoformat(),
            "description": description
        }
        
        self.save_data(data)
        return code


def get_session_id() -> str:
    """获取或生成会话ID"""
    if "session_id" not in st.session_state:
        import uuid
        st.session_state.session_id = str(uuid.uuid4())
    return st.session_state.session_id


def show_login_page(auth: InviteCodeAuth) -> bool:
    """
    显示登录页面
    返回: 是否登录成功
    """
    st.markdown("""
        <div style="text-align: center; padding: 50px 0;">
            <h1>🤖 ALMA AI 助手</h1>
            <h3>请输入邀请码以继续</h3>
        </div>
    """, unsafe_allow_html=True)
    
    # 居中显示登录表单
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.form("login_form"):
            invite_code = st.text_input(
                "邀请码",
                placeholder="请输入您的邀请码",
                help="邀请码格式：ALMA2024XXX"
            )
            
            submit_button = st.form_submit_button(
                "验证并登录",
                use_container_width=True,
                type="primary"
            )
            
            if submit_button:
                if invite_code:
                    is_valid, error_msg = auth.validate_invite_code(invite_code)
                    if is_valid:
                        session_id = get_session_id()
                        if auth.use_invite_code(invite_code, session_id):
                            st.success("登录成功！正在跳转...")
                            st.rerun()
                        else:
                            st.error("登录失败，请重试")
                    else:
                        st.error(f"验证失败：{error_msg}")
                else:
                    st.warning("请输入邀请码")
    
    # 显示说明信息
    st.markdown("""
        <div style="text-align: center; margin-top: 50px; color: #666;">
            <p>📧 如需获取邀请码，请联系管理员</p>
            <p>💡 邀请码示例：ALMA2024000</p>
        </div>
    """, unsafe_allow_html=True)
    
    return False


def show_user_info_and_logout(auth: InviteCodeAuth):
    """在侧边栏显示用户信息和登出按钮"""
    session_id = get_session_id()
    user_info = auth.get_user_info(session_id)
    
    if user_info:
        st.markdown("### 👤 用户信息")
        st.write(f"**邀请码**: {user_info['invite_code']}")
        
        try:
            login_time = datetime.fromisoformat(user_info['login_time'])
            st.write(f"**登录时间**: {login_time.strftime('%Y-%m-%d %H:%M')}")
        except:
            pass
        
        if st.button("🚪 退出登录", use_container_width=True, type="secondary"):
            auth.logout_user(session_id)
            # 清理会话状态
            for key in list(st.session_state.keys()):
                if key != "session_id":
                    del st.session_state[key]
            st.rerun()
        
        st.divider()


def require_login(auth: InviteCodeAuth) -> bool:
    """
    检查登录状态，未登录则显示登录页面
    返回: 是否已登录
    """
    session_id = get_session_id()
    
    if auth.is_user_logged_in(session_id):
        # 更新最后活动时间
        auth.update_last_activity(session_id)
        return True
    else:
        show_login_page(auth)
        return False