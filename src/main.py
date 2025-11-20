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
    max-width: 1180px;
    padding-top: 2.5rem;
    padding-bottom: 3rem;
    margin: 0 auto;
}

[data-testid="stSidebar"] {
    display: flex !important;
    flex-direction: column !important;
    height: 100vh !important;
    padding: 0 !important;
    position: relative !important;
}

[data-testid="stSidebar"] > div:first-child {
    background: linear-gradient(180deg, #e5f0ff 0%, #fdfdff 100%);
    border-right: 1px solid #d3e2ff;
    box-shadow: 4px 0 12px rgba(61, 112, 189, 0.08);
    padding: 1rem 0.5rem 4.5rem;
    display: flex;
    flex-direction: column;
    flex: 1 1 auto;
}

.sidebar-spacer {
    flex: 1 1 auto;
}

.sidebar-history-title {
    text-align: center;
    font-size: 1.15rem;
    font-weight: 700;
    margin: 0.3rem 0 0.3rem;
}

hr.sidebar-section-divider {
    border: none;
    border-top: 1px dashed rgba(148, 163, 184, 0.7);
    margin: 0.75rem 0 0.5rem;
}

.sidebar-bottom-divider {
    margin-top: 0.75rem;
}

.sidebar-empty-state {
    text-align: center;
    font-size: 0.95rem;
    color: #6b7280;
    margin: 0.4rem 0;
}

/* 固定侧边栏底部的“退出登录”区域 */
.sidebar-logout-wrapper {
    position: fixed;
    left: 0.75rem;
    right: 0.75rem;
    bottom: 1.5rem;
}

header[data-testid="stHeader"] {
    background: #f3f8ff;
    border-bottom: none;
    box-shadow: none;
}

header[data-testid="stHeader"] .stToolbar,
.stAppToolbar {
    background: #f3f8ff !important;
}

.stButton > button[data-baseweb="button"] {
    border-radius: 999px;
    background: linear-gradient(135deg, #0ea5e9, #22d3ee);
    border: none;
    color: #ffffff;
    font-weight: 600;
    box-shadow: 0 14px 30px rgba(14, 165, 233, 0.35);
}

.stButton > button[data-baseweb="button"]:hover {
    filter: brightness(1.06);
}

.stButton button[kind="primary"] {
    background: linear-gradient(135deg, #0ea5e9, #22d3ee) !important;
    color: #ffffff !important;
    border: none !important;
    box-shadow: 0 14px 30px rgba(14, 165, 233, 0.35) !important;
}

.stButton button[kind="primary"]:hover {
    filter: brightness(1.07) !important;
}

/* 删除勾选体检报告按钮 - 红粉色警示渐变（提高优先级覆盖通用 primary 样式） */
.st-key-delete_selected_sessions button[kind="primary"] {
    background: linear-gradient(135deg, #fb7185, #ef4444) !important;
    color: #ffffff !important;
    border: none !important;
    box-shadow: 0 10px 20px rgba(248, 113, 113, 0.4) !important;
}

.st-key-delete_selected_sessions button[kind="primary"]:hover {
    filter: brightness(1.06) !important;
}

/* 生成体检报告按钮 */
[aria-label="生成体检报告"] {
    background: linear-gradient(135deg, #22c55e, #16a34a) !important;
    box-shadow: 0 12px 24px rgba(34, 197, 94, 0.35) !important;
}

[aria-label="生成体检报告"]:hover {
    filter: brightness(1.06) !important;
}

/* 历史体检报告会话按钮（包含日期分隔符 | ） */
button[aria-label*="|"] {
    background: linear-gradient(135deg, #eef2ff, #e0f2fe) !important;
    color: #0f172a !important;
    border-radius: 12px !important;
    border: 1px solid #e5e7eb !important;
    box-shadow: 0 4px 8px rgba(15, 23, 42, 0.06) !important;
}

button[aria-label*="|"]:hover {
    background: linear-gradient(135deg, #e0e7ff, #bfdbfe) !important;
}

/* 退出登录按钮 */
.st-key-sidebar_logout_button button {
    background: linear-gradient(135deg, #3b82f6, #1d4ed8) !important;
    color: #f9fafb !important;
    border: none !important;
    box-shadow: 0 10px 22px rgba(37, 99, 235, 0.45) !important;
}

.st-key-sidebar_logout_button button:hover {
    filter: brightness(1.07) !important;
}

/* 新建体检报告按钮 - 卡片样式优化 */
div.stButton > button.st-key-welcome_new_session,
div[data-testid="stButton"] > button[kind="secondary"] {
    /* 这是一个通用回退，但我们主要针对特定key */
}

.st-key-welcome_new_session button,
.st-key-sidebar_new_session button {
    background: #f5f3ff !important;
    color: #111827 !important;
    border: 1px solid #ddd6fe !important;
    border-radius: 18px !important;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06) !important;
    padding: 1.5rem 1rem !important;
    height: auto !important;
    transition: all 0.2s ease !important;
    display: flex !important;
    flex-direction: column !important;
    align-items: center !important;
    justify-content: center !important;
    gap: 0.5rem !important;
    width: 100% !important;
}

/* 主页新建体检报告按钮整体容器宽度与上方卡片对齐 */
.st-key-welcome_new_session {
    max-width: 760px;
    margin: 0 auto;
    width: 100%;
}

.st-key-welcome_new_session button:hover,
.st-key-sidebar_new_session button:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05) !important;
    border-color: #8b5cf6 !important;
    background: #ede9fe !important;
}

/* 按钮文字样式调整 */
.st-key-welcome_new_session button p,
.st-key-sidebar_new_session button p {
    font-size: 1.1rem !important;
    font-weight: 600 !important;
    margin: 0 !important;
    padding: 0 !important;
    line-height: 1.2 !important;
}

/* 添加加号图标 (伪元素) */
.st-key-welcome_new_session button::before,
.st-key-sidebar_new_session button::before {
    content: "+";
    display: flex;
    align-items: center;
    justify-content: center;
    width: 36px;
    height: 36px;
    background: linear-gradient(135deg, #3b82f6, #2563eb);
    color: white;
    border-radius: 50%;
    font-size: 1.75rem;
    font-weight: 300;
    margin-bottom: 0.25rem;
    box-shadow: 0 4px 6px rgba(59, 130, 246, 0.3);
}

/* 主页按钮添加描述文本 */
.st-key-welcome_new_session button::after {
    content: "开启新的体检结果分析";
    font-size: 0.9rem;
    color: #64748b;
    font-weight: 400;
    margin-top: 0.25rem;
}

/* 侧边栏按钮微调 - 更加紧凑 */
.st-key-sidebar_new_session button {
    padding: 1rem 0.5rem !important;
    border-radius: 12px !important;
}

.st-key-sidebar_new_session button::before {
    width: 28px;
    height: 28px;
    font-size: 1.4rem;
    margin-bottom: 0.15rem;
}

.st-key-sidebar_new_session button p {
    font-size: 1rem !important;
}

[data-testid="stForm"] .stButton > button[data-baseweb="button"] {
    background: linear-gradient(135deg, #6366f1, #4338ca) !important;
    border: none !important;
    box-shadow: 0 14px 30px rgba(67, 56, 202, 0.28) !important;
    color: #ffffff !important;
}

[data-testid="stForm"] .stButton > button[data-baseweb="button"]:hover {
    filter: brightness(1.06);
}

[data-testid="stFormSubmitButton"] button,
[data-testid="stForm"] button[kind="primary"] {
    background: linear-gradient(135deg, #4f46e5, #6366f1) !important;
    border: none !important;
    box-shadow: 0 12px 24px rgba(79, 70, 229, 0.32) !important;
    color: #ffffff !important;
}

[data-testid="stFormSubmitButton"] button:hover,
[data-testid="stForm"] button[kind="primary"]:hover {
    filter: brightness(1.07) !important;
}

/* 生成 PDF 按钮 */
.st-key-download_report_pdf button {
    background: linear-gradient(135deg, #0ea5e9, #14b8a6) !important;
    border: none !important;
    color: #ffffff !important;
    box-shadow: 0 12px 24px rgba(14, 165, 233, 0.35) !important;
}

.st-key-download_report_pdf button:hover {
    filter: brightness(1.07) !important;
}

[data-testid="stFileUploader"] {
    padding: 0;
    background: transparent;
    border-radius: 0;
    box-shadow: none;
    border: none;
    margin: 0 auto 0.25rem;
    max-width: 720px;
    width: 100%;
}

[data-testid="stFileUploader"] button {
    display: none !important;
}

[data-testid="stFileUploaderDropzone"] {
    border: 2px dashed #9cc8ff;
    background: linear-gradient(135deg, rgba(239, 246, 255, 0.95), rgba(237, 233, 254, 0.95));
    border-radius: 18px;
    padding: 1.5rem 2.25rem;
    box-shadow: inset 0 0 0 rgba(0,0,0,0);
    width: 100%;
    min-height: 110px;
    height: auto;
    margin: 0 auto;
    position: relative;
}

[data-testid="stFileUploaderDropzone"] span,
[data-testid="stFileUploaderDropzone"] small {
    visibility: hidden;
}

[data-testid="stFileUploaderDropzone"]::before {
    content: "拖拽或点击上传体检结果 PDF 文件";
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -60%);
    font-weight: 700;
    font-size: 1.15rem;
    color: #1f2a37;
    white-space: nowrap;
}

[data-testid="stFileUploaderDropzone"]::after {
    content: "仅支持 PDF · 单文件最大 20MB";
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, 30%);
    font-size: 0.95rem;
    color: #64748b;
}

[data-testid="stCaptionContainer"] {
    text-align: center;
    color: #6b7280;
}

.auth-hero {
    text-align: center;
    margin-bottom: 1.5rem;
    display: flex;
    flex-direction: column;
    align-items: center;
}

.auth-shell {
    padding-top: 2rem;
    padding-bottom: 2rem;
}

.auth-hero__eyebrow {
    font-size: 0.95rem;
    letter-spacing: 0.15rem;
    text-transform: uppercase;
    color: #818cf8;
    font-weight: 600;
    margin: 0 auto 0.75rem;
    display: inline-block;
    text-align: center;
}

.auth-hero__title {
    margin: 0;
    font-size: 4.2rem;
    font-weight: 800;
    background: linear-gradient(120deg, #0ea5e9, #6366f1);
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
    text-align: center;
}

.auth-hero__desc {
    color: #4b5563;
    font-size: 1.05rem;
    line-height: 1.8;
    margin: 0.75rem auto 0;
    max-width: 520px;
    text-align: center !important;
    display: block;
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
    padding: 1.8rem 3rem 2.4rem 3rem;
    margin: 0 auto 0;
    box-shadow: 0 20px 50px rgba(15, 23, 42, 0.06);
    text-align: center;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    max-width: 760px;
    width: 100%;
}

.upload-hero__title {
    font-size: 2.1rem !important;
    font-weight: 700;
    color: #1f2a37;
    margin: 0 0 0.6rem;
}

.upload-hero__desc {
    color: #556177;
    margin: 0 0 1rem;
    font-size: 1.4rem;
    text-align: center;
}

.upload-hero__tags {
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
    justify-content: center;
    margin-top: 0.75rem;
}

.upload-hero__tags span {
    background: #fff;
    border-radius: 999px;
    border: 1px solid rgba(58, 123, 213, 0.2);
    color: #3a7bd5;
    font-size: 1.05rem;
    padding: 0.35rem 0.95rem;
    font-weight: 500;
}

.upload-steps {
    display: flex;
    gap: 0.8rem;
    margin: 1.6rem auto 1.6rem;
    justify-content: center;
    max-width: 760px;
    width: 100%;
}

.upload-steps__item {
    flex: 1;
    background: #fff;
    border-radius: 18px;
    border: 1px solid #e3ecff;
    padding: 1.35rem 1.7rem;
    box-shadow: 0 16px 42px rgba(15, 23, 42, 0.05);
    text-align: center;
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
    margin: 0 auto 0.5rem;
}

.upload-steps__item strong {
    display: block;
    margin-bottom: 0.2rem;
    color: #1f2a37;
    text-align: center;
}

.upload-steps__item span {
    color: #6b7280;
    font-size: 0.85rem;
    text-align: center;
}

.session-date {
    font-weight: 700;
    color: #475569;
    margin: 0.75rem 0 0.35rem;
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

.stAlertContainer {
    display: flex;
    align-items: center;
}
</style>
"""

def apply_custom_theme():
    """注入全局浅蓝+白色主题样式"""
    st.markdown(CUSTOM_THEME, unsafe_allow_html=True)

# 辅助函数：显示欢迎界面
def show_welcome_screen():
    st.markdown(
        """
        <div class='auth-shell welcome-hero'>
            <div class='upload-hero'>
                <p class='upload-hero__title'>✨ 智能体检报告助手</p>
                <p class='upload-hero__desc'>上传体检结果 PDF 文件，自动提取关键指标并生成结构化体检诊断。</p>
                <div class='upload-hero__tags'>
                    <span>AI 诊断</span>
                    <span>PDF 文件解析</span>
                    <span>隐私安全</span>
                </div>
            </div>
            <div class='upload-steps'>
                <div class='upload-steps__item'>
                    <div class='upload-steps__icon'>1</div>
                    <strong>上传体检结果</strong>
                    <span>上传体检结果，拖拽或点击导入 PDF 文件。</span>
                </div>
                <div class='upload-steps__item'>
                    <div class='upload-steps__icon'>2</div>
                    <strong>AI 智能解析</strong>
                    <span>模型提取关键信息并理解指标含义。</span>
                </div>
                <div class='upload-steps__item'>
                    <div class='upload-steps__icon'>3</div>
                    <strong>生成诊断结论</strong>
                    <span>输出结构化诊断建议，可下载与分享。</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<div style='height: 0rem'></div>", unsafe_allow_html=True)

    if st.button("新建体检报告", use_container_width=True, key="welcome_new_session"):
        success, session = SessionManager.create_chat_session()
        if success:
            st.session_state.current_session = session
            # 新建体检报告时清空旧的生成报告内容，避免下拉框提前出现
            st.session_state.generated_report = None
            # 同时重置测试报告使用状态和上传缓存
            st.session_state.use_sample_report = False
            st.session_state.pop("uploaded_text", None)
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

    generated_report = st.session_state.get("generated_report")

    for message in messages:
        role = message.get('role', 'assistant')
        content = message.get('content', '')

        # 避免在聊天记录中再次渲染已经通过下拉框展示的生成报告内容
        if generated_report and role == 'assistant' and content == generated_report:
            continue

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