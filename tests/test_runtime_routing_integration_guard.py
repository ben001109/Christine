from pathlib import Path


def test_policy_router_is_not_wired_into_monolith_yet():
    text = Path("christine_final.py").read_text(encoding="utf-8", errors="ignore")

    assert "route_with_policy" not in text
    assert "allow_side_effect_targets=True" not in text


def test_runtime_routing_hook_is_not_wired_into_monolith_yet():
    text = Path("christine_final.py").read_text(encoding="utf-8", errors="ignore")

    assert "observe_runtime_route" not in text
    assert "RuntimeRoutingHook" not in text
