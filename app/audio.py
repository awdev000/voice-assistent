import sounddevice as sd
import numpy as np
from scipy.signal import resample

DEVICE_ID = 1
INPUT_SR = 48000
TARGET_SR = 16000
CHANNELS = 1

def record_audio(duration=6):
    print("Говорите...")

    frames = []

    def callback(indata, frames_count, time, status):
        if status:
            print(status)
        frames.append(indata.copy())

    with sd.InputStream(
        device=DEVICE_ID,
        samplerate=INPUT_SR,
        channels=CHANNELS,
        dtype="float32",
        blocksize=1024,
        callback=callback,
    ):
        sd.sleep(int(duration * 1000))

    audio = np.concatenate(frames, axis=0).flatten()

    # ресемплируем в 16kHz
    num_samples = int(len(audio) * TARGET_SR / INPUT_SR)
    audio_resampled = resample(audio, num_samples)

    return audio_resampled