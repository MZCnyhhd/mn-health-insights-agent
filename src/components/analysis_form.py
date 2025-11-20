import streamlit as st  # Streamlit 交互式界面库
from services.ai_service import generate_analysis  # 封装好的分析入口
from config.prompts import SPECIALIST_PROMPTS  # 领域专家提示词
from utils.pdf_extractor import extract_text_from_pdf  # PDF 文本抽取工具
from config.sample_data import SAMPLE_REPORT  # 示例体检报告文本
from config.app_config import MAX_UPLOAD_SIZE_MB  # 上传大小限制
from utils.pdf_exporter import create_analysis_pdf  # 导出 PDF 的工具函数
import re

def show_analysis_form():
    """显示分析表单和报告上传器"""
    # 使用列布局控制整体居中效果：中间列展示核心组件，左右列占位
    left_col, center_col, right_col = st.columns([1, 3.5, 1])
    with center_col:
        selected_report = st.session_state.get("current_report_option", "我的体检报告")
        st.session_state.current_report_option = selected_report  # 记录当前选中的报告来源，便于其他组件读取

        pdf_contents = get_report_contents()  # 根据上传/示例报告的选择返回文本内容

        # 若成功获取到报告内容，则展示患者信息输入与生成按钮
        if pdf_contents:
            render_patient_form(pdf_contents)

def get_report_contents():
    """根据报告来源获取报告内容"""
    # 为每个会话单独生成上传控件 key，避免切换会话后延用旧文件
    current_session = st.session_state.get("current_session")
    if isinstance(current_session, dict) and current_session.get("id"):
        base_uploader_key = f"pdf_uploader_{current_session['id']}"
    else:
        base_uploader_key = "pdf_uploader"

    # 上传控件还叠加一个“重置计数器”，只要计数变化，Streamlit 就会重新渲染 file_uploader
    reset_counter_key = f"{base_uploader_key}_reset"
    if reset_counter_key not in st.session_state:
        st.session_state[reset_counter_key] = 0

    uploader_key = f"{base_uploader_key}_{st.session_state[reset_counter_key]}"

    uploaded_file = st.file_uploader(
        "",
        label_visibility="hidden",
        type=['pdf'],
        key=uploader_key,
    )

    # 维护“是否使用测试报告”开关，默认与真实 PDF 二选一
    if 'use_sample_report' not in st.session_state:
        st.session_state.use_sample_report = False

    cols = st.columns([1, 1])
    with cols[0]:
        if st.button("使用-测试-体检结果", use_container_width=True, key="use_sample_report_button"):
            st.session_state.use_sample_report = True
    with cols[1]:
        if st.button("删除-测试-体检结果", use_container_width=True, type="secondary", key="clear_sample_report_button"):
            st.session_state.use_sample_report = False
            st.session_state.pop('uploaded_text', None)

    # 上传真实 PDF 时强制关闭示例模式，确保展示的是最新上传文件
    use_sample = st.session_state.use_sample_report
    if uploaded_file is not None:
        use_sample = False
        st.session_state.use_sample_report = False

    # current_source 标记当前使用的数据来源，便于监测切换动作
    current_source = "sample" if use_sample else ("pdf" if uploaded_file is not None else None)
    previous_source = st.session_state.get("current_report_source")
    if current_source and previous_source and current_source != previous_source:
        st.session_state.generated_report = None  # 切换来源时清空旧的生成结果，避免界面残留
    st.session_state.current_report_source = current_source

    expander_label = "测试-体检结果-内容提取" if use_sample else "PDF-体检结果-内容提取"
    expander_container = st.expander(expander_label)  # 使用折叠面板展示原始文本，避免侵占过多空间

    if use_sample:
        with expander_container:
            st.text(SAMPLE_REPORT)  # 直接展示示例文本
        return SAMPLE_REPORT

    if uploaded_file:
        file_size_mb = uploaded_file.size / (1024 * 1024)
        # 双重校验文件体积与 MIME 类型，避免无效文件导致后续解析失败
        if file_size_mb > MAX_UPLOAD_SIZE_MB:
            st.error(f"文件大小 ({file_size_mb:.1f}MB) 超过 {MAX_UPLOAD_SIZE_MB}MB 的限制。")
            return None

        if uploaded_file.type != 'application/pdf':
            st.error("请上传有效的PDF文件。")
            return None

        pdf_contents = extract_text_from_pdf(uploaded_file)
        # PDF 抽取器可能返回错误消息字符串，这里做统一处理
        if isinstance(pdf_contents, str) and (
            pdf_contents.startswith(("File size exceeds", "Invalid file type", "Error validating")) or
            pdf_contents.startswith("The uploaded file") or
            "error" in pdf_contents.lower()
        ):
            st.error(pdf_contents)
            return None

        with expander_container:
            st.text(pdf_contents)  # 上传文件解析成功后展示原文，方便人工核对

        return pdf_contents

    return None

