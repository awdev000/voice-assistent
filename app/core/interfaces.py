from typing import Protocol


class AIHandler(Protocol):
    def __call__(self, text: str) -> str:
        ...


class Recorder(Protocol):
    def __call__(self) -> object:
        ...


class Transcriber(Protocol):
    def __call__(self, audio: object) -> str:
        ...


class Speaker(Protocol):
    def __call__(self, text: str) -> None:
        ...
