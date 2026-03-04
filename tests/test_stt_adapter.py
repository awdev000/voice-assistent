import unittest
from types import SimpleNamespace

from stt import WhisperTranscriber


class DummyModel:
    def transcribe(self, audio, **kwargs):
        segments = [SimpleNamespace(text="привет"), SimpleNamespace(text="мир")]
        return segments, {"lang": "ru"}


class STTAdapterTests(unittest.TestCase):
    def test_whisper_transcriber_joins_segments(self):
        transcriber = WhisperTranscriber(model=DummyModel())
        text = transcriber(audio=b"dummy")
        self.assertEqual(text, "привет мир")

    def test_whisper_transcriber_uses_factory_lazy(self):
        calls = []

        def factory(model_name, **kwargs):
            calls.append((model_name, kwargs))
            return DummyModel()

        transcriber = WhisperTranscriber(model_name="small", model_factory=factory)
        text = transcriber(audio=b"dummy")
        self.assertEqual(text, "привет мир")
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][0], "small")


if __name__ == "__main__":
    unittest.main()
