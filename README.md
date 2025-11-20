# mn-health-insight-ai 智能体检报告助手

基于 **Streamlit + Supabase + Groq LLM** 打造的智能体检报告分析工具。  
支持上传体检结果 PDF / 使用示例报告，自动提取关键指标并生成结构化、可下载的中文体检分析报告。

---

## ✨ 功能特点

- **PDF 体检报告上传与解析**
  - 支持上传单个 PDF 文件（默认限制 20MB）
  - 自动抽取文本内容并在页面中展开查看
- **示例体检报告一键体验**
  - 内置测试体检报告，无需真实 PDF 也可体验完整流程
- **AI 智能分析**
  - 使用 Groq 模型（Llama 系列）对体检报告进行结构化解读
  - 输出包含：
    - 关键指标总结  
    - 异常项目说明  
    - 生活方式 / 饮食 /运动建议  
    - 风险提醒与随访建议
- **多会话管理**
  - 每次分析会生成一个独立“体检报告会话”
  - 侧边栏支持：
    - 历史会话列表  
    - 按日期筛选  
    - 按是否已生成报告折叠分组  
    - 单选 / 多选 / 批量删除
- **生成报告下载**
  - 支持将 AI 分析结果导出为 PDF 文件
- **登录与会话持久化**
  - 用户注册 / 登录
  - 会话与消息持久化存储在 Supabase
  - 浏览器本地存储配合 Supabase 会话，支持自动恢复登录状态
