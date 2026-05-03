from christine.deployment.protocol import HealthStatus


def test_health_status_serializes_core_fields():
    status = HealthStatus(ok=True, service="christine", detail="ready")

    assert status.to_dict() == {"ok": True, "service": "christine", "detail": "ready"}
