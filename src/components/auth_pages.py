import streamlit as st
from auth.session_manager import SessionManager
from config.app_config import APP_NAME, APP_DESCRIPTION
from utils.validators import validate_signup_fields
import time

def show_login_page():
    """显示登录或注册页面"""
    # 立即初始化form_type，在此之前不能有任何代码！
    if 'form_type' not in st.session_state:
        st.session_state['form_type'] = 'login'  # 使用字典式访问以确保安全
    
    # 从现在开始，可以保证form_type存在
    current_form = st.session_state['form_type']  # 使用字典式访问以保持一致性

    
    st.markdown("<div class='auth-shell'>", unsafe_allow_html=True)

    # 顶部 Hero 区
    st.markdown(
        """
        <div class='auth-hero'>
            <p class='auth-hero__eyebrow'>HEALTH INSIGHT AI</p>
            <h1 class='auth-hero__title'>美年 · 智能健康洞察中心</h1>
            <p class='auth-hero__desc'>聚焦家人健康状态，AI 级联洞察体检数据，带来更安心的健康管理体验。</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 居中表单
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        # 根据当前模式渲染对应表单
        if current_form == 'login':
            show_login_form()
        else:
            show_signup_form()
        
        # 底部的切换按钮
        toggle_text = "注册" if current_form == 'login' else "登录"
        if st.button(toggle_text, use_container_width=True, type="secondary"):
            # 切换表单类型（使用字典访问以确保安全）
            st.session_state['form_type'] = 'signup' if current_form == 'login' else 'login'
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

def show_login_form():
    """显示登录表单"""
    with st.form("login_form"):
        email = st.text_input("电子邮件", key="login_email", placeholder="name@example.com")
        password = st.text_input("密码", type="password", key="login_password", placeholder="请输入密码")
        submitted = st.form_submit_button("登录", use_container_width=True, type="primary")

    if submitted:
        if email and password:
            success, result = SessionManager.login(email, password)
            if success:
                with st.spinner("正在登录..."):
                    success_placeholder = st.empty()
                    success_placeholder.success("登录成功！正在重定向...")
                    time.sleep(1)
                    st.rerun()
            else:
                st.error(f"登录失败: {result}")
        else:
            st.error("请输入电子邮件和密码")

def show_signup_form():
    """显示注册表单"""
    with st.form("signup_form"):
        new_name = st.text_input("全名", key="signup_name")
        new_email = st.text_input("电子邮件", key="signup_email")
        new_password = st.text_input("密码", type="password", key="signup_password")
        confirm_password = st.text_input("确认密码", type="password", key="signup_password2")
        
        # 显示密码要求
        st.markdown("""
            密码要求:
            - 至少8个字符
            - 一个大写字母
            - 一个小写字母
            - 一个数字
        """)
        
        # 注册按钮
        submitted = st.form_submit_button("注册", use_container_width=True, type="primary")

    if submitted:
        # 验证注册字段
        validation_result = validate_signup_fields(
            new_name, new_email, new_password, confirm_password
        )
        
        if not validation_result[0]:
            st.error(validation_result[1])
            return
        
        # 在注册期间显示加载动画
        with st.spinner("正在创建您的账户..."):
            # 尝试注册
            success, response = st.session_state.auth_service.sign_up(
                new_email, new_password, new_name
            )
            
            if success:
                # 如果成功，则设置会话状态并重新运行应用
                st.session_state.authenticated = True
                st.session_state.user = response
                st.success("账户创建成功！正在重定向...")
                time.sleep(1)
                st.rerun()
            else:
                st.error(f"注册失败: {response}")
            with st.spinner("正在创建您的账户..."):
                # 尝试注册
                success, response = st.session_state.auth_service.sign_up(
                    new_email, new_password, new_name
                )
                
                if success:
                    # 如果成功，则设置会话状态并重新运行应用
                    st.session_state.authenticated = True
                    st.session_state.user = response
                    st.success("账户创建成功！正在重定向...")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(f"注册失败: {response}")
