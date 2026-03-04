import logging

from ai import AIEngine
from audio import MicrophoneRecorder
from config import ENABLED_SKILLS, SKILLS_ENABLED, WHISPER_MODEL
from core.interfaces import AIHandler, Recorder, Speaker, Transcriber
from core.router import Router
from modules.registry import build_skills
from stt import WhisperTranscriber
from tts import PiperSpeaker


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


def build_router(ai_handler: AIHandler) -> Router:
    skills = build_skills(enabled=SKILLS_ENABLED, selected=ENABLED_SKILLS)
    return Router(skills=skills, ai_handler=ai_handler)


def run_voice_loop(
    recorder: Recorder,
    transcriber: Transcriber,
    router: Router,
    speaker: Speaker,
) -> None:
    while True:
        audio = recorder()
        text = transcriber(audio)
        logger.info("User said: %s", text)

        if not text:
            continue

        answer = router.route(text)
        logger.info("Assistant answer: %s", answer)
        speaker(answer)


def main() -> None:
    recorder = MicrophoneRecorder()
    transcriber = WhisperTranscriber(model_name=WHISPER_MODEL)
    ai_engine = AIEngine()
    speaker = PiperSpeaker()
    router = build_router(ai_handler=ai_engine.ask)
    logger.info("Voice assistant started")
    run_voice_loop(
        recorder=recorder,
        transcriber=transcriber,
        router=router,
        speaker=speaker,
    )


if __name__ == "__main__":
    main()
