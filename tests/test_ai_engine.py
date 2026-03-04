import sys
import types
import unittest


class OpenAIStub:
    def __init__(self, *args, **kwargs):
        self.chat = types.SimpleNamespace(
            completions=types.SimpleNamespace(
                create=lambda **_: None,
            )
        )


sys.modules.setdefault("openai", types.SimpleNamespace(OpenAI=OpenAIStub))
sys.modules.setdefault("requests", types.SimpleNamespace(post=lambda *args, **kwargs: None))
sys.modules.setdefault("dotenv", types.SimpleNamespace(load_dotenv=lambda: None))

import ai  # noqa: E402
from ai import AIEngine  # noqa: E402


class DummyResponse:
    def __init__(self, content: str):
        self.choices = [types.SimpleNamespace(message=types.SimpleNamespace(content=content))]


class DummyClient:
    def __init__(self, content: str = "openai"):
        self._content = content
        self.chat = types.SimpleNamespace(
            completions=types.SimpleNamespace(create=self._create)
        )

    def _create(self, **kwargs):
        return DummyResponse(self._content)


class FailingClient:
    def __init__(self):
        self.chat = types.SimpleNamespace(
            completions=types.SimpleNamespace(create=self._fail)
        )

    def _fail(self, **kwargs):
        raise RuntimeError("openai down")


class LocalResp:
    def __init__(self, response_text: str):
        self._response_text = response_text

    def json(self):
        return {"response": self._response_text}


class AIEngineTests(unittest.TestCase):
    def setUp(self):
        self.original_post = ai.requests.post

    def tearDown(self):
        ai.requests.post = self.original_post

    def test_ai_engine_prefers_openai_when_available(self):
        engine = AIEngine(client=DummyClient("cloud ok"))
        ai.requests.post = lambda *args, **kwargs: LocalResp("should not be used")
        self.assertEqual(engine.ask("привет"), "cloud ok")

    def test_ai_engine_uses_local_fallback_when_openai_fails(self):
        engine = AIEngine(client=FailingClient(), local_llm_enabled=True)
        ai.requests.post = lambda *args, **kwargs: LocalResp("local ok")
        self.assertEqual(engine.ask("привет"), "local ok")

    def test_ai_engine_returns_service_unavailable_when_all_fail(self):
        engine = AIEngine(client=FailingClient(), local_llm_enabled=True)

        def fail_local(*args, **kwargs):
            raise RuntimeError("ollama down")

        ai.requests.post = fail_local
        self.assertEqual(engine.ask("привет"), "Сервис ИИ временно недоступен.")

    def test_ai_engine_does_not_use_local_when_disabled(self):
        engine = AIEngine(client=FailingClient(), local_llm_enabled=False)

        def fail_if_called(*args, **kwargs):
            raise AssertionError("local fallback must be disabled")

        ai.requests.post = fail_if_called
        self.assertEqual(engine.ask("привет"), "Сервис ИИ временно недоступен.")


if __name__ == "__main__":
    unittest.main()
