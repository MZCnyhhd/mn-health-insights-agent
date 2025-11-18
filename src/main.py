import streamlit as st  # 导入 Streamlit 库，用于构建 Web 应用界面，并简写为 st
from auth.session_manager import SessionManager  # 从自定义模块导入会话管理工具，用于处理登录状态等
from components.auth_pages import show_login_page  # 导入登录/注册页面渲染函数
from components.sidebar import show_sidebar  # 导入侧边栏渲染函数
from components.analysis_form import show_analysis_form  # 导入体检报告分析表单组件
from components.footer import show_footer  # 导入页脚显示函数
from components.header import show_header  # 导入头部问候组件

from config.app_config import APP_NAME, APP_DESCRIPTION  # 导入应用名称和描述配置
from utils.pdf_exporter import create_analysis_pdf  # 导入工具函数，用于将 Markdown 报告转换为 PDF

CUSTOM_THEME = """
<style>
body, .stApp {
    background: linear-gradient(180deg, #eff6ff 0%, #ffffff 55%, #f7fbff 100%);
    font-family: 'PingFang SC', 'Microsoft YaHei', 'Segoe UI', sans-serif;
    color: #1f2a37;
}

.block-container {
    max-width: 960px;
    padding-top: 2.5rem;
    padding-bottom: 3rem;
    margin: 0 auto;
}

[data-testid="stSidebar"] > div:first-child {
    background: linear-gradient(180deg, #e5f0ff 0%, #fdfdff 100%);
    border-right: 1px solid #d3e2ff;
    box-shadow: 4px 0 12px rgba(61, 112, 189, 0.08);
    padding: 1rem 0.5rem 2rem;
}

header[data-testid="stHeader"] {
    background: linear-gradient(180deg, #eff6ff 0%, #ffffff 55%, #f7fbff 100%);
    border-bottom: none;
    box-shadow: none;
}

header[data-testid="stHeader"] .stToolbar,
.stAppToolbar {
    background: linear-gradient(180deg, #eff6ff 0%, #ffffff 55%, #f7fbff 100%) !important;
}

.stButton > button[data-baseweb="button"] {
    border-radius: 999px;
    background: linear-gradient(135deg, #34d399, #10b981);
    border: none;
    color: #0f172a;
    font-weight: 600;
    box-shadow: 0 10px 22px rgba(16, 185, 129, 0.25);
}

.stButton > button[data-baseweb="button"]:hover {
    filter: brightness(1.06);
}

.stButton button[kind="primary"] {
    background: linear-gradient(135deg, #6366f1, #4338ca) !important;
    color: #ffffff !important;
    border: none !important;
    box-shadow: 0 14px 30px rgba(67, 56, 202, 0.28) !important;
}

.stButton button[kind="primary"]:hover {
    filter: brightness(1.07) !important;
}

.stButton > button[data-baseweb="button"] + button[data-baseweb="button"] {
    margin-left: 0.5rem;
}

[aria-label="➕ 创建体检报告"] {
    background: linear-gradient(120deg, #facc15, #f97316) !important;
    box-shadow: 0 12px 24px rgba(249, 115, 22, 0.25) !important;
    color: #1f2937 !important;
    border: none !important;
}

[aria-label="➕ 创建体检报告"]:hover {
    filter: brightness(1.05) !important;
}

[data-testid="stForm"] .stButton > button[data-baseweb="button"] {
    background: linear-gradient(135deg, #5eead4, #0ea5e9);
    box-shadow: 0 12px 24px rgba(14, 165, 233, 0.28);
}

[data-testid="stForm"] .stButton > button[data-baseweb="button"]:hover {
    filter: brightness(1.06);
}

[data-testid="stFormSubmitButton"] button,
[data-testid="stForm"] button[kind="primary"] {
    background: linear-gradient(135deg, #5eead4, #0ea5e9) !important;
    border: none !important;
    box-shadow: 0 12px 24px rgba(14, 165, 233, 0.28) !important;
    color: #ffffff !important;
}

[data-testid="stFormSubmitButton"] button:hover,
[data-testid="stForm"] button[kind="primary"]:hover {
    filter: brightness(1.07) !important;
}

[data-testid="stFileUploader"] {
    padding: 1.75rem 1.75rem 2rem;
    background: rgba(255, 255, 255, 0.98);
    border-radius: 20px;
    box-shadow: 0 18px 40px rgba(15, 23, 42, 0.08);
    border: 1px solid #e0edff;
    margin: 0 auto 1.5rem;
    max-width: 720px;
    width: 100%;
}

[data-testid="stFileUploaderDropzone"] {
    border: 2px dashed #9cc8ff;
    background: rgba(244, 251, 255, 0.85);
    border-radius: 18px;
    padding: 1.5rem;
    box-shadow: inset 0 0 0 rgba(0,0,0,0);
    width: min(500px, 100%);
    height: 50px;
    margin: 0 auto;
}

[data-testid="stCaptionContainer"] {
    text-align: center;
    color: #6b7280;
}

.report-device {
    border-radius: 24px;
    padding: 2rem;
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(255,255,255,0.95);
    border: 1px solid rgba(148, 174, 229, 0.35);
    margin-bottom: 1.5rem;
}

.report-device [data-testid="stSelectbox"] {
    width: 100%;
    max-width: 250px;
    background: rgba(255, 255, 255, 0.95);
    border-radius: 16px;
    padding: 0.75rem 1rem 1rem;
    box-shadow: 0 12px 25px rgba(37, 99, 235, 0.18);
    position: relative;
    z-index: 1;
}

.report-device__hint {
    text-align: center;
    color: #1f2a37;
    font-weight: 600;
    margin-top: 0.75rem;
}

.auth-hero {
    text-align: center;
    margin-bottom: 2rem;
    display: flex;
    flex-direction: column;
    align-items: center;
}

.auth-shell {
    padding-top: 4rem;
    padding-bottom: 3rem;
}

.auth-hero__eyebrow {
    font-size: 0.95rem;
    letter-spacing: 0.15rem;
    text-transform: uppercase;
    color: #818cf8;
    font-weight: 600;
    margin: 0 auto 0.75rem;
    display: inline-block;
}

.auth-hero__title {
    margin: 0;
    font-size: 2.25rem;
    font-weight: 800;
    color: #0f172a;
}

.auth-hero__desc {
    color: #4b5563;
    font-size: 1.05rem;
    line-height: 1.8;
    margin: 0.75rem auto 0;
    max-width: 520px;
    text-align: center;
}

[data-testid="stForm"] {
    background: #ffffff;
    border-radius: 24px;
    padding: 2rem 2.25rem 2.25rem;
    box-shadow: 0 35px 60px rgba(15, 23, 42, 0.12);
    border: 1px solid rgba(226, 232, 240, 0.9);
    margin-bottom: 0.5rem;
}

[data-testid="stFormSubmitterInstructions"] {
    display: none;
}

.upload-hero {
    background: linear-gradient(120deg, rgba(100, 181, 246, 0.12), rgba(58, 123, 213, 0.08));
    border: 1px solid rgba(58, 123, 213, 0.15);
    border-radius: 24px;
    padding: 1.75rem 2rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 20px 50px rgba(15, 23, 42, 0.06);
}

.upload-hero__title {
    font-size: 1.45rem;
    font-weight: 700;
    color: #0f172a;
    margin: 0;
}

.upload-hero__desc {
    color: #556177;
    margin: 0.35rem 0 1rem;
    font-size: 1rem;
}

.upload-hero__tags {
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
}

.upload-hero__tags span {
    background: #fff;
    border-radius: 999px;
    border: 1px solid rgba(58, 123, 213, 0.2);
    color: #3a7bd5;
    font-size: 0.85rem;
    padding: 0.35rem 0.95rem;
    font-weight: 500;
}

.upload-steps {
    display: flex;
    gap: 0.75rem;
    margin-bottom: 1.25rem;
}

.upload-steps__item {
    flex: 1;
    background: #fff;
    border-radius: 18px;
    border: 1px solid #e3ecff;
    padding: 1rem;
    box-shadow: 0 16px 42px rgba(15, 23, 42, 0.05);
}

.upload-steps__icon {
    width: 36px;
    height: 36px;
    border-radius: 999px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, #64b5f6, #3a7bd5);
    color: #fff;
    font-weight: 600;
    margin-bottom: 0.5rem;
}

.upload-steps__item strong {
    display: block;
    margin-bottom: 0.2rem;
    color: #1f2a37;
}

.upload-steps__item span {
    color: #6b7280;
    font-size: 0.85rem;
}

@media (max-width: 768px) {
    .upload-steps {
        flex-direction: column;
    }
}

.stTabs [data-baseweb="tab-list"] {
    background: #f0f6ff;
    border-radius: 999px;
    padding: 0.2rem;
}

.stTabs [role="tab"] {
    border-radius: 999px;
    color: #3a7bd5;
}

.stTabs [aria-selected="true"] {
    background: #ffffff;
    box-shadow: 0 4px 10px rgba(58, 123, 213, 0.15);
}

.st-expander {
    border: 1px solid #d7e6ff !important;
    border-radius: 16px !important;
    background: #ffffff !important;
    box-shadow: 0 8px 20px rgba(58, 123, 213, 0.1) !important;
}

.streamlit-expanderHeader, [data-testid="stExpander"] .streamlit-expanderHeader {
    background: #f5f9ff;
    border-radius: 16px 16px 0 0;
    color: #1f2a37;
    font-weight: 600;
}

.stMarkdown a {
    color: #3a7bd5;
}

[data-testid="stMarkdownContainer"] {
    text-align: left;
}

[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li {
    text-align: left;
    line-height: 1.6;
}
</style>
"""

