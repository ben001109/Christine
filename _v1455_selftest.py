"""V1455 self-test — 驗證 CPU deadline 精度 + §14 toy 期望值"""
import sys, os, time
sys.path.insert(0, r"f:\christine")

# 只 import V1455 需要的部分，繞過 Christine 的 GUI/麥克風啟動
import math, random, re, statistics

# 從 christine_final.py 抓出 V1455 的類別定義 — 直接 exec 相關段落
SRC = open(r"f:\christine\christine_final.py", "r", encoding="utf-8", errors="ignore").read()

# 找 V1455 的 try 塊（從 "import math as _v155_math" 到 "except Exception as _e:" 對應處）
i0 = SRC.find("import math as _v155_math")
i1 = SRC.find("except Exception as _e:\n    print(f\"  {_RD}✗{_R} V1455 Paper4 init err")
raw = SRC[i0:i1]
# strip exactly 4 spaces from start of each line (we're inside try: block)
code = "\n".join((ln[4:] if ln.startswith("    ") else ln) for ln in raw.splitlines())

# 準備一個 stub 環境
stub_globals = {
    "__name__": "__v1455_test__",
    "_RD": "", "_YE": "", "_GR": "", "_B": "", "_R": "", "_GY": "",
    "ask": lambda x: None,   # 基底 ask
    "_V1340_BEACON": type("B", (), {"register": staticmethod(lambda n: None)})(),
}
# 執行 V1455 code（會定義 _V1455_ENGINE 等）
exec(code, stub_globals)

engine = stub_globals["_V1455_ENGINE"]

print("=" * 70)
print("TEST 1  — CPU deadline precision")
print("=" * 70)
for budget in [0.5, 1.0, 3.0, 10.0]:
    t0 = time.perf_counter()
    r = engine.compute_within(budget)
    actual = r["time"]["elapsed"]
    err = r["time"]["error_pct"]
    samples = r["est"]["n_samples"]
    mark = "PASS" if abs(err) < 1.5 else ("OK  " if abs(err) < 3.0 else "FAIL")
    print(f"  [{mark}] budget={budget:5.2f}s  actual={actual:.4f}s  err={err:+.2f}%  samples={samples:,d}")

print()
print("=" * 70)
print("TEST 2  -- Toy example structural assertions (D=J=L=M+1=2, T=4)")
print("=" * 70)
r = engine.verify_toy(seconds=6.0)
for name, ok in r["assertions"].items():
    mark = "PASS" if ok else "FAIL"
    safe = name.encode("ascii", "replace").decode("ascii")
    print(f"  [{mark}] {safe}")
print(f"  Passed {r['passed']}/{r['total']}   samples={r['samples']:,d}   elapsed={r['elapsed']:.3f}s")
e = r["est"]; ref = r["ref_paper_gzip"]
print(f"  runtime Psi={e['Psi']:.4f} Psi_hat={e['Psi_hat']:.4f} Psi_tilde={e['Psi_tilde']:.4f} WI={e['WI']:.4f} EI={e['EI']:.4f}")
print(f"  paper   Psi={ref['Psi']:.2f}   Psi_hat={ref['Psi_hat']:.2f}   Psi_tilde={ref['Psi_tilde']:.2f}   WI={ref['WI']:.2f}   EI={ref['EI']:.2f}")

print()
print("=" * 70)
print("TEST 3  — Verify all theorems")
print("=" * 70)
r = engine.verify_all_theorems(seconds=2.0)
for name, ok in r["reports"]:
    mark = "PASS" if ok else "FAIL"
    safe = name.encode("ascii", "replace").decode("ascii")
    print(f"  [{mark}] {safe}")
print(f"  Total: {r['passed']}/{r['total']}")
print(f"  Predictor a={r['a']:.4f} b={r['b']:.4f} c={r['c']:.4f}  resid={r['predictor_resid']:.6f}")

print()
print("=" * 70)
print("TEST 4  — Bounds (closed-form upper bounds under toy params)")
print("=" * 70)
print(engine.bounds_report().encode("ascii","replace").decode("ascii"))

print()
print("=" * 70)
print("DONE")
print("=" * 70)