def render_patient_form(pdf_contents):
    """渲染包含分析按钮的表单"""
    # “生成体检报告”作为唯一操作入口，确保用户明确触发
    if st.button("生成体检报告", use_container_width=True, type="primary"):
        handle_form_submission(pdf_contents)
    render_generated_report()  # 无论是否刚生成成功，都尝试渲染已有的生成结果

def handle_form_submission(pdf_contents):
    """处理表单提交和分析生成"""
    # 先执行速率限制检查，避免触发昂贵的模型调用
    can_analyze, error_msg = generate_analysis(None, None, check_only=True)
    if not can_analyze:
        st.error(error_msg)
        st.stop()
        return

    # 包裹在 spinner 中突出“后台处理中”状态
    with st.spinner("正在生成体检报告，请稍候..."):
        result = generate_analysis({
            "report": pdf_contents
        }, SPECIALIST_PROMPTS["comprehensive_analyst"])
    
    if result["success"]:
        # 如果分析成功，则保存到本地状态并写入数据库，确保刷新后仍可查看
        content = result["content"]
        st.session_state.generated_report = content
        st.session_state.last_hidden_report = content
        st.session_state.auth_service.save_chat_message(
            st.session_state.current_session['id'],
            content,
            role='assistant'
        )
        exam_no, patient_name = _extract_exam_meta(pdf_contents)  # 从原始文本里提取元信息，更新会话标题
        if (exam_no or patient_name) and 'auth_service' in st.session_state and st.session_state.get('current_session'):
            parts = []
            if exam_no:
                parts.append(exam_no)
            if patient_name:
                parts.append(patient_name)
            new_title = " | ".join(parts)
            update_ok = st.session_state.auth_service.update_session_title(
                st.session_state.current_session['id'],
                new_title,
            )
            if update_ok and isinstance(st.session_state.current_session, dict):
                st.session_state.current_session['title'] = new_title
        st.rerun()
    else:
        # 调用模型失败时及时反馈，将错误信息展示给用户
        st.error(result["error"])
        st.stop()

def render_generated_report():
    report_text = st.session_state.get("generated_report")
    if not report_text:
        return
    with st.expander("体检报告-内容提取", expanded=True):
        centered_html = _center_report_title(report_text)  # 调整标题对齐，提升阅读体验
        st.markdown(centered_html, unsafe_allow_html=True)
        pdf_bytes = create_analysis_pdf(report_text)  # 生成可下载的 PDF 文件流
        st.download_button(
            "生成 PDF",
            data=pdf_bytes,
            file_name="体检报告-内容提取.pdf",
            mime="application/pdf",
            use_container_width=True,
            key="download_report_pdf",
        )

def _center_report_title(report_text: str) -> str:
    """将首行包含“体检报告”的标题居中显示，仅影响前端展示"""
    lines = report_text.splitlines()
    first_idx = None
    for i, line in enumerate(lines):
        if line.strip():
            first_idx = i
            break
    if first_idx is None:
        return report_text

    first_line = lines[first_idx]
    stripped_title = first_line.lstrip("#").strip()
    if "体检报告" not in stripped_title:
        return report_text

    lines[first_idx] = f"<h2 style='text-align:center'>{stripped_title}</h2>"
    return "\n".join(lines)


def _extract_exam_meta(text: str):
    exam_no = None
    name = None
    if not isinstance(text, str):
        return None, None
    # 通过简单正则匹配“体检编号/姓名”字段，为侧边栏标题提供更具可读性的内容
    m = re.search(r"体检编号\s*[:：]?\s*([^\s|，,]+)", text)
    if m:
        exam_no = m.group(1).strip()
    m = re.search(r"姓名\s*[:：]?\s*([^\s|，,]+)", text)
    if m:
        name = m.group(1).strip()
    return exam_no, name