def apply_custom_theme():
    """注入全局浅蓝+白色主题样式"""
    st.markdown(CUSTOM_THEME, unsafe_allow_html=True)

# 辅助函数：显示欢迎界面
def show_welcome_screen():
    st.markdown(
        f"""
        <div style='text-align: center; padding: 3rem 1rem;'>
            <h1 style='margin-bottom: 0.5rem;'>{APP_NAME}</h1>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("➕ 创建体检报告", type="primary", use_container_width=True):
        success, session = SessionManager.create_chat_session()
        if success:
            st.session_state.current_session = session
            st.success("已创建新的体检报告会话")
            st.rerun()
        else:
            st.error(success)


# 辅助函数：显示当前会话聊天记录
def show_chat_history():
    current_session = st.session_state.get('current_session')
    if not current_session:
        st.info("请选择或创建体检报告会话以查看历史记录。")
        return

    success, messages = st.session_state.auth_service.get_session_messages(current_session['id'])
    if not success:
        st.error(f"无法加载聊天记录: {messages}")
        return

    if not messages:
        return

    for message in messages:
        role = message.get('role', 'assistant')
        content = message.get('content', '')
        chat_role = 'assistant' if role == 'assistant' else 'user'
        with st.chat_message(chat_role):
            st.markdown(content)


def main():  # 定义应用的主入口函数
    """应用主函数"""  # 函数文档：应用整体逻辑从此函数开始
    # 初始化会话状态
    SessionManager.init_session()  # 调用会话管理器，初始化或恢复用户会话状态
    apply_custom_theme()  # 应用全局主题样式

    if 'current_session' not in st.session_state:
        st.session_state.current_session = None

    # 未登录用户显示登录/注册页面
    if not st.session_state.get('user'):
        show_login_page()
        show_footer()
        return

    show_header()

    # 显示侧边栏
    show_sidebar()  # 渲染左侧的历史会话列表和退出登录按钮

    # 主聊天区域
    if st.session_state.get('current_session'):  # 如果存在当前选中的体检报告会话
        # 如果有当前会话，则显示分析表单和聊天记录
        show_analysis_form()  # 显示报告上传及“分析报告”按钮表单
        show_chat_history()  # 显示该会话下已有的 AI 分析记录
    else:
        # 否则，显示欢迎界面
        show_welcome_screen()  # 在尚未创建任何会话时显示欢迎页

    show_footer()


# 如果作为主模块运行，则调用main函数
if __name__ == "__main__":  # 仅当当前文件作为脚本直接运行时才执行 main()
    main()  # 调用主函数，启动 Streamlit 应用