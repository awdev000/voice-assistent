from __future__ import annotations

from collections import defaultdict
import logging
import tempfile
import time
from typing import Any

from ai import AIEngine
from core.router import Router
from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.responses import HTMLResponse
from modules.registry import build_skills
from pydantic import BaseModel
from stt import WhisperTranscriber
from tts import PiperSpeaker

from config_store import load_config, set_feature, update_config
from runtime_state import runtime_state


app = FastAPI(title="Voice Assistant Control Plane", version="1.0.0")
runtime_state.attach_logger()
_pipeline: dict[str, Any] = {}
logger = logging.getLogger(__name__)


class ToggleRequest(BaseModel):
    feature: str
    enabled: bool


class ConfigPatchRequest(BaseModel):
    patch: dict[str, Any]


class TextRequest(BaseModel):
    text: str


FEATURE_LABELS: dict[str, str] = {
    "cloud_ai": "Cloud AI",
    "local_fallback": "Local fallback",
    "local_only_mode": "Local-only mode",
    "skills_engine": "Skills engine",
    "conversation_memory": "Conversation memory",
    "wake_word": "Wake word",
    "piper_tts": "Piper TTS",
    "web_tts": "Web TTS",
    "debug_logging": "Debug logging",
}

ROADMAP_STATUSES = [
    "implemented",
    "in_progress",
    "planned",
    "experimental",
    "disabled",
    "deprecated",
]


def _get_pipeline() -> dict[str, Any]:
    if _pipeline:
        return _pipeline

    config = load_config()
    features = config.get("features", {})
    selected_skills = features.get("enabled_skills", ["help"])
    skills_enabled = bool(features.get("skills", True))
    skills = build_skills(enabled=skills_enabled, selected=selected_skills)
    ai_engine = AIEngine()
    router = Router(skills=skills, ai_handler=ai_engine.ask)

    _pipeline["transcriber"] = WhisperTranscriber()
    _pipeline["router"] = router
    _pipeline["speaker"] = PiperSpeaker()
    return _pipeline


def _reset_pipeline() -> None:
    _pipeline.clear()


@app.on_event("startup")
def warmup_pipeline() -> None:
    try:
        pipeline = _get_pipeline()
        # Force model load once at startup to avoid long first request latency.
        _ = pipeline["transcriber"].model
    except Exception as exc:
        logger.warning("Control plane warmup failed: %s", exc)


