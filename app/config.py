import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL = os.getenv("MODEL", "gpt-4o-mini")
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "small")
WHISPER_DEVICE = os.getenv("WHISPER_DEVICE", "cpu")
WHISPER_COMPUTE_TYPE = os.getenv("WHISPER_COMPUTE_TYPE", "int8")


def _parse_bool(raw: str | None, default: bool = True) -> bool:
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _parse_csv(raw: str | None, default: str = "") -> list[str]:
    value = raw if raw is not None else default
    return [item.strip().lower() for item in value.split(",") if item.strip()]


def _parse_int(raw: str | None, default: int) -> int:
    if raw is None:
        return default
    try:
        return int(raw.strip())
    except ValueError:
        return default


SKILLS_ENABLED = _parse_bool(os.getenv("SKILLS_ENABLED"), default=True)
ENABLED_SKILLS = _parse_csv(os.getenv("ENABLED_SKILLS"), default="help")
LOCAL_LLM_ENABLED = _parse_bool(os.getenv("LOCAL_LLM_ENABLED"), default=False)
LOCAL_LLM_MODEL = os.getenv("LOCAL_LLM_MODEL", "tinyllama")
LOCAL_LLM_URL = os.getenv("LOCAL_LLM_URL", "http://ollama:11434/api/generate")

AUDIO_DEVICE_ID = _parse_int(os.getenv("AUDIO_DEVICE_ID"), default=1)
AUDIO_INPUT_SR = _parse_int(os.getenv("AUDIO_INPUT_SR"), default=48000)
AUDIO_TARGET_SR = _parse_int(os.getenv("AUDIO_TARGET_SR"), default=16000)
AUDIO_CHANNELS = _parse_int(os.getenv("AUDIO_CHANNELS"), default=1)
AUDIO_RECORD_DURATION = _parse_int(os.getenv("AUDIO_RECORD_DURATION"), default=6)

WHISPER_CPU_THREADS = _parse_int(os.getenv("WHISPER_CPU_THREADS"), default=4)
WHISPER_BEAM_SIZE = _parse_int(os.getenv("WHISPER_BEAM_SIZE"), default=1)
WHISPER_VAD_FILTER = _parse_bool(os.getenv("WHISPER_VAD_FILTER"), default=True)

PIPER_MODEL_PATH = os.getenv("PIPER_MODEL_PATH", "/models/piper/ru_RU-irina-medium.onnx")
PIPER_SAMPLE_RATE = _parse_int(os.getenv("PIPER_SAMPLE_RATE"), default=22050)
PIPER_AUDIO_FORMAT = os.getenv("PIPER_AUDIO_FORMAT", "S16_LE")
PIPER_PROCESS_TIMEOUT = _parse_int(os.getenv("PIPER_PROCESS_TIMEOUT"), default=30)
