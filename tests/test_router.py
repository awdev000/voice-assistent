import unittest

from core.router import Router
from modules.skill import Skill


class DummySkill(Skill):
    def can_handle(self, text: str) -> bool:
        return "timer" in text.lower()

    def handle(self, text: str) -> str:
        return "Таймер установлен"


class RouterTests(unittest.TestCase):
    def test_router_uses_skill_when_match(self):
        router = Router(skills=[DummySkill()], ai_handler=lambda text: "AI")
        self.assertEqual(router.route("Поставь timer"), "Таймер установлен")

    def test_router_falls_back_to_ai(self):
        router = Router(skills=[DummySkill()], ai_handler=lambda text: "AI response")
        self.assertEqual(router.route("Расскажи анекдот"), "AI response")


if __name__ == "__main__":
    unittest.main()
