from pathlib import Path


def test_boot_launcher_does_not_start_deployment_server():
    text = Path("boot_christine.py").read_text(encoding="utf-8")

    assert "create_health_server" not in text
    assert "serve_forever" not in text


def test_deployment_server_does_not_import_monolith():
    text = Path("christine/deployment/server.py").read_text(encoding="utf-8")

    assert "christine_final" not in text
    assert "boot_christine" not in text
