import os
import json
import streamlit as st
from datetime import datetime
from auth import require_admin_auth
from models import DatabaseManager
from backend import get_workflow_list, test_all_workflows

# -------------------------
# 初始化
# -------------------------
db_manager = DatabaseManager()

# -------------------------
# 页面配置
# -------------------------
st.set_page_config(
    page_title="ALMA 管理后台",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------------
# 管理员认证
# -------------------------
if not require_admin_auth():
    st.stop()

# -------------------------
# 侧边栏导航
# -------------------------
with st.sidebar:
    st.title("🔧 管理后台")
    st.divider()
    
    # 导航菜单
    menu_options = {
        "📊 系统概览": "overview",
        "📁 文件审批": "files",
        "👥 用户管理": "users", 
        "🎫 邀请码管理": "invite_codes",
        "⚙️ 工作流状态": "workflows"
    }
    
    selected_menu = st.selectbox("选择功能", list(menu_options.keys()))
    current_page = menu_options[selected_menu]
    
    st.divider()
    
    if st.button("🚪 退出管理后台", use_container_width=True):
        del st.session_state.is_admin
        st.rerun()

# -------------------------
# 系统概览页面
# -------------------------
if current_page == "overview":
    st.title("📊 系统概览")
    
    try:
        # 获取统计数据
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            # 用户数量
            users = db_manager.get_invite_codes()  # 这里需要添加获取用户数量的方法
            st.metric("总用户数", "N/A", "需要实现")
        
        with col2:
            # 对话数量
            st.metric("总对话数", "N/A", "需要实现")
        
        with col3:
            # 待审批文件
            pending_files = db_manager.get_pending_files()
            st.metric("待审批文件", len(pending_files))
        
        with col4:
            # 工作流状态
            workflow_status = test_all_workflows()
            active_workflows = sum(1 for status in workflow_status.values() if status['status'] == 'ok')
            st.metric("活跃工作流", f"{active_workflows}/{len(workflow_status)}")
        
        # 最近活动
        st.subheader("📈 最近活动")
        st.info("最近活动功能需要进一步实现")
        
    except Exception as e:
        st.error(f"加载系统概览失败: {e}")

# -------------------------
# 文件审批页面
# -------------------------
elif current_page == "files":
    st.title("📁 文件审批管理")
    
    # 标签页
    tab1, tab2 = st.tabs(["待审批文件", "审批历史"])
    
    with tab1:
        st.subheader("⏳ 待审批文件")
        
        try:
            pending_files = db_manager.get_pending_files()
            
            if not pending_files:
                st.info("暂无待审批文件")
            else:
                for file_info in pending_files:
                    with st.container():
                        col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
                        
                        with col1:
                            st.write(f"**文件名**: {file_info['filename']}")
                            st.write(f"**上传用户**: {file_info['username']}")
                            st.write(f"**上传时间**: {file_info['upload_at'].strftime('%Y-%m-%d %H:%M')}")
                        
                        with col2:
                            # 文件信息
                            file_path = file_info['filepath']
                            if os.path.exists(file_path):
                                file_size = os.path.getsize(file_path)
                                st.write(f"**文件大小**: {file_size / 1024:.1f} KB")
                            else:
                                st.error("文件不存在")
                        
                        with col3:
                            # 下载按钮
                            if os.path.exists(file_path):
                                with open(file_path, "rb") as f:
                                    file_data = f.read()
                                
                                st.download_button(
                                    "📥 下载",
                                    file_data,
                                    file_info['filename'],
                                    key=f"download_{file_info['id']}"
                                )
                            else:
                                st.error("文件不存在")
                        
                        with col4:
                            # 审批按钮
                            col_approve, col_reject = st.columns(2)
                            
                            with col_approve:
                                if st.button("✅ 批准", key=f"approve_{file_info['id']}"):
                                    if db_manager.update_file_status(file_info['id'], 'approved'):
                                        st.success("文件已批准")
                                        st.rerun()
                                    else:
                                        st.error("操作失败")
                            
                            with col_reject:
                                if st.button("❌ 拒绝", key=f"reject_{file_info['id']}"):
                                    if db_manager.update_file_status(file_info['id'], 'rejected'):
                                        st.success("文件已拒绝")
                                        st.rerun()
                                    else:
                                        st.error("操作失败")
                        
                        st.divider()
                        
        except Exception as e:
            st.error(f"加载待审批文件失败: {e}")
    
    with tab2:
        st.subheader("📋 审批历史")
        st.info("审批历史功能需要进一步实现")

# -------------------------
# 用户管理页面
# -------------------------
elif current_page == "users":
    st.title("👥 用户管理")
    st.info("用户管理功能需要进一步实现")

# -------------------------
# 邀请码管理页面
# -------------------------
elif current_page == "invite_codes":
    st.title("🎫 邀请码管理")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("现有邀请码")
        
        try:
            invite_codes = db_manager.get_invite_codes()
            
            if not invite_codes:
                st.info("暂无邀请码")
            else:
                for code_info in invite_codes:
                    with st.container():
                        col_name, col_usage, col_status = st.columns([2, 1, 1])
                        
                        with col_name:
                            st.write(f"**{code_info['code']}**")
                            if code_info['description']:
                                st.caption(code_info['description'])
                        
                        with col_usage:
                            usage = f"{code_info['used_count']}/{code_info['max_uses']}"
                            st.write(f"使用: {usage}")
                        
                        with col_status:
                            status_emoji = "✅" if code_info['status'] == 'active' else "❌"
                            st.write(f"{status_emoji} {code_info['status']}")
                        
                        st.divider()
                        
        except Exception as e:
            st.error(f"加载邀请码失败: {e}")
    
    with col2:
        st.subheader("创建新邀请码")
        
        with st.form("create_invite_code"):
            code = st.text_input("邀请码", placeholder="ALMA2024004")
            max_uses = st.number_input("最大使用次数", min_value=1, value=1)
            expires_days = st.number_input("有效期（天）", min_value=1, value=365)
            description = st.text_area("描述", placeholder="邀请码描述")
            
            if st.form_submit_button("创建邀请码"):
                if code:
                    if db_manager.create_invite_code(code, max_uses, expires_days, description):
                        st.success(f"邀请码 {code} 创建成功")
                        st.rerun()
                    else:
                        st.error("创建失败，邀请码可能已存在")
                else:
                    st.warning("请输入邀请码")

# -------------------------
# 工作流状态页面
# -------------------------
elif current_page == "workflows":
    st.title("⚙️ 工作流状态")
    
    try:
        # 获取工作流列表
        workflows = get_workflow_list()
        
        if not workflows:
            st.warning("没有配置工作流")
        else:
            st.subheader("工作流配置")
            
            for workflow in workflows:
                with st.expander(f"📋 {workflow['name']} - {workflow['description']}"):
                    st.write(f"**ID**: {workflow['id']}")
                    st.write(f"**API Base**: {workflow['api_base']}")
                    st.write(f"**API Key**: {workflow['api_key'][:20]}...")
            
            st.divider()
            
            # 测试工作流连接
            st.subheader("连接测试")
            
            if st.button("🔄 测试所有工作流"):
                with st.spinner("正在测试工作流连接..."):
                    workflow_status = test_all_workflows()
                
                for workflow_id, status in workflow_status.items():
                    col1, col2, col3 = st.columns([2, 1, 2])
                    
                    with col1:
                        st.write(f"**{status['name']}**")
                    
                    with col2:
                        if status['status'] == 'ok':
                            st.success("✅ 正常")
                        else:
                            st.error("❌ 异常")
                    
                    with col3:
                        st.caption(status['message'])
                    
                    st.divider()
                    
    except Exception as e:
        st.error(f"加载工作流状态失败: {e}")

# -------------------------
# 页脚
# -------------------------
st.divider()
st.caption("ALMA 管理后台 - 系统时间: " + datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
