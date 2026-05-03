"""
neuron.py — 單神經元動力學
==========================

實作三個模型（從詳細到便宜）：

  1. HodgkinHuxley     Hodgkin & Huxley (1952) J.Physiol. 117:500
  2. Izhikevich        Izhikevich (2003) IEEE TNN 14:1569
  3. LIF               Lapicque (1907) / Stein (1965)

全部回傳 (V_mV, spiked: bool)，所有 step(dt) 接受 ms。
沒有 numpy 就 fallback 純 python；只有內迴圈才考慮 numpy 加速。
"""
from __future__ import annotations
import math, random

try:
    import numpy as _np
    _HAS_NP = True
except Exception:
    _HAS_NP = False


# ─────────────────────── 1. Hodgkin-Huxley ────────────────────────
class HodgkinHuxley:
    """經典 squid giant axon 模型。dt 建議 0.01 ms。"""
    C_m  = 1.0          # μF/cm²
    g_Na = 120.0; E_Na =  50.0
    g_K  =  36.0; E_K  = -77.0
    g_L  =   0.3; E_L  = -54.387

    def __init__(self, V=-65.0):
        self.V = V
        self.m = self._m_inf(V); self.h = self._h_inf(V); self.n = self._n_inf(V)
        self.last_spike = -1e9
        self.t = 0.0

    @staticmethod
    def _alpha_m(V): return 0.1*(V+40.0)/(1.0-math.exp(-(V+40.0)/10.0)) if V != -40.0 else 1.0
    @staticmethod
    def _beta_m(V):  return 4.0*math.exp(-(V+65.0)/18.0)
    @staticmethod
    def _alpha_h(V): return 0.07*math.exp(-(V+65.0)/20.0)
    @staticmethod
    def _beta_h(V):  return 1.0/(1.0+math.exp(-(V+35.0)/10.0))
    @staticmethod
    def _alpha_n(V): return 0.01*(V+55.0)/(1.0-math.exp(-(V+55.0)/10.0)) if V != -55.0 else 0.1
    @staticmethod
    def _beta_n(V):  return 0.125*math.exp(-(V+65.0)/80.0)

    def _m_inf(self,V): a=self._alpha_m(V); return a/(a+self._beta_m(V))
    def _h_inf(self,V): a=self._alpha_h(V); return a/(a+self._beta_h(V))
    def _n_inf(self,V): a=self._alpha_n(V); return a/(a+self._beta_n(V))

    def step(self, I_ext=0.0, dt=0.01):
        V,m,h,n = self.V, self.m, self.h, self.n
        I_Na = self.g_Na * m*m*m * h * (V - self.E_Na)
        I_K  = self.g_K  * n*n*n*n     * (V - self.E_K)
        I_L  = self.g_L                 * (V - self.E_L)
        dV = (I_ext - I_Na - I_K - I_L) / self.C_m
        self.V += dV*dt
        self.m += (self._alpha_m(V)*(1-m) - self._beta_m(V)*m)*dt
        self.h += (self._alpha_h(V)*(1-h) - self._beta_h(V)*h)*dt
        self.n += (self._alpha_n(V)*(1-n) - self._beta_n(V)*n)*dt
        self.t += dt
        spiked = (self.V > 0.0) and (self.t - self.last_spike > 1.0)
        if spiked: self.last_spike = self.t
        return self.V, spiked


# ─────────────────────── 2. Izhikevich ────────────────────────────
class Izhikevich:
    """Izhikevich (2003) 2D model. 用 regular-spiking 預設。
    (a,b,c,d) = (0.02, 0.2, -65, 8) → RS；(0.02,0.2,-50,2) → CH；
    (0.1,0.2,-65,2) → FS inhibitory.
    """
    def __init__(self, a=0.02, b=0.2, c=-65.0, d=8.0, v=-70.0):
        self.a,self.b,self.c,self.d = a,b,c,d
        self.v, self.u = v, b*v
        self.last_spike = -1e9; self.t = 0.0

    def step(self, I=0.0, dt=0.5):
        if self.v >= 30.0:
            self.v = self.c; self.u += self.d
            self.last_spike = self.t
            self.t += dt
            return self.v, True
        # Euler; Izhikevich suggests sub-step for stiffness
        dv = 0.04*self.v*self.v + 5.0*self.v + 140.0 - self.u + I
        du = self.a*(self.b*self.v - self.u)
        self.v += dv*dt; self.u += du*dt
        self.t += dt
        return self.v, False


# ─────────────────────── 3. LIF ────────────────────────────────────
class LIF:
    """Leaky integrate-and-fire."""
    def __init__(self, tau=20.0, V_rest=-65.0, V_thresh=-50.0, V_reset=-70.0, R=10.0):
        self.tau=tau; self.V_rest=V_rest; self.V_thresh=V_thresh
        self.V_reset=V_reset; self.R=R; self.V=V_rest
        self.last_spike=-1e9; self.t=0.0; self.refrac=2.0

    def step(self, I=0.0, dt=0.5):
        self.t += dt
        if self.t - self.last_spike < self.refrac:
            return self.V_reset, False
        dV = (-(self.V - self.V_rest) + self.R*I) / self.tau
        self.V += dV*dt
        if self.V >= self.V_thresh:
            self.last_spike = self.t; self.V = self.V_reset
            return self.V_thresh, True
        return self.V, False


# ─────────────────────── Population (fast) ────────────────────────
class LIFPopulation:
    """向量化 N 個 LIF；numpy 有裝就飛快。"""
    def __init__(self, N, tau=20.0, V_rest=-65.0, V_thresh=-50.0, V_reset=-70.0,
                 R=10.0, refrac=2.0, seed=0):
        self.N=N; self.tau=tau; self.Vr=V_rest; self.Vt=V_thresh
        self.Vrst=V_reset; self.R=R; self.refrac=refrac
        rng = random.Random(seed)
        if _HAS_NP:
            self.V = _np.full(N, V_rest, dtype=_np.float32)
            self.last = _np.full(N, -1e9, dtype=_np.float32)
        else:
            self.V = [V_rest]*N; self.last = [-1e9]*N
        self.t = 0.0

    def step(self, I, dt=0.5):
        """I: array/list 長度 N。回 spikes: bool array."""
        self.t += dt
        if _HAS_NP:
            active = (self.t - self.last) >= self.refrac
            dV = (-(self.V - self.Vr) + self.R*_np.asarray(I, dtype=_np.float32)) / self.tau
            self.V = _np.where(active, self.V + dV*dt, self.Vrst)
            spikes = self.V >= self.Vt
            if spikes.any():
                self.last = _np.where(spikes, self.t, self.last)
                self.V    = _np.where(spikes, self.Vrst, self.V)
            return spikes
        # pure python
        out = [False]*self.N
        for i in range(self.N):
            if self.t - self.last[i] < self.refrac:
                self.V[i] = self.Vrst; continue
            dV = (-(self.V[i] - self.Vr) + self.R*I[i]) / self.tau
            self.V[i] += dV*dt
            if self.V[i] >= self.Vt:
                out[i] = True; self.last[i] = self.t; self.V[i] = self.Vrst
        return out
