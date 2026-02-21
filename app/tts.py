import subprocess

PIPER_MODEL = "/models/piper/ru_RU-irina-medium.onnx"

def speak(text):
    """
    Генерируем речь через Piper и сразу отправляем
    аудиопоток в ALSA (aplay).
    """

    # Запускаем piper
    piper = subprocess.Popen(
        ["piper", "--model", PIPER_MODEL, "--output-raw"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE
    )

    # Запускаем воспроизведение
    aplay = subprocess.Popen(
        ["aplay", "-r", "22050", "-f", "S16_LE", "-t", "raw"],
        stdin=piper.stdout
    )

    # Передаём текст в piper
    piper.stdin.write(text.encode("utf-8"))
    piper.stdin.close()

    piper.wait()
    aplay.wait()