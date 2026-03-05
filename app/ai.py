import logging
import time

import requests
from openai import OpenAI

from config import (
    LOCAL_LLM_ENABLED,
    LOCAL_LLM_MODEL,
    LOCAL_LLM_URL,
    MODEL,
    OPENAI_API_KEY,
)
from runtime_state import runtime_state


logger = logging.getLogger(__name__)


class AIEngine:
    def __init__(
        self,
        client: OpenAI | None = None,
        model: str = MODEL,
        local_llm_enabled: bool = LOCAL_LLM_ENABLED,
        local_model: str = LOCAL_LLM_MODEL,
        local_url: str = LOCAL_LLM_URL,
    ):
        self.client = client or OpenAI(api_key=OPENAI_API_KEY)
        self.model = model
        self.local_llm_enabled = local_llm_enabled
        self.local_model = local_model
        self.local_url = local_url
        self.conversation: list[dict[str, str]] = []

    def ask_openai(self, text: str) -> str:
        self.conversation.append({"role": "user", "content": text})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=self.conversation,
            max_tokens=200,
        )

        answer = response.choices[0].message.content
        self.conversation.append({"role": "assistant", "content": answer})
        return answer

    def ask_local_llm(self, text: str) -> str:
        prompt = f"""
Ты домашний голосовой ассистент.
Отвечай кратко.
Отвечай только на русском языке.
Не используй подписи типа "Best regards".
Вопрос пользователя: {text}
Ответ:
"""
        response = requests.post(
            self.local_url,
            json={
                "model": self.local_model,  # llama3
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_predict": 120,
                    "temperature": 0.7,
                },
            },
            timeout=180,
        )
        data = response.json()
        return data.get("response", "Локальная модель не ответила.")

    def ask(self, text: str) -> str:
        start = time.perf_counter()
        try:
            logger.info("Trying OpenAI")
            answer = self.ask_openai(text)
            runtime_state.record_request(
                text=text,
                answer=answer,
                latency_ms=(time.perf_counter() - start) * 1000,
                engine="cloud",
            )
            return answer
        except Exception as exc:
            logger.warning("OpenAI unavailable: %s", exc)
            if not self.local_llm_enabled:
                logger.warning("Local LLM fallback disabled by config")
                answer = "Сервис ИИ временно недоступен."
                runtime_state.record_request(
                    text=text,
                    answer=answer,
                    latency_ms=(time.perf_counter() - start) * 1000,
                    engine="unavailable",
                )
                return answer

            try:
                logger.info("Trying local LLM")
                answer = self.ask_local_llm(text)
                runtime_state.record_request(
                    text=text,
                    answer=answer,
                    latency_ms=(time.perf_counter() - start) * 1000,
                    engine="local",
                )
                return answer
            except Exception as local_exc:
                logger.error("Local LLM unavailable: %s", local_exc)
                answer = "Сервис ИИ временно недоступен."
                runtime_state.record_request(
                    text=text,
                    answer=answer,
                    latency_ms=(time.perf_counter() - start) * 1000,
                    engine="unavailable",
                )
                return answer


default_engine = AIEngine()


def ask_ai(text: str) -> str:
    return default_engine.ask(text)
