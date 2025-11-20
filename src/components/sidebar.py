import streamlit as st
from datetime import datetime
from auth.session_manager import SessionManager
from components.footer import show_footer

def show_sidebar():
    """显示侧边栏"""
    with st.sidebar:
        if st.button("新建体检报告", use_container_width=True, key="sidebar_new_session"):
            success, session = SessionManager.create_chat_session()
            if success:
                st.session_state.current_session = session
                # 新建会话时清空上一份生成报告，避免下拉框提前出现
                st.session_state.generated_report = None
                # 同时重置测试报告使用状态和上传缓存
                st.session_state.use_sample_report = False
                st.session_state.pop("uploaded_text", None)
                st.rerun()
            else:
                st.error("创建会话失败")

        # 顶部分隔线
        st.markdown("<hr class='sidebar-section-divider' />", unsafe_allow_html=True)

        # 显示会话列表
        show_session_list()

        # 底部分隔线（位于会话列表和退出按钮之间）
        st.markdown("<hr class='sidebar-section-divider sidebar-bottom-divider' />", unsafe_allow_html=True)

        # 固定在底部的退出登录区域
        st.markdown("<div class='sidebar-logout-wrapper'>", unsafe_allow_html=True)
        if st.button("退出登录", use_container_width=True, key="sidebar_logout_button"):
            SessionManager.logout()
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        show_footer(in_sidebar=True)

def show_session_list():
    """显示用户的会话列表"""
    # 检查用户是否已登录
    if st.session_state.user and 'id' in st.session_state.user:
        # 获取用户会话
        success, sessions = SessionManager.get_user_sessions()
        if success:
            if sessions:
                st.markdown("<h3 class='sidebar-history-title'>历史体检报告</h3>", unsafe_allow_html=True)
                render_session_list(sessions)  # 渲染会话列表

                selected_sessions = st.session_state.get("selected_sessions", [])
                if selected_sessions:
                    if st.button(
                        "删除勾选体检报告",
                        type="primary",
                        use_container_width=True,
                        key="delete_selected_sessions",
                    ):
                        handle_bulk_delete(selected_sessions)
            else:
                # 空状态文案，位于上下分割线之间居中显示
                st.markdown(
                    "<div class='sidebar-empty-state'>没有历史体检报告</div>",
                    unsafe_allow_html=True,
                )

def render_session_list(sessions):
    """渲染按日期分组的会话列表"""
    if 'selected_sessions' not in st.session_state:
        st.session_state.selected_sessions = []

    # 统一 selected_sessions / deleted_sessions 的 ID 类型为字符串
    normalized_selected = [
        str(sid) for sid in st.session_state.get("selected_sessions", []) if sid is not None
    ]
    st.session_state.selected_sessions = normalized_selected
    selected_sessions = normalized_selected

    deleted_ids = set(
        str(sid) for sid in st.session_state.get("deleted_sessions", []) if sid is not None
    )
    if deleted_ids:
        sessions = [
            s for s in sessions
            if isinstance(s, dict) and s.get('id') is not None and str(s.get('id')) not in deleted_ids
        ]

    # 计算所有会话 ID，用于“全选”逻辑
    all_session_ids = [
        str(s['id'])
        for s in sessions
        if isinstance(s, dict) and s.get('id') is not None
    ]
    all_selected_default = bool(all_session_ids) and len(selected_sessions) == len(all_session_ids)

    # 顶部“全选”复选框
    select_all = st.checkbox(
        "选择全部",
        key="select_all_sessions",
        value=all_selected_default,
    )

    # “全选”切换逻辑：
    # - 从未全选 -> 勾选：选中全部会话
    # - 从已全选 -> 取消勾选：清空选择
    if select_all and not all_selected_default:
        st.session_state.selected_sessions = all_session_ids
        for session_id in all_session_ids:
            st.session_state[f"select_{session_id}"] = True
        st.rerun()
    elif not select_all and all_selected_default:
        st.session_state.selected_sessions = []
        for session_id in all_session_ids:
            st.session_state[f"select_{session_id}"] = False
        st.rerun()

    sorted_sessions = sorted(sessions, key=lambda x: x.get('created_at', ''), reverse=True)

    selected_date_str = None
    if sorted_sessions:
        date_labels = sorted({format_session_date(s) for s in sorted_sessions}, reverse=True)
        first_label = date_labels[0]
        try:
            default_date = datetime.strptime(first_label, "%Y-%m-%d")
        except Exception:
            default_date = None

        if default_date is not None:
            selected_date = st.date_input(
                "按日期查找",
                value=default_date.date(),
                key="session_date_filter",
            )
            selected_date_str = selected_date.strftime("%Y-%m-%d")

    def _match_date(s):
        if not selected_date_str:
            return True
        return format_session_date(s) == selected_date_str

    generated_sessions = [s for s in sorted_sessions if is_generated_session(s) and _match_date(s)]
    pending_sessions = [s for s in sorted_sessions if not is_generated_session(s) and _match_date(s)]

    if generated_sessions:
        with st.expander("已生成体检报告", expanded=True):
            for session in generated_sessions:
                render_session_item(session)

    if pending_sessions:
        with st.expander("未生成体检报告", expanded=True):
            for session in pending_sessions:
                render_session_item(session)


