import christine_g3_frontier as g3


def test_contract_web_is_research():
    c = g3.ContractParser().parse("去網上查陳大坑")
    assert c.operation == "research"
    assert c.requires_web is True


def test_contract_python_is_code_not_web():
    c = g3.ContractParser().parse("寫一個很難的 python 爬蟲")
    assert c.operation == "create"
    assert c.output_kind == "code"
    assert c.requires_web is False


def test_contract_image_is_image():
    c = g3.ContractParser().parse("生成一張 Christine 網頁設計圖")
    assert c.output_kind == "image"


def test_argus_rejects_text_for_code():
    c = g3.ContractParser().parse("寫一個 python 程式")
    ok, reason = g3.ARGUS.verify(c, "我可以幫你寫程式", [])
    assert not ok
    assert reason == "expected-code-artifact"


def test_argus_accepts_valid_python():
    c = g3.ContractParser().parse("寫一個 python 程式")
    ok, reason = g3.ARGUS.verify(c, "```python\nprint('hi')\n```", [])
    assert ok


def test_math_does_not_need_web():
    c = g3.ContractParser().parse("1+31021242是多少")
    assert c.operation == "compute"
    assert c.requires_web is False


def test_web_required_without_evidence_rejected():
    c = g3.ContractParser().parse("去網上查陳大坑")
    ok, reason = g3.ARGUS.verify(c, "5D9A 沒有資料", [])
    assert not ok
    assert reason == "web-required-but-no-evidence"


def test_current_turn_does_not_include_previous_answer():
    c = g3.ContractParser().parse("寫個 python 程式給我")
    assert "陳大坑" not in c.goal
