"""
_brain_selftest.py — Christine Brain 端到端測試
================================================
1. 編譯整個 brain/ package
2. 建立 Brain("small")
3. 餵 5 句中文，驗證 perceive_text → respond 都回東西
4. 測 dream() 不崩
"""
import os, sys, py_compile, traceback, time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if ROOT not in sys.path: sys.path.insert(0, ROOT)

def step(name):
    print(f"\n━━━ {name} ━━━")

fail = 0

# ── 1. compile 全部 .py ──
step("STEP 1 · 編譯 brain/*.py")
ok_n = 0; bad = []
for fn in sorted(os.listdir(HERE)):
    if not fn.endswith(".py"): continue
    if fn.startswith("_brain_selftest"): continue
    p = os.path.join(HERE, fn)
    try:
        py_compile.compile(p, doraise=True)
        ok_n += 1
    except Exception as e:
        bad.append((fn, str(e))); fail += 1
print(f"  ok={ok_n}  fail={len(bad)}")
for fn,e in bad: print(f"    ✗ {fn}: {e[:200]}")

# ── 2. Brain 啟動 ──
step("STEP 2 · 建立 Brain('small')")
try:
    from brain.brain import Brain, build_default_brain
    t0 = time.time()
    b = Brain(size="small", seed=42)
    print(f"  build ok in {time.time()-t0:.2f}s")
    print(f"  status: {b.status()}")
except Exception:
    traceback.print_exc(); fail += 1; b = None

# ── 3. perceive + respond ──
if b is not None:
    step("STEP 3 · 5 句中文輸入")
    sentences = [
        "你好，我叫 Josh。",
        "今天天氣不錯。",
        "你是誰？你能做什麼？",
        "我喜歡用 CPU 思考這件事。",
        "告訴我你的感覺。",
    ]
    try:
        for i,s in enumerate(sentences,1):
            t0 = time.time()
            perc = b.perceive_text(s)
            resp = b.respond(seed=s, max_len=24)
            dt = (time.time()-t0)*1000
            print(f"  [{i}] in={s!r}")
            print(f"      perc.keys={list(perc.keys())[:6]}...")
            print(f"      resp={resp!r}   ({dt:.1f}ms)")
    except Exception:
        traceback.print_exc(); fail += 1

# ── 4. dream ──
if b is not None:
    step("STEP 4 · dream(3) 睡眠鞏固")
    try:
        out = b.dream(cycles=3)
        print(f"  dream out: {out}")
    except Exception:
        traceback.print_exc(); fail += 1

# ── 5. 小批量 generator smoke (只產 1000 行，不產 500k) ──
step("STEP 5 · generator smoke (target=2000 行)")
try:
    from brain.generator import generate
    r = generate(target_lines=2000, cols_per_area=8, verbose=False,
                 out_dir=os.path.join(HERE, "generated"))
    print(f"  {r}")
    # 驗證產物可 import
    sys.path.insert(0, ROOT)
    import importlib
    mod = importlib.import_module("brain.generated.all_areas")
    it = mod.iter_areas()
    first = next(it)
    print(f"  first area class = {type(first).__name__}  n_cols={len(first.columns)}")
    # 跑一次 step
    out = first.step([0.5]*len(first.columns), dt=0.5)
    print(f"  area.step() returned {len(out)} rates, e.g. {out[:3]}")
except Exception:
    traceback.print_exc(); fail += 1

# ── 結果 ──
step("RESULT")
if fail == 0:
    print("✓ ALL GREEN")
    sys.exit(0)
else:
    print(f"✗ {fail} failure(s)")
    sys.exit(1)
