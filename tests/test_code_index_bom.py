import ast
from pathlib import Path


def test_utf8_sig_decode_removes_bom_before_ast_parse():
    source = b"\xef\xbb\xbfx = 1\n".decode("utf-8-sig")

    ast.parse(source)
    assert not source.startswith("\ufeff")


def test_monolith_code_index_reads_self_with_bom_tolerant_encoding():
    text = Path("christine_final.py").read_text(encoding="utf-8", errors="ignore")
    start = text.index("# ── Christine 快速程式碼索引")
    end = text.index("def self_quick_map", start)
    block = text[start:end]

    assert 'open(SELF_PATH, "r", encoding="utf-8-sig")' in block
    assert "_ast_module.parse(src)" in block


def test_current_monolith_source_bom_is_stripped_by_tolerant_decode():
    source = Path("christine_final.py").read_text(encoding="utf-8-sig")[:16]

    assert not source.startswith("\ufeff")
