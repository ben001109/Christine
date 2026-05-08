from christine.conversation import router
from christine.conversation.router import (
    augment_input_with_hint,
    dedupe_tool_specs,
    route_voice_then_fallback,
)


def test_dedupe_tool_specs_matches_legacy_name_priority():
    first = {"name": "capture_screen", "description": "old"}
    replacement = {"name": "capture_screen", "description": "new"}
    function_tool = {"function": {"name": "write_file"}, "description": "fn"}
    unnamed = {"description": "ignored legacy shape"}

    assert dedupe_tool_specs([first, function_tool, replacement, unnamed]) == [
        replacement,
        function_tool,
    ]


def test_augment_input_with_hint_preserves_legacy_newline_prefix():
    assert augment_input_with_hint("hello", "【Christine 大腦的即時感受】情緒=中性") == (
        "【Christine 大腦的即時感受】情緒=中性\nhello"
    )


def test_augment_input_with_hint_returns_original_when_disabled_or_empty():
    assert augment_input_with_hint("hello", "hint", enabled=False) == "hello"
    assert augment_input_with_hint("hello", "") == "hello"
    assert augment_input_with_hint("hello", None) == "hello"


def test_route_voice_then_fallback_returns_voice_result_without_fallback():
    calls = []

    def voice(inp):
        calls.append(("voice", inp))
        return "voice-result"

    def fallback(inp, *args, **kwargs):
        calls.append(("fallback", inp, args, kwargs))
        return "fallback-result"

    assert route_voice_then_fallback("hi", voice, fallback, lambda: "hint") == "voice-result"
    assert calls == [("voice", "hi")]


def test_route_voice_then_fallback_augments_before_fallback():
    seen = {}

    def fallback(inp, *args, **kwargs):
        seen["inp"] = inp
        seen["args"] = args
        seen["kwargs"] = kwargs
        return "fallback-result"

    result = route_voice_then_fallback(
        "hi",
        lambda inp: None,
        fallback,
        lambda: "hint",
        hybrid_enabled=True,
        args=("extra",),
        kwargs={"flag": True},
    )

    assert result == "fallback-result"
    assert seen == {"inp": "hint\nhi", "args": ("extra",), "kwargs": {"flag": True}}


def test_route_voice_then_fallback_ignores_hint_provider_errors():
    def broken_hint():
        raise RuntimeError("hint failed")

    seen = {}

    def fallback(inp):
        seen["inp"] = inp
        return "ok"

    assert route_voice_then_fallback("hi", lambda inp: None, fallback, broken_hint) == "ok"
    assert seen["inp"] == "hi"


def test_route_observed_voice_then_fallback_observes_before_voice():
    calls = []

    def observer(inp):
        calls.append(("observe", inp))

    def voice(inp):
        calls.append(("voice", inp))
        return "voice-result"

    def fallback(inp):
        calls.append(("fallback", inp))
        return "fallback-result"

    result = router.route_observed_voice_then_fallback(
        "hi", observer, voice, fallback, lambda: "hint"
    )

    assert result == "voice-result"
    assert calls == [("observe", "hi"), ("voice", "hi")]


def test_route_observed_voice_then_fallback_ignores_observer_errors():
    calls = []

    def observer(inp):
        calls.append(("observe", inp))
        raise RuntimeError("routing observation failed")

    def fallback(inp, *args, **kwargs):
        calls.append(("fallback", inp, args, kwargs))
        return "fallback-result"

    result = router.route_observed_voice_then_fallback(
        "hi",
        observer,
        lambda inp: None,
        fallback,
        lambda: "hint",
        hybrid_enabled=True,
        args=("extra",),
        kwargs={"flag": True},
    )

    assert result == "fallback-result"
    assert calls == [
        ("observe", "hi"),
        ("fallback", "hint\nhi", ("extra",), {"flag": True}),
    ]
