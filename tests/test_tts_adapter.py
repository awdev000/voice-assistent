import unittest
from unittest.mock import patch
import subprocess

from tts import PiperSpeaker


class DummyPipe:
    def __init__(self):
        self.written = b""
        self.closed = False

    def write(self, payload):
        self.written += payload

    def close(self):
        self.closed = True


class DummyProcess:
    def __init__(self, stdout=None):
        self.stdin = DummyPipe()
        self.stdout = stdout if stdout is not None else object()
        self.wait_called = False
        self.wait_timeout = None
        self.killed = False

    def wait(self, timeout=None):
        self.wait_called = True
        self.wait_timeout = timeout

    def kill(self):
        self.killed = True


class TTSAdapterTests(unittest.TestCase):
    def test_piper_speaker_starts_processes_and_streams_text(self):
        created = []

        def fake_popen(*args, **kwargs):
            cmd = args[0]
            if cmd[0] == "piper":
                proc = DummyProcess(stdout=object())
            else:
                proc = DummyProcess()
            created.append((cmd, kwargs, proc))
            return proc

        speaker = PiperSpeaker(model_path="/models/piper/model.onnx", process_timeout=7)
        with patch("tts.subprocess.Popen", side_effect=fake_popen):
            speaker("Привет")

        self.assertEqual(len(created), 2)
        self.assertEqual(created[0][0], ["piper", "--model", "/models/piper/model.onnx", "--output-raw"])
        self.assertEqual(created[1][0], ["aplay", "-r", "22050", "-f", "S16_LE", "-t", "raw"])
        self.assertEqual(created[0][2].stdin.written, "Привет".encode("utf-8"))
        self.assertTrue(created[0][2].stdin.closed)
        self.assertTrue(created[0][2].wait_called)
        self.assertTrue(created[1][2].wait_called)
        self.assertEqual(created[0][2].wait_timeout, 7)
        self.assertEqual(created[1][2].wait_timeout, 7)

    def test_piper_speaker_kills_processes_on_timeout(self):
        created = []

        def fake_popen(*args, **kwargs):
            cmd = args[0]
            proc = DummyProcess(stdout=object())
            if cmd[0] == "piper":
                def timeout_wait(timeout=None):
                    raise subprocess.TimeoutExpired(cmd="piper", timeout=timeout or 0)
                proc.wait = timeout_wait
            created.append((cmd, kwargs, proc))
            return proc

        speaker = PiperSpeaker(process_timeout=2)
        with patch("tts.subprocess.Popen", side_effect=fake_popen):
            speaker("Привет")

        self.assertEqual(len(created), 2)
        self.assertTrue(created[0][2].killed)
        self.assertTrue(created[1][2].killed)


if __name__ == "__main__":
    unittest.main()