- **中文界面与详细中文注释**
  - 核心代码文件（[main.py](cci:7://file:///e:/PythonProjects/GitHub/AI-Agent/hia/src/main.py:0:0-0:0)、[analysis_form.py](cci:7://file:///e:/PythonProjects/GitHub/AI-Agent/hia/src/components/analysis_form.py:0:0-0:0)、[sidebar.py](cci:7://file:///e:/PythonProjects/GitHub/AI-Agent/hia/src/components/sidebar.py:0:0-0:0)、[auth_service.py](cci:7://file:///e:/PythonProjects/GitHub/AI-Agent/hia/src/auth/auth_service.py:0:0-0:0)、[session_manager.py](cci:7://file:///e:/PythonProjects/GitHub/AI-Agent/hia/src/auth/session_manager.py:0:0-0:0)）提供了详细的中文注释，方便二次开发与维护

---

## 🧱 技术栈

- 前端 & 应用框架：**[Streamlit](https://streamlit.io/)**
- 鉴权与数据存储：**[Supabase](https://supabase.com/)**
  - 用户表：`users`
  - 会话表：`chat_sessions`
  - 消息表：`chat_messages`
- 大模型调用：**[Groq](https://groq.com/)**（Llama 系列模型）
- 部署环境：支持本地运行，亦可部署到 Streamlit Community / 自行托管

---

## 📂 目录结构（关键部分）

```bash
hia/
├─ src/
│  ├─ main.py                # Streamlit 应用入口，主题、路由与主界面逻辑
│  ├─ agents/
│  │   ├─ model_manager.py   # 模型管理与 Groq API 调用
│  │   └─ analysis_agent.py  # 报告分析代理封装
│  ├─ auth/
│  │   ├─ auth_service.py    # 与 Supabase 的认证 / 会话 / 消息交互
│  │   └─ session_manager.py # Streamlit 会话状态管理、登录态持久化
│  ├─ components/
│  │   ├─ analysis_form.py   # PDF 上传、示例报告切换、生成报告按钮与展示
│  │   ├─ sidebar.py         # 历史会话列表、日期筛选、批量删除
│  │   ├─ auth_pages.py      # 登录/注册界面
│  │   ├─ header.py          # 顶部欢迎信息
│  │   └─ footer.py          # 底部版权信息
│  ├─ config/
│  │   ├─ app_config.py      # 应用基础配置（上传大小、会话超时等）
│  │   ├─ prompts.py         # 分析用系统提示词
│  │   └─ sample_data.py     # 示例体检报告文本
│  ├─ services/
│  │   └─ ai_service.py      # 分析服务入口，封装 AnalysisAgent 调用
│  └─ utils/
│      ├─ pdf_extractor.py   # PDF 文本抽取
│      └─ pdf_exporter.py    # 将分析结果导出为 PDF
└─ public/
   └─ db/
      └─ script.sql          # Supabase 表结构（users / chat_sessions / chat_messages）
```

---

## ⚙️ 环境准备

### 1. 克隆项目

```bash
git clone <your-repo-url>
cd hia
```

### 2. 创建虚拟环境并安装依赖

建议使用 Python 3.10+。

```bash
python -m venv .venv
.\.venv\Scripts\activate   # Windows PowerShell
# 或 source .venv/bin/activate  # macOS / Linux

pip install -r requirements.txt
```

（如果仓库中还没有 `requirements.txt`，可以根据当前环境通过 `pip freeze > requirements.txt` 生成一份。）

### 3. 配置环境变量 / secrets

在项目根目录 **创建 `.streamlit/secrets.toml` 文件**，填入 Supabase 与 Groq 的密钥（示例）：

```toml
SUPABASE_URL = "https://xxx.supabase.co"
SUPABASE_KEY = "your-supabase-service-role-or-anon-key"

GROQ_API_KEY = "your-groq-api-key"
```

> ⚠️ 不要将真实密钥提交到 Git 仓库。  
> 建议在本地手动创建 `.streamlit/secrets.toml`，并在 `.gitignore` 中忽略。

### 4. 初始化 Supabase 数据库

使用 `public/db/script.sql` 中的建表脚本在 Supabase SQL 编辑器中执行，创建：

- `users`
- `chat_sessions`
- `chat_messages`

三张表及其外键关系。

---

## 🚀 启动应用

在项目根目录执行：

```bash
streamlit run src/main.py
```

启动成功后，浏览器访问：

- 默认：http://localhost:8501

---

## 💡 使用指南

1. **登录 / 注册**
   - 首次进入显示登录/注册界面
   - 完成注册后即可登录并使用体检助手

2. **创建新体检报告会话**
   - 点击首页或侧边栏中的「新建体检报告」
   - 页面右侧将进入上传与分析界面

3. **上传体检报告**
   - 在「PDF 体检结果-内容提取」折叠面板中上传 PDF 文件
   - 或点击「使用-测试-体检结果」快速加载示例报告

4. **生成 AI 分析**
   - 确认原始报告文本无误后，点击「生成体检报告」
   - 等待 AI 返回结构化分析（包括指标说明与建议）

5. **查看与导出**
   - 生成完成后会在页面中显示「体检报告-内容提取」折叠面板
   - 可点击「生成 PDF」下载分析结果

6. **历史会话管理**
   - 侧边栏展示历史体检报告列表
   - 支持按日期筛选、分组折叠、复选框批量删除等

---

## 🔍 核心实现说明（简要）

- **会话与用户状态**
  - [SessionManager](cci:2://file:///e:/PythonProjects/GitHub/AI-Agent/hia/src/auth/session_manager.py:5:0-186:33) 通过 `st.session_state` 维护当前用户、会话、令牌等
  - 利用浏览器 `localStorage` 与 Supabase 自带 session 实现登录持久化

- **PDF 抽取与示例切换**
  - [analysis_form.get_report_contents()](cci:1://file:///e:/PythonProjects/GitHub/AI-Agent/hia/src/components/analysis_form.py:23:0-106:15) 根据当前会话 ID 生成唯一上传控件 key，避免新建会话沿用旧文件
  - 支持示例报告与上传 PDF 二选一，并在切换来源时清空旧的生成结果

- **AI 调用**
  - [ModelManager](cci:2://file:///e:/PythonProjects/GitHub/AI-Agent/hia/src/agents/model_manager.py:7:0-97:87) 封装 Groq API 的调用和模型降级逻辑
  - [AnalysisAgent](cci:2://file:///e:/PythonProjects/GitHub/AI-Agent/hia/src/agents/analysis_agent.py:3:0-43:21) 负责将报告内容和系统 Prompt 交给模型，并统一返回结构化结果

- **聊天记录与去重展示**
  - [show_chat_history()](cci:1://file:///e:/PythonProjects/GitHub/AI-Agent/hia/src/main.py:621:0-654:32) 中会根据 `generated_report` / `last_hidden_report` 过滤掉已经在折叠面板中展示过的完整报告内容，避免重复显示

---

## 🧪 本地开发建议

- 修改代码后可直接保存，Streamlit 会自动热重载
- 遇到奇怪的状态问题时，可以：
  - 清空浏览器缓存 / localStorage
  - 调用注销按钮触发 [SessionManager.clear_session_state()](cci:1://file:///e:/PythonProjects/GitHub/AI-Agent/hia/src/auth/session_manager.py:92:4-101:41)
- 建议在开发环境中使用 **独立的 Supabase 项目** 和测试 API Key

---

## 🤝 贡献

欢迎对以下方面进行改进：

- 模型提示词与输出结构优化  
- 报告可视化组件（图表、颜色标记等）  
- 更多体检报告模版支持  
- 部署脚本与 CI/CD 配置  

可以通过 Pull Request 或 Issue 的形式参与。

---

## 📜 License

根据你实际情况选择（例如）：

- MIT License  
- 或遵循原项目 License

（如你希望，我也可以按你指定的 License 模板补全此部分。）

---

## 🙋‍♂️ Author

- Maintainer: **你的名字 / Your Name**  
- Email / WeChat / 主页：自行补充

> 若本项目基于其他开源模板或示例，可以在这里附上原作者或仓库链接以示感谢。