import streamlit as st
from auth.session_manager import SessionManager
from components.footer import show_footer

def show_sidebar():
    """显示侧边栏"""
    with st.sidebar:
        if st.button("➕ 创建体检报告", use_container_width=True, type="primary"):
            success, session = SessionManager.create_chat_session()
            if success:
                st.session_state.current_session = session
                st.rerun()
            else:
                st.error("创建会话失败")

        # 显示会话列表
        show_session_list()
        
        # 退出登录按钮
        st.markdown("---")  # 分隔线
        if st.button("退出登录", use_container_width=True):
            SessionManager.logout()  # 调用登出方法
            st.rerun()  # 重新运行应用
        
        # 在侧边栏添加页脚
        show_footer(in_sidebar=True)

def show_session_list():
    """显示用户的会话列表"""
    # 检查用户是否已登录
    if st.session_state.user and 'id' in st.session_state.user:
        # 获取用户会话
        success, sessions = SessionManager.get_user_sessions()
        if success:
            if sessions:
                st.subheader("历史体检报告")  # 显示子标题
                render_session_list(sessions)  # 渲染会话列表

                selected_sessions = st.session_state.get("selected_sessions", [])
                if selected_sessions:
                    if st.button("删除勾选体检报告", type="primary", use_container_width=True):
                        handle_bulk_delete(selected_sessions)
            else:
                st.info("没有历史体检报告")  # 如果没有会话，则显示信息

def render_session_list(sessions):
    """渲染会话列表"""
    if 'selected_sessions' not in st.session_state:
        st.session_state.selected_sessions = []

    for session in sessions:
        render_session_item(session)

def render_session_item(session):
    """渲染单个会话项"""
    # 检查会话数据是否有效
    if not session or not isinstance(session, dict) or 'id' not in session:
        return
        
    session_id = session['id']
    current_session = st.session_state.get('current_session', {})
    current_session_id = current_session.get('id') if isinstance(current_session, dict) else None
    
    checkbox_col, title_col = st.columns([0.7, 4])

    selected_sessions = st.session_state.get("selected_sessions", [])

    with checkbox_col:
        checked = st.checkbox(
            "",
            key=f"select_{session_id}",
            value=session_id in selected_sessions,
            help="勾选后可批量删除体检报告",
        )
        if checked and session_id not in selected_sessions:
            selected_sessions.append(session_id)
        elif not checked and session_id in selected_sessions:
            selected_sessions.remove(session_id)
        st.session_state.selected_sessions = selected_sessions

    with title_col:
        if st.button(
            f"📝 {session['title']}",
            key=f"session_{session_id}",
            use_container_width=True,
        ):
            st.session_state.current_session = session
            st.rerun()


def handle_bulk_delete(selected_session_ids):
    """批量删除选中的会话"""
    if not selected_session_ids:
        return

    current_session = st.session_state.get("current_session", {})
    current_session_id = current_session.get("id") if isinstance(current_session, dict) else None

    for session_id in list(selected_session_ids):
        success, error = SessionManager.delete_session(session_id)
        if not success:
            st.error(f"删除失败: {error}")
            return

    if current_session_id and current_session_id in selected_session_ids:
        st.session_state.current_session = None

    st.session_state.selected_sessions = []
    st.success("已删除选中的体检报告")
    st.rerun()
