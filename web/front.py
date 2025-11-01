import os
import json
import time
import streamlit as st
from uuid import uuid4
from datetime import datetime
from auth import AuthManager, require_unified_auth
from models import DatabaseManager
from backend import get_workflow_list, run_dify_workflow, test_all_workflows

# -------------------------
# 初始化
# -------------------------
auth_manager = AuthManager()
db_manager = DatabaseManager()

# -------------------------
# 页面配置（必须在最前面）
# -------------------------
st.set_page_config(
    page_title="ALMA AI 助手",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------------
# 统一登录检查
# -------------------------
is_authenticated, is_admin = require_unified_auth(auth_manager)

# 如果未登录，显示登录页面
if not is_authenticated:
    auth_manager.show_login_page()
    st.stop()

# -------------------------
# 管理员界面
# -------------------------
if is_admin:
    
    # 侧边栏导航
    with st.sidebar:
        st.title("🔧 管理后台")
        st.divider()
        
        # 导航菜单
        menu_options = {
            "📊 系统概览": "overview",
            "📁 文件审批": "files",
            "👥 用户管理": "users", 
            "🎫 邀请码管理": "invite_codes",
            "⚙️ 工作流管理": "workflows"
        }
        
        selected_menu = st.selectbox("选择功能", list(menu_options.keys()))
        current_page = menu_options[selected_menu]
        
        st.divider()
        
        if st.button("🚪 退出管理后台", use_container_width=True):
            del st.session_state.is_admin
            st.rerun()
    
    # 系统概览页面
    if current_page == "overview":
        st.title("📊 系统概览")
        
        try:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                all_users = db_manager.get_all_users()
                st.metric("总用户数", len(all_users))
            
            with col2:
                total_conversations = db_manager.get_total_conversation_count()
                st.metric("总对话数", total_conversations)
            
            with col3:
                pending_files = db_manager.get_pending_files()
                st.metric("待审批文件", len(pending_files))
            
            with col4:
                workflow_status = test_all_workflows(db_manager)
                active_workflows = sum(1 for status in workflow_status.values() if status['status'] == 'ok')
                st.metric("活跃工作流", f"{active_workflows}/{len(workflow_status)}")
            
            st.subheader("📈 最近活动")
            st.info("最近活动功能需要进一步实现")
            
        except Exception as e:
            st.error(f"加载系统概览失败: {e}")
    
    # 文件审批页面
    elif current_page == "files":
        st.title("📁 文件审批管理")
        
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
                            
                            user = db_manager.get_user_by_id(file_info.user_id)
                            username = user.username if user else f"用户{file_info.user_id}"
                            
                            with col1:
                                st.write(f"**文件名**: {file_info.filename}")
                                st.write(f"**上传用户**: {username}")
                                st.write(f"**上传时间**: {file_info.upload_at.strftime('%Y-%m-%d %H:%M')}")
                            
                            with col2:
                                file_path = file_info.filepath
                                if os.path.exists(file_path):
                                    file_size = os.path.getsize(file_path)
                                    st.write(f"**文件大小**: {file_size / 1024:.1f} KB")
                                else:
                                    st.error("文件不存在")
                            
                            with col3:
                                if os.path.exists(file_path):
                                    with open(file_path, "rb") as f:
                                        file_data = f.read()
                                    
                                    st.download_button(
                                        "📥 下载",
                                        file_data,
                                        file_info.filename,
                                        key=f"download_{file_info.id}"
                                    )
                                else:
                                    st.error("文件不存在")
                            
                            with col4:
                                col_approve, col_reject = st.columns(2)
                                
                                with col_approve:
                                    if st.button("✅ 批准", key=f"approve_{file_info.id}"):
                                        if db_manager.update_file_status(file_info.id, 'approved'):
                                            st.success("文件已批准")
                                            st.rerun()
                                        else:
                                            st.error("操作失败")
                                
                                with col_reject:
                                    if st.button("❌ 拒绝", key=f"reject_{file_info.id}"):
                                        if db_manager.update_file_status(file_info.id, 'rejected'):
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
    
    # 用户管理页面
    elif current_page == "users":
        st.title("👥 用户管理")
        
        try:
            # 搜索和筛选
            col_search, col_sort = st.columns([3, 1])
            with col_search:
                search_keyword = st.text_input("🔍 搜索用户", placeholder="输入用户名搜索", key="user_search")
            with col_sort:
                sort_option = st.selectbox("排序方式", ["注册时间（新→旧）", "注册时间（旧→新）", "最后登录（新→旧）"], key="user_sort")
            
            # 获取所有用户及统计
            all_users_data = db_manager.get_all_users_with_stats()
            
            # 搜索过滤
            if search_keyword:
                all_users_data = [
                    item for item in all_users_data
                    if search_keyword.lower() in item["user"].username.lower()
                ]
            
            # 排序
            if sort_option == "注册时间（新→旧）":
                all_users_data.sort(key=lambda x: x["user"].created_at, reverse=True)
            elif sort_option == "注册时间（旧→新）":
                all_users_data.sort(key=lambda x: x["user"].created_at, reverse=False)
            elif sort_option == "最后登录（新→旧）":
                all_users_data.sort(
                    key=lambda x: x["user"].last_login if x["user"].last_login else datetime.min,
                    reverse=True
                )
            
            st.write(f"共找到 {len(all_users_data)} 个用户")
            st.divider()
            
            if not all_users_data:
                st.info("没有找到匹配的用户")
            else:
                for user_data in all_users_data:
                    user = user_data["user"]
                    stats = user_data["stats"]
                    
                    with st.container():
                        col1, col2, col3, col4, col5 = st.columns([2, 1.5, 1, 1, 1])
                        
                        with col1:
                            st.write(f"**{user.username}**")
                            st.caption(f"注册时间: {user.created_at.strftime('%Y-%m-%d %H:%M')}")
                            if user.last_login:
                                st.caption(f"最后登录: {user.last_login.strftime('%Y-%m-%d %H:%M')}")
                            else:
                                st.caption("最后登录: 从未登录")
                            st.caption(f"邀请码: {user.invite_code}")
                        
                        with col2:
                            st.write("**统计数据**")
                            st.caption(f"💬 对话: {stats['conversation_count']}")
                            st.caption(f"📁 文件: {stats['file_count']}")
                            if stats['last_activity']:
                                st.caption(f"📊 最后活动: {stats['last_activity'].strftime('%Y-%m-%d %H:%M')}")
                        
                        with col3:
                            # 活跃度计算
                            if user.last_login:
                                days_since_login = (datetime.now() - user.last_login).days
                                if days_since_login <= 1:
                                    activity = "🟢 活跃"
                                elif days_since_login <= 7:
                                    activity = "🟡 一般"
                                elif days_since_login <= 30:
                                    activity = "🟠 较少"
                                else:
                                    activity = "🔴 不活跃"
                            else:
                                activity = "⚪ 未登录"
                            
                            st.write("**活跃度**")
                            st.caption(activity)
                        
                        with col4:
                            if st.button("📋 详情", key=f"detail_{user.id}", use_container_width=True):
                                st.session_state[f"viewing_user_{user.id}"] = True
                                st.rerun()
                            
                            if st.button("🔑 重置密码", key=f"reset_pwd_{user.id}", use_container_width=True):
                                st.session_state[f"resetting_pwd_{user.id}"] = True
                                st.rerun()
                        
                        with col5:
                            if st.button("🗑️ 删除", key=f"del_user_{user.id}", use_container_width=True):
                                st.session_state[f"confirming_delete_{user.id}"] = True
                                st.rerun()
                        
                        # 查看详情
                        if st.session_state.get(f"viewing_user_{user.id}", False):
                            st.divider()
                            st.subheader(f"用户详情: {user.username}")
                            
                            col_info, col_stats = st.columns(2)
                            
                            with col_info:
                                st.markdown("### 基本信息")
                                st.write(f"**用户ID**: {user.id}")
                                st.write(f"**用户名**: {user.username}")
                                st.write(f"**注册时间**: {user.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
                                st.write(f"**邀请码**: {user.invite_code}")
                                if user.last_login:
                                    st.write(f"**最后登录**: {user.last_login.strftime('%Y-%m-%d %H:%M:%S')}")
                                else:
                                    st.write("**最后登录**: 从未登录")
                            
                            with col_stats:
                                st.markdown("### 统计数据")
                                st.metric("对话数量", stats['conversation_count'])
                                st.metric("文件数量", stats['file_count'])
                                if stats['last_activity']:
                                    st.write(f"**最后活动**: {stats['last_activity'].strftime('%Y-%m-%d %H:%M:%S')}")
                                else:
                                    st.write("**最后活动**: 无")
                            
                            # 对话列表
                            st.markdown("### 💬 对话列表")
                            conversations = db_manager.load_user_conversations(user.id)
                            if conversations:
                                for conv in conversations[:10]:  # 最多显示10个
                                    with st.expander(f"📋 {conv.conversation_name} - {conv.workflow_id}"):
                                        st.write(f"**创建时间**: {conv.created_at.strftime('%Y-%m-%d %H:%M')}")
                                        st.write(f"**更新时间**: {conv.updated_at.strftime('%Y-%m-%d %H:%M')}")
                            else:
                                st.info("该用户还没有对话")
                            
                            # 文件列表
                            st.markdown("### 📁 文件列表")
                            files = db_manager.get_user_uploaded_files(user.id)
                            if files:
                                for file_info in files[:10]:  # 最多显示10个
                                    status_emoji = {'pending': '⏳', 'approved': '✅', 'rejected': '❌'}
                                    status_text = {'pending': '待审批', 'approved': '已通过', 'rejected': '已拒绝'}
                                    with st.expander(f"{status_emoji.get(file_info.status, '❓')} {file_info.filename}"):
                                        st.write(f"**状态**: {status_text.get(file_info.status, '未知')}")
                                        st.write(f"**上传时间**: {file_info.upload_at.strftime('%Y-%m-%d %H:%M')}")
                                        if file_info.reviewed_at:
                                            st.write(f"**审批时间**: {file_info.reviewed_at.strftime('%Y-%m-%d %H:%M')}")
                            else:
                                st.info("该用户还没有上传文件")
                            
                            if st.button("关闭", key=f"close_detail_{user.id}"):
                                st.session_state[f"viewing_user_{user.id}"] = False
                                st.rerun()
                            
                            st.divider()
                        
                        # 重置密码
                        if st.session_state.get(f"resetting_pwd_{user.id}", False):
                            st.divider()
                            st.subheader(f"重置密码: {user.username}")
                            
                            with st.form(f"reset_pwd_form_{user.id}"):
                                new_password = st.text_input("新密码", type="password", key=f"new_pwd_{user.id}")
                                confirm_password = st.text_input("确认密码", type="password", key=f"confirm_pwd_{user.id}")
                                
                                col_submit, col_cancel = st.columns(2)
                                with col_submit:
                                    if st.form_submit_button("重置密码"):
                                        if not new_password or len(new_password) < 6:
                                            st.error("密码长度至少6位")
                                        elif new_password != confirm_password:
                                            st.error("两次输入的密码不一致")
                                        else:
                                            if db_manager.reset_user_password(user.id, new_password):
                                                st.success("密码重置成功")
                                                st.session_state[f"resetting_pwd_{user.id}"] = False
                                                st.rerun()
                                            else:
                                                st.error("密码重置失败")
                                with col_cancel:
                                    if st.form_submit_button("取消"):
                                        st.session_state[f"resetting_pwd_{user.id}"] = False
                                        st.rerun()
                            
                            st.divider()
                        
                        # 删除确认
                        if st.session_state.get(f"confirming_delete_{user.id}", False):
                            st.divider()
                            st.warning(f"⚠️ 确认删除用户: {user.username}")
                            st.error("此操作将永久删除用户及其所有相关数据，包括：")
                            st.write(f"- {stats['conversation_count']} 个对话及其所有消息")
                            st.write(f"- {stats['file_count']} 个文件记录")
                            st.write("- 所有工作流权限")
                            
                            col_confirm, col_cancel = st.columns(2)
                            with col_confirm:
                                if st.button("⚠️ 确认删除", key=f"confirm_del_{user.id}", type="primary"):
                                    success, message = db_manager.delete_user(user.id)
                                    if success:
                                        st.success(message)
                                        st.session_state[f"confirming_delete_{user.id}"] = False
                                        st.rerun()
                                    else:
                                        st.error(message)
                            with col_cancel:
                                if st.button("取消", key=f"cancel_del_{user.id}"):
                                    st.session_state[f"confirming_delete_{user.id}"] = False
                                    st.rerun()
                            
                            st.divider()
                        
                        st.divider()
                        
        except Exception as e:
            st.error(f"加载用户管理失败: {e}")
            import traceback
            st.code(traceback.format_exc())
    
    # 邀请码管理页面
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
                                st.write(f"**{code_info.code}**")
                                if code_info.description:
                                    st.caption(code_info.description)
                            
                            with col_usage:
                                usage = f"{code_info.used_count}/{code_info.max_uses}"
                                st.write(f"使用: {usage}")
                            
                            with col_status:
                                status_emoji = "✅" if code_info.status == 'active' else "❌"
                                st.write(f"{status_emoji} {code_info.status}")
                            
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
    
    # 工作流管理页面
    elif current_page == "workflows":
        st.title("⚙️ 工作流管理")
        
        try:
            # 初始化后端，传入 db_manager
            from backend import get_dify_backend
            backend = get_dify_backend(db_manager)
            
            # 标签页
            tab1, tab2 = st.tabs(["工作流列表", "新增工作流"])
            
            with tab1:
                st.subheader("📋 工作流列表")
                
                all_workflows = db_manager.get_all_workflows()
                
                if not all_workflows:
                    st.info("暂无工作流，请在「新增工作流」标签页中创建")
                else:
                    # 筛选选项
                    filter_status = st.selectbox("筛选状态", ["全部", "启用", "禁用"], key="workflow_filter")
                    
                    # 筛选工作流
                    filtered_workflows = all_workflows
                    if filter_status == "启用":
                        filtered_workflows = [w for w in all_workflows if w.status == "active"]
                    elif filter_status == "禁用":
                        filtered_workflows = [w for w in all_workflows if w.status == "inactive"]
                    
                    st.write(f"共 {len(filtered_workflows)} 个工作流")
                    st.divider()
                    
                    for workflow in filtered_workflows:
                        with st.container():
                            col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])
                            
                            with col1:
                                status_icon = "✅" if workflow.status == "active" else "❌"
                                global_icon = "🌐" if workflow.is_global else "👤"
                                st.write(f"**{status_icon} {global_icon} {workflow.name}**")
                                st.caption(f"ID: {workflow.workflow_id}")
                                st.caption(workflow.description if workflow.description else "无描述")
                            
                            with col2:
                                st.write(f"**状态**")
                                st.caption("启用" if workflow.status == "active" else "禁用")
                            
                            with col3:
                                st.write(f"**可见性**")
                                st.caption("全局" if workflow.is_global else "指定用户")
                            
                            with col4:
                                if st.button("✏️ 编辑", key=f"edit_wf_{workflow.id}", use_container_width=True):
                                    st.session_state[f"editing_workflow_{workflow.id}"] = True
                                    st.rerun()
                                
                                # 权限管理按钮
                                if not workflow.is_global:
                                    if st.button("👥 权限", key=f"perm_wf_{workflow.id}", use_container_width=True):
                                        st.session_state[f"manage_perms_{workflow.id}"] = True
                                        st.rerun()
                            
                            with col5:
                                if st.button("🗑️ 删除", key=f"del_wf_{workflow.id}", use_container_width=True):
                                    if db_manager.delete_workflow(workflow.id):
                                        st.success(f"工作流 {workflow.name} 已删除")
                                        st.rerun()
                                    else:
                                        st.error("删除失败：可能有对话正在使用此工作流")
                            
                            # 编辑表单
                            if st.session_state.get(f"editing_workflow_{workflow.id}", False):
                                st.divider()
                                with st.form(f"edit_form_{workflow.id}"):
                                    st.subheader(f"编辑工作流: {workflow.name}")
                                    
                                    new_workflow_id = st.text_input("工作流ID", value=workflow.workflow_id)
                                    new_name = st.text_input("名称", value=workflow.name)
                                    new_description = st.text_area("描述", value=workflow.description)
                                    new_api_base = st.text_input("API Base", value=workflow.api_base)
                                    new_api_key = st.text_input("API Key", value=workflow.api_key, type="password")
                                    new_status = st.selectbox("状态", ["active", "inactive"], 
                                                              index=0 if workflow.status == "active" else 1)
                                    new_is_global = st.checkbox("全局可见", value=workflow.is_global)
                                    
                                    col_submit, col_cancel = st.columns(2)
                                    with col_submit:
                                        if st.form_submit_button("保存"):
                                            if db_manager.update_workflow(
                                                workflow.id,
                                                workflow_id=new_workflow_id,
                                                name=new_name,
                                                description=new_description,
                                                api_base=new_api_base,
                                                api_key=new_api_key,
                                                status=new_status,
                                                is_global=new_is_global
                                            ):
                                                st.success("更新成功")
                                                st.session_state[f"editing_workflow_{workflow.id}"] = False
                                                st.rerun()
                                            else:
                                                st.error("更新失败")
                                    with col_cancel:
                                        if st.form_submit_button("取消"):
                                            st.session_state[f"editing_workflow_{workflow.id}"] = False
                                            st.rerun()
                            
                            # 权限管理
                            if st.session_state.get(f"manage_perms_{workflow.id}", False):
                                st.divider()
                                st.subheader(f"管理权限: {workflow.name}")
                                
                                all_users = db_manager.get_all_users()
                                current_user_ids = set(db_manager.get_workflow_users(workflow.id))
                                
                                selected_users = st.multiselect(
                                    "选择可见用户",
                                    options=[(u.id, u.username) for u in all_users],
                                    default=[(u.id, u.username) for u in all_users if u.id in current_user_ids],
                                    format_func=lambda x: x[1]
                                )
                                
                                user_ids = [uid for uid, _ in selected_users]
                                
                                col_save, col_cancel = st.columns(2)
                                with col_save:
                                    if st.button("保存权限", key=f"save_perms_{workflow.id}"):
                                        if db_manager.set_workflow_users(workflow.id, user_ids):
                                            st.success("权限已更新")
                                            st.session_state[f"manage_perms_{workflow.id}"] = False
                                            st.rerun()
                                        else:
                                            st.error("保存失败")
                                with col_cancel:
                                    if st.button("取消", key=f"cancel_perms_{workflow.id}"):
                                        st.session_state[f"manage_perms_{workflow.id}"] = False
                                        st.rerun()
                            
                            st.divider()
                    
                    # 连接测试
                    st.subheader("🔗 连接测试")
                    if st.button("🔄 测试所有工作流"):
                        with st.spinner("正在测试工作流连接..."):
                            workflow_status = test_all_workflows(db_manager)
                        
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
            
            with tab2:
                st.subheader("➕ 新增工作流")
                
                # 显示创建结果消息
                if "workflow_create_result" in st.session_state:
                    result = st.session_state.workflow_create_result
                    if result.get("success"):
                        st.success(result.get("message", "工作流创建成功！"))
                        if result.get("not_global"):
                            st.info("请在工作流列表中为此工作流设置可见用户")
                        # 清除结果消息和表单标志，避免重复显示
                        del st.session_state.workflow_create_result
                        # 切换到工作流列表标签页
                        st.info("✅ 工作流已创建，请切换到「工作流列表」标签页查看")
                    else:
                        st.error(result.get("message", "创建失败"))
                        del st.session_state.workflow_create_result
                
                with st.form("create_workflow", clear_on_submit=True):
                    workflow_id = st.text_input("工作流ID *", placeholder="workflow_1", 
                                                help="唯一标识符，不能与现有工作流重复")
                    name = st.text_input("名称 *", placeholder="通用助手")
                    description = st.text_area("描述", placeholder="适用于一般性问答和对话")
                    api_base = st.text_input("API Base *", placeholder="http://ai.wenhan.top:8080", 
                                            help="Dify API 服务器地址，无需尾部斜杠")
                    api_key = st.text_input("API Key *", type="password", placeholder="app-xxx 或 Bearer app-xxx", 
                                            help="Dify API Key，可以包含或不包含 'Bearer ' 前缀，系统会自动处理")
                    status = st.selectbox("状态", ["active", "inactive"], index=0)
                    is_global = st.checkbox("全局可见", value=True, 
                                          help="勾选后所有用户可见，取消勾选后需要指定可见用户")
                    
                    submitted = st.form_submit_button("创建工作流", use_container_width=True, type="primary")
                    
                    if submitted:
                        # 验证必填字段
                        if not all([workflow_id.strip(), name.strip(), api_base.strip(), api_key.strip()]):
                            st.session_state.workflow_create_result = {
                                "success": False,
                                "message": "请填写所有必填字段（标*）"
                            }
                        else:
                            # 显示处理中的提示
                            with st.spinner("正在创建工作流..."):
                                try:
                                    result = db_manager.create_workflow(
                                        workflow_id=workflow_id.strip(),
                                        name=name.strip(),
                                        description=description.strip() if description else "",
                                        api_base=api_base.strip(),
                                        api_key=api_key.strip(),
                                        status=status,
                                        is_global=is_global
                                    )
                                    if result:
                                        st.session_state.workflow_create_result = {
                                            "success": True,
                                            "message": f"工作流「{name.strip()}」创建成功！",
                                            "not_global": not is_global
                                        }
                                    else:
                                        st.session_state.workflow_create_result = {
                                            "success": False,
                                            "message": "创建失败：工作流ID可能已存在，请使用其他ID"
                                        }
                                except Exception as e:
                                    st.session_state.workflow_create_result = {
                                        "success": False,
                                        "message": f"创建失败：{str(e)}"
                                    }
                        # Streamlit 表单提交后会自动重新运行，不需要手动调用 st.rerun()
                        
        except Exception as e:
            st.error(f"加载工作流管理失败: {e}")
            import traceback
            st.code(traceback.format_exc())
    
    st.divider()
    st.caption("ALMA 管理后台 - 系统时间: " + datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    
    st.stop()  # 管理员界面结束后停止执行

# -------------------------
# 用户界面（原有逻辑）
# -------------------------

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
    # 检查是否已加载，以及是否是为当前用户加载的
    loaded_user_id = st.session_state.get("conversations_loaded_user_id")
    current_user_id = st.session_state.get("user_id")
    
    if st.session_state.get("conversations_loaded", False) and loaded_user_id == current_user_id:
        return
    
    try:
        user_id = st.session_state.user_id
        conversations = db_manager.load_user_conversations(user_id)
        
        if conversations:
            st.session_state.conversations = {}
            # 用于处理同名对话，确保名称唯一
            name_count = {}
            
            for conv in conversations:
                # 加载对话消息
                messages = db_manager.load_conversation_messages(conv.id)
                message_list = []
                for msg in messages:
                    message_list.append({
                        "role": msg.role,
                        "content": msg.content
                    })
                
                # 处理同名对话：如果有重复名称，添加后缀
                display_name = conv.conversation_name
                if display_name in name_count:
                    name_count[display_name] += 1
                    display_name = f"{conv.conversation_name} ({name_count[display_name]})"
                else:
                    name_count[display_name] = 0
                
                # 使用显示名称作为键，但保存原始名称和ID
                st.session_state.conversations[display_name] = {
                    "id": conv.id,
                    "workflow_id": conv.workflow_id,
                    "history": message_list,
                    "original_name": conv.conversation_name  # 保存原始名称
                }
            
            # 设置当前对话
            if not st.session_state.current_conversation:
                st.session_state.current_conversation = list(st.session_state.conversations.keys())[0]
        else:
            # 如果没有对话，创建一个默认对话
            workflows = get_workflow_list(user_id=user_id, db_manager=db_manager)
            if workflows:
                default_workflow = workflows[0]['id']
                if create_new_conversation("新对话 1", default_workflow):
                    st.session_state.current_conversation = "新对话 1"
        
        st.session_state.conversations_loaded = True
        st.session_state.conversations_loaded_user_id = user_id
        
    except Exception as e:
        st.error(f"加载对话失败: {e}")

def create_new_conversation(name: str, workflow_id: str):
    """创建新对话"""
    try:
        user_id = st.session_state.user_id
        
        # 检查是否已有同名对话，确保名称唯一
        existing_convs = db_manager.load_user_conversations(user_id)
        existing_names = {conv.conversation_name for conv in existing_convs}
        
        # 如果名称已存在，添加序号后缀
        base_name = name
        counter = 1
        while name in existing_names:
            name = f"{base_name} ({counter})"
            counter += 1
        
        conversation_id = db_manager.save_conversation(user_id, name, workflow_id)
        
        if conversation_id:
            # 添加欢迎消息
            db_manager.save_message(conversation_id, "assistant", "让我们开始聊天吧！👇")
            
            st.session_state.conversations[name] = {
                "id": conversation_id,
                "workflow_id": workflow_id,
                "history": [{"role": "assistant", "content": "让我们开始聊天吧！👇"}],
                "original_name": name
            }
            
            # 设置当前对话
            st.session_state.current_conversation = name
            
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
            # 会话级去重：避免同一文件在一次会话重跑时重复入库
            if "uploaded_dedup" not in st.session_state:
                st.session_state.uploaded_dedup = {}
            file_buffer = uploaded_file.getbuffer()
            dedup_key = f"{st.session_state.user_id}:{uploaded_file.name}:{len(file_buffer)}"
            if st.session_state.uploaded_dedup.get(dedup_key):
                st.info("该文件已处理，无需重复上传。")
                raise Exception("DUPLICATE_SKIP")
            
            # 创建用户上传目录
            user_upload_dir = f"uploads/{st.session_state.username}"
            os.makedirs(user_upload_dir, exist_ok=True)
            
            # 保存文件
            file_path = os.path.join(user_upload_dir, uploaded_file.name)
            with open(file_path, "wb") as f:
                f.write(file_buffer)
            
            # 保存到数据库
            file_id = db_manager.save_uploaded_file(
                st.session_state.user_id,
                uploaded_file.name,
                file_path
            )
            
            if file_id:
                st.success(f"文件 {uploaded_file.name} 上传成功，等待管理员审批")
                st.session_state.uploaded_dedup[dedup_key] = True
            else:
                st.error("文件上传失败")
                
        except Exception as e:
            if str(e) != "DUPLICATE_SKIP":
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
                
                st.write(f"{status_emoji.get(file_info.status, '❓')} {file_info.filename} - {status_text.get(file_info.status, '未知')}")
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
        workflows = get_workflow_list(user_id=st.session_state.user_id, db_manager=db_manager)
        
        if workflows:
            workflow_options = {f"{w['name']} - {w['description']}": w['id'] for w in workflows}
            selected_workflow = st.selectbox("选择工作流", list(workflow_options.keys()))
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("确认", key="confirm_workflow"):
                    workflow_id = workflow_options[selected_workflow]
                    
                    # 获取现有对话数量，生成唯一名称
                    existing_convs = db_manager.load_user_conversations(st.session_state.user_id)
                    base_name = "新对话"
                    counter = len(existing_convs) + 1
                    new_name = f"{base_name} {counter}"
                    
                    # 确保名称唯一
                    existing_names = {conv.conversation_name for conv in existing_convs}
                    while new_name in existing_names:
                        counter += 1
                        new_name = f"{base_name} {counter}"
                    
                    if create_new_conversation(new_name, workflow_id):
                        st.session_state.current_conversation = new_name
                        st.session_state.show_workflow_selector = False
                        st.rerun()
            with col2:
                if st.button("取消", key="cancel_workflow"):
                    st.session_state.show_workflow_selector = False
                    st.rerun()
        else:
            st.warning("没有可用的工作流。请联系管理员为您分配工作流权限。")

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
                workflows = get_workflow_list(user_id=st.session_state.user_id, db_manager=db_manager)
                # 如果用户没有权限看到该工作流，从数据库直接获取名称
                workflow_name = next((w['name'] for w in workflows if w['id'] == workflow_id), None)
                if not workflow_name:
                    # 尝试从数据库获取工作流名称
                    from models import Workflow
                    workflow = db_manager.get_workflow_by_workflow_id(workflow_id)
                    workflow_name = workflow.name if workflow else workflow_id
                
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
    workflows = get_workflow_list(user_id=st.session_state.user_id, db_manager=db_manager)
    # 如果用户没有权限看到该工作流，从数据库直接获取名称
    workflow_name = next((w['name'] for w in workflows if w['id'] == workflow_id), None)
    if not workflow_name:
        # 尝试从数据库获取工作流名称
        workflow = db_manager.get_workflow_by_workflow_id(workflow_id)
        workflow_name = workflow.name if workflow else workflow_id
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
                        workflow_id,
                        db_manager=db_manager
                    )
                    
                except Exception as e:
                    answer = f"AI 回复生成失败: {str(e)}"

                message_placeholder.markdown(f"**AI助手**: {answer}")

        # 添加AI回复到会话状态和数据库
        current_conv["history"].append({"role": "assistant", "content": answer})
        save_message_to_db(current_conv["id"], "assistant", answer)
else:
    st.info("请选择一个对话或创建新对话开始聊天")