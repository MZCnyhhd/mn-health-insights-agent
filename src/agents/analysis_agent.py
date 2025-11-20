from agents.model_manager import ModelManager


class AnalysisAgent:
    """报告分析代理

    负责协调模型管理器，对体检报告进行分析，
    并在后续扩展中接入速率限制统计、知识库情境学习等能力。
    """
    
    def __init__(self):
        """初始化 AnalysisAgent 代理实例"""
        self.model_manager = ModelManager()  # 创建模型管理器，用于实际调用大模型
            
    def check_rate_limit(self):
        """检查当前用户是否触达分析次数上限

        目前配置为不限次数，因此始终返回允许分析。
        返回:
            (True, None)
        """
        return True, None

    def analyze_report(self, data, system_prompt, check_only=False, chat_history=None):
        """分析体检报告数据的主入口

        参数:
            data: 要分析的原始报告数据（通常为字符串）
            system_prompt: 系统提示词，控制模型输出风格
            check_only: 为 True 时仅做额度检查，不真正调用模型
            chat_history: 当前会话中已有的聊天记录（预留扩展）
        """
        can_analyze, error_msg = self.check_rate_limit()
        if not can_analyze:
            return {"success": False, "error": error_msg}
        
        if check_only:
            # 调用方只希望查询是否允许分析，此时直接返回检查结果
            return can_analyze, error_msg

        # 使用模型管理器生成分析结果
        result = self.model_manager.generate_analysis(data, system_prompt)

        return result
