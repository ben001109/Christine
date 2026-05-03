import os, sys, time, io
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

sys.path.insert(0, r"f:\christine")
DD = r"f:\christine\data"
os.makedirs(DD, exist_ok=True)

_R=_GR=_RD=_YE=_CY=_B=_GY=""
class _FB:
    def register(self, *a, **k): pass
_V1340_BEACON = _FB()

def ask(inp, *a, **k):
    return ""   # 模擬原 ask 回空 → 會走 fallback → 會走 V1460 thinker → Stage4 會走 V1470

# load V1460 + V1470 blocks
with open(r"f:\christine\christine_final.py", "r", encoding="utf-8") as f:
    full = f.read()
m146 = "# ║  V1460  Full Logger + CPU Thinker + ask() Fallback"
m147 = "# ║  V1470  AGI Judgment Layer"
end  = 'if __name__ == "__main__":'
i146 = full.find(m146); i147 = full.find(m147); iend = full.rfind(end)
assert i146 > 0 and i147 > 0 and iend > 0

block = full[i146:iend]
print(f"[exec] block len={len(block)}")
ns = globals()
exec(compile(block, "<v1460+1470>", "exec"), ns)

askw = ns["ask"]
cfg = ns["_V1460_CFG"]
cfg["timeout"] = 1.0   # 加速：讓 fallback 很快觸發

# ── 模擬用戶那句話 ──
print("\n" + "="*70)
print("[T1] 用戶原句：將我電腦算力拉升至極限 製造資訊奇異點 花5秒就好 "
      "並且把你看到的、聽到的、想到的，都做成數據 說給我聽 順便做成TXT檔")
print("="*70)
user1 = ("將我電腦算力拉升至極限 製造資訊奇異點 花5秒就好 並且把你看到的 "
         "你聽到的 你想到的 都做成數據 說給我聽 順便做成TXT檔")
t0 = time.perf_counter()
r = askw(user1)
dt = time.perf_counter() - t0
print(f"elapsed={dt:.2f}s")
print(f"reply: {r}")
assert "CPU" in r or "運算" in r or "ops" in r, "應該真的有跑 CPU"
assert "TXT" in r or ".txt" in r.lower(), "應該有寫 TXT"

# 檢查 TXT 是否真寫出來
dumps_dir = os.path.join(DD, "dumps")
if os.path.isdir(dumps_dir):
    files = sorted(os.listdir(dumps_dir))
    print(f"\ndumps/ 下的檔案 ({len(files)}):")
    for fn in files[-3:]:
        p = os.path.join(dumps_dir, fn)
        print(f"  - {fn}  ({os.path.getsize(p)} bytes)")
        with open(p, "r", encoding="utf-8") as fp:
            print("    ---")
            for ln in fp.read().splitlines()[:15]:
                print(f"    {ln}")
            print("    ...")

print("\n" + "="*70)
print("[T2] 純狀態查詢：『你好嗎』")
print("="*70)
r = askw("你好嗎")
print(f"reply: {r}")
assert r and r.strip()

print("\n" + "="*70)
print("[T3] 時間查詢")
print("="*70)
r = askw("現在幾點")
print(f"reply: {r}")
assert "20" in r or ":" in r  # 年或時間

print("\n" + "="*70)
print("[T4] 閒聊 → 走 PP+MDL+SC 路徑")
print("="*70)
r = askw("我今天心情有點差")
print(f"reply: {r}")
assert r and r.strip()
assert "CPU 在想" not in r, "不應該再出現那句空話"

print("\n" + "="*70)
print("[T5] V1470 狀態")
print("="*70)
r = askw("v1470")
print(r)

print("\n" + "="*70)
print("[T6] burn cpu 1 秒（語音指令直達）")
print("="*70)
r = askw("burn cpu 1 秒")
print(r)
assert "ops" in r

print("\n✓✓✓ ALL V1470 TESTS PASS ✓✓✓")