@app.get("/", response_class=HTMLResponse)
def ui() -> str:
    return """<!doctype html>
<html lang=\"ru\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>Control Plane</title>
  <style>
    :root {
      --bg: linear-gradient(145deg, #f4eee8, #e7f0ec);
      --surface: #ffffffcc;
      --text: #102018;
      --muted: #4f6f60;
      --accent: #0d8f68;
      --border: #1a6b4f33;
      --chip: #f0f8f4;
    }

    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: "IBM Plex Sans", "Segoe UI", sans-serif;
      background: var(--bg);
      color: var(--text);
      min-height: 100vh;
      padding: 18px;
      overflow-x: hidden;
    }

    .wrap {
      width: min(100%, 980px);
      max-width: 980px;
      margin: 0 auto;
      display: grid;
      gap: 16px;
    }

    .card {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 16px;
      box-shadow: 0 10px 25px #0f322422;
    }

    h1 {
      margin: 0;
      font-size: 32px;
      font-family: "Space Grotesk", "Segoe UI", sans-serif;
    }

    h2 {
      margin: 0 0 12px;
      font-size: 20px;
      font-family: "Space Grotesk", "Segoe UI", sans-serif;
    }

    .sub {
      color: var(--muted);
      margin-top: 6px;
    }

    .grid {
      display: grid;
      gap: 12px;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    }

    .metric {
      border: 1px solid var(--border);
      background: #f9fdfb;
      border-radius: 10px;
      padding: 10px;
    }

    .metric .k {
      color: var(--muted);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: .05em;
    }

    .metric .v {
      font-weight: 700;
      font-size: 19px;
      margin-top: 3px;
    }

    .switches {
      display: grid;
      gap: 8px;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    }

    .sw {
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 9px;
      background: #f8fcfa;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
    }

    .roadmap {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
      gap: 10px;
    }

    .group {
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 8px;
      background: #fafdfe;
    }

    .group h3 {
      margin: 0 0 8px;
      color: var(--accent);
      font-size: 13px;
      text-transform: uppercase;
      letter-spacing: .04em;
    }

    .chip {
      background: var(--chip);
      border: 1px solid var(--border);
      border-radius: 9px;
      padding: 5px 7px;
      margin-bottom: 5px;
      font-size: 13px;
    }

    pre {
      max-height: 160px;
      overflow: auto;
      white-space: pre-wrap;
      overflow-wrap: anywhere;
      word-break: break-word;
      background: #0f1613;
      color: #d9f8e8;
      border-radius: 8px;
      padding: 10px;
      font-size: 12px;
    }
  </style>
</head>
<body>
  <div class=\"wrap\">
    <section class=\"card\">
      <h1>Control Plane</h1>
      <div class=\"sub\">Панель разработчика и управления системой ассистента</div>
    </section>

    <section class=\"card\">
      <h2>Runtime Dashboard</h2>
      <div id=\"metrics\" class=\"grid\"></div>
      <h3>Последние запросы</h3>
      <pre id=\"requests\">[]</pre>
      <h3>Состояние сервисов</h3>
      <pre id=\"services\">{}</pre>
    </section>

    <section class=\"card\">
      <h2>Feature Switch Panel</h2>
      <div id=\"switches\" class=\"switches\"></div>
    </section>

    <section class=\"card\">
      <h2>Architecture Explorer</h2>
      <div id=\"roadmap\" class=\"roadmap\"></div>
    </section>

    <section class=\"card\">
      <h2>Voice Trigger</h2>
      <div class=\"sub\">Запись с микрофона браузера, отправка в STT/AI/TTS</div>
      <div style=\"margin-top:10px; display:flex; gap:10px; align-items:center; flex-wrap:wrap;\">
        <button id=\"voiceBtn\" style=\"border:1px solid var(--border); background:#e9fff5; color:#0f4f38; border-radius:8px; padding:10px 14px; font-weight:700; cursor:pointer;\">Start recording</button>
        <label style=\"display:flex; align-items:center; gap:6px;\">
          <input id=\"speakToggle\" type=\"checkbox\" checked />
          Озвучить ответ (TTS)
        </label>
        <label style=\"display:flex; align-items:center; gap:6px;\">
          STT model:
          <select id=\"sttModelSel\" style=\"padding:6px 8px; border:1px solid var(--border); border-radius:8px;\">
            <option value=\"tiny\">tiny</option>
            <option value=\"base\">base</option>
            <option value=\"small\">small</option>
            <option value=\"medium\">medium</option>
            <option value=\"large-v3\">large-v3</option>
          </select>
        </label>
        <button id=\"applySttBtn\" style=\"border:1px solid var(--border); background:#fff; border-radius:8px; padding:8px 10px; cursor:pointer;\">Apply STT</button>
      </div>
      <div style=\"margin-top:10px; display:flex; gap:10px; align-items:center; flex-wrap:wrap;\">
        <input id=\"textInput\" type=\"text\" placeholder=\"Введите вопрос\" style=\"flex:1; min-width:220px; padding:10px; border:1px solid var(--border); border-radius:8px;\" />
        <button id=\"sendTextBtn\" style=\"border:1px solid var(--border); background:#f4fffa; border-radius:8px; padding:10px 12px; cursor:pointer;\">Send text</button>
        <button id=\"retryBtn\" style=\"border:1px solid var(--border); background:#fff; border-radius:8px; padding:10px 12px; cursor:pointer;\">Retry last</button>
      </div>
      <pre id=\"voiceResult\">Ожидание записи...</pre>
    </section>

    <section class=\"card\">
      <h2>Runtime Logs</h2>
      <pre id=\"logs\">[]</pre>
    </section>
  </div>

  <script>
    const metricKeys = {
      active_ai_model: "Active AI model",
      ai_mode: "AI mode",
      stt_model: "STT model",
      tts_model: "TTS model",
      ram_usage_mb: "RAM, MB",
      avg_response_time_ms: "Avg response, ms"
    };

    async function getJson(url) {
      const res = await fetch(url);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return res.json();
    }

    function renderMetrics(status) {
      const node = document.getElementById("metrics");
      node.innerHTML = "";
      for (const [key, label] of Object.entries(metricKeys)) {
        const el = document.createElement("div");
        el.className = "metric";
        el.innerHTML = `<div class=\"k\">${label}</div><div class=\"v\">${status[key]}</div>`;
        node.appendChild(el);
      }
      document.getElementById("requests").textContent = JSON.stringify(status.recent_requests, null, 2);
      document.getElementById("services").textContent = JSON.stringify(status.services, null, 2);
    }

    async function toggle(feature, enabled) {
      await fetch("/api/toggle", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ feature, enabled })
      });
      await refresh();
    }

    function renderSwitches(features) {
      const node = document.getElementById("switches");
      node.innerHTML = "";
      useWebTts = false;

      for (const item of features.items) {
        if (item.key === "web_tts") {
          useWebTts = !!item.enabled;
        }

        const row = document.createElement("div");
        row.className = "sw";

        const name = document.createElement("span");
        name.textContent = item.label;

        const check = document.createElement("input");
        check.type = "checkbox";
        check.checked = item.enabled;
        check.onchange = () => toggle(item.key, check.checked);

        row.appendChild(name);
        row.appendChild(check);
        node.appendChild(row);
      }
    }

    function renderRoadmap(roadmap) {
      const node = document.getElementById("roadmap");
      node.innerHTML = "";

      for (const [status, items] of Object.entries(roadmap.categories)) {
        const group = document.createElement("div");
        group.className = "group";
        group.innerHTML = `<h3>${status}</h3>`;

        for (const it of items) {
          const chip = document.createElement("div");
          chip.className = "chip";
          chip.textContent = it.component;
          group.appendChild(chip);
        }

        node.appendChild(group);
      }
    }

    function renderLogs(data) {
      document.getElementById("logs").textContent = JSON.stringify(data.logs, null, 2);
    }

    async function refresh() {
      const [status, features, roadmap, logs, config] = await Promise.all([
        getJson("/api/status"),
        getJson("/api/features"),
        getJson("/api/roadmap"),
        getJson("/api/logs"),
        getJson("/api/config")
      ]);
      renderMetrics(status);
      renderSwitches(features);
      renderRoadmap(roadmap);
      renderLogs(logs);
      const model = config?.stt?.model || "small";
      if (sttModelSel) {
        sttModelSel.value = model;
      }
    }

    let recorder = null;
    let chunks = [];
    let useWebTts = false;
    let autoStopTimer = null;
    let lastPrompt = "";
    const voiceBtn = document.getElementById("voiceBtn");
    const voiceResult = document.getElementById("voiceResult");
    const speakToggle = document.getElementById("speakToggle");
    const sttModelSel = document.getElementById("sttModelSel");
    const applySttBtn = document.getElementById("applySttBtn");
    const textInput = document.getElementById("textInput");
    const sendTextBtn = document.getElementById("sendTextBtn");
    const retryBtn = document.getElementById("retryBtn");
    const MAX_RECORDING_MS = 6000;

    function speakInBrowser(text) {
      if (!text || !("speechSynthesis" in window)) return;
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = "ru-RU";
      utterance.rate = 1.0;
      utterance.pitch = 1.0;
      window.speechSynthesis.cancel();
      window.speechSynthesis.speak(utterance);
    }

    async function sendRecording(blob) {
      const formData = new FormData();
      formData.append("audio", blob, "voice.webm");

      const backendSpeak = speakToggle.checked && !useWebTts;
      const res = await fetch(`/api/interact/upload?speak=${backendSpeak}`, {
        method: "POST",
        body: formData
      });
      if (!res.ok) {
        const body = await res.text();
        throw new Error(body || `HTTP ${res.status}`);
      }
      return res.json();
    }

    async function sendText(text) {
      const backendSpeak = speakToggle.checked && !useWebTts;
      const res = await fetch(`/api/interact/text?speak=${backendSpeak}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text })
      });
      if (!res.ok) {
        const body = await res.text();
        throw new Error(body || `HTTP ${res.status}`);
      }
      return res.json();
    }

    async function runTextInteraction(text) {
      const trimmed = (text || "").trim();
      if (!trimmed) return;

      voiceResult.textContent = "Отправка текста...";
      lastPrompt = trimmed;
      textInput.value = trimmed;
      try {
        const result = await sendText(trimmed);
        voiceResult.textContent = JSON.stringify(result, null, 2);
        if (speakToggle.checked && result.answer && (useWebTts || !result.spoken)) {
          speakInBrowser(result.answer);
        }
        await refresh();
      } catch (err) {
        voiceResult.textContent = `Ошибка: ${err.message}`;
      }
    }

    sendTextBtn.onclick = async () => {
      await runTextInteraction(textInput.value);
    };

    textInput.addEventListener("keydown", async (event) => {
      if (event.key !== "Enter") return;
      event.preventDefault();
      await runTextInteraction(textInput.value);
    });

    retryBtn.onclick = async () => {
      await runTextInteraction(lastPrompt || textInput.value);
    };

    applySttBtn.onclick = async () => {
      const selected = sttModelSel.value;
      try {
        await fetch("/api/config", {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ patch: { stt: { model: selected } } })
        });
        voiceResult.textContent = `STT model переключен на ${selected}.`;
        await refresh();
      } catch (err) {
        voiceResult.textContent = `Ошибка смены STT: ${err.message}`;
      }
    };

    voiceBtn.onclick = async () => {
      try {
        if (recorder && recorder.state === "recording") {
          if (autoStopTimer) {
            clearTimeout(autoStopTimer);
            autoStopTimer = null;
          }
          recorder.stop();
          return;
        }

        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        chunks = [];
        recorder = new MediaRecorder(stream);
        recorder.ondataavailable = (e) => chunks.push(e.data);

        recorder.onstop = async () => {
          if (autoStopTimer) {
            clearTimeout(autoStopTimer);
            autoStopTimer = null;
          }
          voiceBtn.textContent = "Start recording";
          const blob = new Blob(chunks, { type: "audio/webm" });
          voiceResult.textContent = "Отправка и обработка...";
          try {
            const result = await sendRecording(blob);
            voiceResult.textContent = JSON.stringify(result, null, 2);
            if (result.transcript) {
              lastPrompt = result.transcript;
              textInput.value = result.transcript;
            }
            if (speakToggle.checked && result.answer && (useWebTts || !result.spoken)) {
              speakInBrowser(result.answer);
            }
            await refresh();
          } catch (err) {
            voiceResult.textContent = `Ошибка: ${err.message}`;
          } finally {
            stream.getTracks().forEach((t) => t.stop());
          }
        };

        recorder.start();
        autoStopTimer = setTimeout(() => {
          if (recorder && recorder.state === "recording") {
            recorder.stop();
          }
        }, MAX_RECORDING_MS);
        voiceBtn.textContent = "Stop recording";
        voiceResult.textContent = "Идет запись (макс 6 сек)...";
      } catch (err) {
        voiceResult.textContent = `Ошибка доступа к микрофону: ${err.message}`;
      }
    };

    refresh();
    setInterval(refresh, 3000);
  </script>
</body>
</html>"""


