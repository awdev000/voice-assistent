from typing import Callable, Iterable

from modules.skill import Skill


class Router:
    def __init__(self, skills: Iterable[Skill], ai_handler: Callable[[str], str]):
        self.skills = list(skills)
        self.ai_handler = ai_handler

    def route(self, text: str) -> str:
        for skill in self.skills:
            if skill.can_handle(text):
                return skill.handle(text)
        return self.ai_handler(text)
