# Home AI Hub

Голосовой ассистент на базе Raspberry Pi с гибридной архитектурой (OpenAI + Ollama).

## Возможности
- Локальное распознавание речи (Whisper)
- Облачный ИИ (OpenAI)
- Локальный fallback (Ollama)
- Озвучивание (Piper)
- Поддержка Bluetooth

## Запуск

docker-compose build
docker-compose up

## Требования
- Raspberry Pi 5 (8GB рекомендуется)
- Docker
- Bluetooth-динамик или USB аудио

## Архитектура
Whisper → Router → OpenAI / Ollama → Piper → PipeWire