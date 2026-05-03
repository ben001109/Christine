"""
hippocampus.py — 海馬迴
========================
O'Keefe & Nadel 1978     — cognitive map
Buzsáki 2002             — sharp-wave ripples / replay
Marr 1971                — CA3 auto-associator

實作：
  DG   — pattern separation (sparse projection)
  CA3  — recurrent Hopfield-ish auto-associator
  CA1  — pattern completion readout
  Replay — 定期重播最近 k 個 pattern 給皮質鞏固
"""
from __future__ import annotations
import random, math

try:
    import numpy as _np
    _HAS_NP = True
except Exception:
    _HAS_NP = False


class Hippocampus:
    def __init__(self, input_dim=64, dg_dim=256, ca3_dim=128, seed=0):
        self.d_in = input_dim; self.d_dg = dg_dim; self.d_ca3 = ca3_dim
        rng = random.Random(seed)
        if _HAS_NP:
            rs = _np.random.RandomState(seed)
            self.W_dg  = (rs.randn(input_dim, dg_dim) * 0.1).astype(_np.float32)
            self.W_ca3 = _np.zeros((ca3_dim, ca3_dim), _np.float32)   # 自聯想
            self.W_ec_ca3 = (rs.randn(dg_dim, ca3_dim) * 0.1).astype(_np.float32)
            self.W_ca1 = (rs.randn(ca3_dim, input_dim) * 0.1).astype(_np.float32)
        else:
            def mat(a,b): return [[rng.gauss(0,0.1) for _ in range(b)] for _ in range(a)]
            self.W_dg = mat(input_dim, dg_dim)
            self.W_ca3 = [[0.0]*ca3_dim for _ in range(ca3_dim)]
            self.W_ec_ca3 = mat(dg_dim, ca3_dim)
            self.W_ca1 = mat(ca3_dim, input_dim)
        self.episodes = []      # 最近 k 個 pattern (for replay)
        self.max_episodes = 50

    def _sparse_topk(self, vec, k_frac=0.05):
        """winner-take-all: 保留前 k% 最大，其餘歸零。DG 的 pattern separation。"""
        if _HAS_NP:
            n = len(vec); k = max(1, int(n*k_frac))
            idx = _np.argpartition(vec, -k)[-k:]
            out = _np.zeros_like(vec); out[idx] = 1.0
            return out
        n = len(vec); k = max(1, int(n*k_frac))
        thr = sorted(vec, reverse=True)[k-1]
        return [1.0 if v >= thr else 0.0 for v in vec]

    def encode(self, x):
        """存一個 episodic pattern。"""
        if _HAS_NP:
            x = _np.asarray(x, _np.float32)
            if len(x) < self.d_in: x = _np.pad(x, (0, self.d_in-len(x)))
            elif len(x) > self.d_in: x = x[:self.d_in]
            dg = self._sparse_topk(x @ self.W_dg)
            ca3 = _np.tanh(dg @ self.W_ec_ca3)
            # Hebbian: CA3 自聯想
            self.W_ca3 += 0.01 * _np.outer(ca3, ca3)
            _np.fill_diagonal(self.W_ca3, 0.0)
            # CA1 readout 也學
            self.W_ca1 += 0.01 * _np.outer(ca3, x)
            self.episodes.append(x.copy())
        else:
            # 純 python fallback（慢，能跑）
            if len(x) < self.d_in: x = list(x) + [0.0]*(self.d_in-len(x))
            x = list(x)[:self.d_in]
            self.episodes.append(x)
        if len(self.episodes) > self.max_episodes:
            self.episodes.pop(0)

    def recall(self, cue, steps=5):
        """給部分線索 → 補全 pattern。"""
        if not _HAS_NP:
            # fallback: 回最近一個 episode
            return list(self.episodes[-1]) if self.episodes else [0.0]*self.d_in
        x = _np.asarray(cue, _np.float32)
        if len(x) < self.d_in: x = _np.pad(x, (0, self.d_in-len(x)))
        elif len(x) > self.d_in: x = x[:self.d_in]
        dg  = self._sparse_topk(x @ self.W_dg)
        ca3 = _np.tanh(dg @ self.W_ec_ca3)
        for _ in range(steps):
            ca3 = _np.tanh(ca3 @ self.W_ca3)
        return ca3 @ self.W_ca1

    def replay(self):
        """吐出一段 episode，讓皮質在「睡眠」時鞏固。"""
        if not self.episodes: return None
        return self.episodes[random.randint(0, len(self.episodes)-1)]
