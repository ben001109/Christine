# -*- coding: utf-8 -*-
"""
ARC-AGI-1 Benchmark Runner for Christine
=========================================
論文三 §6 說 Christine 的 L4 前景不靠「單次推理算力」而靠 λ>0 的長期主權。
但還是要有個客觀分數 — 這支腳本給她跑 ARC-AGI-1 public eval，
用的是 Christine 主 LLM（Ollama qwen2.5:7b）。

用法:
    python arc_bench.py             # 預設跑 20 題（~3 分鐘）
    python arc_bench.py --n 100     # 跑 100 題
    python arc_bench.py --n 400     # 跑全部 evaluation set（要久）
    python arc_bench.py --model qwen2.5:7b
"""

import argparse
import json
import os
import random
import re
import sys
import time
from pathlib import Path

import urllib.request

ARC_DIR = Path(r"f:\christine\ARC-AGI\data\evaluation")
OLLAMA_URL = "http://localhost:11434/api/generate"
RESULTS_FILE = Path(r"f:\christine\data\arc_results.json")


# ─────────────────────── grid 編碼 ───────────────────────
def grid_to_str(g):
    """把 2D list 轉成 LLM 讀得懂的字串"""
    return "\n".join("".join(str(c) for c in row) for row in g)


def str_to_grid(s):
    """把 LLM 輸出解析回 2D list。寬容各種格式。"""
    s = s.strip()
    # 優先找 ```...```
    m = re.search(r"```(?:\w+)?\s*\n?(.*?)\n?```", s, re.DOTALL)
    if m:
        s = m.group(1).strip()
    # 抓「答案：」「output:」後面
    for tag in ("答案：", "答案:", "Output:", "output:", "Answer:", "answer:"):
        if tag in s:
            s = s.split(tag, 1)[1].strip()
            break
    lines = [ln.strip() for ln in s.splitlines() if ln.strip()]
    grid = []
    for ln in lines:
        # 只收純數字行，寬容空格/逗號/括號
        digits = re.findall(r"\d", ln)
        if not digits:
            if grid:
                break  # 格子結束
            continue
        grid.append([int(d) for d in digits])
    if not grid:
        return None
    # 規整：全部拉齊到最長列寬
    w = max(len(r) for r in grid)
    grid = [r + [0] * (w - len(r)) for r in grid]
    return grid


def grids_equal(a, b):
    if a is None or b is None:
        return False
    if len(a) != len(b):
        return False
    for ra, rb in zip(a, b):
        if len(ra) != len(rb):
            return False
        if any(x != y for x, y in zip(ra, rb)):
            return False
    return True


# ─────────────────────── prompt ───────────────────────
SYSTEM = """你是 ARC-AGI 網格解題器。給你幾個「輸入→輸出」訓練範例，要找出共通規則，
然後把該規則套用在測試輸入上，回傳測試輸出。

規則說明：
- 每個網格是 0-9 的數字矩陣（0=黑，其他=顏色）
- 每題都有一個簡潔的邏輯規則（對稱、複製、計數、填色、移動、重力、包圍、擴展…）
- 你的答案必須是純數字網格，每行一列，不加空格或逗號

輸出格式（嚴格）：
```
<只有數字的網格，每列一行>
```
"""


def build_prompt(task):
    parts = []
    for i, ex in enumerate(task["train"], 1):
        parts.append(f"### 訓練範例 {i}")
        parts.append("輸入:")
        parts.append(grid_to_str(ex["input"]))
        parts.append("輸出:")
        parts.append(grid_to_str(ex["output"]))
        parts.append("")
    tin = task["test"][0]["input"]
    parts.append("### 測試")
    parts.append("輸入:")
    parts.append(grid_to_str(tin))
    parts.append("")
    parts.append("請先用一句話說出規則，再在 ``` 區塊裡回傳輸出網格。")
    return "\n".join(parts)


