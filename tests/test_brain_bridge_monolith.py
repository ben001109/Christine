from pathlib import Path


def _v1480_block() -> str:
    text = Path("christine_final.py").read_text(encoding="utf-8")
    start = text.index("V1480  Christine 自己的大腦")
    end = text.index("V1483 AutoBoot", start)
    return text[start:end]


def test_v1480_uses_brain_bridge_service_for_construction():
    block = _v1480_block()

    assert "from christine.brain_bridge.service import BrainService, BrainServiceConfig" in block
    assert "_V1480_SERVICE" in block
    assert "from brain.brain import build_default_brain" not in block


def test_v1480_preserves_legacy_brain_globals():
    block = _v1480_block()

    assert 'globals()["brain_say"] = brain_say' in block
    assert 'globals()["brain_dream"] = brain_dream' in block
    assert 'globals()["brain_understand"] = brain_understand' in block
    assert "_V1480_CFG" in block
    assert "_V1480_BRAIN" in block
