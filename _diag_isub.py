import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
from brain.brain import build_default_brain
b = build_default_brain("tiny")
for s in ["你好","我叫Josh","今天天氣很糟","我很開心","再見","你是誰","你會做什麼"]:
    r = b.perceive_text(s)
    print("IN:", s, "ISUB:", r.get("intersubjective"))
print("---FINAL ISUB SNAP---")
print(b.isub.snapshot())
print("---LAST_ISUB_ERR---")
print(getattr(b, "_last_isub_err", "none"))
print("---LAST_PHIL_ERR---")
print(getattr(b, "_last_phil_err", "none"))
