from typing import Any
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.runnables import RunnableLambda, Runnable
from app.core.config import SETTINGS

class DualBrainLLM(Runnable):
    def __init__(self, primary_model: str, fallback_model: str, temperature: float = 0.7):
        self.primary_model_name = primary_model
        self.fallback_model_name = fallback_model
        self.temperature = temperature
        self._primary = None
        self._fallback = None

    @property
    def primary(self):
        if not self._primary:
            self._primary = ChatGroq(
                temperature=self.temperature,
                model_name=self.primary_model_name,
                api_key=SETTINGS.GROQ_API_KEY
            )
        return self._primary

    @property
    def fallback(self):
        if not self._fallback:
            self._fallback = ChatGoogleGenerativeAI(
                model=self.fallback_model_name,
                google_api_key=SETTINGS.GEMINI_API_KEY,
                temperature=self.temperature
            )
        return self._fallback

    def __or__(self, other):
        # Explicit piping support for LCEL
        return RunnableLambda(self.ainvoke) | other

    def pipe(self, other):
        return self.__or__(other)

    async def ainvoke(self, input: Any, config: Any = None, **kwargs) -> Any:
        try:
            return await self.primary.ainvoke(input, config=config, **kwargs)
        except Exception as e:
            print(f"⚠️ PRIMARY BRAIN (Groq) FAILED: {e}. Falling back to ANALYST (Gemini).")
            return await self.fallback.ainvoke(input, config=config, **kwargs)

    def invoke(self, input: Any, config: Any = None, **kwargs) -> Any:
        try:
            return self.primary.invoke(input, config=config, **kwargs)
        except Exception as e:
            print(f"⚠️ PRIMARY BRAIN (Groq) FAILED: {e}. Falling back to ANALYST (Gemini).")
            return self.fallback.invoke(input, config=config, **kwargs)

# Refined model instances with failover
fast_llm = DualBrainLLM(
    primary_model="llama-3.3-70b-versatile",
    fallback_model="gemini-2.0-flash",
    temperature=0.7
)

smart_llm = DualBrainLLM(
    primary_model="llama-3.3-70b-versatile",
    fallback_model="gemini-2.0-flash",
    temperature=0.3
)
