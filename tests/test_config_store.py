import tempfile
import unittest
from pathlib import Path

import config_store


class ConfigStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_path = config_store.CONFIG_PATH
        config_store.CONFIG_PATH = Path(self.temp_dir.name) / "config.yaml"

    def tearDown(self):
        config_store.CONFIG_PATH = self.original_path
        self.temp_dir.cleanup()

    def test_load_config_creates_default_file(self):
        data = config_store.load_config()
        self.assertTrue(config_store.CONFIG_PATH.exists())
        self.assertIn("ai", data)
        self.assertIn("features", data)

    def test_set_feature_updates_toggles(self):
        data = config_store.set_feature("local_only_mode", True)
        self.assertTrue(data["features"]["local_only_mode"])
        self.assertEqual(data["ai"]["mode"], "local")


if __name__ == "__main__":
    unittest.main()
