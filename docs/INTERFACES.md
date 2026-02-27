# INTERFACES

## AI Engine Interface

def generate_response(text: str) -> str

## Skill Interface

class Skill:
def can_handle(text: str) -> bool
def handle(text: str) -> str

## Audio Interface

def record() -> bytes
def speak(text: str) -> None