@app.get("/api/status")
def get_status() -> dict[str, Any]:
    config = load_config()
    ai_cfg = config.get("ai", {})
    stt_cfg = config.get("stt", {})
    tts_cfg = config.get("tts", {})

    active_model = ai_cfg.get("cloud_model", "unknown")
    if ai_cfg.get("mode") == "local":
        active_model = ai_cfg.get("local_model", active_model)

    features = config.get("features", {})
    services = {
        "openai": "enabled" if features.get("cloud_ai", ai_cfg.get("cloud_enabled", False)) else "disabled",
        "local_llm": "enabled" if features.get("local_fallback", ai_cfg.get("local_enabled", False)) else "disabled",
        "skills_engine": "enabled" if features.get("skills_engine", False) else "disabled",
        "wake_word": "enabled" if features.get("wake_word", False) else "disabled",
        "stt": stt_cfg.get("engine", "unknown"),
        "tts": tts_cfg.get("engine", "unknown"),
    }

    return {
        "active_ai_model": active_model,
        "ai_mode": ai_cfg.get("mode", "hybrid"),
        "stt_model": stt_cfg.get("model", stt_cfg.get("engine", "unknown")),
        "tts_model": tts_cfg.get("model", tts_cfg.get("engine", "unknown")),
        "ram_usage_mb": runtime_state.memory_usage_mb(),
        "avg_response_time_ms": runtime_state.average_latency_ms(),
        "recent_requests": runtime_state.recent_requests(limit=10),
        "services": services,
    }


