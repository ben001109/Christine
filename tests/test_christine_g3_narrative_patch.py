import christine_g3_frontier as g3
import christine_g3_narrative_patch as v13


def ev(text, url, conf=.85, rel=.8):
    return g3.Evidence(text, url, conf, rel)


def test_narrative_not_numbered():
    sage = v13.SAGE3Narrative()
    evidence = [
        ev("我是大坑，一個台灣的coser C齡約三年，目前只出女角，可以約拍，可以委託，Instagram jonse1030 Threads jonse1030。", "https://lit.link/a"),
        ev("陳大坑是台灣 coser，也有約拍相關公開資訊。", "https://threads.net/b", .82, .75),
    ]
    ans, _, meta = sage.synthesize(goal="陳大坑是誰", evidence=evidence, packet=g3.ResearchPacket(tuple(evidence), .80, ("陳大坑",)))
    assert not any(line.lstrip().startswith(("1.", "2.", "3.")) for line in ans.splitlines())
    assert "台灣" in ans and "coser" in ans.casefold()
    assert meta["mode"] == "fact-graph-narrative"


def test_no_raw_search_dump():
    sage = v13.SAGE3Narrative()
    raw = "陳大坑/大坑 lit.link 陳大坑/大坑 台灣Coserw /音遊玩家 我是大坑，一個台灣的coser C齡約三年，目前只出女角 可以約拍，可以委托，價目表在底下 歡迎大家跟我交流 Instagram jonse1030 FB jonse1030 Threads jonse1030"
    evidence = [ev(raw, "https://lit.link/a")]
    ans, _, _ = sage.synthesize(goal="陳大坑是誰", evidence=evidence, packet=g3.ResearchPacket(tuple(evidence), .63, ("陳大坑",)))
    assert raw not in ans
    assert "目前資料能支持的重點是：" not in ans


def test_boilerplate_removed():
    sage = v13.SAGE3Narrative()
    evidence = [
        ev("Instagram メイク・美容 趣味 個人 Created by lit.link All Rights Reserved.", "https://lit.link/noise"),
        ev("我是大坑，一個台灣的coser。", "https://lit.link/good"),
    ]
    ans, _, _ = sage.synthesize(goal="陳大坑是誰", evidence=evidence, packet=g3.ResearchPacket(tuple(evidence), .6, ("陳大坑",)))
    assert "All Rights Reserved" not in ans
    assert "Created by lit.link" not in ans


def test_138b_preserved():
    assert v13.FIVED9A_TOKEN_CAPACITY == 138_000_000_000
