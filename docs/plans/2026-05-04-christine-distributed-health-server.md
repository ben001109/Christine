# Christine Distributed Health Server Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add the first local distributed server process surface: a safe `/health` HTTP endpoint that exposes no tool control and does not start unless explicitly called.

**Architecture:** Implement a stdlib-only health server in `christine.deployment.server` using `http.server.ThreadingHTTPServer`. Reuse `HealthStatus` from `christine.deployment.protocol`, keep import-time side effects at zero, and provide pure request-routing helpers that can be tested without starting Christine.

**Tech Stack:** Python 3.10+, stdlib `http.server`, `json`, `threading`, `urllib.request` in tests, uv, pytest. No new runtime dependencies.

---

## Requirements Captured

- Local-first distributed readiness without cloud dependency.
- Do not start a server at import time.
- Do not expose tool execution, memory mutation, GUI control, or runtime state modification.
- Do not require optional `fastapi` or `uvicorn` for this first server wave.
- Preserve existing entry points: `boot_christine.py`, `christine_final.py`, Windows launchers.
- Keep health payload compatible with existing `HealthStatus.to_dict()`.
- Do not import `christine_final.py` from tests.
- Do not change persisted data formats or runtime artifacts.

## Current Facts

- `christine/deployment/protocol.py` already defines `HealthStatus(ok, service, detail).to_dict()`.
- `tests/test_deployment_protocol.py` already verifies the protocol dict shape.
- `pyproject.toml` has an optional `distributed` extra for future FastAPI/Uvicorn/httpx, but default `uv sync` does not install FastAPI/Uvicorn.
- This wave should not alter `boot_christine.py` or auto-start server behavior.

## Out Of Scope

- Remote tool execution.
- Authentication, API keys, TLS, or network exposure beyond explicit host/port config.
- FastAPI/Uvicorn integration.
- Background daemon management.
- GUI or Windows launcher changes.

---

### Task 1: Add Distributed Health Server Contract Tests

**Files:**
- Create: `tests/test_deployment_server.py`
- Create later: `christine/deployment/server.py`
- Modify later: `christine/deployment/__init__.py`

**Step 1: Write failing pure routing tests**

Create `tests/test_deployment_server.py`:

```python
from christine.deployment.protocol import HealthStatus
from christine.deployment.server import (
    HealthServerConfig,
    build_health_payload,
    route_health_request,
)


def test_build_health_payload_reuses_protocol_shape():
    payload = build_health_payload(HealthStatus(ok=True, service="christine", detail="ready"))

    assert payload == {"ok": True, "service": "christine", "detail": "ready"}


def test_route_health_request_serves_health_only():
    status_code, payload = route_health_request(
        "/health",
        status_provider=lambda: HealthStatus(ok=True, service="christine", detail="ready"),
    )

    assert status_code == 200
    assert payload == {"ok": True, "service": "christine", "detail": "ready"}


def test_route_health_request_rejects_unknown_paths():
    status_code, payload = route_health_request("/tools")

    assert status_code == 404
    assert payload == {"ok": False, "service": "christine", "detail": "not found"}


def test_health_server_config_defaults_to_loopback():
    config = HealthServerConfig()

    assert config.host == "127.0.0.1"
    assert config.port == 8765
```

**Step 2: Write failing HTTP smoke test**

Add:

```python
from urllib.request import urlopen
import json
import threading

from christine.deployment.server import create_health_server


def test_create_health_server_serves_health_endpoint():
    server = create_health_server(
        HealthServerConfig(port=0),
        status_provider=lambda: HealthStatus(ok=True, service="christine", detail="ready"),
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address
        with urlopen(f"http://{host}:{port}/health", timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))
        assert payload == {"ok": True, "service": "christine", "detail": "ready"}
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
```

**Step 3: Run RED**

Run: `uv run pytest tests/test_deployment_server.py -q`

Expected: fail with missing `christine.deployment.server`.

---

### Task 2: Implement Stdlib Health Server

**Files:**
- Create: `christine/deployment/server.py`
- Modify: `christine/deployment/__init__.py`
- Modify: `tests/test_deployment_server.py` only if needed for import/style.

**Step 1: Implement config and pure helpers**

Create `christine/deployment/server.py`:

```python
from __future__ import annotations

from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from typing import Callable

from .protocol import HealthStatus


StatusProvider = Callable[[], HealthStatus]


@dataclass(frozen=True)
class HealthServerConfig:
    host: str = "127.0.0.1"
    port: int = 8765


def default_health_status() -> HealthStatus:
    return HealthStatus(ok=True, service="christine", detail="ready")


def build_health_payload(status: HealthStatus | None = None) -> dict:
    return (status or default_health_status()).to_dict()


def route_health_request(
    path: str,
    status_provider: StatusProvider = default_health_status,
) -> tuple[int, dict]:
    if path == "/health":
        return 200, build_health_payload(status_provider())
    return 404, HealthStatus(ok=False, service="christine", detail="not found").to_dict()
```

