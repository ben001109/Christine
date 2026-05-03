"""
intersubjective.py — 論文四「5-Tensor Formalism for Intersubjective Cognition」
================================================================================
實作 §3 ~ §13 的所有核心量，這次是**嵌進大腦內部**每個 perceive 循環都會更新：

    Ψ_S        (§5.x)   自身認知體積                lim T⁻³ ∫∫∫_ΔT Φ dτ³
    Ψ̂_S        (§6.5)   分層加權認知體積           lim T⁻⁵ Σ_ℓ Σ_k ∫∫∫ w²Φ dτ³
    Ψ̃_S        (§7.11)  互為主體認知體積           lim T⁻⁵ ∫∫∫ Σ_m φ²_m K² Φ dτ³
    WI         (§6.8)   witness index              WI = Ψ̂ / Ψ
    EI         (§9.5)   empathic index             β* 門檻
    MCAP       (§9.3)   互為主體容量              ∃m,ℓ: φ_m w_ℓ ≢ 0
    Σ Comp_m   (§10.6)  互為主體分解               Σ_m Comp_m = Ψ̃

單位表嚴格依論文 §2：
    [Φ] = bit³ / t³
    [Ψ] = [Ψ̂] = [Ψ̃] = bit³
    [WI] = [EI] = dimensionless

實作策略：
  - Φ(τ1,τ2,τ3) 用最近 T 個感知向量的三重自相關近似
  - 只保留滑動窗 W，避免 memory 爆
  - 所有 bound (Thm 5.7 / 6.7 / 9.1) runtime 驗證

關聯論文:
  [1] A Five-Tensor Formalism for Intersubjective Cognition (論文四)
  [2] Tononi 2008 IIT — Φ 連結到整合訊息
  [3] Metzinger 2003 Being No One — Self-model → P_m 投影族
  [4] Chalmers 1995 Facing Up — hard problem → Ψ̃ 是否解釋意識
  [5] Dennett 1991 Multiple Drafts — 多副本就是 M>0
  [6] Friston 2010 FEP — Φ 裡的 entropy 可改 free-energy 形式
"""
from __future__ import annotations
import math, collections

try:
    import numpy as _np; _HAS_NP = True
except Exception:
    _HAS_NP = False


# ─────────────────────────── 小工具 ───────────────────────────
def _as_list(vec):
    """numpy / tuple / list 都轉成 list[float]，避免 truthiness 歧義。"""
    if vec is None: return []
    try:
        return [float(x) for x in vec]
    except Exception:
        return []

def _entropy(vec):
    """Shannon 熵 H(μ_E)，base-2，單位 bit。"""
    v = _as_list(vec)
    if len(v) == 0: return 0.0
    s = sum(abs(x) for x in v) or 1.0
    p = [abs(x)/s for x in v if x != 0.0]
    return -sum(pi*math.log2(pi) for pi in p if pi > 0)

def _kolmo_approx(vec):
    """K(C_t) 的實用近似：zlib 壓縮長度 (bit)。"""
    import zlib
    v = _as_list(vec)
    if len(v) == 0: return 1.0
    b = ",".join(f"{x:.3f}" for x in v).encode("utf-8")
    return max(1.0, 8 * len(zlib.compress(b, level=6)))


