import streamlit as st  # 引入 Streamlit 以构建交互式侧边栏
from datetime import datetime  # 负责时间格式化与解析
from auth.session_manager import SessionManager  # 会话管理工具，统一处理增删查
from components.footer import show_footer  # 侧边栏底部的版权/辅助信息

def show_sidebar():
    """显示侧边栏"""
    with st.sidebar:  # 使用 Streamlit 内置 sidebar 容器确保布局贴边
        if st.button("新建体检报告", use_container_width=True, key="sidebar_new_session"):
            # 点击按钮时尝试创建新会话
            success, session = SessionManager.create_chat_session()
            if success:
                st.session_state.current_session = session  # 保存当前会话，供主区渲染
                st.session_state.generated_report = None  # 清空生成报告，避免旧数据泄露
                st.session_state.use_sample_report = False  # 回退到真实 PDF 模式
                st.session_state.pop("uploaded_text", None)  # 清除上传缓存
                st.rerun()  # 立刻刷新界面以切入新会话
            else:
                st.error("创建会话失败")  # 后端创建失败时提示用户

        st.markdown("<hr class='sidebar-section-divider' />", unsafe_allow_html=True)  # 顶部装饰分割线

        show_session_list()  # 渲染历史体检报告列表

        st.markdown(
            "<hr class='sidebar-section-divider sidebar-bottom-divider' />",
            unsafe_allow_html=True,
        )  # 下部装饰分割线

        st.markdown("<div class='sidebar-logout-wrapper'>", unsafe_allow_html=True)  # 固定底部退出区域
        if st.button("退出登录", use_container_width=True, key="sidebar_logout_button"):
            SessionManager.logout()  # 调用登出逻辑
            st.rerun()  # 刷新以回到登录页
        st.markdown("</div>", unsafe_allow_html=True)

        show_footer(in_sidebar=True)  # 侧边栏内部显示统一页脚

def show_session_list():
    """显示用户的会话列表"""
    if st.session_state.user and 'id' in st.session_state.user:  # 仅在已登录状态下才展示
        success, sessions = SessionManager.get_user_sessions()  # 向后端请求当前账号的会话
        if success:
            if sessions:
                st.markdown(
                    "<h3 class='sidebar-history-title'>历史体检报告</h3>",
                    unsafe_allow_html=True,
                )  # 标题装饰
                render_session_list(sessions)  # 渲染具体列表

                selected_sessions = st.session_state.get("selected_sessions", [])  # 已勾选的会话 ID
                if selected_sessions:  # 只有选中后才显示批量删除按钮
                    if st.button(
                        "删除勾选体检报告",
                        type="primary",
                        use_container_width=True,
                        key="delete_selected_sessions",
                    ):
                        handle_bulk_delete(selected_sessions)  # 触发批量删除
            else:
                st.markdown(
                    "<div class='sidebar-empty-state'>没有历史体检报告</div>",
                    unsafe_allow_html=True,
                )  # 空态提示文案

def render_session_list(sessions):
    """渲染按日期分组的会话列表"""
    if 'selected_sessions' not in st.session_state:
        st.session_state.selected_sessions = []  # 初始化选择集合

    normalized_selected = [
        str(sid) for sid in st.session_state.get("selected_sessions", []) if sid is not None
    ]  # 将当前选中会话统一转为字符串
    st.session_state.selected_sessions = normalized_selected
    selected_sessions = normalized_selected  # 准备在本函数内使用

    deleted_ids = set(
        str(sid) for sid in st.session_state.get("deleted_sessions", []) if sid is not None
    )  # 记录用户刚删除的会话，避免重新显示
    if deleted_ids:
        sessions = [
            s for s in sessions
            if isinstance(s, dict) and s.get('id') is not None and str(s.get('id')) not in deleted_ids
        ]  # 过滤掉“已删除但后端尚未返回”的项

    all_session_ids = [
        str(s['id'])
        for s in sessions
        if isinstance(s, dict) and s.get('id') is not None
    ]  # 计算列表中可操作的全部 ID，供全选使用
    all_selected_default = bool(all_session_ids) and len(selected_sessions) == len(all_session_ids)  # 默认全选状态

    select_all = st.checkbox(
        "选择全部",
        key="select_all_sessions",
        value=all_selected_default,
    )  # 顶部“全选”复选框，绑定固定 key 便于同步

    if select_all and not all_selected_default:
        st.session_state.selected_sessions = all_session_ids  # 勾选后写入全部 ID
        for session_id in all_session_ids:
            st.session_state[f"select_{session_id}"] = True  # 同步每个行内复选框状态
        st.rerun()  # 立即刷新以反映勾选状态
    elif not select_all and all_selected_default:
        st.session_state.selected_sessions = []  # 取消全选则清空列表
        for session_id in all_session_ids:
            st.session_state[f"select_{session_id}"] = False
        st.rerun()

    sorted_sessions = sorted(sessions, key=lambda x: x.get('created_at', ''), reverse=True)  # 按创建时间倒序

    selected_date_str = None  # 当前日期过滤条件（字符串形式）
    if sorted_sessions:
        date_labels = sorted({format_session_date(s) for s in sorted_sessions}, reverse=True)  # 预生成日期列表
        first_label = date_labels[0]
        try:
            default_date = datetime.strptime(first_label, "%Y-%m-%d")  # 尝试解析最新日期作为默认值
        except Exception:
            default_date = None

        if default_date is not None:
            selected_date = st.date_input(
                "按日期查找",
                value=default_date.date(),
                key="session_date_filter",
            )  # 日期选择器，帮助快速筛选
            selected_date_str = selected_date.strftime("%Y-%m-%d")

    def _match_date(s):
        if not selected_date_str:
            return True  # 未设置日期时不过滤
        return format_session_date(s) == selected_date_str  # 只保留匹配日期的会话

    generated_sessions = [s for s in sorted_sessions if is_generated_session(s) and _match_date(s)]  # 已生成报告
    pending_sessions = [s for s in sorted_sessions if not is_generated_session(s) and _match_date(s)]  # 待生成

    if generated_sessions:
        with st.expander("已生成体检报告", expanded=True):
            for session in generated_sessions:
                render_session_item(session)  # 展示可点击的会话卡片

    if pending_sessions:
        with st.expander("未生成体检报告", expanded=True):
            for session in pending_sessions:
                render_session_item(session)


