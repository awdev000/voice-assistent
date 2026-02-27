# ARCHITECTURAL DECISIONS

## ADR-001
Использовать Docker для изоляции среды.

## ADR-002
Использовать локальный STT (Whisper), а не облачный.

## ADR-003
Использовать гибридную AI архитектуру:
Cloud → Local fallback.

## ADR-004
Разделить систему на слои:
Audio / Router / Skills / AI / Output.