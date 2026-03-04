from typing import Callable

from config import (
    WHISPER_BEAM_SIZE,
    WHISPER_COMPUTE_TYPE,
    WHISPER_CPU_THREADS,
    WHISPER_DEVICE,
    WHISPER_MODEL,
    WHISPER_VAD_FILTER,
)


class WhisperTranscriber:
    def __init__(
        self,
        model_name: str = WHISPER_MODEL,
        device: str = WHISPER_DEVICE,
        compute_type: str = WHISPER_COMPUTE_TYPE,
        cpu_threads: int = WHISPER_CPU_THREADS,
        beam_size: int = WHISPER_BEAM_SIZE,
        vad_filter: bool = WHISPER_VAD_FILTER,
        model: object | None = None,
        model_factory: Callable[..., object] | None = None,
    ):
        self.model_name = model_name
        self.device = device
        self.compute_type = compute_type
        self.cpu_threads = cpu_threads
        self.beam_size = beam_size
        self.vad_filter = vad_filter
        self._model = model
        self._model_factory = model_factory

    def _build_model(self):
        if self._model_factory is not None:
            return self._model_factory(
                self.model_name,
                device=self.device,
                compute_type=self.compute_type,
                cpu_threads=self.cpu_threads,
            )

        # Lazy import to keep tests independent from external packages.
        from faster_whisper import WhisperModel

        return WhisperModel(
            self.model_name,
            device=self.device,
            compute_type=self.compute_type,
            cpu_threads=self.cpu_threads,
        )

    @property
    def model(self):
        if self._model is None:
            self._model = self._build_model()
        return self._model

    def __call__(self, audio: object) -> str:
        segments, _ = self.model.transcribe(
            audio,
            beam_size=self.beam_size,
            vad_filter=self.vad_filter,
        )
        return " ".join(seg.text for seg in segments).strip()
