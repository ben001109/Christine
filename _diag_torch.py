"""_diag_torch.py — 子診斷：測 torch 載入實際耗時 + CUDA 狀態。"""
import sys, time, threading

print("    [測試中] import torch ...", flush=True)
t0 = time.time()
result = {"ok": False, "err": None, "dt": 0}

def _load():
    try:
        import torch
        result["torch"] = torch
        result["dt"] = time.time() - t0
        result["ok"] = True
    except Exception as e:
        result["err"] = f"{type(e).__name__}: {e}"
        result["dt"] = time.time() - t0

th = threading.Thread(target=_load, daemon=True)
th.start()
th.join(timeout=60.0)

if th.is_alive():
    print(f"    [!!] import torch 已超過 60 秒仍未完成 => 嚴重卡頓")
    print(f"         建議: pip install --force-reinstall torch --index-url https://download.pytorch.org/whl/cpu")
    sys.exit(1)

if not result["ok"]:
    print(f"    [X] torch import 失敗 ({result['dt']:.1f}s)")
    print(f"        錯誤: {result['err']}")
    print(f"        建議: pip install --upgrade --force-reinstall torch")
    sys.exit(2)

torch = result["torch"]
dt = result["dt"]
print(f"    [OK] torch {torch.__version__} 載入耗時 {dt:.2f} 秒")
if dt > 15:
    print(f"    [!] 偏慢 (> 15s)，很可能是 Defender 掃描 DLL — 加入白名單可加速")
elif dt > 5:
    print(f"    [~] 普通 (5~15s)，首次啟動正常")
else:
    print(f"    [✓] 很快 (< 5s)，完全正常")

print(f"    CUDA available = {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"    CUDA version   = {torch.version.cuda}")
    try:
        print(f"    cuDNN          = {torch.backends.cudnn.version()}")
    except Exception: pass
    for i in range(torch.cuda.device_count()):
        p = torch.cuda.get_device_properties(i)
        print(f"    GPU[{i}]        = {p.name}  VRAM={p.total_memory/1024**3:.1f}GB  sm_{p.major}{p.minor}")
    # 實際跑一次 matmul 確認 CUDA 能正常工作
    try:
        t = time.time()
        a = torch.randn(512, 512, device="cuda")
        b = torch.randn(512, 512, device="cuda")
        c = (a @ b).sum().item()
        torch.cuda.synchronize()
        print(f"    [OK] GPU matmul 測試通過 ({(time.time()-t)*1000:.0f}ms)")
    except Exception as e:
        print(f"    [X] GPU matmul 失敗: {e}")
        print(f"        CUDA runtime 可能損壞，建議重裝 torch")
else:
    print(f"    [提示] CUDA 不可用 — 檢查 nvidia-smi 或改用 CPU 版 torch")
