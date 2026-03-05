from __future__ import annotations

import logging
import resource
import time
from collections import deque
from threading import Lock
from typing import Any


class InMemoryLogHandler(logging.Handler):
    def __init__(self, max_entries: int = 400):
        super().__init__()
        self._records: deque[str] = deque(maxlen=max_entries)

    def emit(self, record: logging.LogRecord) -> None:
        self._records.append(self.format(record))

    def get_logs(self, limit: int = 100) -> list[str]:
        return list(self._records)[-limit:]


class RuntimeState:
    def __init__(self, max_requests: int = 50):
        self._lock = Lock()
        self._request_history: deque[dict[str, Any]] = deque(maxlen=max_requests)
        self._latencies_ms: deque[float] = deque(maxlen=max_requests)
        self.log_handler = InMemoryLogHandler(max_entries=400)

    def attach_logger(self, logger: logging.Logger | None = None) -> None:
        target_logger = logger or logging.getLogger()
        if self.log_handler in target_logger.handlers:
            return

        self.log_handler.setLevel(logging.INFO)
        self.log_handler.setFormatter(
            logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
        )
        target_logger.addHandler(self.log_handler)

    def record_request(
        self,
        text: str,
        answer: str,
        latency_ms: float,
        engine: str,
    ) -> None:
        payload = {
            "timestamp": int(time.time()),
            "text": text,
            "answer": answer,
            "latency_ms": round(latency_ms, 2),
            "engine": engine,
        }

        with self._lock:
            self._request_history.append(payload)
            self._latencies_ms.append(latency_ms)

    def average_latency_ms(self) -> float:
        with self._lock:
            if not self._latencies_ms:
                return 0.0
            return round(sum(self._latencies_ms) / len(self._latencies_ms), 2)

    def recent_requests(self, limit: int = 10) -> list[dict[str, Any]]:
        with self._lock:
            return list(self._request_history)[-limit:]

    def memory_usage_mb(self) -> float:
        usage_kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        # macOS reports bytes, Linux reports kilobytes.
        if usage_kb > 10_000_000:
            return round(usage_kb / (1024 * 1024), 2)
        return round(usage_kb / 1024, 2)


runtime_state = RuntimeState()