@app.get("/api/features")
def get_features() -> dict[str, Any]:
    config = load_config()
    features = config.get("features", {})

    items = []
    for key, label in FEATURE_LABELS.items():
        items.append({"key": key, "label": label, "enabled": bool(features.get(key, False))})

    return {
        "items": items,
        "raw": features,
    }


@app.get("/api/config")
def get_config() -> dict[str, Any]:
    return load_config()


@app.put("/api/config")
def patch_config(payload: ConfigPatchRequest) -> dict[str, Any]:
    if not isinstance(payload.patch, dict):
        raise HTTPException(status_code=400, detail="patch must be an object")
    updated = update_config(payload.patch)
    _reset_pipeline()
    return updated


@app.post("/api/toggle")
def toggle_feature(payload: ToggleRequest) -> dict[str, Any]:
    if payload.feature not in FEATURE_LABELS:
        raise HTTPException(status_code=400, detail=f"unknown feature: {payload.feature}")
    config = set_feature(payload.feature, payload.enabled)
    _reset_pipeline()
    return {
        "ok": True,
        "feature": payload.feature,
        "enabled": payload.enabled,
        "features": config.get("features", {}),
    }


@app.get("/api/logs")
def get_logs(limit: int = 100) -> dict[str, Any]:
    return {
        "logs": runtime_state.log_handler.get_logs(limit=max(1, min(limit, 400))),
    }


