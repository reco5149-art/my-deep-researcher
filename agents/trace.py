"""실행 기록. 누가 무엇을 읽고 무엇을 썼는지 전부 output/traces/<실행ID>.json 에 남긴다."""
import json
import threading
import time
from datetime import datetime
from pathlib import Path

import config


class RunTrace:
    def __init__(self, run_id: str, base: dict, progress=None):
        self.run_id = run_id
        self.path = config.TRACES_DIR / f"{run_id}.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.data = {**base, "run_id": run_id, "events": [], "sections": {},
                     "started_at": datetime.now().isoformat(timespec="seconds")}
        self._lock = threading.RLock()
        self._t0 = time.time()
        self._progress = progress

    def log(self, who: str, text: str) -> None:
        with self._lock:
            event = {"t": round(time.time() - self._t0, 1), "who": who, "text": text}
            self.data["events"].append(event)
        if self._progress:
            try:
                self._progress(f"[{event['t']:>6.1f}s] {who}: {text}")
            except Exception:
                pass

    def section(self, sid: str) -> dict:
        with self._lock:
            return self.data["sections"].setdefault(sid, {})

    def set(self, key: str, value) -> None:
        with self._lock:
            self.data[key] = value

    def save(self) -> None:
        with self._lock:
            self.data["elapsed_sec"] = round(time.time() - self._t0, 1)
            text = json.dumps(self.data, ensure_ascii=False, indent=1)
        self.path.write_text(text, encoding="utf-8")


def load_trace(path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))
