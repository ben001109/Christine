from pathlib import Path


def _source() -> str:
    return Path("christine_final.py").read_text(encoding="utf-8")


def _v10_ask_block() -> str:
    text = _source()
    start = text.index("V10 ask()")
    end = text.index("# === BUILT-IN EVOLUTION ADDON ===", start)
    return text[start:end]


def test_v10_ask_delegates_user_message_to_session_helper():
    text = _source()
    block = _v10_ask_block()

    assert "from christine.conversation.session import" in text
    assert "append_user_message(conv, inp)" in block
    assert 'conv.append({"role":"user","content":inp})' not in block


def test_v10_ask_delegates_reply_memory_update_to_session_helper():
    block = _v10_ask_block()

    assert "commit_assistant_turn(" in block
    assert "save_memory=sm" in block
    assert 'conv.append({"role":"assistant","content":reply})' not in block
    assert 'mem["tc"]=mem.get("tc",0)+1' not in block
    assert 'mem["lc"]=datetime.datetime.now().strftime("%Y-%m-%d %H:%M")' not in block
    assert "sm(mem)" not in block
