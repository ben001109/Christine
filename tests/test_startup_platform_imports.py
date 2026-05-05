from pathlib import Path


def _early_import_block() -> str:
    text = Path("christine_final.py").read_text(encoding="utf-8", errors="ignore")
    start = text.index("CHRISTINE_VERSION")
    end = text.index("# ═══ V22", start)
    return text[start:end]


def test_monolith_bootstrap_does_not_import_windows_audio_unconditionally():
    block = _early_import_block()

    assert "\nimport pyaudiowpatch as pyaudio\n" not in block
    assert "\nimport anthropic,speech_recognition as sr,edge_tts,psutil,msvcrt\n" not in block
    assert "try:\n    import pyaudiowpatch as pyaudio" in block
    assert "try:\n    import msvcrt" in block
