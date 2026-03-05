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

Control Plane будет доступен на `http://localhost:8000`.

## Требования
- Raspberry Pi 5 (8GB рекомендуется)
- Docker
- Bluetooth-динамик или USB аудио

## Архитектура
Whisper → Router → OpenAI / Ollama → Piper → PipeWire

## API Control Plane
- `GET /api/status`
- `GET /api/features`
- `GET /api/config`
- `PUT /api/config`
- `POST /api/toggle`
- `GET /api/logs`
- `GET /api/roadmap`
- `POST /api/interact/text`
- `POST /api/interact/upload`
