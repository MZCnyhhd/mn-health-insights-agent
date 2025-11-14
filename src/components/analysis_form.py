import streamlit as st
from services.ai_service import generate_analysis
from config.prompts import SPECIALIST_PROMPTS
from utils.pdf_extractor import extract_text_from_pdf
from config.sample_data import SAMPLE_REPORT
from config.app_config import MAX_UPLOAD_SIZE_MB

def show_analysis_form():
    """显示分析表单和报告上传器"""
    # 使用列布局使上传和分析区域居中
    left_col, center_col, right_col = st.columns([1, 2, 1])
    with center_col:
        # 根据要求，报告来源固定为“上传PDF”
        report_source = "Upload PDF"
        # 获取报告内容
        pdf_contents = get_report_contents(report_source)
                
        # 如果有报告内容，则渲染患者表单
        if pdf_contents:
            render_patient_form(pdf_contents)

def get_report_contents(report_source):
    """根据报告来源获取报告内容"""
    if report_source == "Upload PDF":
        # 创建文件上传器
        uploaded_file = st.file_uploader(
            "上传体检报告 PDF 文件（支持拖拽或点击，单个文件最大 20MB）",
            label_visibility="visible",
            type=['pdf'],
            help=f"最大文件大小: {MAX_UPLOAD_SIZE_MB}MB。只支持包含医疗报告的 PDF 文件"
        )
        if uploaded_file:
            # 在处理前检查文件大小
            file_size_mb = uploaded_file.size / (1024 * 1024)  # 转换为MB
            if file_size_mb > MAX_UPLOAD_SIZE_MB:
                st.error(f"文件大小 ({file_size_mb:.1f}MB) 超过 {MAX_UPLOAD_SIZE_MB}MB 的限制。")
                return None
                
            if uploaded_file.type != 'application/pdf':
                st.error("请上传有效的PDF文件。")
                return None
                
            # 从PDF中提取文本
            pdf_contents = extract_text_from_pdf(uploaded_file)
            # 检查提取过程中是否出错
            if isinstance(pdf_contents, str) and (
                pdf_contents.startswith(("File size exceeds", "Invalid file type", "Error validating")) or
                pdf_contents.startswith("The uploaded file") or
                "error" in pdf_contents.lower()
            ):
                st.error(pdf_contents)
                return None
            # 在可展开部分显示提取的报告内容
            with st.expander("报告数据"):
                st.text(pdf_contents)
            return pdf_contents
    else:
        # 显示示例报告
        with st.expander("查看示例报告"):
            st.text(SAMPLE_REPORT)
        return SAMPLE_REPORT
    return None

def render_patient_form(pdf_contents):
    """渲染包含分析按钮的表单"""
    # 创建“分析报告”按钮
    if st.button("分析报告", use_container_width=True, type="primary"):
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
