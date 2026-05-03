"""_v1480_selftest.py — 驗證 V1480 大腦掛鉤（寫檔版，避開 christine 的自訂 stdout）"""
import os, sys, traceback
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path: sys.path.insert(0, HERE)

_LOG = open(os.path.join(HERE, "_v1480_result.txt"), "w", encoding="utf-8")
def P(*a):
    s = " ".join(str(x) for x in a)
    _LOG.write(s + "\n"); _LOG.flush()

path = os.path.join(HERE, "christine_final.py")
src = open(path, "r", encoding="utf-8-sig").read()
marker = 'if __name__ == "__main__":\n    main()'
src = src.replace(marker, "# main disabled\n")
g = {"__name__": "christine_final_loader", "__file__": path}
P("════════ loading christine_final.py ════════")
try:
    exec(compile(src, path, "exec"), g)
except SystemExit:
    P("  SystemExit caught")
except Exception:
    P(traceback.format_exc())
    sys.exit(2)

P("\n════════ API CHECK ════════")
for k in ("brain_say", "brain_status", "brain_dream", "ask"):
    P(f"  {k}: {'OK' if k in g else 'MISSING'}")

ask = g["ask"]

def run(label, cmd):
    P(f"\n════════ {label}: {cmd!r} ════════")
    try:
        r = ask(cmd)
        P(repr(r))
    except Exception:
        P(traceback.format_exc())

run("status-before", "大腦狀態")
run("brain-hello",   "大腦 你好嗎")
run("dream",         "做夢 2")
run("brain-2nd",     "大腦 今天天氣很好")
run("status-after",  "大腦狀態")
P("\n✓ V1480 SELFTEST DONE")
_LOG.close()