def format_session_date(session: dict) -> str:
    timestamp = (session or {}).get('created_at') or (session or {}).get('updated_at')
    if timestamp:
        try:
            ts = datetime.fromisoformat(str(timestamp).replace('Z', '+00:00'))
            return ts.strftime('%Y-%m-%d')
        except Exception:
            pass

    title = (session or {}).get('title', '')
    if isinstance(title, str):
        date_prefix = title.split('|')[0].strip()
        try:
            parsed = datetime.strptime(date_prefix, '%Y-%m-%d')
            return parsed.strftime('%Y-%m-%d')
        except Exception:
            pass

    return datetime.utcnow().strftime('%Y-%m-%d')


def is_generated_session(session: dict) -> bool:
    title = (session or {}).get('title', '') or ''
    parts = [p.strip() for p in str(title).split('|')]
    if len(parts) >= 2:
        try:
            datetime.strptime(parts[0], '%Y-%m-%d')
            datetime.strptime(parts[1], '%H-%M-%S')
            return False
        except Exception:
            return True
    return True

def render_session_item(session):
    """渲染单个会话项"""
    # 检查会话数据是否有效
    if not session or not isinstance(session, dict) or 'id' not in session:
        return
        
    session_id_raw = session['id']
    session_id = str(session_id_raw)
    current_session = st.session_state.get('current_session', {})
    current_session_id = current_session.get('id') if isinstance(current_session, dict) else None
    
    checkbox_col, title_col = st.columns([0.4, 5], gap="small")

    selected_sessions = st.session_state.get("selected_sessions", [])

    with checkbox_col:
        checked = st.checkbox(
            "",
            key=f"select_{session_id}",
            value=session_id in selected_sessions,
        )
        if checked and session_id not in selected_sessions:
            selected_sessions.append(session_id)
        elif not checked and session_id in selected_sessions:
            selected_sessions.remove(session_id)
        st.session_state.selected_sessions = selected_sessions

    with title_col:
        # 去掉标题前面的图标（例如 "📝"），仅影响展示
        raw_title = session.get('title', '')
        display_title = raw_title.lstrip('📝 ').strip()

        if st.button(
            display_title,
            key=f"session_{session_id}",
            use_container_width=True,
        ):
            st.session_state.current_session = session
            st.rerun()


def handle_bulk_delete(selected_session_ids):
    """批量删除选中的会话"""
    if not selected_session_ids:
        return

    current_session = st.session_state.get("current_session", {})
    current_session_id = current_session.get("id") if isinstance(current_session, dict) else None

    normalized_ids = [str(sid) for sid in selected_session_ids if sid is not None]
    if not normalized_ids:
        return

    # 1. 前端乐观删除：先把这些会话 ID 标记为已删除，让列表立刻隐藏
    existing_deleted = [
        str(sid) for sid in st.session_state.get("deleted_sessions", []) if sid is not None
    ]
    st.session_state.deleted_sessions = list(set(existing_deleted + normalized_ids))

    # 2. 后端实际删除，尽最大努力
    failed_errors = []
    for session_id in normalized_ids:
        success, error = SessionManager.delete_session(session_id)
        if not success:
            failed_errors.append(error)

    current_session_id_str = str(current_session_id) if current_session_id else None
    if current_session_id_str and current_session_id_str in normalized_ids:
        st.session_state.current_session = None

    st.session_state.selected_sessions = []

    if failed_errors:
        # 如果后端有失败，给出警告，但不恢复前端删除状态
        st.warning("部分体检报告在服务器端删除失败，请稍后重试或联系管理员。")
    else:
        st.success("已删除选中的体检报告")

    st.rerun()
