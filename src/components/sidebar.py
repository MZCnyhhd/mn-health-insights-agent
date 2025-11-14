import streamlit as st
from auth.session_manager import SessionManager
from components.footer import show_footer

def show_sidebar():
    """显示侧边栏"""
    with st.sidebar:
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
            else:
                st.info("没有以前的会话")  # 如果没有会话，则显示信息

def render_session_list(sessions):
    """渲染会话列表"""
    # 存储删除确认状态
    if 'delete_confirmation' not in st.session_state:
        st.session_state.delete_confirmation = None
    
    # 遍历并渲染每个会话项
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
    
    # 为每个会话创建一个容器
    with st.container():
        # 会话标题和删除按钮并排显示
        title_col, delete_col = st.columns([4, 1])
        
        with title_col:
            # 显示会话标题按钮
            if st.button(f"📝 {session['title']}", key=f"session_{session_id}", use_container_width=True):
                st.session_state.current_session = session  # 设置为当前会话
                st.rerun()  # 重新运行应用
        
        with delete_col:
            # 显示删除按钮
            if st.button("🗑️", key=f"delete_{session_id}", help="删除此会话"):
                # 切换删除确认状态
                if st.session_state.delete_confirmation == session_id:
                    st.session_state.delete_confirmation = None
                else:
                    st.session_state.delete_confirmation = session_id
                st.rerun()
        
        # 如果此会话正在被删除，则显示确认信息
        if st.session_state.delete_confirmation == session_id:
            st.warning("删除以上会话？")
            left_btn, right_btn = st.columns(2)
            with left_btn:
                # 确认删除按钮
                if st.button("是", key=f"confirm_delete_{session_id}", type="primary", use_container_width=True):
                    handle_delete_confirmation(session_id, current_session_id)
            with right_btn:
                # 取消删除按钮
                if st.button("否", key=f"cancel_delete_{session_id}", use_container_width=True):
                    st.session_state.delete_confirmation = None
                    st.rerun()

def handle_delete_confirmation(session_id, current_session_id):
    """处理删除确认"""
    if not session_id:
        st.error("无效的会话")
        return
        
    # 删除会话
    success, error = SessionManager.delete_session(session_id)
    if success:
        st.session_state.delete_confirmation = None
        # 如果删除的是当前会话，则清除当前会话状态
        if current_session_id and current_session_id == session_id:
            st.session_state.current_session = None
        st.rerun()
    else:
        st.error(f"删除失败: {error}")
