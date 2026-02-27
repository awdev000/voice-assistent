# ARCHITECTURE

## Общая схема

AudioInput
↓
SpeechToText (Whisper)
↓
Intent Router
↓
Skill Engine
↓
AI Engine (Cloud / Local)
↓
TextToSpeech (Piper)
↓
AudioOutput

## Принципы

- Каждый слой независим
- Можно заменить Whisper на другой STT
- Можно заменить Piper на другой TTS
- AI Engine не знает про Audio слой

## Компоненты

### core/
Router, события, интерфейсы

### ai/
Cloud и Local LLM

### audio/
Input / Output

### modules/
Skills