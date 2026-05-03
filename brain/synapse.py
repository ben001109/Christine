"""
synapse.py — 突觸與學習律
=========================

  Hebb (1949)           "neurons that fire together wire together"
  Oja (1982)            normalized Hebb（weight 不會爆）
  Bienenstock-Cooper-Munro 1982  BCM：滑動 threshold
  Bi & Poo (1998)       STDP：spike-timing-dependent plasticity
  Markram 1997          triplet STDP
  Gerstner 2002         SRM synapse
  Abbott-Nelson 2000    短期可塑性 STP (facilitation/depression)
"""
from __future__ import annotations
import math, random

try:
    import numpy as _np
    _HAS_NP = True
except Exception:
    _HAS_NP = False


# ─────────────────────── STDP (pair-based) ────────────────────────
class STDPSynapse:
    """Bi-Poo exponential window.
       Δw = A+ exp(-Δt/τ+) for post-after-pre
       Δw = −A− exp(Δt/τ−)  for pre-after-post
    """
    def __init__(self, w=0.5, A_plus=0.01, A_minus=0.012,
                 tau_plus=20.0, tau_minus=20.0, w_min=0.0, w_max=1.0):
        self.w=w; self.Ap=A_plus; self.Am=A_minus
        self.tp=tau_plus; self.tm=tau_minus
        self.wmin=w_min; self.wmax=w_max
        self.last_pre = -1e9; self.last_post = -1e9

    def pre(self, t):
        self.last_pre = t
        dt = t - self.last_post
        if dt > 0:
            self.w -= self.Am * math.exp(-dt/self.tm)
            self._clip()

    def post(self, t):
        self.last_post = t
        dt = t - self.last_pre
        if dt > 0:
            self.w += self.Ap * math.exp(-dt/self.tp)
            self._clip()

    def _clip(self):
        if self.w < self.wmin: self.w = self.wmin
        if self.w > self.wmax: self.w = self.wmax


# ─────────────────────── STDP (matrix, vectorised) ────────────────
class STDPMatrix:
    """N_pre × N_post 矩陣版 STDP，給大規模 column 用。"""
    def __init__(self, n_pre, n_post, w_init=0.3, sparsity=0.1,
                 A_plus=0.005, A_minus=0.006, tau=20.0, wmax=1.0, seed=0):
        self.n_pre=n_pre; self.n_post=n_post
        self.Ap=A_plus; self.Am=A_minus; self.tau=tau; self.wmax=wmax
        rng = random.Random(seed)
        if _HAS_NP:
            rs = _np.random.RandomState(seed)
            mask = (rs.rand(n_pre, n_post) < sparsity).astype(_np.float32)
            self.W = (w_init * mask).astype(_np.float32)
            self.x_pre  = _np.zeros(n_pre, _np.float32)
            self.x_post = _np.zeros(n_post, _np.float32)
        else:
            self.W = [[(w_init if rng.random()<sparsity else 0.0)
                       for _ in range(n_post)] for _ in range(n_pre)]
            self.x_pre  = [0.0]*n_pre
            self.x_post = [0.0]*n_post

    def step(self, pre_spikes, post_spikes, dt=1.0):
        """輸入布林 vector。更新 traces + STDP."""
        decay = math.exp(-dt/self.tau)
        if _HAS_NP:
            ps = _np.asarray(pre_spikes, dtype=_np.float32)
            qs = _np.asarray(post_spikes, dtype=_np.float32)
            self.x_pre  = self.x_pre  * decay + ps
            self.x_post = self.x_post * decay + qs
            # pre spike + existing post trace → depression
            if ps.any():
                self.W -= self.Am * _np.outer(ps, self.x_post)
            # post spike + existing pre trace → potentiation
            if qs.any():
                self.W += self.Ap * _np.outer(self.x_pre, qs)
            _np.clip(self.W, 0.0, self.wmax, out=self.W)
            return
        # python fallback（慢，但能跑）
        for i in range(self.n_pre):  self.x_pre[i]  *= decay
        for j in range(self.n_post): self.x_post[j] *= decay
        for i,s in enumerate(pre_spikes):
            if s:
                self.x_pre[i] += 1.0
                for j in range(self.n_post):
                    self.W[i][j] = max(0.0, self.W[i][j] - self.Am*self.x_post[j])
        for j,s in enumerate(post_spikes):
            if s:
                self.x_post[j] += 1.0
                for i in range(self.n_pre):
                    self.W[i][j] = min(self.wmax, self.W[i][j] + self.Ap*self.x_pre[i])

    def project(self, pre_spikes):
        """輸入 pre bool → post 的突觸後電流"""
        if _HAS_NP:
            ps = _np.asarray(pre_spikes, dtype=_np.float32)
            return ps @ self.W
        out = [0.0]*self.n_post
        for i,s in enumerate(pre_spikes):
            if s:
                for j in range(self.n_post): out[j] += self.W[i][j]
        return out


# ─────────────────────── Oja + BCM ────────────────────────────────
class OjaBCM:
    """Oja 1982 + BCM 1982 滑動 threshold（rate-based）。
       dw/dt = η·y·(x − y·w)           (Oja)
       θ     = ⟨y²⟩                    (BCM moving threshold)
       dw/dt = η·x·y·(y − θ)           (BCM)
    用 numpy；沒 numpy 就報錯。"""
    def __init__(self, n_in, n_out, eta=1e-3, tau_theta=1000.0, seed=0):
        if not _HAS_NP:
            raise RuntimeError("OjaBCM needs numpy")
        rs = _np.random.RandomState(seed)
        self.W = (0.1*rs.randn(n_in, n_out)).astype(_np.float32)
        self.theta = _np.ones(n_out, _np.float32)
        self.eta = eta; self.tau_theta = tau_theta

    def forward(self, x):
        return x @ self.W

    def learn(self, x, y, dt=1.0):
        # BCM 調 theta
        self.theta += (y*y - self.theta) * (dt/self.tau_theta)
        # Oja 正規化
        self.W += self.eta * _np.outer(x, y) - self.eta * (y*y) * self.W
        # BCM 疊加
        self.W += 0.1 * self.eta * _np.outer(x, y*(y - self.theta))


# ─────────────────────── Short-term plasticity (Tsodyks-Markram) ──
class TMSynapse:
    """Tsodyks-Markram 1998. 短期 facilitation + depression."""
    def __init__(self, U=0.5, tau_rec=800.0, tau_fac=0.0, A=1.0):
        self.U=U; self.tau_rec=tau_rec; self.tau_fac=tau_fac; self.A=A
        self.u=U; self.x=1.0; self.last=-1e9

    def transmit(self, t):
        dt = max(0.0, t - self.last); self.last = t
        # recovery
        self.x = 1.0 - (1.0 - self.x)*math.exp(-dt/self.tau_rec)
        if self.tau_fac > 0:
            self.u = self.U + (self.u - self.U)*math.exp(-dt/self.tau_fac)
            self.u += self.U*(1.0 - self.u)
        else:
            self.u = self.U
        psp = self.A * self.u * self.x
        self.x -= self.u*self.x
        return psp
