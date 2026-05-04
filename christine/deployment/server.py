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
        try:
            return 200, build_health_payload(status_provider())
        except Exception:
            return 503, HealthStatus(ok=False, service="christine", detail="unavailable").to_dict()
    return 404, HealthStatus(ok=False, service="christine", detail="not found").to_dict()


def route_method_not_allowed() -> tuple[int, dict]:
    return 405, HealthStatus(ok=False, service="christine", detail="method not allowed").to_dict()


def _send_json(handler: BaseHTTPRequestHandler, status_code: int, payload: dict) -> None:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status_code)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def _handler_class(status_provider: StatusProvider) -> type[BaseHTTPRequestHandler]:
    class ChristineHealthHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            status_code, payload = route_health_request(self.path, status_provider)
            _send_json(self, status_code, payload)

        def do_POST(self) -> None:
            status_code, payload = route_method_not_allowed()
            _send_json(self, status_code, payload)

        def log_message(self, format: str, *args) -> None:
            return

    return ChristineHealthHandler


def create_health_server(
    config: HealthServerConfig | None = None,
    status_provider: StatusProvider = default_health_status,
) -> ThreadingHTTPServer:
    cfg = config or HealthServerConfig()
    return ThreadingHTTPServer((cfg.host, int(cfg.port)), _handler_class(status_provider))