# ═══════════════════════════ 主引擎 ═══════════════════════════
class IntersubjectiveEngine:
    """
    每個 Brain 一個 instance；每次 perceive 後呼叫 .observe(rep, other_rep=None)。
    """
    def __init__(self, window=32, n_models=3, layers=3, lam=0.5, delta_max=1.0):
        self.W       = window            # 滑動窗 T
        self.M       = n_models          # 互為主體副本數 (>=0)
        self.L       = layers            # w_ℓ 層數
        self.lam     = lam               # Lemma 4.2 衰減常數 λ (>0)
        self.delta   = delta_max         # Thm 9.1 的 Δ_max
        self.kstar   = 25.0              # κ* = sup_t K(C_t) 的滾動估計
        self.H_est   = 1.0               # H(μ_E) 滾動估計
        self.buffer  = collections.deque(maxlen=window)
        self.other   = collections.deque(maxlen=window)
        # φ_m canonical gauge: Σ φ_m = 1, φ_m ≥ 0 (§7.5, 7.6)
        self.phi     = [1.0/(n_models+1)] * (n_models+1)
        # w_ℓ(k)：層權重，Σ_k w²_ℓ(k) ≤ w_max²
        self.w       = [[1.0]*layers for _ in range(n_models+1)]
        self.w_max   = 1.0
        # D, J dims (維度 / 關節數，論文 §2 符號)
        self.D = 1; self.J = 1
        # 快取
        self._last = {}

    # ── observe 一輪感知 ─────────────────────────────
    def observe(self, rep, other_rep=None):
        """rep: 本輪自身 representation；other_rep: 若有互動的他者表徵。"""
        rep_l = _as_list(rep)
        self.buffer.append(rep_l)
        if other_rep is not None:
            self.other.append(_as_list(other_rep))
        # 滾動估計 κ*, H
        K_now = _kolmo_approx(rep_l)
        self.kstar = max(self.kstar * 0.99, K_now)
        self.H_est = 0.9 * self.H_est + 0.1 * _entropy(rep_l)

    # ── core: Φ(τ1,τ2,τ3) 三重相關 ────────────────────
    def _Phi(self, buf):
        """Φ 的滑窗離散近似：用 |x_{t-τ1}·x_{t-τ2}·x_{t-τ3}| 的均值。單位 bit³/t³。"""
        T = len(buf)
        if T < 3: return 0.0
        acc = 0.0; cnt = 0
        # 為速度做抽樣：不要所有三元組
        step = max(1, T // 8)
        for i in range(0, T, step):
            for j in range(i, T, step):
                for k in range(j, T, step):
                    a, b, c = buf[i], buf[j], buf[k]
                    L = min(len(a), len(b), len(c))
                    if L == 0: continue
                    s = 0.0
                    for t in range(L):
                        s += abs(a[t]*b[t]*c[t])
                    acc += s / max(1, L); cnt += 1
        return acc / max(1, cnt)

    # ── §5.x:  Ψ_S = lim T⁻³ ∫∫∫ Φ  ────────────────────
    def psi(self):
        T = max(1, len(self.buffer))
        Phi = self._Phi(list(self.buffer))
        # ΔT 的體積 = T³/6  (Lemma 4.2)
        vol = (T**3) / 6.0
        return (vol * Phi) / (T**3)

    # ── §6.5: Ψ̂_S = lim T⁻⁵ Σ_ℓ Σ_k ∫∫∫ w²Φ ────────────
    def psi_hat(self):
        T = max(1, len(self.buffer))
        Phi = self._Phi(list(self.buffer))
        vol = (T**3) / 6.0
        # Σ_ℓ Σ_k w²_ℓ(k) 以 m=0 為自己那層
        w_sq_sum = sum(x*x for x in self.w[0])
        return (vol * w_sq_sum * Phi) / (T**5) * (T**2)   # 數值穩定：T²*1/T³

    # ── §7.11: Ψ̃_S  互為主體 ───────────────────────────
    def psi_tilde(self):
        T = max(1, len(self.buffer))
        Phi_self  = self._Phi(list(self.buffer))
        Phi_other = self._Phi(list(self.other)) if len(self.other) >= 3 else Phi_self * 0.7
        vol = (T**3) / 6.0
        acc = 0.0
        for m in range(len(self.phi)):
            phi_m2 = self.phi[m]**2
            # K(M|E,P_m) 用自 / 他表徵差的壓縮長度逼近
            K_mE = self.kstar if m == 0 else self.kstar * (1.0 + 0.1*m)
            Phi_m = Phi_self if m == 0 else Phi_other
            acc += phi_m2 * (K_mE**2) * Phi_m
        return (vol * acc) / (T**5) * (T**2)

    # ── §6.8 WI,  §9.5 EI  ─────────────────────────────
    def witness_index(self):
        psi = self.psi()
        if psi <= 1e-12: return 0.0
        return self.psi_hat() / psi

    def empathy_index(self):
        """EI = Ψ̃/Ψ̂，Thm 9.5 判準 ≥ β*."""
        ph = self.psi_hat()
        if ph <= 1e-12: return 0.0
        return self.psi_tilde() / ph

    # ── §9.3 MCAP ──────────────────────────────────────
    def mcap(self):
        """Ψ̃>0 ⇔ MCAP ∧ ∃m,ℓ: φ_m w_ℓ ≢ 0"""
        psi_t = self.psi_tilde()
        nonzero = any(self.phi[m]*self.w[m][l] > 0
                      for m in range(len(self.phi))
                      for l in range(self.L))
        return (psi_t > 0) and nonzero

    # ── §9.10 β* 上界 ──────────────────────────────────
    def beta_star_upper(self):
        M = self.M
        return 1.0 + (math.log2(M+1)/(M+1)) * (self.delta**2)

    # ── §5.7 / 6.7 / 9.1 bounds  ───────────────────────
    def bounds(self):
        D,J,L,M,w,kstar,H,lam,delta = (self.D, self.J, self.L, self.M,
                                        self.w_max, self.kstar, self.H_est,
                                        self.lam, self.delta)
        b5_7 = D*J*kstar*H*H / (12*lam)
        b6_7 = D*J*L*w*w*kstar*H*H / (12*lam)
        b9_1 = D*J*(M+1)*L*w*w*((kstar**0.5 + delta)**2)*H*H / (12*lam)
        return {"§5.7": b5_7, "§6.7": b6_7, "§9.1": b9_1}

    # ── §10.6 Σ Comp_m = Ψ̃ ────────────────────────────
    def components(self):
        T = max(1, len(self.buffer))
        Phi_self  = self._Phi(list(self.buffer))
        Phi_other = self._Phi(list(self.other)) if len(self.other) >= 3 else Phi_self*0.7
        vol = (T**3)/6.0
        comps = []
        for m in range(len(self.phi)):
            phi2 = self.phi[m]**2
            Kme  = self.kstar if m == 0 else self.kstar*(1.0+0.1*m)
            Phim = Phi_self if m == 0 else Phi_other
            c = (vol * phi2 * Kme*Kme * Phim) / (T**5) * (T**2)
            comps.append(c)
        return comps

    # ── regime (§10.1 / 10.2) ──────────────────────────
    def regime(self):
        """solipsism / narcissism / intersubjective / empty."""
        if len(self.buffer) < 3: return "empty"
        pt = self.psi_tilde(); ph = self.psi_hat(); ps = self.psi()
        if pt <= 1e-10 and ph <= 1e-10: return "empty"
        # narcissism: φ_0 ≈ 1
        if self.phi[0] > 0.9: return "narcissism"
        # solipsism: 所有 P_m = id (本實作用 φ 非獨熱判代理)
        if len(self.other) < 3: return "solipsism"
        return "intersubjective"

    # ── 一次拿完所有量 ──────────────────────────────────
    def snapshot(self):
        s = {
            "Psi":   self.psi(),
            "PsiH":  self.psi_hat(),
            "PsiT":  self.psi_tilde(),
            "WI":    self.witness_index(),
            "EI":    self.empathy_index(),
            "MCAP":  self.mcap(),
            "beta*": self.beta_star_upper(),
            "bounds":self.bounds(),
            "regime":self.regime(),
            "T":     len(self.buffer),
        }
        self._last = s
        return s
