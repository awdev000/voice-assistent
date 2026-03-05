# CONFIGURATION

Все параметры должны быть в config.yaml

Пример:

audio:
sample_rate: 16000

ai:
  mode: hybrid
  cloud_enabled: true
  local_enabled: true
  cloud_model: gpt-4o-mini
  local_model: tinyllama

stt:
  engine: whisper
  model: small

tts:
  engine: piper
  model: ru_RU-irina-medium.onnx

features:
  cloud_ai: true
  local_fallback: true
  local_only_mode: false
  skills_engine: true
  conversation_memory: false
  wake_word: false
  piper_tts: true
  web_tts: false
  debug_logging: false
