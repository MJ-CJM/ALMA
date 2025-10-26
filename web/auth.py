import json
import os
import streamlit as st
from datetime import datetime
from typing import Optional, Dict
from models import DatabaseManager

class AuthManager:
    """认证管理类 - 支持注册和登录"""
    
    def __init__(self, config_file: str = "config.json"):
        self.db = DatabaseManager(config_file)
    
    def get_session_id(self) -> str:
        """获取或生成会话ID"""
        if "session_id" not in st.session_state:
            import uuid
            st.session_state.session_id = str(uuid.uuid4())
        return st.session_state.session_id
    
    def is_logged_in(self) -> bool:
        """检查用户是否已登录"""
        return "user_id" in st.session_state and "username" in st.session_state
    
    def get_current_user(self) -> Optional[Dict]:
        """获取当前用户信息"""
        if not self.is_logged_in():
            return None
        
        return {
            "id": st.session_state.user_id,
            "username": st.session_state.username
        }
    
    def login(self, username: str, password: str) -> bool:
        """用户登录"""
        try:
            user = self.db.get_user_by_username(username)
            if not user:
                return False
            
            if self.db.verify_password(password, user.password_hash):
                # 设置会话状态
                st.session_state.user_id = user.id
                st.session_state.username = user.username
                st.session_state.login_time = datetime.now()
                return True
            
            return False
            
        except Exception as e:
            print(f"登录失败: {e}")
            return False
    
    def register(self, username: str, password: str, invite_code: str) -> tuple[bool, str]:
        """用户注册"""
        try:
            # 验证邀请码
            if not self.db.validate_invite_code(invite_code):
                return False, "邀请码无效或已过期"
            
            # 创建用户
            if self.db.create_user(username, password, invite_code):
                return True, "注册成功"
            else:
                return False, "用户名已存在或注册失败"
                
        except Exception as e:
            print(f"注册失败: {e}")
            return False, f"注册失败: {str(e)}"
    
    def logout(self):
        """用户登出"""
        # 清理会话状态
        keys_to_remove = [
            "user_id", "username", "login_time", "conversations", 
            "current_conversation", "conversation_counter", "rename_mode",
            "user_avatar", "user_name"
        ]
        
        for key in keys_to_remove:
            if key in st.session_state:
                del st.session_state[key]
    
    def show_login_page(self) -> bool:
        """显示登录页面"""
        st.markdown("""
            <div style="text-align: center; padding: 50px 0;">
                <h1>🤖 ALMA AI 助手</h1>
                <h3>请登录以继续</h3>
            </div>
        """, unsafe_allow_html=True)
        
        # 创建标签页
        tab1, tab2 = st.tabs(["登录", "注册"])
        
        with tab1:
            with st.form("login_form"):
                st.subheader("用户登录")
                
                username = st.text_input(
                    "用户名",
                    placeholder="请输入用户名",
                    help="请输入您的用户名"
                )
                
                password = st.text_input(
                    "密码",
                    type="password",
                    placeholder="请输入密码",
                    help="请输入您的密码"
                )
                
                submit_button = st.form_submit_button(
                    "登录",
                    use_container_width=True,
                    type="primary"
                )
                
                if submit_button:
                    if username and password:
                        if self.login(username, password):
                            st.success("登录成功！正在跳转...")
                            st.rerun()
                        else:
                            st.error("用户名或密码错误")
                    else:
                        st.warning("请输入用户名和密码")
        
        with tab2:
            with st.form("register_form"):
                st.subheader("用户注册")
                
                new_username = st.text_input(
                    "用户名",
                    key="reg_username",
                    placeholder="请输入用户名",
                    help="用户名将用于登录"
                )
                
                new_password = st.text_input(
                    "密码",
                    key="reg_password",
                    type="password",
                    placeholder="请输入密码",
                    help="请设置一个安全的密码"
                )
                
                confirm_password = st.text_input(
                    "确认密码",
                    key="reg_confirm_password",
                    type="password",
                    placeholder="请再次输入密码",
                    help="请确认您的密码"
                )
                
                invite_code = st.text_input(
                    "邀请码",
                    key="reg_invite_code",
                    placeholder="请输入邀请码",
                    help="需要有效的邀请码才能注册"
                )
                
                submit_register = st.form_submit_button(
                    "注册",
                    use_container_width=True,
                    type="primary"
                )
                
                if submit_register:
                    if not all([new_username, new_password, confirm_password, invite_code]):
                        st.warning("请填写所有字段")
                    elif new_password != confirm_password:
                        st.error("两次输入的密码不一致")
                    elif len(new_password) < 6:
                        st.error("密码长度至少6位")
                    else:
                        success, message = self.register(new_username, new_password, invite_code)
                        if success:
                            st.success(message + "，请使用新账号登录")
                        else:
                            st.error(message)
        
        # 显示说明信息
        st.markdown("""
            <div style="text-align: center; margin-top: 50px; color: #666;">
                <p>📧 如需获取邀请码，请联系管理员</p>
                <p>💡 邀请码示例：ALMA2024001</p>
            </div>
        """, unsafe_allow_html=True)
        
        return False
    
    def show_user_info_and_logout(self):
        """在侧边栏显示用户信息和登出按钮"""
        if not self.is_logged_in():
            return
        
        user = self.get_current_user()
        if not user:
            return
        
        st.markdown("### 👤 用户信息")
        st.write(f"**用户名**: {user['username']}")
        
        if "login_time" in st.session_state:
            login_time = st.session_state.login_time
            st.write(f"**登录时间**: {login_time.strftime('%Y-%m-%d %H:%M')}")
        
        if st.button("🚪 退出登录", use_container_width=True, type="secondary"):
            self.logout()
            st.rerun()
        
        st.divider()

def require_auth(auth_manager: AuthManager) -> bool:
    """
    检查登录状态，未登录则显示登录页面
    返回: 是否已登录
    """
    if auth_manager.is_logged_in():
        return True
    else:
        auth_manager.show_login_page()
        return False

def show_admin_login() -> bool:
    """显示管理员登录页面"""
    st.markdown("""
        <div style="text-align: center; padding: 50px 0;">
            <h1>🔧 ALMA 管理后台</h1>
            <h3>管理员登录</h3>
        </div>
    """, unsafe_allow_html=True)
    
    with st.form("admin_login_form"):
        admin_password = st.text_input(
            "管理员密码",
            type="password",
            placeholder="请输入管理员密码"
        )
        
        submit_button = st.form_submit_button(
            "登录管理后台",
            use_container_width=True,
            type="primary"
        )
        
        if submit_button:
            if admin_password:
                # 从配置文件读取管理员密码
                try:
                    with open("config.json", 'r', encoding='utf-8') as f:
                        config = json.load(f)
                    
                    if admin_password == config['admin']['password']:
                        st.session_state.is_admin = True
                        st.success("管理员登录成功！")
                        st.rerun()
                    else:
                        st.error("管理员密码错误")
                except Exception as e:
                    st.error(f"登录失败: {e}")
            else:
                st.warning("请输入管理员密码")
    
    return False

def require_admin_auth() -> bool:
    """检查管理员认证状态"""
    if "is_admin" not in st.session_state:
        show_admin_login()
        return False
    return True