"""_v1481_selftest.py — V1481 自動啟動 + 全句接管 測試"""
import os, sys, traceback
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path: sys.path.insert(0, HERE)

_LOG = open(os.path.join(HERE, "_v1481_result.txt"), "w", encoding="utf-8")
def P(*a):
    s = " ".join(str(x) for x in a)
    _LOG.write(s + "\n"); _LOG.flush()

path = os.path.join(HERE, "christine_final.py")
src = open(path, "r", encoding="utf-8-sig").read()
src = src.replace('if __name__ == "__main__":\n    main()', "# main disabled\n")
g = {"__name__": "christine_final_loader", "__file__": path}
P("═══ loading christine_final.py ═══")
try: exec(compile(src, path, "exec"), g)
except SystemExit: pass
except Exception:
    P(traceback.format_exc()); sys.exit(2)

# 檢查 brain 已 eager 啟動
P("\n═══ ready check ═══")
cfg = g.get("_V1480_CFG")
brain = g.get("_V1480_BRAIN")
P(f"  ready={cfg.get('ready') if cfg else '?'}")
P(f"  brain obj={type(brain).__name__ if brain else None}")
P(f"  takeover={cfg.get('takeover') if cfg else '?'}")
P(f"  threshold={cfg.get('confidence_threshold') if cfg else '?'}")

ask = g["ask"]

def run(label, text):
    P(f"\n— {label} — in: {text!r}")
    try:
        r = ask(text)
        P(f"    out: {r!r}")
    except Exception:
        P(traceback.format_exc())

# 不加「大腦」前綴，測試全句接管
run("greet",         "你好")
run("greet2",        "嗨，我叫 Josh")
run("identity",      "你是誰？")
run("capability",    "你能做什麼？")
run("time",          "現在幾點？")
run("thanks",        "謝謝你")
run("farewell",      "掰掰")
run("positive",      "我今天真的超開心，好棒")
run("negative",      "我好難過，好煩")
run("question_what", "什麼是愛？")
run("question_how",  "我該怎麼辦？")
run("command",       "幫我寫一個 txt")
run("self_query",    "你現在在想什麼？")
run("statement",     "今天下雨了")
run("vague",         "嗯")
run("name_learn",    "我叫 Josh，你記得嗎？")
run("recall_name",   "你還記得我叫什麼嗎？")

run("status",        "大腦狀態")

P("\n✓ V1481 SELFTEST DONE")
_LOG.close()
