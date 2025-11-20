import streamlit as st
from services.ai_service import generate_analysis
from config.prompts import SPECIALIST_PROMPTS
from utils.pdf_extractor import extract_text_from_pdf
from config.sample_data import SAMPLE_REPORT
from config.app_config import MAX_UPLOAD_SIZE_MB
from utils.pdf_exporter import create_analysis_pdf
import re

REPORT_CONTENT_MD = """
### 体检报告
| 项目 | 内容 |
| --- | --- |
| 体检报告 | 个人信息 |
| 姓名 | 张伟 |
| 年龄 | 55 |
| 性别 | 男 |
| 体检编号 | MN-20230915143000-001 |

#### 🧍 一般检查
| 项目 | 检测结果 | 单位 | 说明 |
| --- | --- | --- | --- |
| 体重 | 85 | kg |  |
| BMI | 29.4 | kg/m² | 超重 |
| 血压 | 155/95 | mmHg | 高血压 |

#### 🩸 血液检查 · 血常规
| 项目 | 检测结果 | 单位 | 说明 |
| --- | --- | --- | --- |
| 血红蛋白 | 110 | g/L | 贫血 |
| 白细胞 | 11.5 | x10^9/L | 白细胞增多 |
| 血小板 | 120 | x10^9/L | 正常 |

#### 🩸 肝功能
| 项目 | 检测结果 | 单位 | 说明 |
| --- | --- | --- | --- |
| ALT | 85 | U/L | 肝细胞损伤 |
| AST | 60 | U/L | 肝细胞损伤 |

#### 🩸 肾功能
| 项目 | 检测结果 | 单位 | 说明 |
| --- | --- | --- | --- |
| 肌酐 | 115 | umol/L | 肾功能减退 |
| 尿酸 | 580 | umol/L | 高尿酸血症 |

#### 🩸 代谢指标
| 项目 | 检测结果 | 单位 | 说明 |
| --- | --- | --- | --- |
| 总胆固醇 | 7.2 | mmol/L | 高胆固醇 |
| 空腹血糖 | 8.9 | mmol/L | 糖尿病或血糖控制不良 |

#### 🚽 尿液检查
| 项目 | 检测结果 | 单位 | 说明 |
| --- | --- | --- | --- |
| 尿蛋白 | + | — | 肾小球损伤可能 |

#### 🖥️ 影像学检查
| 项目 | 描述 | 说明 |
| --- | --- | --- |
| 肝脏 | 回声密集增强 | 脂肪肝或肝纤维化可能 |
| 胆囊 | 胆囊壁毛糙 | 胆囊炎可能 |
| 前列腺 | 体积增大 | 前列腺增生 |

#### ❤️ 心电图检查
| 项目 | 描述 | 说明 |
| --- | --- | --- |
| 心电图 | ST段压低 0.1mV | 心肌缺血可能 |

### 异常指标总结
| 系统/器官 | 异常指标及方向 |
| --- | --- |
| 一般检查 | BMI超重，血压升高 |
| 血液检查 | 血红蛋白降低，白细胞增多，ALT和AST升高，肌酐升高，尿酸升高，总胆固醇升高，空腹血糖升高 |
| 尿液检查 | 尿蛋白阳性 |
| 影像学检查 | 肝脏回声密集增强，胆囊壁毛糙，前列腺体积增大 |
| 心电图检查 | ST段压低 |

### 建议
| 维度 | 建议内容 |
| --- | --- |
| 饮食 | 低盐低脂饮食，控制糖摄入，增加蔬菜水果摄入 |
| 运动 | 定期进行有氧运动，如快走、游泳、骑自行车等 |
| 睡眠 | 保证7-8小时的良好睡眠 |
| 心理 | 进行压力管理，必要时寻求心理咨询 |
| 预防 | 定期监测血压、血糖、血脂，预防心血管疾病 |
| 定期体检 | 每6个月进行一次全面体检 |
| 医疗咨询 | 咨询心血管、内分泌科医生关于高血压、糖尿病的管理 |

### ⚠️ 免责声明
此分析由人工智能生成，不应被视为专业医疗建议的替代品。请咨询医疗保健提供者以获取正确的医疗诊断和治疗。
"""

def show_analysis_form():
    """显示分析表单和报告上传器"""
    # 使用列布局使上传和分析区域居中
    left_col, center_col, right_col = st.columns([1, 3.5, 1])
    with center_col:
        selected_report = st.session_state.get("current_report_option", "我的体检报告")
        st.session_state.current_report_option = selected_report

        pdf_contents = get_report_contents()

        # 如果有报告内容，则渲染患者表单
        if pdf_contents:
            render_patient_form(pdf_contents)

def get_report_contents():
    """根据报告来源获取报告内容"""
    # 为每个会话使用单独的上传控件 key，避免新建体检报告时沿用上一次上传的文件
    current_session = st.session_state.get("current_session")
    if isinstance(current_session, dict) and current_session.get("id"):
        base_uploader_key = f"pdf_uploader_{current_session['id']}"
    else:
        base_uploader_key = "pdf_uploader"

    # 使用一个重置计数器拼接到 key 上，点击“删除”时只需增加计数即可重建上传控件
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

    # 当用户上传真实 PDF 后，即使之前点了“使用-测试-体检结果”，也自动切回 PDF 模式
    use_sample = st.session_state.use_sample_report
    if uploaded_file is not None:
        use_sample = False
        st.session_state.use_sample_report = False

    expander_label = "测试-体检结果-内容提取" if use_sample else "PDF-体检结果-内容提取"
    expander_container = st.expander(expander_label)

    if use_sample:
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
    render_generated_report()

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
        st.session_state.generated_report = content
        st.session_state.auth_service.save_chat_message(
            st.session_state.current_session['id'],
            content,
            role='assistant'
        )
        exam_no, patient_name = _extract_exam_meta(pdf_contents)
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
        # 如果分析失败，则显示错误信息
        st.error(result["error"])
        st.stop()

def render_generated_report():
    report_text = st.session_state.get("generated_report")
    if not report_text:
        return
    with st.expander("体检报告-内容提取", expanded=True):
        centered_html = _center_report_title(report_text)
        st.markdown(centered_html, unsafe_allow_html=True)
        pdf_bytes = create_analysis_pdf(report_text)
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
    m = re.search(r"体检编号\s*[:：]?\s*([^\s|，,]+)", text)
    if m:
        exam_no = m.group(1).strip()
    m = re.search(r"姓名\s*[:：]?\s*([^\s|，,]+)", text)
    if m:
        name = m.group(1).strip()
    return exam_no, name
