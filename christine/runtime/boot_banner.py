from __future__ import annotations


PLAIN_COLORS = {"CY": "", "GR": "", "YE": "", "RD": "", "B": "", "D": "", "R": "", "M": ""}


def _colors(enabled: bool) -> dict[str, str]:
    if not enabled:
        return PLAIN_COLORS
    return {
        "CY": "\033[36m",
        "GR": "\033[32m",
        "YE": "\033[33m",
        "RD": "\033[31m",
        "B": "\033[1m",
        "D": "\033[2m",
        "R": "\033[0m",
        "M": "\033[35m",
    }


def render_boot_banner(
    hw,
    cpu_cores,
    gpu_ready,
    elapsed,
    *,
    gpu_frac="0.8",
    gpu_warm_ms="?",
    colors=True,
) -> list[str]:
    c = _colors(colors)
    bar = "═" * 70
    lines = [
        "",
        f"  {c['CY']}{bar}{c['R']}",
        f"  {c['M']}◆{c['R']}  {c['B']}CHRISTINE V1485 — Boot Sequence{c['R']}",
        f"  {c['CY']}{bar}{c['R']}",
        "",
        f"  {c['YE']}[Hardware]{c['R']}",
        f"    OS        : {hw['os']}     Python {hw['python']}",
        f"    CPU       : {hw['cpu_name'][:60]}",
        f"    Cores     : {c['B']}{cpu_cores}{c['R']} / {hw['cpu_count']}   (給 Christine: {int(cpu_cores / hw['cpu_count'] * 100)}%)",
        f"    RAM       : {hw['ram_gb']} GB",
    ]
    if hw["gpu"]:
        g = hw["gpu"]
        mark = f"{c['GR']}✓{c['R']}" if gpu_ready else f"{c['YE']}~{c['R']}"
        lines.append(f"    GPU       : {mark} {g['name']}  ({g['vram_gb']} GB, sm_{g['capability']})")
        if gpu_ready:
            lines.append(f"    GPU 預算  : {int(float(gpu_frac) * 100)}% VRAM  warm={gpu_warm_ms}ms")
    else:
        lines.append(f"    GPU       : {c['D']}— (CPU-only){c['R']}")
    if hw["torch"]:
        lines.append(f"    PyTorch   : {hw['torch']}")
    lines.extend(
        [
            "",
            f"  {c['GR']}◆{c['R']}  Boot budget applied in {c['B']}{elapsed * 1000:.0f}ms{c['R']}  →  {c['B']}handing off to christine_final.py …{c['R']}",
            f"  {c['CY']}{bar}{c['R']}",
            "",
        ]
    )
    return lines
