from pathlib import Path


def _v1480_block() -> str:
    text = Path("christine_final.py").read_text(encoding="utf-8")
    start = text.index("V1480  Christine 自己的大腦")
    end = text.index("except Exception as _e_v180:", start)
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


def test_v1480_dream_command_does_not_wrap_unavailable_as_success():
    block = _v1480_block()
    start = block.index("r = brain_dream(n)")
    end = block.index("# ── V1484 混合模式", start)
    dream_command = block[start:end]

    assert "if isinstance(r, str):" in dream_command
    assert "return r" in dream_command
