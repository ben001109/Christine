# -*- coding: utf-8 -*-
"""測試 V14.4 UTF-8 修復是否解決 daemon thread 中的 locale encoding 問題"""
import os, sys, threading, time, datetime

# 模擬 V14.4 修復 (和 christine_final.py 開頭一樣)
os.environ["PYTHONUTF8"] = "1"
os.environ["PYTHONIOENCODING"] = "utf-8"
try:
    import io as _io_early
    _raw_stdout = sys.stdout.buffer if hasattr(sys.stdout, 'buffer') else sys.stdout
    _raw_stderr = sys.stderr.buffer if hasattr(sys.stderr, 'buffer') else sys.stderr
    sys.stdout = _io_early.TextIOWrapper(_raw_stdout, encoding='utf-8', errors='replace', line_buffering=True)
    sys.stderr = _io_early.TextIOWrapper(_raw_stderr, encoding='utf-8', errors='replace', line_buffering=True)
except Exception:
    pass

print(f"[主線程] stdout.encoding = {sys.stdout.encoding}")
print(f"[主線程] locale preferred = {__import__('locale').getpreferredencoding()}")

errors = []

def daemon_test():
    try:
        # 舊寫法（會 crash）: datetime.datetime.now().strftime("%Y年%m月")
        # 新寫法（安全）:
        _now = datetime.datetime.now()
        _today = f"{_now.year}年{_now.month}月"
        print(f"[daemon] 年月(安全拼接): {_today}", flush=True)
        print(f"[daemon] 自由探索 第 1 輪", flush=True)
        print(f"[daemon] 💭 Christine 想學:", flush=True)
        print(f"[daemon] 🤖 2026年最新AI技術", flush=True)
        print(f"[daemon] 🔬 量子計算的延伸探索", flush=True)
        print(f"[daemon] 🎲 {_today} 科技新聞重大突破", flush=True)
        
        # 額外驗證：舊 strftime 的確會失敗
        try:
            _old_way = datetime.datetime.now().strftime("%Y年%m月")
            print(f"[daemon] ⚠ 舊 strftime 竟然也成功了: {_old_way}", flush=True)
        except Exception as e2:
            print(f"[daemon] ✓ 確認舊 strftime 會失敗: {e2}", flush=True)
        
        print("[daemon] ✅ 全部成功！沒有 encoding 錯誤", flush=True)
    except Exception as e:
        errors.append(str(e))
        print(f"[daemon] ❌ 錯誤: {e}", flush=True)

t = threading.Thread(target=daemon_test, daemon=True)
t.start()
t.join(timeout=5)

if errors:
    print(f"\n❌ 測試失敗: {errors}")
    sys.exit(1)
else:
    print("\n✅ UTF-8 修復測試全部通過！daemon thread 中文輸出正常")
    sys.exit(0)
