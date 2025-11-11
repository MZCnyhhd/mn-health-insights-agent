from datetime import datetime, timedelta
import streamlit as st
from agents.model_manager import ModelManager
from config.app_config import ANALYSIS_DAILY_LIMIT

class AnalysisAgent:
    """
    负责管理报告分析、速率限制以及从先前分析中实现情境学习的代理。
    """
    
    def __init__(self):
        """初始化AnalysisAgent"""
        self.model_manager = ModelManager()  # 初始化模型管理器
        self._init_state()  # 初始化会话状态
        
    def _init_state(self):
        """初始化与分析相关的会话状态变量"""
        if 'analysis_count' not in st.session_state:
            st.session_state.analysis_count = 0  # 分析次数
        if 'last_analysis' not in st.session_state:
            st.session_state.last_analysis = datetime.now()  # 上次分析时间
        if 'analysis_limit' not in st.session_state:
            st.session_state.analysis_limit = ANALYSIS_DAILY_LIMIT  # 分析限制
        if 'models_used' not in st.session_state:
            st.session_state.models_used = {}  # 使用的模型
        if 'knowledge_base' not in st.session_state:
            st.session_state.knowledge_base = {}  # 知识库
            
    def check_rate_limit(self):
        """检查用户是否已达到其分析限制"""
        # 计算距离重置的时间
        time_until_reset = timedelta(days=1) - (datetime.now() - st.session_state.last_analysis)
        hours, remainder = divmod(time_until_reset.seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        
        # 24小时后重置计数器
        if time_until_reset.days < 0:
            st.session_state.analysis_count = 0
            st.session_state.last_analysis = datetime.now()
            return True, None
        
        # 检查是否达到限制
        if st.session_state.analysis_count >= st.session_state.analysis_limit:
            error_msg = f"已达到每日限制。重置时间还剩 {hours}小时 {minutes}分钟"
            return False, error_msg
        return True, None

    def analyze_report(self, data, system_prompt, check_only=False, chat_history=None):
        """
        使用先前分析的情境学习来分析报告数据。
        
        参数:
            data: 要分析的报告数据
            system_prompt: 基本系统提示
            check_only: 如果为True，则仅检查速率限制而不生成分析
            chat_history: 当前会话中的先前消息 (可选)
        """
        can_analyze, error_msg = self.check_rate_limit()
        if not can_analyze:
            return {"success": False, "error": error_msg}
        
        if check_only:
            return can_analyze, error_msg
        
        # 在发送到模型之前处理数据
        processed_data = self._preprocess_data(data)
        
        # 使用情境学习增强提示 (仅当提供了chat_history时)
        enhanced_prompt = self._build_enhanced_prompt(system_prompt, processed_data, chat_history) if chat_history else system_prompt
        
        # 使用模型管理器生成分析
        result = self.model_manager.generate_analysis(processed_data, enhanced_prompt)
        
        if result["success"]:
            # 更新分析和学习系统
            self._update_analytics(result)
            self._update_knowledge_base(processed_data, result["content"])
        
        return result
    
    def _update_analytics(self, result):
        """在成功分析后更新分析数据"""
        st.session_state.analysis_count += 1
        st.session_state.last_analysis = datetime.now()
        
        # 跟踪正在使用的模型
        model_used = result.get("model_used", "unknown")
        if model_used in st.session_state.models_used:
            st.session_state.models_used[model_used] += 1
        else:
            st.session_state.models_used[model_used] = 1
    
    def _update_knowledge_base(self, data, analysis):
        """
        使用新的分析结果更新知识库以进行情境学习。
        将关键健康指标映射到分析模式。
        """
        if not isinstance(data, dict) or 'report' not in data:
            return
            
        # 提取关键健康指标并将其映射到分析结果
        # 这个基本实现可以通过更复杂的提取方法进行扩展
        report_text = data['report'].lower()
        patient_profile = f"{data.get('age', '未知')}-{data.get('gender', '未知')}"
        
        # 在报告中查找关键健康指标
        key_indicators = [
            "hemoglobin", "glucose", "cholesterol", "triglycerides", 
            "hdl", "ldl", "wbc", "rbc", "platelet", "creatinine"
        ]
        
        # 存储与关键健康指标相关的分析片段
        for indicator in key_indicators:
            if indicator in report_text:
                # 在分析中查找此指标的任何提及
                if indicator in analysis.lower():
                    # 在知识库中存储此学习
                    if indicator not in st.session_state.knowledge_base:
                        st.session_state.knowledge_base[indicator] = {}
                    
                    if patient_profile not in st.session_state.knowledge_base[indicator]:
                        st.session_state.knowledge_base[indicator][patient_profile] = []
                    
                    # 从分析中提取相关部分 (简单方法)
                    lines = analysis.split('\n')
                    relevant_lines = [l for l in lines if indicator in l.lower()]
                    if relevant_lines:
                        # 限制知识库大小以防止溢出
                        if len(st.session_state.knowledge_base[indicator][patient_profile]) >= 3:
                            st.session_state.knowledge_base[indicator][patient_profile].pop(0)
                        st.session_state.knowledge_base[indicator][patient_profile].append(relevant_lines[0])
    
    def _build_enhanced_prompt(self, system_prompt, data, chat_history):
        """
        使用以下来源的情境学习构建增强提示:
        1. 先前分析的知识库
        2. 当前会话的聊天记录
        """
        enhanced_prompt = system_prompt
        
        # 从知识库中添加情境学习
        if isinstance(data, dict) and 'report' in data:
            kb_context = self._get_knowledge_base_context(data)
            if kb_context:
                enhanced_prompt += "\n\n## 先前分析的相关学习\n" + kb_context
        
        # 从聊天记录中添加会话上下文
        if chat_history:
            session_context = self._get_session_context(chat_history)
            if session_context:
                enhanced_prompt += "\n\n## 当前会话历史\n" + session_context
        
        return enhanced_prompt
    
    def _get_knowledge_base_context(self, data):
        """从知识库中提取相关上下文"""
        if 'knowledge_base' not in st.session_state or not st.session_state.knowledge_base:
            return ""
            
        report_text = data.get('report', '').lower()
        patient_profile = f"{data.get('age', '未知')}-{data.get('gender', '未知')}"
        
        context_items = []
        
        # 从先前分析中查找相关知识
        for indicator, profiles in st.session_state.knowledge_base.items():
            if indicator in report_text:
                # 首先从相似的患者资料中获取见解
                if patient_profile in profiles:
                    for insight in profiles[patient_profile]:
                        context_items.append(f"- {indicator} (相似患者资料): {insight}")
                
                # 然后获取一般见解
                for profile, insights in profiles.items():
                    if profile != patient_profile:
                        for insight in insights:
                            context_items.append(f"- {indicator} (其他患者资料): {insight}")
        
        # 限制上下文大小
        if len(context_items) > 5:
            context_items = context_items[:5]
            
        return "\n".join(context_items) if context_items else ""
    
    def _get_session_context(self, chat_history):
        """从当前会话中提取相关上下文"""
        if not chat_history or len(chat_history) < 2:
            return ""
            
        # 获取最后几对消息 (最多2对)
        context_items = []
        for i in range(len(chat_history) - 1, 0, -2):
            if i >= 1 and chat_history[i-1]['role'] == 'user' and chat_history[i]['role'] == 'assistant':
                user_msg = chat_history[i-1]['content']
                ai_msg = chat_history[i]['content']
                
                # 每条消息只保留前200个字符以避免令牌爆炸
                if len(user_msg) > 200:
                    user_msg = user_msg[:197] + "..."
                if len(ai_msg) > 200:
                    ai_msg = ai_msg[:197] + "..."
                    
                context_items.append(f"用户: {user_msg}\n助手: {ai_msg}")
                
                # 限制为最后2次交流
                if len(context_items) >= 2:
                    break
                    
        return "\n\n".join(reversed(context_items)) if context_items else ""
    
    def _preprocess_data(self, data):
        """在发送到模型之前预处理数据"""
        if isinstance(data, dict):
            # 仅提取必要信息以减少令牌使用
            processed = {
                "patient_name": data.get("patient_name", ""),
                "age": data.get("age", ""),
                "gender": data.get("gender", ""),
                "report": data.get("report", "")
            }
            return processed
        return data