**Step 2: Implement HTTP handler factory**

Add to `server.py`:

```python
def _handler_class(status_provider: StatusProvider) -> type[BaseHTTPRequestHandler]:
    class ChristineHealthHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            status_code, payload = route_health_request(self.path, status_provider)
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status_code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args) -> None:
            return

    return ChristineHealthHandler


def create_health_server(
    config: HealthServerConfig | None = None,
    status_provider: StatusProvider = default_health_status,
) -> ThreadingHTTPServer:
    cfg = config or HealthServerConfig()
    return ThreadingHTTPServer((cfg.host, int(cfg.port)), _handler_class(status_provider))
```

**Step 3: Export from deployment package**

Modify `christine/deployment/__init__.py`:

```python
"""Deployment protocol primitives for Christine."""

from .protocol import HealthStatus
from .server import HealthServerConfig, build_health_payload, create_health_server, route_health_request

__all__ = [
    "HealthStatus",
    "HealthServerConfig",
    "build_health_payload",
    "create_health_server",
    "route_health_request",
]
```

**Step 4: Run focused tests**

Run: `uv run pytest tests/test_deployment_server.py tests/test_deployment_protocol.py -q`

Expected: pass.

**Step 5: Run compile check**

Run: `uv run python -m compileall -q -x "brain/generated" boot_christine.py brain christine`

Expected: pass.

**Step 6: Commit**

Commit message: `refactor: add distributed health server`

---

### Task 3: Add Launcher-Safe Static Contract

**Files:**
- Create: `tests/test_deployment_server_contract.py`

**Step 1: Write static contract tests**

Create `tests/test_deployment_server_contract.py`:

```python
from pathlib import Path


def test_boot_launcher_does_not_start_deployment_server():
    text = Path("boot_christine.py").read_text(encoding="utf-8")

    assert "create_health_server" not in text
    assert "serve_forever" not in text


def test_deployment_server_does_not_import_monolith():
    text = Path("christine/deployment/server.py").read_text(encoding="utf-8")

    assert "christine_final" not in text
    assert "boot_christine" not in text
```

**Step 2: Run focused tests**

Run: `uv run pytest tests/test_deployment_server.py tests/test_deployment_server_contract.py -q`

Expected: pass.

**Step 3: Commit**

Commit message: `test: guard deployment server boundaries`

---

### Task 4: Final Verification And Review

**Files:**
- No new implementation files expected.

**Step 1: Run focused tests**

Run: `uv run pytest tests/test_deployment_server.py tests/test_deployment_server_contract.py tests/test_deployment_protocol.py -q`

Expected: pass.

**Step 2: Run full test suite**

Run: `uv run pytest -q`

Expected: pass.

**Step 3: Run compile gate**

Run: `uv run python -m compileall -q -x "brain/generated" boot_christine.py brain christine christine_final.py`

Expected: pass.

**Step 4: Run boot smoke**

Run: `uv run python boot_christine.py --check --notorch --fast --no-banner`

Expected: pass and print `自檢完成`.

**Step 5: Run whitespace diff check**

Run: `git diff --check`

Expected: no output.

**Step 6: Request code review**

Review requirements:

- Server has no import-time side effects.
- Server is loopback-only by default.
- Only `/health` is served.
- No tool execution or state mutation is exposed.
- `boot_christine.py` and `christine_final.py` behavior unchanged.
- No new dependencies added.

**Step 7: Fix review findings if needed**

Use TDD for behavior fixes, verify focused tests, and commit each verified fix.

**Step 8: Finish branch**

Use `finishing-a-development-branch` after review and verification are clean.

---

## Verification Gate For This Wave

```bash
uv run pytest tests/test_deployment_server.py tests/test_deployment_server_contract.py tests/test_deployment_protocol.py -q
uv run pytest -q
uv run python -m compileall -q -x "brain/generated" boot_christine.py brain christine christine_final.py
uv run python boot_christine.py --check --notorch --fast --no-banner
git diff --check
```

## Rollback Notes

- Revert only this branch's commits if the server surface regresses.
- Do not modify runtime state artifacts.
- Do not start any server automatically from launchers.
- If the HTTP smoke test is flaky on a platform, keep pure routing helpers and revisit the network smoke with a platform-specific skip reason.
