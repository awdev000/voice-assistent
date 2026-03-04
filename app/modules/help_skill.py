from modules.skill import Skill


class HelpSkill(Skill):
    TRIGGERS = (
        "что ты умеешь",
        "что умеешь",
        "помощь",
        "help",
    )

    def can_handle(self, text: str) -> bool:
        normalized = text.lower()
        return any(trigger in normalized for trigger in self.TRIGGERS)

    def handle(self, text: str) -> str:
        return (
            "Я могу слушать голос, распознавать речь, отвечать через ИИ и озвучивать ответ. "
            "Также у меня есть локальный fallback на случай проблем с облаком."
        )
