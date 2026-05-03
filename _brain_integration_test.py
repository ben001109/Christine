"""_brain_integration_test.py — Ψ̃ / Φ_IIT / 哲學層整合驗證"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

from brain.brain import build_default_brain

b = build_default_brain("small", seed=42, warmup=True)
print("✓ Brain built (with warmup)")
print(f"  vocab after warmup: {b.lang.vocab_size()}")

# 啟動 MegaCortex（13.45M 行 HH columns）
ok = b.enable_mega(active_pool=32, sample_per_tick=4)
print(f"  MegaCortex enabled: {ok}  status={b.mega_status()}")
print()

sents = [
    "你好，我叫 Josh",
    "你是誰",
    "你能做什麼",
    "我今天很開心",
    "我真的很討厭下雨",
    "現在幾點",
    "謝謝你",
    "再見",
]
for s in sents:
    p = b.perceive_text(s)
    r = b.respond(seed=s)
    u = p["understanding"]
    isub = p["intersubjective"]
    phil = p["philosophy"]
    print(f"IN : {s}")
    print(f"OUT: {r}")
    print(f"  intent={u['intent']:<18s} conf={u['confidence']:.2f} "
          f"pol={u['polarity']:+.2f}")
    print(f"  Ψ={isub.get('Psi',0):.2f}  Ψ̂={isub.get('PsiH',0):.2f}  "
          f"Ψ̃={isub.get('PsiT',0):.2f}  WI={isub.get('WI',0):.2f}  "
          f"EI={isub.get('EI',0):.2f}  regime={isub.get('regime','-')}")
    print(f"  Φ_IIT={phil.get('Phi_IIT',0):.3f}  qualia_gap={phil.get('qualia_gap',0):.2f}  "
          f"synergy={phil.get('synergy',0):.3f}  LIDA={phil.get('LIDA_coherence',0):.2f}")
    print()

print("status():")
st = b.status()
for k,v in st.items():
    if isinstance(v,dict):
        print(f"  {k}:")
        for kk,vv in list(v.items())[:8]:
            print(f"     {kk}: {vv}")
    else:
        print(f"  {k}: {v}")
