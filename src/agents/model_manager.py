import groq
import streamlit as st
import logging
import time

logger = logging.getLogger(__name__)

class ModelManager:
    """
    Manages AI model selection, fallback, and rate limits.
    Implements an agent-based approach for model management.
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
        self.clients = {}
        self._initialize_clients()

    def _initialize_clients(self):
        """Initialize API clients for each provider."""
        try:
            self.clients["groq"] = groq.Groq(api_key=st.secrets["GROQ_API_KEY"])
        except Exception as e:
            logger.error(f"Failed to initialize Groq client: {str(e)}")

    def generate_analysis(self, data, system_prompt, retry_count=0):
        """
        Generate analysis using the best available model with automatic fallback.
        Implements agent-based decision making for model selection.
        """
        if retry_count > 3:
            return {"success": False, "error": "All models failed after multiple retries"}

        index = retry_count if retry_count < len(self.MODELS) else len(self.MODELS) - 1
        provider = "groq"
        model = self.MODELS[index]

        # Check if we have a client for this provider
        if provider not in self.clients:
            logger.error(f"No client available for provider: {provider}")
            return self.generate_analysis(data, system_prompt, retry_count + 1)

        try:
            client = self.clients[provider]
            logger.info(f"Attempting generation with {provider} model: {model}")

            if provider == "groq":
                completion = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": str(data)}
                    ],
                    temperature=self.TEMPERATURE,
                    max_tokens=self.MAX_TOKENS,
                )

                return {
                    "success": True,
                    "content": completion.choices[0].message.content,
                    "model_used": f"{provider}/{model}"
                }
                
        except Exception as e:
            error_message = str(e).lower()
            logger.warning(f"Model {model} failed: {error_message}")
            
            # Check for rate limit errors
            if "rate limit" in error_message or "quota" in error_message:
                # Wait briefly before retrying with a different model
                time.sleep(2)
            
            # Try next model in hierarchy
            return self.generate_analysis(data, system_prompt, retry_count + 1)
            
        return {"success": False, "error": "Analysis failed with all available models"}
