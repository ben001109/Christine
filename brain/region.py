"""
region.py — 皮質區域（一堆 column 組成）
========================================

Felleman & Van Essen 1991 — hierarchical visual cortex
Mesulam 1998               — large-scale networks
Hawkins HTM                — hierarchical temporal memory

一個 region = grid of columns；鄰近 column 橫向投射；
region 有一個 "abstract rate vector" = 每個 column 的 L5 輸出率。
這個向量就是往上層送的 "符號"。
"""
from __future__ import annotations
from .column import CorticalColumn

try:
    import numpy as _np
    _HAS_NP = True
except Exception:
    _HAS_NP = False


class CorticalRegion:
    def __init__(self, name, n_columns=16, n_per_layer=48, seed=0):
        self.name = name
        self.columns = [
            CorticalColumn(n_per_layer=n_per_layer, seed=seed*1000 + i)
            for i in range(n_columns)
        ]
        self.n = n_columns

    def step(self, input_vec, dt=0.5):
        """input_vec: length n_columns。每個 column 拿到的 L4 輸入的總 drive。"""
        outs = []
        for i, col in enumerate(self.columns):
            # 把 drive 變成 L4 population 的輸入電流
            drive = float(input_vec[i]) if i < len(input_vec) else 0.0
            n_L4 = col.pops["L4"].N
            if _HAS_NP:
                I = _np.full(n_L4, drive, dtype=_np.float32)
            else:
                I = [drive]*n_L4
            col.step(I, dt=dt)
            outs.append(col.get_output_rate())
        return outs  # 長度 = n_columns 的 rate 向量


class Hierarchy:
    """多個 region 串起來。低層輸入 → 高層抽象。"""
    def __init__(self, sizes, seed=0):
        """sizes: list of (name, n_columns)"""
        self.regions = [CorticalRegion(n, c, seed=seed+i)
                        for i,(n,c) in enumerate(sizes)]

    def step(self, raw_input, dt=0.5):
        v = list(raw_input)
        for r in self.regions:
            # 如果上層 column 數 ≠ 下層，用投影
            n = r.n
            if len(v) < n:
                v = v + [0.0]*(n-len(v))
            elif len(v) > n:
                # 簡單平均池化
                k = len(v) / n
                v = [sum(v[int(i*k):int((i+1)*k)]) / max(1,int(k)) for i in range(n)]
            v = r.step(v, dt=dt)
        return v   # 最高層輸出
