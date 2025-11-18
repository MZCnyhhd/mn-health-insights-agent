import streamlit as st
from services.ai_service import generate_analysis
from config.prompts import SPECIALIST_PROMPTS
from utils.pdf_extractor import extract_text_from_pdf
from config.sample_data import SAMPLE_REPORT
from config.app_config import MAX_UPLOAD_SIZE_MB

def show_analysis_form():
    """显示分析表单和报告上传器"""
    # 使用列布局使上传和分析区域居中
    left_col, center_col, right_col = st.columns([1, 3.5, 1])
    with center_col:
        st.markdown(
            """
            <div class='upload-hero'>
                <p class='upload-hero__title'>✨ 智能体检报告助手</p>
                <p class='upload-hero__desc'>上传体检 PDF，自动提取关键指标并生成结构化体检诊断。</p>
                <div class='upload-hero__tags'>
                    <span>AI 诊断</span>
                    <span>PDF 解析</span>
                    <span>隐私安全</span>
                </div>
            </div>
            <div class='upload-steps'>
                <div class='upload-steps__item'>
                    <div class='upload-steps__icon'>1</div>
                    <strong>上传体检报告</strong>
                    <span>拖拽或点击导入 PDF，大小不超过 20MB。</span>
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
            """,
            unsafe_allow_html=True,
        )

        with st.container():
            st.markdown("<div class='report-device'>", unsafe_allow_html=True)
            selected_report = st.selectbox(
                "选择体检报告",
                options=["我的体检报告", "家人共享报告"],
                index=0,
                label_visibility="collapsed",
                key="report_select"
            )
            st.markdown("</div>", unsafe_allow_html=True)
            st.caption("选择对应人群的体检报告后再上传 PDF")

        st.session_state.current_report_option = selected_report

        pdf_contents = get_report_contents()

        # 如果有报告内容，则渲染患者表单
        if pdf_contents:
            render_patient_form(pdf_contents)

def get_report_contents():
    """根据报告来源获取报告内容"""
    uploaded_file = st.file_uploader(
        "上传体检结果 PDF 文件（支持拖拽或点击，单个文件最大 20MB）",
        label_visibility="visible",
        type=['pdf'],
        help=f"最大文件大小: {MAX_UPLOAD_SIZE_MB}MB。只支持包含医疗报告的 PDF 文件"
    )

    st.caption("提示：【使用测试体检结果】仅用于项目演示！")

    if 'use_sample_report' not in st.session_state:
        st.session_state.use_sample_report = False

    cols = st.columns([1, 1])
    with cols[0]:
        if st.button("使用测试体检结果", use_container_width=True):
            st.session_state.use_sample_report = True
    with cols[1]:
        if st.button("上传新文件", use_container_width=True, type="secondary"):
            st.session_state.use_sample_report = False
            st.session_state.pop('uploaded_text', None)
            st.rerun()

    selected_report = st.session_state.get("current_report_option", "我的体检报告")
    expander_label = f"{selected_report} - 体检结果" if st.session_state.use_sample_report else f"{selected_report} - 上传的体检结果"
    expander_container = st.expander(expander_label)

    if st.session_state.use_sample_report:
        with expander_container:
            st.text(SAMPLE_REPORT)
        return SAMPLE_REPORT

    if uploaded_file:
        file_size_mb = uploaded_file.size / (1024 * 1024)
        if file_size_mb > MAX_UPLOAD_SIZE_MB:
            st.error(f"文件大小 ({file_size_mb:.1f}MB) 超过 {MAX_UPLOAD_SIZE_MB}MB 的限制。")
            return None

        if uploaded_file.type != 'application/pdf':
            st.error("请上传有效的PDF文件。")
            return None

        pdf_contents = extract_text_from_pdf(uploaded_file)
        if isinstance(pdf_contents, str) and (
            pdf_contents.startswith(("File size exceeds", "Invalid file type", "Error validating")) or
            pdf_contents.startswith("The uploaded file") or
            "error" in pdf_contents.lower()
        ):
            st.error(pdf_contents)
            return None

        with expander_container:
            st.text(pdf_contents)
        return pdf_contents

    return None

def render_patient_form(pdf_contents):
    """渲染包含分析按钮的表单"""
    # 创建“分析报告”按钮
    if st.button("生成体检报告", use_container_width=True, type="primary"):
        handle_form_submission(pdf_contents)

def handle_form_submission(pdf_contents):
    """处理表单提交和分析生成"""
    # 首先检查速率限制
    can_analyze, error_msg = generate_analysis(None, None, check_only=True)
    if not can_analyze:
        st.error(error_msg)
        st.stop()
        return

    # 生成分析
    with st.spinner("正在生成体检报告，请稍候..."):
        result = generate_analysis({
            "report": pdf_contents
        }, SPECIALIST_PROMPTS["comprehensive_analyst"])
    
    if result["success"]:
        # 如果分析成功，则保存聊天消息并重新运行应用
        content = result["content"]
        st.session_state.auth_service.save_chat_message(
            st.session_state.current_session['id'],
            content,
            role='assistant'
        )
        st.rerun()
    else:
        # 如果分析失败，则显示错误信息
        st.error(result["error"])
        st.stop()
