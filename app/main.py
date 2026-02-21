from faster_whisper import WhisperModel
from audio import record_audio
from ai import ask_ai
from tts import speak
from config import WHISPER_MODEL

# Создаём модель Whisper с оптимизацией под Raspberry
model = WhisperModel(
    WHISPER_MODEL,
    device="cpu",
    compute_type="int8",  # экономия памяти
    cpu_threads=4         # не перегружаем систему
)

def transcribe(audio):
    segments, _ = model.transcribe(audio)
    text = " ".join([seg.text for seg in segments])
    return text

while True:
    audio = record_audio()

    segments, _ = model.transcribe(
        audio,
        beam_size=1,
        vad_filter=True
    )

    text = " ".join([seg.text for seg in segments])
    
    print("Вы сказали:", text)

    if not text.strip():
        continue

    answer = ask_ai(text)

    print("Ответ:", answer)
    speak(answer)