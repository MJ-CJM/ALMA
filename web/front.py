import os
import json
import streamlit as st
from uuid import uuid4
from datetime import datetime
from auth import AuthManager, require_auth
from models import DatabaseManager
from backend import get_workflow_list, run_dify_workflow

# -------------------------
# 初始化
# -------------------------
auth_manager = AuthManager()
db_manager = DatabaseManager()

# -------------------------
# 页面配置
# -------------------------
st.set_page_config(
    page_title="ALMA AI 助手",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------------
# 登录检查
# -------------------------
if not require_auth(auth_manager):
    st.stop()  # 停止执行，显示登录页面

# -------------------------
# 常量定义
# -------------------------
MAX_CONVERSATIONS = 12
DEFAULT_AVATAR = "🙋‍♂️"
DEFAULT_NAME = "用户"
AVATAR_OPTIONS = ["👤", "😊", "🎮", "👻", "🐱", "🐶", "🦊", "🐼", "🐨", "🦁", "🐯", "🦋", "🐵"]

# -------------------------
# 初始化会话状态
# -------------------------
if "conversations" not in st.session_state:
    st.session_state.conversations = {}
if "current_conversation" not in st.session_state:
    st.session_state.current_conversation = None
if "conversation_counter" not in st.session_state:
    st.session_state.conversation_counter = 0
if "rename_mode" not in st.session_state:
    st.session_state.rename_mode = None
if "user_avatar" not in st.session_state:
    st.session_state.user_avatar = DEFAULT_AVATAR
if "user_name" not in st.session_state:
    st.session_state.user_name = DEFAULT_NAME
if "conversations_loaded" not in st.session_state:
    st.session_state.conversations_loaded = False

# -------------------------
# 加载用户对话
# -------------------------
def load_user_conversations():
    """从数据库加载用户对话"""
    if st.session_state.conversations_loaded:
        return
    
    try:
        user_id = st.session_state.user_id
        conversations = db_manager.load_user_conversations(user_id)
        
        if conversations:
            st.session_state.conversations = {}
            for conv in conversations:
                # 加载对话消息
                messages = db_manager.load_conversation_messages(conv['id'])
                message_list = []
                for msg in messages:
                    message_list.append({
                        "role": msg['role'],
                        "content": msg['content']
                    })
                
                st.session_state.conversations[conv['conversation_name']] = {
                    "id": conv['id'],
                    "workflow_id": conv['workflow_id'],
                    "history": message_list
                }
            
            # 设置当前对话
            if not st.session_state.current_conversation:
                st.session_state.current_conversation = list(st.session_state.conversations.keys())[0]
        else:
            # 如果没有对话，创建一个默认对话
            workflows = get_workflow_list()
            if workflows:
                default_workflow = workflows[0]['id']
                create_new_conversation("新对话 1", default_workflow)
        
        st.session_state.conversations_loaded = True
        
    except Exception as e:
        st.error(f"加载对话失败: {e}")

def create_new_conversation(name: str, workflow_id: str):
    """创建新对话"""
    try:
        user_id = st.session_state.user_id
        conversation_id = db_manager.save_conversation(user_id, name, workflow_id)
        
        if conversation_id:
            # 添加欢迎消息
            db_manager.save_message(conversation_id, "assistant", "让我们开始聊天吧！👇")
            
            st.session_state.conversations[name] = {
                "id": conversation_id,
                "workflow_id": workflow_id,
                "history": [{"role": "assistant", "content": "让我们开始聊天吧！👇"}]
            }
            
            return True
        return False
        
    except Exception as e:
        st.error(f"创建对话失败: {e}")
        return False

def save_message_to_db(conversation_id: int, role: str, content: str):
    """保存消息到数据库"""
    try:
        db_manager.save_message(conversation_id, role, content)
    except Exception as e:
        st.error(f"保存消息失败: {e}")

# 加载用户对话
load_user_conversations()

# -------------------------
# 侧边栏
# -------------------------
with st.sidebar:
    # 显示用户信息和登出按钮
    auth_manager.show_user_info_and_logout()
    
    st.title("探索功能")
    st.divider()

    st.subheader("个人设置")
    with st.expander("自定义个人资料", expanded=False):
        new_name = st.text_input("你的名称", value=st.session_state.user_name)
        if new_name != st.session_state.user_name:
            st.session_state.user_name = new_name

        st.write("选择头像")
        cols = st.columns(6)
        for i, avatar in enumerate(AVATAR_OPTIONS):
            with cols[i % 6]:
                if st.button(
                    avatar,
                    key=f"avatar_{i}",
                    use_container_width=True,
                    type="secondary" if avatar != st.session_state.user_avatar else "primary"
                ):
                    st.session_state.user_avatar = avatar

    st.divider()

    # 文件上传功能
    st.subheader("📁 知识库文件上传")
    uploaded_file = st.file_uploader(
        "选择文件",
        type=['pdf', 'txt', 'doc', 'docx', 'md'],
        help="支持 PDF、TXT、DOC、DOCX、MD 格式"
    )
    
    if uploaded_file is not None:
        try:
            # 创建用户上传目录
            user_upload_dir = f"uploads/{st.session_state.username}"
            os.makedirs(user_upload_dir, exist_ok=True)
            
            # 保存文件
            file_path = os.path.join(user_upload_dir, uploaded_file.name)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # 保存到数据库
            file_id = db_manager.save_uploaded_file(
                st.session_state.user_id,
                uploaded_file.name,
                file_path
            )
            
            if file_id:
                st.success(f"文件 {uploaded_file.name} 上传成功，等待管理员审批")
            else:
                st.error("文件上传失败")
                
        except Exception as e:
            st.error(f"文件上传失败: {e}")
    
    # 显示用户上传的文件
    try:
        user_files = db_manager.get_user_uploaded_files(st.session_state.user_id)
        if user_files:
            st.write("**我的文件**")
            for file_info in user_files:
                status_emoji = {
                    'pending': '⏳',
                    'approved': '✅',
                    'rejected': '❌'
                }
                status_text = {
                    'pending': '待审批',
                    'approved': '已通过',
                    'rejected': '已拒绝'
                }
                
                st.write(f"{status_emoji.get(file_info['status'], '❓')} {file_info['filename']} - {status_text.get(file_info['status'], '未知')}")
    except Exception as e:
        st.error(f"加载文件列表失败: {e}")

    st.divider()

    # 对话管理
    current_conv_count = len(st.session_state.conversations)
    st.caption(f"当前对话数量: {current_conv_count}/{MAX_CONVERSATIONS}")

    if current_conv_count >= MAX_CONVERSATIONS:
        st.button("➕ 新建对话", disabled=True, use_container_width=True)
        st.markdown("""
            <div class="warning">
                ⚠️ 已达到最大对话数量限制（12个）<br>
                请删除一些旧对话后再创建新对话
            </div>
        """, unsafe_allow_html=True)
    else:
        if st.button("➕ 新建对话", use_container_width=True):
            # 显示工作流选择对话框
            st.session_state.show_workflow_selector = True
            st.rerun()

    # 工作流选择对话框
    if st.session_state.get("show_workflow_selector", False):
        st.markdown("**选择工作流**")
        workflows = get_workflow_list()
        
        if workflows:
            workflow_options = {f"{w['name']} - {w['description']}": w['id'] for w in workflows}
            selected_workflow = st.selectbox("选择工作流", list(workflow_options.keys()))
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("确认", key="confirm_workflow"):
                    workflow_id = workflow_options[selected_workflow]
                    st.session_state.conversation_counter += 1
                    new_name = f"新对话 {st.session_state.conversation_counter}"
                    
                    if create_new_conversation(new_name, workflow_id):
                        st.session_state.current_conversation = new_name
                        st.session_state.show_workflow_selector = False
                        st.rerun()
            with col2:
                if st.button("取消", key="cancel_workflow"):
                    st.session_state.show_workflow_selector = False
                    st.rerun()
        else:
            st.error("没有可用的工作流")

    st.divider()

    st.subheader("对话列表")
    for conv_name in list(st.session_state.conversations.keys()):
        col1, col2, col3 = st.columns([0.7, 0.15, 0.15])

        with col1:
            if st.session_state.rename_mode == conv_name:
                new_name = st.text_input(
                    "新名称",
                    value=conv_name,
                    key=f"rename_{conv_name}",
                    label_visibility="collapsed"
                )
                if st.button("确认", key=f"confirm_{conv_name}"):
                    if new_name and new_name != conv_name:
                        if new_name not in st.session_state.conversations:
                            st.session_state.conversations[new_name] = st.session_state.conversations[conv_name]
                            del st.session_state.conversations[conv_name]
                            if conv_name == st.session_state.current_conversation:
                                st.session_state.current_conversation = new_name
                            st.session_state.rename_mode = None
                            st.rerun()
                        else:
                            st.warning("对话名称已存在")
            else:
                # 显示工作流信息
                conv_info = st.session_state.conversations[conv_name]
                workflow_id = conv_info.get('workflow_id', '')
                workflows = get_workflow_list()
                workflow_name = next((w['name'] for w in workflows if w['id'] == workflow_id), workflow_id)
                
                btn_label = f"{'🔵' if conv_name == st.session_state.current_conversation else '⚪'} {conv_name}"
                btn_label += f"\n📋 {workflow_name}"
                
                if st.button(btn_label, key=f"conv_{conv_name}"):
                    st.session_state.current_conversation = conv_name
                    st.rerun()

        with col2:
            if st.button("✏️", key=f"edit_{conv_name}"):
                st.session_state.rename_mode = conv_name
                st.rerun()

        with col3:
            if len(st.session_state.conversations) > 1:
                if st.button("🗑️", key=f"del_{conv_name}"):
                    # 从数据库删除对话
                    conv_info = st.session_state.conversations[conv_name]
                    conversation_id = conv_info['id']
                    db_manager.delete_conversation(conversation_id, st.session_state.user_id)
                    
                    # 从会话状态删除
                    del st.session_state.conversations[conv_name]
                    if conv_name == st.session_state.current_conversation:
                        st.session_state.current_conversation = list(st.session_state.conversations.keys())[0]
                    st.rerun()

# -------------------------
# 主界面
# -------------------------
if st.session_state.current_conversation:
    st.caption(f"当前对话：{st.session_state.current_conversation}")
    
    # 显示工作流信息
    current_conv = st.session_state.conversations[st.session_state.current_conversation]
    workflow_id = current_conv.get('workflow_id', '')
    workflows = get_workflow_list()
    workflow_name = next((w['name'] for w in workflows if w['id'] == workflow_id), workflow_id)
    st.caption(f"工作流：{workflow_name}")

    # 显示聊天记录
    for message in current_conv["history"]:
        with st.chat_message(
            message["role"],
            avatar=st.session_state.user_avatar if message["role"] == "user" else "🤖"
        ):
            if message["role"] == "user":
                st.markdown(f"**{st.session_state.user_name}**: {message['content']}")
            else:
                st.markdown(f"**AI助手**: {message['content']}")

    # 用户输入
    if prompt := st.chat_input(f"你好，{st.session_state.user_name}，有什么可以帮你的吗？"):
        # 添加用户消息到会话状态
        current_conv["history"].append({"role": "user", "content": prompt})
        
        # 保存用户消息到数据库
        save_message_to_db(current_conv["id"], "user", prompt)

        # 显示用户消息
        with st.chat_message("user", avatar=st.session_state.user_avatar):
            st.markdown(f"**{st.session_state.user_name}**: {prompt}")

        # 获取AI回复
        with st.chat_message("assistant", avatar="🤖"):
            message_placeholder = st.empty()
            with st.spinner("正在生成回复..."):
                try:
                    # 调用 Dify 工作流
                    answer = run_dify_workflow(
                        prompt, 
                        st.session_state.username, 
                        workflow_id
                    )
                    
                except Exception as e:
                    answer = f"AI 回复生成失败: {str(e)}"

                message_placeholder.markdown(f"**AI助手**: {answer}")

        # 添加AI回复到会话状态和数据库
        current_conv["history"].append({"role": "assistant", "content": answer})
        save_message_to_db(current_conv["id"], "assistant", answer)
else:
    st.info("请选择一个对话或创建新对话开始聊天")