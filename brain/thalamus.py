"""
thalamus.py — Sherman & Guillery 2006
======================================
Thalamus = 皮質之間的中繼。First-order (lateral geniculate) + Higher-order
(pulvinar) 分工；皮質 L6 → thalamic reticular nucleus (TRN) → 抑制 thalamus
→ gated relay.
"""
from __future__ import annotations
from collections.abc import Sequence
import math
from numbers import Real
try:
    import numpy as _np
    _HAS_NP = True
except Exception:
    _HAS_NP = False


class Thalamus:
    def __init__(self, n=64, gain=1.0):
        self.n = n; self.gain = gain
        if _HAS_NP:
            self.gate = _np.ones(n, _np.float32)
        else:
            self.gate = [1.0]*n

    def relay(self, signal):
        """signal → gated signal. gate 由 L6 feedback 調整（set_gate）。"""
        if _HAS_NP:
            s = _np.asarray(signal, _np.float32)
            if len(s) < self.n: s = _np.pad(s, (0, self.n-len(s)))
            elif len(s) > self.n: s = s[:self.n]
            return s * self.gate * self.gain
        out = list(signal)
        if len(out) < self.n: out = out + [0.0]*(self.n-len(out))
        else: out = out[:self.n]
        return [out[i]*self.gate[i]*self.gain for i in range(self.n)]

    def set_gate(self, g):
        """g: 長度 n 的 0..1 向量（TRN 抑制後剩下的通過率）"""
        gate = self._validate_gate(g)
        if _HAS_NP:
            self.gate = _np.clip(_np.asarray(gate, _np.float32), 0.0, 1.0)
        else:
            self.gate = [min(1.0, max(0.0, value)) for value in gate]

    def _validate_gate(self, g):
        is_numpy_array = _HAS_NP and isinstance(g, _np.ndarray)
        if isinstance(g, (str, bytes)) or not (isinstance(g, Sequence) or is_numpy_array):
            raise ValueError("invalid-thalamus-gate")
        values = list(g)
        if len(values) != self.n or any(isinstance(value, bool) or not isinstance(value, Real) for value in values):
            raise ValueError("invalid-thalamus-gate")
        try:
            gate = [float(value) for value in values]
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError("invalid-thalamus-gate") from exc
        if not all(math.isfinite(value) for value in gate):
            raise ValueError("invalid-thalamus-gate")
        return gate
