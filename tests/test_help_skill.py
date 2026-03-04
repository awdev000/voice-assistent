import unittest

from modules.help_skill import HelpSkill


class HelpSkillTests(unittest.TestCase):
    def test_help_skill_trigger_detected(self):
        skill = HelpSkill()
        self.assertTrue(skill.can_handle("Что ты умеешь?"))

    def test_help_skill_no_trigger(self):
        skill = HelpSkill()
        self.assertFalse(skill.can_handle("Какая сегодня погода?"))

    def test_help_skill_response_is_string(self):
        skill = HelpSkill()
        self.assertIsInstance(skill.handle("помощь"), str)


if __name__ == "__main__":
    unittest.main()
