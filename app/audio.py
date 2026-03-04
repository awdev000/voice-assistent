import logging

import sounddevice as sd
import numpy as np
from scipy.signal import resample

from config import (
    AUDIO_CHANNELS,
    AUDIO_DEVICE_ID,
    AUDIO_INPUT_SR,
    AUDIO_RECORD_DURATION,
    AUDIO_TARGET_SR,
)

logger = logging.getLogger(__name__)


class MicrophoneRecorder:
    def __init__(self, duration: int = AUDIO_RECORD_DURATION):
        self.duration = duration

    def __call__(self):
        logger.info("Listening...")

        frames = []

        def callback(indata, frames_count, time, status):
            if status:
                logger.warning("Audio input status: %s", status)
            frames.append(indata.copy())

        with sd.InputStream(
            device=AUDIO_DEVICE_ID,
            samplerate=AUDIO_INPUT_SR,
            channels=AUDIO_CHANNELS,
            dtype="float32",
            blocksize=1024,
            callback=callback,
        ):
            sd.sleep(int(self.duration * 1000))

        audio = np.concatenate(frames, axis=0).flatten()

        # ресемплируем в 16kHz
        num_samples = int(len(audio) * AUDIO_TARGET_SR / AUDIO_INPUT_SR)
        audio_resampled = resample(audio, num_samples)

        return audio_resampled


default_recorder = MicrophoneRecorder()


def record_audio(duration=AUDIO_RECORD_DURATION):
    if duration != default_recorder.duration:
        return MicrophoneRecorder(duration=duration)()
    return default_recorder()
