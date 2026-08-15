import christine_g3_frontier as g3
import christine_g3_context_intent as v15


def ctx():
    return v15.ContextGraph(state_path=None)


def test_url_is_inspectable_not_conversation():
    i = v15.IntentKernel().analyze("https://www.threads.com/@tt_duuss")
    assert i.mode == "inspect_url"
    assert i.requires_web
    assert i.urls
    assert i.source_hint == "threads"


def test_url_question_is_research():
    i = v15.IntentKernel().analyze("https://www.threads.com/@tt_duuss 這個人在幹嘛")
    assert i.mode == "research"
    assert i.requires_web


def test_explicit_threads_lookup_is_mandatory_research():
    i = v15.IntentKernel().analyze("花栗鼠🍋是誰 去threads上查")
    assert i.mode == "research"
    assert i.requires_web
    assert i.source_hint == "threads"


def test_social_donation_talk_is_not_web_research():
    i = v15.IntentKernel().analyze("可以幫我@錫蘭嗎，我都想斗內十萬塊了")
    assert i.mode == "conversation"
    assert not i.requires_web


def test_reflection_is_support_not_factual_web():
    i = v15.IntentKernel().analyze("那支PUA影片多少支撐著現在的我")
    assert i.mode == "support"
    assert not i.requires_web


def test_trauma_reflection_is_support():
    i = v15.IntentKernel().analyze("其實我也有同樣的困惑，為什麼我女朋友不反抗、不逃，為什麼會僵住，但其實完全不是默認")
    assert i.mode == "support"


def test_vague_plugin_requests_clarification():
    i = v15.IntentKernel().analyze("寫一個外掛程式")
    assert i.mode == "clarify"
    assert "purpose" in i.missing_slots
    assert "target_platform" in i.missing_slots


def test_vague_hard_python_requests_goal_instead_of_quicksort():
    i = v15.IntentKernel().analyze("寫一個超難的 python 腳本")
    assert i.mode == "clarify"
    assert "purpose" in i.missing_slots


def test_concrete_async_crawler_is_create_code():
    i = v15.IntentKernel().analyze("寫一個 asyncio 爬蟲，同時抓取十個網址並整理 title")
    assert i.mode == "create_code"
    assert not i.missing_slots


def test_context_url_followup_inherits_url_but_not_mode():
    parser = v15.IntentKernel()
    c = ctx()
    first = parser.analyze("https://www.threads.com/@tt_duuss")
    r1 = c.resolve("https://www.threads.com/@tt_duuss", first)
    c.commit("https://www.threads.com/@tt_duuss", r1)
    second = parser.analyze("這個人在幹嘛")
    r2 = c.resolve("這個人在幹嘛", second)
    assert r2.continuity >= .34
    assert r2.inherited_urls
    assert second.mode == "answer"


def test_context_does_not_turn_reflection_into_previous_answer_task():
    kernel = v15.IntentKernel()
    c = ctx()
    first = kernel.analyze("可以幫我@錫蘭嗎，我都想斗內十萬塊了")
    r1 = c.resolve(first.goal, first)
    c.commit(first.goal, r1)
    second = kernel.analyze("那支PUA影片多少支撐著現在的我")
    r2 = c.resolve(second.goal, second)
    assert second.mode == "support"
    assert r2.intent.mode == "support"


def test_native_support_response_explains_freeze_without_blame():
    intent = v15.IntentKernel().analyze("其實我也有同樣的困惑，為什麼我女朋友不反抗、不逃，為什麼會僵住，但其實完全不是默認")
    r = v15.ContextResolution(intent, intent.goal)
    answer = v15.NativeDialogue().respond(intent.goal, r)
    assert "僵住" in answer
    assert "同意" in answer or "默認" in answer
    assert "自動防衛" in answer


def test_138b_preserved():
    assert v15.FIVED9A_TOKEN_CAPACITY == 138_000_000_000
