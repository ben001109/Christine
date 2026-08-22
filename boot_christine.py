#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
boot_christine.py — V1485 Christine 快速啟動器（CPU/GPU 預算）
════════════════════════════════════════════════════════════════════════════
流程：
  1) 偵測環境：CPU 核心、記憶體、PyTorch、CUDA GPU
  2) 套用論文 §3 「資源預算」哲學：
       - CPU：給 Christine  floor(N/2) 核心（留一半給系統），最少 2 核
       - GPU：若有 CUDA，預熱並把 VRAM 上限設到 80%
  3) 把環境變數傳給子程序，exec christine_final.py
════════════════════════════════════════════════════════════════════════════
用法：
  python boot_christine.py              # 預設：CPU 50%, GPU 80%
  python boot_christine.py --cpu 4      # 指定 4 核
  python boot_christine.py --gpu 0.5    # GPU 上限 50% VRAM
  python boot_christine.py --nogpu      # 強制 CPU-only
  python boot_christine.py --fast       # 相容旗標；不做額外檢查
  python boot_christine.py --check      # 只檢查啟動流程、不啟動主程式
  python boot_christine.py --legacy-monolith --allow-legacy-side-effects
                                       # 明確允許舊 monolith 與其副作用
"""
from __future__ import annotations
import os, sys, time, argparse, multiprocessing, platform, subprocess

from christine.legacy.runtime_gate import _issue_legacy_runtime_authorization
from christine.runtime.boot_banner import render_boot_banner
from christine.runtime.boot_config import build_basic_hardware_info, build_cpu_thread_env, compute_cpu_budget
from christine.runtime.health_summary import RuntimeVersionInfo, build_runtime_health_summary, render_runtime_health_summary
from christine.runtime.optional_dependencies import (
    check_ollama_service,
    optional_dependency_report,
)
from christine.versioning import current_version

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

# ── ANSI colours ──────────────────────────────────────────────
try:
    import colorama; colorama.just_fix_windows_console()
except Exception: pass
_CY = "\033[36m"; _GR = "\033[32m"; _YE = "\033[33m"; _RD = "\033[31m"
_B  = "\033[1m";  _D  = "\033[2m";  _R  = "\033[0m";   _M = "\033[35m"


# ══════════════════════════════════════════════════════════════
# §1  偵測硬體
# ══════════════════════════════════════════════════════════════
def detect_hardware():
    info = {
        "os":         f"{platform.system()} {platform.release()}",
        "python":     platform.python_version(),
        "cpu_count":  multiprocessing.cpu_count(),
        "cpu_name":   platform.processor() or "unknown",
        "ram_gb":     None,
        "gpu":        None,        # dict 或 None
        "torch":      None,         # version 或 None
    }
    try:
        import psutil
        info["ram_gb"] = round(psutil.virtual_memory().total / (1024**3), 1)
    except Exception: pass
    # torch 首次載入 + CUDA DLL 可能 5~15 秒 → 印提示 + 10 秒 timeout
    print(f"  {_D}      └ 載入 PyTorch / CUDA runtime（最多等 10 秒，超時自動降級）…{_R}", flush=True)
    import threading
    _torch_result = {"torch": None, "err": None}
    def _load_torch():
        try:
            import torch as _t
            _torch_result["torch"] = _t
        except Exception as e:
            _torch_result["err"] = f"{type(e).__name__}: {e}"
    th = threading.Thread(target=_load_torch, daemon=True)
    _t0 = time.time()
    th.start()
    th.join(timeout=10.0)
    if th.is_alive():
        print(f"  {_YE}      └ PyTorch 載入逾時（> 10 秒），自動降級為 CPU-only 模式{_R}", flush=True)
        return info   # 不等了，直接回傳（torch=None, gpu=None）
    if _torch_result["err"]:
        print(f"  {_YE}      └ PyTorch 載入失敗: {_torch_result['err'][:100]}{_R}", flush=True)
        return info
    try:
        torch = _torch_result["torch"]
        info["torch"] = torch.__version__
        print(f"  {_D}      └ PyTorch {torch.__version__} 已載入（{(time.time()-_t0)*1000:.0f}ms）{_R}", flush=True)
        if torch.cuda.is_available():
            print(f"  {_D}      └ 偵測 CUDA GPU …{_R}", flush=True)
            _t = time.time()
            i = 0
            info["gpu"] = {
                "name":     torch.cuda.get_device_name(i),
                "vram_gb":  round(torch.cuda.get_device_properties(i).total_memory / (1024**3), 2),
                "capability": ".".join(map(str, torch.cuda.get_device_capability(i))),
                "count":    torch.cuda.device_count(),
            }
            print(f"  {_D}      └ GPU: {info['gpu']['name']} ({info['gpu']['vram_gb']} GB, {(time.time()-_t)*1000:.0f}ms){_R}", flush=True)
        else:
            print(f"  {_D}      └ 未偵測到 CUDA（使用 CPU）{_R}", flush=True)
    except Exception as e:
        print(f"  {_YE}      └ GPU 偵測錯誤: {type(e).__name__}: {str(e)[:80]}{_R}", flush=True)
    return info


# ══════════════════════════════════════════════════════════════
# §2  套用計算預算
# ══════════════════════════════════════════════════════════════
def apply_compute_budget(hw: dict, cpu_cores: int | None = None,
                         gpu_frac: float = 0.80, use_gpu: bool = True,
                         allow_torch: bool = True):
    """按照論文 §3.4 的 architectural ceiling κ 哲學：
       不把所有資源吃光，只給她一份合理的配額。"""
    # ── CPU ──
    cpu_cores = compute_cpu_budget(hw["cpu_count"], cpu_cores)       # 一半留給系統
    env = build_cpu_thread_env(cpu_cores)

    # ── torch 層級：現在就設 ──
    if allow_torch:
        try:
            import torch
            torch.set_num_threads(cpu_cores)
            torch.set_num_interop_threads(max(1, cpu_cores // 2))
        except Exception: pass

    # ── GPU ──
    gpu_ready = False
    if allow_torch and use_gpu and hw.get("gpu"):
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.init()
                # 設 VRAM 上限 (Ampere+ 才支援 set_per_process_memory_fraction)
                try:
                    torch.cuda.set_per_process_memory_fraction(float(gpu_frac), 0)
                except Exception: pass
                # 預熱：跑一次 matmul 觸發 kernel 編譯
                t0 = time.time()
                a = torch.randn(512, 512, device="cuda")
                b = torch.randn(512, 512, device="cuda")
                _ = (a @ b).sum().item()
                torch.cuda.synchronize()
                warm_ms = (time.time() - t0) * 1000
                env["CHRISTINE_GPU"] = "1"
                env["CHRISTINE_GPU_FRAC"] = f"{gpu_frac:.2f}"
                env["CHRISTINE_GPU_WARM_MS"] = f"{warm_ms:.0f}"
                gpu_ready = True
        except Exception as e:
            env["CHRISTINE_GPU_ERR"] = str(e)[:120]
    else:
        env["CHRISTINE_GPU"] = "0"

    env["CHRISTINE_BOOT_TIME"] = str(int(time.time()))
    return env, cpu_cores, gpu_ready


# ══════════════════════════════════════════════════════════════
# §4  印 banner
# ══════════════════════════════════════════════════════════════
def print_boot_banner(hw, cpu_cores, gpu_ready, elapsed):
    lines = render_boot_banner(
        hw,
        cpu_cores,
        gpu_ready,
        elapsed,
        gpu_frac=os.environ.get("CHRISTINE_GPU_FRAC", "0.8"),
        gpu_warm_ms=os.environ.get("CHRISTINE_GPU_WARM_MS", "?"),
        colors=True,
    )
    for line in lines:
        print(line)


def _check_ollama_for_report():
    status = check_ollama_service()
    return status.available, status.message


def print_runtime_health_summary():
    statuses = optional_dependency_report(service_checkers={"ollama": _check_ollama_for_report})
    version = current_version()
    summary = build_runtime_health_summary(
        statuses,
        version_info=RuntimeVersionInfo(version.public, version.package_metadata),
    )
    for line in render_runtime_health_summary(summary, colors=True):
        print(line)


# ══════════════════════════════════════════════════════════════
# §5  主流程
# ══════════════════════════════════════════════════════════════
def main():
    ap = argparse.ArgumentParser(description="Christine V1485 Launcher")
    ap.add_argument("--cpu",  type=int,   default=None, help="CPU 核心數（預設 N/2）")
    ap.add_argument("--gpu",  type=float, default=0.80, help="GPU VRAM 上限 0.1~1.0")
    ap.add_argument("--nogpu", action="store_true", help="強制 CPU-only（仍載入 torch）")
    ap.add_argument("--notorch", action="store_true", help="完全跳過 torch 載入（最快啟動）")
    ap.add_argument("--fast", action="store_true", help="相容旗標；目前不做額外檢查")
    ap.add_argument("--check", action="store_true", help="只跑自檢、不啟動主程式")
    ap.add_argument("--no-banner", action="store_true", help="不顯示 banner")
    ap.add_argument("--legacy-monolith", action="store_true", help="明確選擇啟動舊 monolith")
    ap.add_argument("--allow-legacy-side-effects", action="store_true", help="明確允許舊 monolith 副作用")
    args, extra = ap.parse_known_args()

    if not args.check and not (args.legacy_monolith and args.allow_legacy_side_effects):
        raise SystemExit(86)

    # 強制 unbuffered stdout（Windows 有時會 buffer 4KB）
    try: sys.stdout.reconfigure(line_buffering=True)
    except Exception: pass

    t0 = time.time()
    print(f"  {_D}[1/3] 偵測硬體 …{_R}", flush=True)
    if args.notorch:
        # 最快路徑：完全不碰 torch
        hw = build_basic_hardware_info(
            system=platform.system(),
            release=platform.release(),
            python_version=platform.python_version(),
            cpu_count=multiprocessing.cpu_count(),
            cpu_name=platform.processor() or "unknown",
            ram_gb=None,
        )
        try:
            import psutil
            hw["ram_gb"] = round(psutil.virtual_memory().total / (1024**3), 1)
        except Exception: pass
        print(f"  {_D}      └ (--notorch) 跳過 PyTorch / CUDA 偵測{_R}", flush=True)
    else:
        hw = detect_hardware()
    print(f"  {_D}[2/3] 套用 CPU/GPU 計算預算 …{_R}", flush=True)
    env_delta, cpu_cores, gpu_ready = apply_compute_budget(
        hw, cpu_cores=args.cpu, gpu_frac=args.gpu,
        use_gpu=(not args.nogpu) and (not args.notorch),
        allow_torch=not args.notorch)
    for k, v in env_delta.items():
        os.environ[k] = v

    if args.fast:
        print(f"  {_D}[3/3] (--fast 相容旗標，無額外檢查){_R}", flush=True)
    else:
        print(f"  {_D}[3/3] 印 banner …{_R}", flush=True)

    elapsed = time.time() - t0

    if args.check:
        if not args.no_banner:
            print_boot_banner(hw, cpu_cores, gpu_ready, elapsed)
        print(f"  {_D}[--check] 自檢完成，不啟動主程式。{_R}")
        return 0

    print_runtime_health_summary()

    if not args.no_banner:
        print_boot_banner(hw, cpu_cores, gpu_ready, elapsed)

    # ── exec christine_final.py ──
    target = os.path.join(HERE, "christine_final.py")
    if not os.path.exists(target):
        print(f"  {_RD}✗{_R} 找不到 {target}")
        return 2

    # 把 boot 資訊注入（主程式 V1485 區塊會讀）
    os.environ["CHRISTINE_BOOTED_BY_V1485"] = "1"

    # 傳遞未知 args 給 christine_final.py
    sys.argv = [target] + list(extra)

    print(f"  {_GR}▶{_R}  移交給 christine_final.py（首次啟動會建大腦 + 載入 MegaCortex，約 5~30 秒…）", flush=True)
    print()

    # ── exec in-process（比 subprocess 省 2~3 秒，大腦也只載入一次） ──
    import runpy
    authorization = _issue_legacy_runtime_authorization()
    try:
        runpy.run_path(
            target,
            run_name="__main__",
            init_globals={"_CHRISTINE_LEGACY_RUNTIME_AUTHORIZATION": authorization},
        )
    except SystemExit as se:
        return int(se.code or 0)
    except KeyboardInterrupt:
        print(f"\n  {_YE}～{_R} 再見，Christine 記得你。")
        return 0
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        import traceback
        print(f"\n{_RD}[BOOT FATAL]{_R} {type(e).__name__}: {e}")
        traceback.print_exc()
        input("\n按 Enter 關閉…")
        sys.exit(99)
