"""
cerebellum.py — Marr 1969 / Albus 1971 / Ito
=============================================
Mossy fibres → granule cells (sparse expansion) → Purkinje cells.
Climbing fibre 提供 error signal → LTD on parallel-fibre→Purkinje synapses.
= 線上監督學習，適合學精細 timing / forward model。
"""
from __future__ import annotations
import random
try:
    import numpy as _np
    _HAS_NP = True
except Exception:
    _HAS_NP = False


class Cerebellum:
    def __init__(self, n_in=64, n_granule=512, n_out=16, eta=0.01, seed=0):
        self.n_in=n_in; self.n_gr=n_granule; self.n_out=n_out; self.eta=eta
        rng = random.Random(seed)
        if _HAS_NP:
            rs = _np.random.RandomState(seed)
            # MF→GC 是固定稀疏投射（Marr/Albus 假設）
            self.W_mf = (rs.randn(n_in, n_granule) * 0.5).astype(_np.float32)
            self.W_mf *= (rs.rand(n_in, n_granule) < 0.1)   # 稀疏
            self.W_pc = _np.zeros((n_granule, n_out), _np.float32)  # 可學
        else:
            def mat(a,b,d=0.5): return [[rng.gauss(0,d) if rng.random()<0.1 else 0.0
                                         for _ in range(b)] for _ in range(a)]
            self.W_mf = mat(n_in, n_granule)
            self.W_pc = [[0.0]*n_out for _ in range(n_granule)]

    def _gr(self, x):
        if _HAS_NP:
            g = x @ self.W_mf
            # 稀疏化：保留前 10% activations（granule 稀疏碼）
            k = max(1, int(0.1*self.n_gr))
            idx = _np.argpartition(g, -k)[-k:]
            out = _np.zeros_like(g); out[idx] = _np.tanh(g[idx])
            return out
        # pure python
        n_gr = self.n_gr; g = [0.0]*n_gr
        for i,xi in enumerate(x):
            if xi == 0: continue
            for j in range(n_gr): g[j] += xi*self.W_mf[i][j]
        # top 10%
        k = max(1, int(0.1*n_gr))
        thr = sorted(g, reverse=True)[k-1]
        return [v if v >= thr else 0.0 for v in g]

    def forward(self, x):
        g = self._gr(x)
        if _HAS_NP: return g @ self.W_pc
        out = [0.0]*self.n_out
        for i,gi in enumerate(g):
            if gi == 0: continue
            for j in range(self.n_out): out[j] += gi*self.W_pc[i][j]
        return out

    def learn(self, x, target):
        """監督：error = target - output；climbing fibre LTD on active PF."""
        g = self._gr(x)
        if _HAS_NP:
            y = g @ self.W_pc
            err = _np.asarray(target, _np.float32) - y
            self.W_pc += self.eta * _np.outer(g, err)
            return float(_np.linalg.norm(err))
        y = [0.0]*self.n_out
        for i,gi in enumerate(g):
            if gi == 0: continue
            for j in range(self.n_out): y[j] += gi*self.W_pc[i][j]
        err = [target[j]-y[j] for j in range(self.n_out)]
        for i,gi in enumerate(g):
            if gi == 0: continue
            for j in range(self.n_out): self.W_pc[i][j] += self.eta*gi*err[j]
        return sum(e*e for e in err)**0.5
