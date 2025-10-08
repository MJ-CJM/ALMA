import os
import json
import requests
import streamlit as st
from uuid import uuid4

# -------------------------
# Dify 配置（自建请改 API_BASE；生产建议改用环境变量传 Key）
# -------------------------
DIFY_API_BASE = os.getenv("DIFY_API_BASE", "http://ai.wenhan.top:8080")
DIFY_API_KEY  = os.getenv("DIFY_API_KEY", "Bearer app-F4F2QM3rjs8DZgTtpIitoxlx")
DIFY_HEADERS  = {
    "Authorization": DIFY_API_KEY,
    "Content-Type": "application/json",
}

def run_dify_workflow_blocking(question: str, user_id: str) -> dict:
    """
    调用 Dify 工作流（blocking 模式），返回 JSON。
    你的 Start 节点输入只有 question:string，则按如下 inputs 发送。
    """
    url = f"{DIFY_API_BASE}/v1/workflows/run"
    payload = {
        "inputs": {"question": question},
        "response_mode": "blocking",
        "user": user_id,
    }
    resp = requests.post(url, headers=DIFY_HEADERS, json=payload, timeout=120)
    resp.raise_for_status()
    return resp.json()

# -------------------------
# 页面配置
# -------------------------
st.set_page_config(
    page_title="AI Chat Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
    st.session_state.conversations = {
        "新对话 1": {
            "id": str(uuid4()),
            "history": [{"role": "assistant", "content": "让我们开始聊天吧！👇"}]
        }
    }
if "current_conversation" not in st.session_state:
    st.session_state.current_conversation = "新对话 1"
if "conversation_counter" not in st.session_state:
    st.session_state.conversation_counter = 1
if "rename_mode" not in st.session_state:
    st.session_state.rename_mode = None
if "user_avatar" not in st.session_state:
    st.session_state.user_avatar = DEFAULT_AVATAR
if "user_name" not in st.session_state:
    st.session_state.user_name = DEFAULT_NAME

# -------------------------
# 侧边栏
# -------------------------
with st.sidebar:
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
            st.session_state.conversation_counter += 1
            new_name = f"新对话 {st.session_state.conversation_counter}"
            st.session_state.conversations[new_name] = {
                "id": str(uuid4()),
                "history": [{"role": "assistant", "content": "让我们开始新的对话吧！👇"}]
            }
            st.session_state.current_conversation = new_name
            st.rerun()

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
                btn_label = f"{'🔵' if conv_name == st.session_state.current_conversation else '⚪'} {conv_name}"
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
                    # 这里原来会请求 http://localhost:8000/reset
                    # Dify 的工作流执行接口是无状态的，删除会话只需清本地状态即可
                    del st.session_state.conversations[conv_name]
                    if conv_name == st.session_state.current_conversation:
                        st.session_state.current_conversation = list(st.session_state.conversations.keys())[0]
                    st.rerun()

# -------------------------
# 主界面
# -------------------------
st.caption(f"当前对话：{st.session_state.current_conversation}")

# 显示聊天记录
current_conv = st.session_state.conversations[st.session_state.current_conversation]
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
    current_conv["history"].append({"role": "user", "content": prompt})

    # 显示用户消息
    with st.chat_message("user", avatar=st.session_state.user_avatar):
        st.markdown(f"**{st.session_state.user_name}**: {prompt}")

    # 获取AI回复（调用 Dify 工作流：blocking）
    with st.chat_message("assistant", avatar="🤖"):
        message_placeholder = st.empty()
        with st.spinner("正在生成回复..."):
            try:
                data = run_dify_workflow_blocking(prompt, st.session_state.user_name or "cjm")

                # ✅ 关键：有些版本/部署下，结果在 data.outputs
                payload = data.get("data") or data  # 兼容不同结构
                outputs = payload.get("outputs") or {}

                # 按你的 End 节点命名来取值（常见是 answer 或 text）
                answer = (
                        outputs.get("answer")
                        or outputs.get("text")
                        or outputs.get("result")
                        or (payload.get("message") if isinstance(payload.get("message"), str) else None)
                        or json.dumps(outputs, ensure_ascii=False)  # 兜底：把整个 outputs 打出来
                        or "暂时无法生成回复"
                )
            except requests.RequestException as e:
                answer = f"请求失败: {str(e)}"

            message_placeholder.markdown(f"**AI助手**: {answer}")

    # 添加AI回复
    current_conv["history"].append({"role": "assistant", "content": answer})