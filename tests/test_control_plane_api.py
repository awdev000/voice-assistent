import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

import config_store
import control_plane


class ControlPlaneApiTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_path = config_store.CONFIG_PATH
        config_store.CONFIG_PATH = Path(self.temp_dir.name) / "config.yaml"
        self.client = TestClient(control_plane.app)

    def tearDown(self):
        config_store.CONFIG_PATH = self.original_path
        self.temp_dir.cleanup()

    def test_status_endpoint(self):
        response = self.client.get("/api/status")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIn("active_ai_model", body)
        self.assertIn("services", body)

    def test_toggle_endpoint(self):
        response = self.client.post(
            "/api/toggle",
            json={"feature": "wake_word", "enabled": True},
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["features"]["wake_word"])


if __name__ == "__main__":
    unittest.main()
