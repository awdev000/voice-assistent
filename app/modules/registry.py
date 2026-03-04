import logging

from modules.help_skill import HelpSkill
from modules.skill import Skill


logger = logging.getLogger(__name__)


SKILL_FACTORIES = {
    "help": HelpSkill,
}


def build_skills(enabled: bool, selected: list[str]) -> list[Skill]:
    if not enabled:
        logger.info("Skills disabled by config")
        return []

    if not selected:
        logger.info("No skills selected in config")
        return []

    skills: list[Skill] = []
    for skill_name in selected:
        factory = SKILL_FACTORIES.get(skill_name)
        if factory is None:
            logger.warning("Unknown skill in config: %s", skill_name)
            continue
        skills.append(factory())

    return skills