@app.get("/api/roadmap")
def get_roadmap() -> dict[str, Any]:
    config = load_config()
    entries = config.get("roadmap", [])
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for status in ROADMAP_STATUSES:
        groups[status] = []

    for item in entries:
        if not isinstance(item, dict):
            continue
        status = str(item.get("status", "planned")).lower()
        if status not in groups:
            groups[status] = []
        groups[status].append(item)

    return {
        "categories": groups,
    }


@app.post("/api/interact/text")
def interact_text(
    payload: TextRequest,
    speak: bool = Query(default=True),
) -> dict[str, Any]:
    text = payload.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="text is required")

    pipeline = _get_pipeline()
    router: Router = pipeline["router"]
    speaker: PiperSpeaker = pipeline["speaker"]

    started = time.perf_counter()
    ai_started = time.perf_counter()
    answer = router.route(text)
    ai_ms = round((time.perf_counter() - ai_started) * 1000, 2)

    spoken = False
    tts_error = ""
    tts_ms = 0.0
    if speak and answer:
        tts_started = time.perf_counter()
        try:
            speaker(answer)
            spoken = True
        except Exception as exc:
            tts_error = str(exc)
        tts_ms = round((time.perf_counter() - tts_started) * 1000, 2)

    return {
        "transcript": text,
        "answer": answer,
        "spoken": spoken,
        "tts_error": tts_error,
        "stt_ms": 0.0,
        "ai_ms": ai_ms,
        "tts_ms": tts_ms,
        "latency_ms": round((time.perf_counter() - started) * 1000, 2),
    }


@app.post("/api/interact/upload")
async def interact_upload(
    audio: UploadFile = File(...),
    speak: bool = Query(default=True),
) -> dict[str, Any]:
    if not audio.filename:
        raise HTTPException(status_code=400, detail="audio file is required")

    pipeline = _get_pipeline()
    transcriber: WhisperTranscriber = pipeline["transcriber"]
    router: Router = pipeline["router"]
    speaker: PiperSpeaker = pipeline["speaker"]

    suffix = ".webm"
    if "." in audio.filename:
        suffix = "." + audio.filename.rsplit(".", 1)[-1]

    content = await audio.read()
    if not content:
        raise HTTPException(status_code=400, detail="empty audio payload")

    tts_error = ""
    with tempfile.NamedTemporaryFile(delete=True, suffix=suffix) as handle:
        handle.write(content)
        handle.flush()

        started = time.perf_counter()
        stt_started = time.perf_counter()
        text = transcriber(handle.name)
        stt_ms = round((time.perf_counter() - stt_started) * 1000, 2)

        ai_started = time.perf_counter()
        answer = router.route(text) if text else ""
        ai_ms = round((time.perf_counter() - ai_started) * 1000, 2)

        spoken = False
        tts_ms = 0.0
        if speak and answer:
            tts_started = time.perf_counter()
            try:
                speaker(answer)
                spoken = True
            except Exception as exc:
                tts_error = str(exc)
            tts_ms = round((time.perf_counter() - tts_started) * 1000, 2)
        latency = round((time.perf_counter() - started) * 1000, 2)

    return {
        "transcript": text,
        "answer": answer,
        "spoken": spoken,
        "tts_error": tts_error,
        "stt_ms": stt_ms,
        "ai_ms": ai_ms,
        "tts_ms": tts_ms,
        "latency_ms": latency,
    }
