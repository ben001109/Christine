# V1460 self-test: logger + CPU thinker + ask fallback
# 不啟動 Christine GUI/mic，只把 V1460 那塊跑起來
import os, sys, time, traceback, io
# 強制 stdout/stderr 用 utf-8（避過 Windows cp1252）
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, r"f:\christine")

DD = r"f:\christine\data"
os.makedirs(DD, exist_ok=True)

# 模擬 Christine 環境的最小 globals
_R = ""; _GR = ""; _RD = ""; _YE = ""; _CY = ""; _B = ""; _GY = ""

class _FakeBeacon:
    def register(self, *a, **k): pass
_V1340_BEACON = _FakeBeacon()

# 模擬一個會「卡住」、「回空」、「丟例外」、「正常」的 ask
ask_mode = "normal"
def ask(inp, *a, **k):
    if ask_mode == "timeout":
        time.sleep(30)  # 比 wrapper timeout 大
        return "should-never-arrive"
    if ask_mode == "empty":
        return ""
    if ask_mode == "exc":
        raise RuntimeError("simulated boom")
    return f"NORMAL-REPLY[{inp}]"

# 取 V1460 程式碼（從 line 119008 起到檔尾，去掉 if __name__ 尾巴 + 強制不縮排）
src_path = r"f:\christine\christine_final.py"
with open(src_path, "r", encoding="utf-8") as f:
    full = f.read()

# 找 V1460 區塊
marker = "# ║  V1460  Full Logger + CPU Thinker + ask() Fallback"
idx = full.find(marker)
if idx < 0:
    print("✗ V1460 marker not found"); sys.exit(1)
end_marker = 'if __name__ == "__main__":'
end_idx = full.rfind(end_marker)
v1460_src = full[idx:end_idx]

# 不需要 dedent，V1460 是頂層
ns = globals()
print(f"[exec] V1460 source len={len(v1460_src)}")
try:
    exec(compile(v1460_src, "<v1460>", "exec"), ns)
except Exception:
    traceback.print_exc(); sys.exit(2)

print("\n" + "="*60)
print("V1460 loaded. Running scenarios...")
print("="*60)

ask_w = ns["ask"]            # wrapped ask
think = ns["cpu_think"]
log = ns["log"]
cfg = ns["_V1460_CFG"]
cfg["timeout"] = 2.0          # 加速測試

# ── Scenario 0: thinker raw budget ─────────────────────
print("\n[0] thinker raw budget test")
for b in (0.5, 1.0, 2.0):
    t0 = time.perf_counter()
    r = think("我心情不好", b)
    dt = time.perf_counter() - t0
    err = abs(dt - b)/b * 100
    ok = "✓" if dt <= b + 0.5 else "✗"
    print(f"  {ok} budget={b:.1f}s elapsed={dt:.3f}s err={err:+.1f}%  reply={r[:60]!r}")

# ── Scenario 1: voice command 想 N 秒 ──────────────────
print("\n[1] voice: 想 1 秒")
t0 = time.perf_counter()
r = ask_w("想 1 秒")
dt = time.perf_counter() - t0
print(f"  elapsed={dt:.3f}s")
print(f"  reply={r[:200]}")

# ── Scenario 2: normal ask (no fallback) ───────────────
print("\n[2] normal ask")
ask_mode = "normal"
r = ask_w("hello")
print(f"  reply={r!r}  (fb_hits={cfg['fallback_hits']})")
assert r.startswith("NORMAL-REPLY"), "should pass through"

# ── Scenario 3: empty reply → fallback ─────────────────
print("\n[3] empty ask → fallback")
ask_mode = "empty"
fb_before = cfg["fallback_hits"]
r = ask_w("空回覆測試")
print(f"  reply={r[:120]!r}")
assert cfg["fallback_hits"] == fb_before + 1, "fallback should trigger"
assert r and r.strip(), "must be non-empty"

# ── Scenario 4: exception → fallback ───────────────────
print("\n[4] exception ask → fallback")
ask_mode = "exc"
fb_before = cfg["fallback_hits"]
r = ask_w("例外測試")
print(f"  reply={r[:120]!r}")
assert cfg["fallback_hits"] == fb_before + 1
assert r and r.strip()

# ── Scenario 5: timeout → fallback ─────────────────────
print("\n[5] timeout ask → fallback (timeout=2s, fb_budget=10s)")
ask_mode = "timeout"
fb_before = cfg["fallback_hits"]
t0 = time.perf_counter()
r = ask_w("超時測試")
dt = time.perf_counter() - t0
print(f"  elapsed={dt:.3f}s  reply={r[:120]!r}")
assert cfg["fallback_hits"] == fb_before + 1
assert r and r.strip()
# 應該大約 = timeout(2s) + fb_budget thinker time(<=10s)
assert dt < 2.0 + 10.0 + 1.0, f"took too long: {dt}"

# ── Scenario 6: log file exists ────────────────────────
print("\n[6] log file check")
log_path = os.path.join(DD, "logs", "christine.log")
print(f"  log path: {log_path}")
print(f"  exists: {os.path.exists(log_path)}")
print(f"  size:   {os.path.getsize(log_path) if os.path.exists(log_path) else 0} bytes")
assert os.path.exists(log_path), "log file should exist"
assert os.path.getsize(log_path) > 0, "log should have content"

# ── Scenario 7: voice 'log' / 'v1460' ──────────────────
print("\n[7] voice: v1460 status")
ask_mode = "normal"
r = ask_w("v1460")
print(r[:600])

print("\n[8] voice: log tail")
r = ask_w("log")
# 只印頭幾行
print("\n".join(r.splitlines()[:8]))

print("\n" + "="*60)
print("✓✓✓  ALL V1460 SCENARIOS PASS  ✓✓✓")
print("="*60)
