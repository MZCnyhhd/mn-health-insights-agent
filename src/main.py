import streamlit as st  # 导入 Streamlit 库，用于构建 Web 应用界面，并简写为 st
from auth.session_manager import SessionManager  # 从自定义模块导入会话管理工具，用于处理登录状态等
from components.auth_pages import show_login_page  # 导入登录/注册页面渲染函数
from components.sidebar import show_sidebar  # 导入侧边栏渲染函数
from components.analysis_form import show_analysis_form  # 导入体检报告分析表单组件
from components.footer import show_footer  # 导入页脚显示函数
from config.app_config import APP_NAME, APP_DESCRIPTION  # 导入应用名称和描述配置
from utils.pdf_exporter import create_analysis_pdf  # 导入工具函数，用于将分析结果导出为 PDF

# 必须是第一个Streamlit命令
st.set_page_config(  # 配置 Streamlit 页面基本属性（标题、布局等）
	page_title="美年-健康洞察代理 AI智能助手",  # 设置浏览器标签页显示的标题
	layout="wide"  # 设置页面布局为宽屏模式，充分利用横向空间
)

# 初始化会话状态
SessionManager.init_session()  # 调用会话管理器，初始化或恢复用户会话状态


def show_welcome_screen():  # 定义函数，用于在没有当前会话时显示欢迎界面
	"""显示欢迎界面"""  # 函数文档：说明该函数用于渲染欢迎页
	st.markdown(  # 显示应用的名称和描述，这里使用 HTML 居中显示标题
		f"""
		<div style='text-align: center; padding: 50px;'>
			<h1>{APP_NAME}</h1>
		</div>
		""",
		unsafe_allow_html=True  # 允许渲染 HTML 字符串，而不仅是纯 Markdown
	)
	
	# 创建列布局以居中按钮
	col1, col2, col3 = st.columns([2, 3, 2])  # 创建三列布局，中间列更宽，用来放置按钮并实现居中
	with col2:  # 只在第二列（中间列）中放内容
		# 创建“创建体检报告”按钮
		if st.button("➕ 创建体检报告", use_container_width=True, type="primary"):  # 创建一个主按钮，点击后创建新会话
			# 创建新的聊天会话
			success, session = SessionManager.create_chat_session()  # 向后端请求创建一条新的体检报告会话记录
			if success:  # 如果创建成功
				# 如果成功，则设置当前会话并重新运行应用
				st.session_state.current_session = session  # 将新建会话保存到会话状态中，作为当前会话
				st.rerun()  # 重新运行应用，使页面根据新会话重新渲染
			else:
				# 如果失败，则显示错误信息
				st.error("创建会话失败")  # 在页面上展示错误提示


def show_chat_history():  # 定义函数，用于显示当前会话中的聊天记录和报告内容
	"""显示聊天记录"""  # 函数文档：说明该函数的用途是渲染聊天历史
	# 获取当前会话的消息
	success, messages = st.session_state.auth_service.get_session_messages(  # 向后端请求当前会话的所有消息
		st.session_state.current_session['id']  # 传入当前会话的 ID
	)
	
	last_assistant_content = None  # 用于记录最后一条助手回复内容
	report_content = None  # 用于记录包含完整体检报告的那条消息内容

	# 使用列布局使内容区域居中
	left_col, center_col, right_col = st.columns([1, 2, 1])  # 三列布局，中间列更宽，用来显示聊天内容
	with center_col:  # 在中间列中渲染聊天记录
		if success:  # 如果消息获取成功
			# 遍历并显示消息
			for msg in messages:  # 遍历当前会话的每一条消息
				if msg['role'] == 'assistant':  # 只渲染助手（AI）发出的消息
					content = msg['content']  # 取出消息文本内容
					# 将包含体检报告的主要报告放入下拉框中
					if "### 体检报告" in content:  # 如果该消息包含完整体检报告标题
						with st.expander("体检报告", expanded=True):  # 使用可折叠面板展示报告内容，默认展开
							# 仅在展示时将主标题居中，避免影响原始内容
							display_content = content.replace(  # 在显示时把 Markdown 标题替换为居中的加粗 HTML 标题
								"### 体检报告",  # 原始 Markdown 标题
								"<div style='text-align: center; font-size: 24px; font-weight: bold;'>体检报告</div>",  # 居中加粗的 HTML 标题
								1  # 只替换第一次出现，避免误伤其他内容
							)
							st.markdown(display_content, unsafe_allow_html=True)  # 渲染替换后的内容，允许 HTML
						report_content = content  # 记录原始报告内容，用于生成 PDF
					else:
						st.markdown(content)  # 对非报告类消息，直接用 Markdown 渲染显示
					last_assistant_content = content  # 记录最后一条助手回复内容

		# 在最新报告下方添加生成 PDF 按钮（如果包含免责声明段落）
		target_content = report_content or last_assistant_content  # 优先使用完整报告内容，其次使用最后一条助手回复
		if target_content and "### ⚠️ 免责声明" in target_content:  # 只有包含免责声明段落的内容才提供导出 PDF
			if st.button("生成PDF", key="generate_pdf_button", use_container_width=True):  # 点击按钮后生成 PDF
				pdf_bytes = create_analysis_pdf(target_content)  # 调用工具函数，将 Markdown 报告转换为 PDF 字节流
				st.download_button(  # 在页面上渲染下载按钮
					label="点击下载PDF",  # 下载按钮文字
					data=pdf_bytes,  # 提供 PDF 二进制数据
					file_name="health_report.pdf",  # 下载文件名
					mime="application/pdf",  # 指定文件类型为 PDF
					use_container_width=True,  # 按钮宽度占满容器
					key="download_pdf_button"  # 为下载按钮指定唯一键，避免和其他按钮冲突
				)


def show_user_greeting():  # 定义函数，用于在页面顶部显示用户问候语
	"""显示用户问候语"""  # 函数文档：说明该函数用于展示问候信息
	if st.session_state.user:  # 如果当前会话中存在已登录用户信息
		# 从用户数据中获取姓名，如果姓名为空则回退到电子邮件
		display_name = st.session_state.user.get('name') or st.session_state.user.get('email', '')  # 优先显示姓名，缺失则用邮箱
		st.markdown(  # 使用 HTML + 内联样式在右上角显示欢迎语
			f"""<div style='text-align: right; padding: 1rem; color: #64B5F6; font-size: 1.1em;'>欢迎您, {display_name}</div>""",
			unsafe_allow_html=True  # 允许渲染 HTML，保证样式生效
		)


def main():  # 定义应用的主入口函数
	"""应用主函数"""  # 函数文档：应用整体逻辑从此函数开始
	# 初始化会话
	SessionManager.init_session()  # 再次确保会话已正确初始化（防御性调用）

	# 如果用户未通过身份验证，则显示登录页面
	if not SessionManager.is_authenticated():  # 如果当前用户未登录
		show_login_page()  # 渲染登录/注册界面
		show_footer()  # 在未登录页面底部显示页脚（目前为空实现，占位用）
		return  # 提前返回，不再渲染后续主界面

	# 在顶部显示用户问候语
	show_user_greeting()  # 已登录用户时，在页面右上角显示欢迎文案
	
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
	
# 如果作为主模块运行，则调用main函数
if __name__ == "__main__":  # 仅当当前文件作为脚本直接运行时才执行 main()
	main()  # 调用主函数，启动 Streamlit 应用