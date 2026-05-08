from pathlib import Path


def test_policy_router_is_not_wired_into_monolith_yet():
    text = Path("christine_final.py").read_text(encoding="utf-8", errors="ignore")

    assert "route_with_policy" not in text
    assert "allow_side_effect_targets=True" not in text


def test_runtime_routing_hook_is_wired_as_disabled_observation_only():
    text = Path("christine_final.py").read_text(encoding="utf-8", errors="ignore")

    assert "observe_direct_runtime_route" in text
    assert "RuntimeRoutingHook(enabled=False)" in text
    assert "_v180_observe_runtime_route(" in text
    assert "import RuntimeRoutingHook, observe_runtime_route" not in text
    assert " observe_runtime_route(" not in text
    assert "allow_side_effect_targets=True" not in text