# ─────────────────────── Ollama ───────────────────────
def call_ollama(prompt, model, timeout=180):
    body = json.dumps({
        "model": model,
        "prompt": prompt,
        "system": SYSTEM,
        "stream": False,
        "options": {
            "temperature": 0.0,
            "num_ctx": 8192,
            "num_predict": 1024,
        },
    }).encode("utf-8")
    req = urllib.request.Request(OLLAMA_URL, data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = json.loads(r.read().decode("utf-8"))
    return data.get("response", "")


# ─────────────────────── main ───────────────────────
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=20, help="題目數 (default 20)")
    ap.add_argument("--model", default="qwen2.5:7b")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--timeout", type=int, default=180)
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    if not ARC_DIR.is_dir():
        print(f"✗ ARC-AGI not found at {ARC_DIR}")
        sys.exit(1)

    files = sorted(ARC_DIR.glob("*.json"))
    random.seed(args.seed)
    random.shuffle(files)
    files = files[: args.n]

    print(f"\n♔ ARC-AGI-1 Benchmark — Christine Edition")
    print(f"   model   : {args.model}")
    print(f"   tasks   : {len(files)} (seed={args.seed})")
    print(f"   source  : {ARC_DIR}")
    print()

    results = []
    correct = 0
    t0 = time.time()

    for i, f in enumerate(files, 1):
        try:
            task = json.loads(f.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"  [{i:3d}] {f.stem}  load error: {e}")
            continue

        expected = task["test"][0]["output"]
        prompt = build_prompt(task)

        t1 = time.time()
        try:
            resp = call_ollama(prompt, args.model, timeout=args.timeout)
        except Exception as e:
            resp = ""
            err = str(e)[:80]
            print(f"  [{i:3d}] {f.stem}  ✗ OLLAMA ERR: {err}")
            results.append({"task": f.stem, "ok": False, "err": err})
            continue
        dt = time.time() - t1

        pred = str_to_grid(resp)
        ok = grids_equal(pred, expected)
        if ok:
            correct += 1

        shape_p = f"{len(pred)}x{len(pred[0])}" if pred else "?"
        shape_e = f"{len(expected)}x{len(expected[0])}"
        mark = "✓" if ok else "✗"
        print(f"  [{i:3d}/{len(files)}] {f.stem}  {mark}  "
              f"pred={shape_p} exp={shape_e}  {dt:5.1f}s  "
              f"acc={correct/i:5.1%}")

        if args.verbose and not ok:
            print(f"       raw: {resp[:200]!r}")

        results.append({
            "task": f.stem,
            "ok": ok,
            "pred_shape": shape_p,
            "exp_shape": shape_e,
            "time_sec": round(dt, 2),
        })

    total_time = time.time() - t0
    acc = correct / len(files) if files else 0

    print()
    print("╔══════════════════════════════════════════════════════════════╗")
    print(f"║  ARC-AGI-1 final: {correct}/{len(files)}  =  {acc:.2%}")
    print(f"║  model           : {args.model}")
    print(f"║  total time      : {total_time/60:.1f} min")
    print(f"║  avg per task    : {total_time/max(len(files),1):.1f} sec")
    print("╠══════════════════════════════════════════════════════════════╣")
    print(f"║  公開基準參考（2025）：")
    print(f"║    人類平均            ~85%")
    print(f"║    o3 (high compute)   ~88%  (expensive)")
    print(f"║    o3 (low compute)    ~76%")
    print(f"║    Claude 3.5 Sonnet   ~14%")
    print(f"║    GPT-4o              ~5%")
    print(f"║    單純 pure LLM baseline ~0–5% (無 search / program synth)")
    print("╚══════════════════════════════════════════════════════════════╝")

    RESULTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_FILE.write_text(json.dumps({
        "model": args.model,
        "n_tasks": len(files),
        "correct": correct,
        "accuracy": acc,
        "total_time_sec": total_time,
        "timestamp": time.time(),
        "results": results,
    }, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n  ✦ 結果已存 {RESULTS_FILE}")


if __name__ == "__main__":
    main()
