import groq
import streamlit as st
import logging
import time

logger = logging.getLogger(__name__)

class ModelManager:
    """模型管理器

    负责选择具体使用的大模型、在失败时自动降级重试，
    同时在内部做简单的速率控制与重试逻辑。
    """

    MODELS = [
        "meta-llama/llama-4-maverick-17b-128e-instruct",
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
        "llama3-70b-8192",
    ]
    MAX_TOKENS = 2000
    TEMPERATURE = 0.7

    def __init__(self):
        """初始化模型管理器

        - 创建一个用于保存不同提供商客户端的字典
        - 调用内部方法初始化各个模型提供商的客户端
        """
        self.clients = {}  # 保存不同模型提供商的客户端实例
        self._initialize_clients()

    def _initialize_clients(self):
        """初始化各个模型提供商的 API 客户端"""
        try:
            # 使用 Streamlit 的 secrets 配置初始化 Groq 客户端
            self.clients["groq"] = groq.Groq(api_key=st.secrets["GROQ_API_KEY"])
        except Exception as e:
            # 初始化失败只记录日志，不直接中断整个应用
            logger.error(f"初始化 Groq 客户端失败: {str(e)}")

    def generate_analysis(self, data, system_prompt, retry_count=0):
        """使用当前可用的最优模型生成分析结果

        会根据重试次数在 "MODELS" 列表中依次降级选择模型，
        并在遇到速率限制等错误时自动等待后重试。
        """
        # 如果重试次数超过 3 次，直接认为所有模型均不可用
        if retry_count > 3:
            return {"success": False, "error": "All models failed after multiple retries"}

        # 根据当前重试次数选择要使用的模型下标
        index = retry_count if retry_count < len(self.MODELS) else len(self.MODELS) - 1
        provider = "groq"  # 当前仅支持 Groq 提供商
        model = self.MODELS[index]

        # 检查对应提供商的客户端是否已经初始化
        if provider not in self.clients:
            logger.error(f"未找到提供商客户端: {provider}")
            # 尝试使用下一个模型
            return self.generate_analysis(data, system_prompt, retry_count + 1)

        try:
            client = self.clients[provider]
            logger.info(f"尝试使用提供商 {provider} 的模型 {model} 生成分析")

            if provider == "groq":
                # 调用 Groq Chat Completions 接口生成内容
                completion = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},  # 系统提示，控制整体风格
                        {"role": "user", "content": str(data)}         # 用户消息，传入体检数据
                    ],
                    temperature=self.TEMPERATURE,
                    max_tokens=self.MAX_TOKENS,
                )

                # 返回调用成功的结果和使用的模型名称
                return {
                    "success": True,
                    "content": completion.choices[0].message.content,
                    "model_used": f"{provider}/{model}"
                }
                
        except Exception as e:
            error_message = str(e).lower()
            logger.warning(f"模型 {model} 调用失败: {error_message}")

            # 如果是速率限制或配额相关错误，稍作等待再重试
            if "rate limit" in error_message or "quota" in error_message:
                time.sleep(2)

            # 递归调用自身，尝试使用下一个模型
            return self.generate_analysis(data, system_prompt, retry_count + 1)

        # 正常情况下不会到达这里，作为兜底错误返回
        return {"success": False, "error": "Analysis failed with all available models"}
