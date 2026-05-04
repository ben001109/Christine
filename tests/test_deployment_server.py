from urllib.error import HTTPError
from urllib.request import Request, urlopen
import json
import threading

from christine.deployment.protocol import HealthStatus
from christine.deployment.server import (
    HealthServerConfig,
    build_health_payload,
    create_health_server,
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


def test_route_health_request_handles_provider_failures():
    def broken_status():
        raise RuntimeError("boom")

    status_code, payload = route_health_request("/health", status_provider=broken_status)

    assert status_code == 503
    assert payload == {"ok": False, "service": "christine", "detail": "unavailable"}


def test_health_server_config_defaults_to_loopback():
    config = HealthServerConfig()

    assert config.host == "127.0.0.1"
    assert config.port == 8765


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


def test_create_health_server_rejects_post_with_json_405():
    server = create_health_server(HealthServerConfig(port=0))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address
        request = Request(f"http://{host}:{port}/health", data=b"{}", method="POST")
        try:
            urlopen(request, timeout=5)
        except HTTPError as response:
            payload = json.loads(response.read().decode("utf-8"))
            assert response.code == 405
            assert payload == {"ok": False, "service": "christine", "detail": "method not allowed"}
        else:
            raise AssertionError("POST /health unexpectedly succeeded")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