def format_session_date(session: dict) -> str:
    timestamp = (session or {}).get('created_at') or (session or {}).get('updated_at')  # 优先读取后端时间戳
    if timestamp:
        try:
            ts = datetime.fromisoformat(str(timestamp).replace('Z', '+00:00'))  # 兼容含 Z 的 ISO 字符串
            return ts.strftime('%Y-%m-%d')  # 转换为日期字符串
        except Exception:
            pass  # 解析失败则回退到标题推断

    title = (session or {}).get('title', '')  # 标题可能包含“日期 | 时间”结构
    if isinstance(title, str):
        date_prefix = title.split('|')[0].strip()
        try:
            parsed = datetime.strptime(date_prefix, '%Y-%m-%d')
            return parsed.strftime('%Y-%m-%d')
        except Exception:
            pass

    return datetime.utcnow().strftime('%Y-%m-%d')  # 若无任何信息，则使用当前日期，保证有值


def is_generated_session(session: dict) -> bool:
    title = (session or {}).get('title', '') or ''  # 标题存储了会话状态线索
    parts = [p.strip() for p in str(title).split('|')]  # 以 "|" 拆成多个字段
    if len(parts) >= 2:
        try:
            datetime.strptime(parts[0], '%Y-%m-%d')  # 第一段若为日期
            datetime.strptime(parts[1], '%H-%M-%S')  # 第二段若为时间，视为未生成报告
            return False
        except Exception:
            return True  # 任一解析失败都认为已生成报告（标题已被改写）
    return True  # 没有两个片段也视为已生成

def render_session_item(session):
    """渲染单个会话项"""
    if not session or not isinstance(session, dict) or 'id' not in session:
        return  # 没有 ID 的异常数据直接忽略
        
    session_id_raw = session['id']
    session_id = str(session_id_raw)  # 统一为字符串方便与状态数组比较
    current_session = st.session_state.get('current_session', {})
    current_session_id = current_session.get('id') if isinstance(current_session, dict) else None  # 记录当前使用中的会话
    
    checkbox_col, title_col = st.columns([0.4, 5], gap="small")  # 左侧复选框，右侧标题按钮

    selected_sessions = st.session_state.get("selected_sessions", [])  # 引用已选集合

    with checkbox_col:
        checkbox_key = f"select_{session_id}"
        if checkbox_key not in st.session_state:
            st.session_state[checkbox_key] = session_id in selected_sessions  # 首次渲染同步状态
        checked = st.checkbox(
            "",
            key=checkbox_key,
        )  # 不显示文字，只呈现勾选框
        if checked and session_id not in selected_sessions:
            selected_sessions.append(session_id)  # 勾选则添加
        elif not checked and session_id in selected_sessions:
            selected_sessions.remove(session_id)  # 取消勾选则移除
        st.session_state.selected_sessions = selected_sessions  # 回写到全局状态

    with title_col:
        raw_title = session.get('title', '')
        display_title = raw_title.lstrip('📝 ').strip()  # 去掉装饰图标，仅保留文本

        if st.button(
            display_title,
            key=f"session_{session_id}",
            use_container_width=True,
        ):  # 点击即切换当前会话
            st.session_state.current_session = session
            st.rerun()


def handle_bulk_delete(selected_session_ids):
    """批量删除选中的会话"""
    if not selected_session_ids:
        return  # 没有选中内容直接返回

    current_session = st.session_state.get("current_session", {})
    current_session_id = current_session.get("id") if isinstance(current_session, dict) else None  # 记录当前会话 ID

    normalized_ids = [str(sid) for sid in selected_session_ids if sid is not None]
    if not normalized_ids:
        return  # 过滤后为空则无需继续

    existing_deleted = [
        str(sid) for sid in st.session_state.get("deleted_sessions", []) if sid is not None
    ]  # 取出已有的删除列表
    st.session_state.deleted_sessions = list(set(existing_deleted + normalized_ids))  # 合并并去重，实现乐观更新

    failed_errors = []  # 用于收集后端失败信息
    for session_id in normalized_ids:
        success, error = SessionManager.delete_session(session_id)
        if not success:
            failed_errors.append(error)  # 记录失败原因

    current_session_id_str = str(current_session_id) if current_session_id else None
    if current_session_id_str and current_session_id_str in normalized_ids:
        st.session_state.current_session = None  # 若当前会话被删除，则清空引用

    st.session_state.selected_sessions = []  # 操作完成后清空所有勾选

    if failed_errors:
        st.warning("部分体检报告在服务器端删除失败，请稍后重试或联系管理员。")  # 提示部分失败
    else:
        st.success("已删除选中的体检报告")  # 全部成功时给出成功反馈

    st.rerun()  # 无论成功失败都刷新列表，保持 UI 同步
