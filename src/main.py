import streamlit as st
from auth.session_manager import SessionManager
from components.auth_pages import show_login_page
from components.sidebar import show_sidebar
from components.analysis_form import show_analysis_form
from components.footer import show_footer
from config.app_config import APP_NAME, APP_DESCRIPTION

# 必须是第一个Streamlit命令
st.set_page_config(
    page_title="HIA - 您的个人健康洞察智能助理",  # 设置页面标题
    layout="wide"  # 设置页面布局为宽屏
)

# 初始化会话状态
SessionManager.init_session()


def show_welcome_screen():
    """显示欢迎界面"""
    st.markdown(  # 显示应用的名称和描述
        f"""
        <div style='text-align: center; padding: 50px;'>
            <h1>{APP_NAME}</h1>
            <h3>{APP_DESCRIPTION}</h3>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # 创建列布局以居中按钮
    col1, col2, col3 = st.columns([2, 3, 2])
    with col2:
        # 创建“创建体检报告”按钮
        if st.button("➕ 创建体检报告", use_container_width=True, type="primary"):
            # 创建新的聊天会话
            success, session = SessionManager.create_chat_session()
            if success:
                # 如果成功，则设置当前会话并重新运行应用
                st.session_state.current_session = session
                st.rerun()
            else:
                # 如果失败，则显示错误信息
                st.error("创建会话失败")

def show_chat_history():
    """显示聊天记录"""
    # 获取当前会话的消息
    success, messages = st.session_state.auth_service.get_session_messages(
        st.session_state.current_session['id']
    )
    
    if success:
        # 遍历并显示消息
        for msg in messages:
            if msg['role'] == 'assistant':
                # 以Markdown格式显示助手的消息
                st.markdown(msg['content'])

def show_user_greeting():
    """显示用户问候语"""
    if st.session_state.user:
        # 从用户数据中获取姓名，如果姓名为空则回退到电子邮件
        display_name = st.session_state.user.get('name') or st.session_state.user.get('email', '')
        st.markdown(f"""<div style='text-align: right; padding: 1rem; color: #64B5F6; font-size: 1.1em;'>欢迎您, {display_name}</div>""", unsafe_allow_html=True)

def main():
    """应用主函数"""
    # 初始化会话
    SessionManager.init_session()

    # 如果用户未通过身份验证，则显示登录页面
    if not SessionManager.is_authenticated():
        show_login_page()
        show_footer()
        return

    # 在顶部显示用户问候语
    show_user_greeting()
    
    # 显示侧边栏
    show_sidebar()

    # 主聊天区域
    if st.session_state.get('current_session'):
        # 如果有当前会话，则显示会话标题、分析表单和聊天记录
        st.markdown(f"<h1 style='text-align: center;'>{st.session_state.current_session['title']}</h1>", unsafe_allow_html=True)
        show_analysis_form()
        show_chat_history()
    else:
        # 否则，显示欢迎界面
        show_welcome_screen()

# 如果作为主模块运行，则调用main函数
if __name__ == "__main__":
    main()