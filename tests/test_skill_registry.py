import unittest

from modules.registry import build_skills


class SkillRegistryTests(unittest.TestCase):
    def test_build_skills_returns_empty_when_disabled(self):
        skills = build_skills(enabled=False, selected=["help"])
        self.assertEqual(skills, [])

    def test_build_skills_returns_empty_when_no_selected_skills(self):
        skills = build_skills(enabled=True, selected=[])
        self.assertEqual(skills, [])

    def test_build_skills_builds_known_skills(self):
        skills = build_skills(enabled=True, selected=["help"])
        self.assertEqual(len(skills), 1)
        self.assertTrue(skills[0].can_handle("помощь"))

    def test_build_skills_skips_unknown_skill_names(self):
        skills = build_skills(enabled=True, selected=["unknown", "help"])
        self.assertEqual(len(skills), 1)


if __name__ == "__main__":
    unittest.main()
