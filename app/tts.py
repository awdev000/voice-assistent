import subprocess
import logging

from config import (
    PIPER_AUDIO_FORMAT,
    PIPER_MODEL_PATH,
    PIPER_PROCESS_TIMEOUT,
    PIPER_SAMPLE_RATE,
)

logger = logging.getLogger(__name__)


class PiperSpeaker:
    def __init__(
        self,
        model_path: str = PIPER_MODEL_PATH,
        sample_rate: int = PIPER_SAMPLE_RATE,
        audio_format: str = PIPER_AUDIO_FORMAT,
        process_timeout: int = PIPER_PROCESS_TIMEOUT,
    ):
        self.model_path = model_path
        self.sample_rate = sample_rate
        self.audio_format = audio_format
        self.process_timeout = process_timeout

    def __call__(self, text: str) -> None:
        """
        Генерируем речь через Piper и сразу отправляем
        аудиопоток в ALSA (aplay).
        """
        piper = subprocess.Popen(
            ["piper", "--model", self.model_path, "--output-raw"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
        )

        aplay = subprocess.Popen(
            [
                "aplay",
                "-r",
                str(self.sample_rate),
                "-f",
                self.audio_format,
                "-t",
                "raw",
            ],
            stdin=piper.stdout,
        )

        piper.stdin.write(text.encode("utf-8"))
        piper.stdin.close()

        try:
            piper.wait(timeout=self.process_timeout)
            aplay.wait(timeout=self.process_timeout)
        except subprocess.TimeoutExpired:
            logger.error("TTS process timeout exceeded (%ss), terminating.", self.process_timeout)
            piper.kill()
            aplay.kill()


default_speaker = PiperSpeaker()


def speak(text: str) -> None:
    default_speaker(text)
