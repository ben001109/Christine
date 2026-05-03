"""
intersubjective.py — 論文四「A Five-Tensor Formalism for Intersubjective Cognition」
================================================================================
Version 7 — Expanded Edition with Information Singularity Control
Josh, Independent Researcher, April 2026

★ 本檔案是論文 Appendix D Listing D.1 + Listing E.1 的 **1:1 Python 實作**，
   並嵌進 Brain 的 perceive cycle，每 tick 更新一次。

────────────────────── 符號表 (嚴格依論文 §Nomenclature) ──────────────────────
    K(x), K(x|y)          : 前綴 Kolmogorov 複雜度（近似：8·|gzip(x)|）
    λ                     : overwrite rate (§3.3)         λ>0
    κ                     : architectural ceiling (§3.4)
    κ* = sup_{k,i,j} K(M_k^(i)|E^(j))²                  (§3.6 A5)
    Δ_T ⊂ R³              : time simplex {0≤τ1≤τ2≤τ3≤T} (§4.1)
    vol(Δ_T) = T³/6                                        (Lemma 4.2)
    Φ(τ1,τ2,τ3) = e^{-λ|τ3-τ2|} · [K(M_τ1)−K(C_τ2)]₊ · H(μ_E|M_[0,τ1]) (Def 4.6)
    T⁽²⁾_ij,k  = K(M_k^(i) | E^(j))                     (Def 5.1)
    T̂⁽⁴⁾_ij,k,ℓ = K(M_k^(i) | E^(j)) · w_ℓ(k)            (Def 6.2)
    T̃⁽⁵⁾_ij,k,ℓ,m = K(M_k^(i) | E^(j), P_m) · w_ℓ(k) · φ_m (Def 7.8)
    N⁽²⁾(τ1) = Σ_{i,j} (Σ_{k≤τ1} T² ê_k)²              (Def 5.2)
    N⁽⁴⁾(τ1) = Σ_{i,j,ℓ}  (Σ_{k≤τ1} T̂² ê_k)²           (Def 6.3)
    N⁽⁵⁾(τ1) = Σ_{i,j,ℓ,m} (Σ_{k≤τ1} T̃  ê_k)²   (m 在平方內側 Def 7.9)

    Ψ_S   = lim_T T⁻⁵ ∫∫∫_ΔT T²·N⁽²⁾·Φ d³τ               (Def 5.4)
    Ψ̂_S   = lim_T T⁻⁵ ∫∫∫_ΔT  T·N⁽⁴⁾·Φ d³τ               (Def 6.5)
    Ψ̃_S   = lim_T T⁻⁵ ∫∫∫_ΔT    N⁽⁵⁾·Φ d³τ               (Def 7.11)

    WI(S) = Ψ̂/Ψ                                           (Def 6.8)
    EI(S) = Ψ̃/Ψ̂                                           (Def 11.2)
    α*    : wisdom threshold > 1                           (Thm 6.9)
    β*(M,Δ_max) = 1 + (log₂(M+1)/(M+1))·max(1 − Δ/(ln2·log₂(M+1)), 0)  (Thm 9.10)

    Comp_m(S) = lim_T T⁻⁵ ∫∫∫ Σ_{i,j,ℓ}‖·_m‖² Φ d³τ       (Def 10.5)
    Σ_m Comp_m = Ψ̃                                        (Thm 10.6)

    S_m^(n) : blow-up operator of order n (§13.1)
    R_μ     : retrieval operator to horizon H_μ (§13.2)
    P_Θ(n)  = a·n + b·log₂(1+n) + c_Θ   (Def 13.9)  predictor

★ 與論文 Appendix D Listing D.1 的對應：
    _estimate_K()       ≡ estimate_K(s)             Thm 2.11 coding
    _K_cond()           ≡ K_cond(x,y)               §2
    Perspective         ≡ Perspective dataclass     Def 7.1
    Sing()              ≡ Sing(P,n)                 Def 13.1 / Thm 13.2
    Ret()               ≡ Ret(P,mu)                 Def 13.5
    Pred()              ≡ Pred(n,a,b,c)             Def 13.9
    canonical_gauge()   ≡ canonical_gauge(phi_raw)  Conv 7.6
    _T5_entry()         ≡ T5(...)                   Def 7.8
    _N5()               ≡ N5(...)                   Def 7.9
    _K_mem()            ≡ K_mem                     Def 4.6 部件
    _K_code()           ≡ K_code                    Def 3.4 / Lemma 3.5
    _H_cond()           ≡ H_cond                    §4.6
    _Phi()              ≡ Phi(t1,t2,t3,...)         Def 4.6
    psi_tilde()         ≡ Psi_tilde(T,...)          Def 7.11
    empathy_index()     ≡ EI(psi_hat,psi_tilde)     Def 11.2
    singularity_trajectory()                        Thm 13.7
"""
from __future__ import annotations
import math, gzip, collections
from dataclasses import dataclass
from typing import Callable, List, Sequence, Optional

try:
    import numpy as _np
    _HAS_NP = True
except Exception:
    _HAS_NP = False


# ═══════════════════════════════════════════════════════════════════════════
#  §2.3 Algorithmic complexity — Appendix D Listing D.1
# ═══════════════════════════════════════════════════════════════════════════
def _estimate_K(s) -> int:
    """K(x) ≈ 8·|gzip(x)|  (Thm 2.11 upper bound via coding)."""
    if s is None:
        return 1
    if not isinstance(s, (bytes, bytearray)):
        s = str(s).encode("utf-8", errors="replace")
    return 8 * len(gzip.compress(bytes(s), compresslevel=9))


def _K_cond(x, y) -> int:
    """K(x|y) ≈ max(0, K(y·x) − K(y))."""
    if not isinstance(x, (bytes, bytearray)):
        x = (str(x) if x is not None else "").encode("utf-8", errors="replace")
    if not isinstance(y, (bytes, bytearray)):
        y = (str(y) if y is not None else "").encode("utf-8", errors="replace")
    return max(0, _estimate_K(bytes(y) + bytes(x)) - _estimate_K(bytes(y)))


def _to_bytes(v) -> bytes:
    """把任何向量 / 文字 / bytes 統一編成 bytes（做 K 用）。"""
    if v is None:
        return b""
    if isinstance(v, (bytes, bytearray)):
        return bytes(v)
    if isinstance(v, str):
        return v.encode("utf-8", errors="replace")
    try:
        if _HAS_NP and isinstance(v, _np.ndarray):
            arr = v.tolist()
        else:
            arr = list(v)
        return (",".join(f"{float(x):.4f}" for x in arr)).encode("utf-8")
    except Exception:
        return repr(v).encode("utf-8", errors="replace")


# ═══════════════════════════════════════════════════════════════════════════
#  §7.1 Perspectives — Listing D.1
# ═══════════════════════════════════════════════════════════════════════════
@dataclass
class Perspective:
    """§7.1 Def 7.1 — (P1) Borel; (P2) |K(π₁P)−K(x)| ≤ Δ_P; (P3) computable."""
    name: str
    description: bytes       # d_P — 有限描述 (Δ_P 的載體)
    distortion: float        # Δ_P ≥ 0

    def __call__(self, tok: bytes) -> bytes:
        return bytes(self.description) + (tok if isinstance(tok, (bytes, bytearray)) else _to_bytes(tok))

    def __repr__(self):
        return f"P({self.name},Δ={self.distortion:.2f},|d|={len(self.description)})"


# 三個論文標配 perspective
P_IDENTITY  = Perspective("identity",  b"",       0.0)   # P₀ = id
P_ADVERSARY = Perspective("adversary", b"ADV:",   1.0)
P_OBSERVER  = Perspective("observer",  b"OBS:",   1.0)


def Sing(P: Perspective, n: int) -> Perspective:
    """§13.1 Def 13.1 — S_m^(n) := P∘P∘…∘P (n 次)。
    Thm 13.2: K(M|E, S^(n)) ∈ [n·Δ_P − c·log n, n·Δ_P + c·log n]."""
    n = max(0, int(n))
    return Perspective(f"{P.name}^{n}", bytes(P.description) * n, n * P.distortion)


def Ret(P: Perspective, mu: float) -> Perspective:
    """§13.2 Def 13.5 — R_μ(P) := arg min_{Q∈H_μ} Δ(P,Q),  H_μ = {Q:Δ_Q ≤ μ}."""
    mu = float(mu)
    if P.distortion <= mu:
        return P
    keep = max(1, int(len(P.description) * mu / max(P.distortion, 1e-9)))
    return Perspective(f"R({P.name},μ={mu:g})", bytes(P.description[:keep]), mu)


def Pred(n: int, a: float, b: float, c: float) -> float:
    """§13.3 Def 13.9 — P_Θ(n) = a·n + b·log₂(1+n) + c."""
    return a * n + b * math.log2(1 + max(0, n)) + c


def canonical_gauge(phi_raw: Sequence[float]) -> List[float]:
    """§7.6 Convention — Σ φ_m = 1, φ_m ≥ 0."""
    vals = [max(0.0, float(p)) for p in phi_raw]
    s = sum(vals)
    if s <= 0:
        raise ValueError("canonical_gauge: all weights non-positive.")
    return [p / s for p in vals]


# ═══════════════════════════════════════════════════════════════════════════
#  主引擎：IntersubjectiveEngine
# ═══════════════════════════════════════════════════════════════════════════
class IntersubjectiveEngine:
    """Five-Tensor Formalism, Version 7 — runtime instance for one Brain.

    每次 perceive 呼叫 .observe(self_rep, other_rep=...) 一次；
    .snapshot() 回傳 {Ψ, Ψ̂, Ψ̃, WI, EI, β*, MCAP, regime, Comp_m, bounds}.

    預設對應論文 §14 toy: D=J=1, M+1=2, L=2, T=4, λ=0.5, Δ_max=1, κ=32.
    """

    def __init__(self,
                 window: int = 32,
                 n_models: int = 3,                # M+1
                 layers: int = 3,                  # L
                 lam: float = 0.5,                 # λ
                 delta_max: float = 1.0,           # Δ_max
                 perspectives: Optional[List[Perspective]] = None,
                 phi_raw: Optional[Sequence[float]] = None,
                 kappa_ceiling: int = 32):         # κ
        self.W        = int(window)
        self.M        = max(0, int(n_models) - 1)
        self.L        = max(1, int(layers))
        self.lam      = float(lam)
        self.delta    = float(delta_max)
        self.kappa    = int(kappa_ceiling)
        self.kstar    = 25.0                            # κ* rolling
        self.H_est    = 1.0                             # H(μ_E) rolling (bit)
        self.H_env    = 1.0                             # prior
        self.D, self.J = 1, 1

        # perspective family {P_0=id, P_1, ..., P_M}
        if perspectives is None:
            defaults = [P_IDENTITY, P_ADVERSARY, P_OBSERVER,
                        Perspective("child",   b"CHILD:",   0.8),
                        Perspective("elder",   b"ELDER:",   0.9),
                        Perspective("stranger",b"STRANGER:",1.2)]
            perspectives = defaults[:(self.M + 1)]
            while len(perspectives) < self.M + 1:
                perspectives.append(P_IDENTITY)
        self.P = list(perspectives)
        assert len(self.P) == self.M + 1

        # φ_m canonical gauge
        if phi_raw is None:
            phi_raw = [1.0] + [0.7] + [0.5] * max(0, self.M - 1)
            phi_raw = phi_raw[:(self.M + 1)]
            while len(phi_raw) < self.M + 1:
                phi_raw.append(0.3)
        self.phi = canonical_gauge(phi_raw)

        # w_ℓ(k) layers
        self.w_funcs: List[Callable[[int], float]] = [
            (lambda k: 1.0),
            (lambda k: math.exp(-k / 2.0)),
            (lambda k: math.exp(-k / 4.0)),
        ][:self.L]
        while len(self.w_funcs) < self.L:
            self.w_funcs.append(lambda k: 1.0)
        self.w_max = 1.0

        # sliding buffers
        self._mem_buf: collections.deque = collections.deque(maxlen=self.W)
        self._env_buf: collections.deque = collections.deque(maxlen=self.W)
        self._other_buf: collections.deque = collections.deque(maxlen=self.W)

        self._last: dict = {}
        self._n_observations = 0
        self._cache_valid = False
        self._cache: dict = {}

    # ──────────── observe ────────────
    def observe(self, rep, other_rep=None, env=None):
        rep_b = _to_bytes(rep) or b"\x00"
        mem_row: List[bytes] = [rep_b]
        self._mem_buf.append(mem_row)

        if env is None:
            env_row: List[bytes] = [bytes(((b ^ 0x55) & 0xFF) for b in rep_b[:32])]
        else:
            env_row = [_to_bytes(env)]
        self._env_buf.append(env_row)

        self._other_buf.append(_to_bytes(other_rep) if other_rep is not None else rep_b)

        K_now = _estimate_K(rep_b)
        self.kstar = max(0.99 * self.kstar, float(K_now * K_now))
        self.H_est = 0.9 * self.H_est + 0.1 * self._shannon_entropy(rep_b)
        self._n_observations += 1
        self._cache_valid = False

    # ──────────── 低階組件 ────────────
    @staticmethod
    def _shannon_entropy(b: bytes) -> float:
        if not b:
            return 0.0
        from collections import Counter
        c = Counter(b); n = len(b); h = 0.0
        for v in c.values():
            p = v / n
            if p > 0:
                h -= p * math.log2(p)
        return h

    def _K_mem(self, t1: int) -> float:
        """K(M_[0,τ1])."""
        if t1 < 0 or len(self._mem_buf) == 0:
            return 0.0
        mem_list = list(self._mem_buf)
        t1 = min(t1, len(mem_list) - 1)
        blob = b"".join(b"".join(step) for step in mem_list[: t1 + 1])
        return float(_estimate_K(blob))

    def _K_code(self, t2: int) -> float:
        """K(C_τ2).  Listing D.1: min(ceiling, 2·log₂(2+t2))."""
        return float(min(self.kappa, int(2 * math.log2(2 + max(0, t2)))))

    def _H_cond(self, t1: int) -> float:
        """H(μ_E | M_[0,τ1]) ≈ 0.8 · H_env (Listing D.1)."""
        return 0.8 * self.H_env

    def _Phi(self, t1: int, t2: int, t3: int) -> float:
        """Def 4.6:  Φ = e^{−λ|τ3−τ2|} · [K(M_τ1) − K(C_τ2)]₊ · H(μ_E | M_[0,τ1])."""
        decay = math.exp(-self.lam * abs(t3 - t2))
        gate  = max(0.0, self._K_mem(t1) - self._K_code(t2))
        ent   = self._H_cond(t1)
        return decay * gate * ent

    # ──────────── tensor entries ────────────
    def _T2_entry(self, i: int, j: int, k: int) -> float:
        if k >= len(self._mem_buf):
            return 0.0
        mem_row = list(self._mem_buf)[k]
        env_row = list(self._env_buf)[k]
        return float(_K_cond(mem_row[i % self.D], env_row[j % self.J]))

    def _T4_entry(self, i: int, j: int, k: int, ell: int) -> float:
        return self._T2_entry(i, j, k) * float(self.w_funcs[ell % self.L](k))

    def _T5_entry(self, i: int, j: int, k: int, ell: int, m: int) -> float:
        """Def 7.8: T̃_{ij,k,ℓ,m} = K(M_k^(i) | E^(j), P_m) · w_ℓ(k) · φ_m."""
        if k >= len(self._mem_buf):
            return 0.0
        mem_row = list(self._mem_buf)[k]
        env_row = list(self._env_buf)[k]
        P_m = self.P[m % len(self.P)]
        cond = bytes(env_row[j % self.J]) + bytes(P_m.description)
        k_cond = _K_cond(mem_row[i % self.D], cond)
        return float(k_cond) * float(self.w_funcs[ell % self.L](k)) * float(self.phi[m])

    # ──────────── N^(2), N^(4), N^(5) ────────────
    def _N2(self, t1: int) -> float:
        if len(self._mem_buf) == 0: return 0.0
        t1 = min(t1, len(self._mem_buf) - 1)
        total = 0.0
        for i in range(self.D):
            for j in range(self.J):
                acc = 0.0
                for k in range(t1 + 1):
                    v = self._T2_entry(i, j, k)
                    acc += v * v
                total += acc
        return total

    def _N4(self, t1: int) -> float:
        if len(self._mem_buf) == 0: return 0.0
        t1 = min(t1, len(self._mem_buf) - 1)
        total = 0.0
        for i in range(self.D):
            for j in range(self.J):
                for ell in range(self.L):
                    acc = 0.0
                    for k in range(t1 + 1):
                        v = self._T4_entry(i, j, k, ell)
                        acc += v * v
                    total += acc
        return total

    def _N5(self, t1: int) -> float:
        if len(self._mem_buf) == 0: return 0.0
        t1 = min(t1, len(self._mem_buf) - 1)
        total = 0.0
        for i in range(self.D):
            for j in range(self.J):
                for m in range(self.M + 1):
                    for ell in range(self.L):
                        acc = 0.0
                        for k in range(t1 + 1):
                            v = self._T5_entry(i, j, k, ell, m)
                            acc += v * v
                        total += acc
        return total

    # ──────────── 三重離散積分 ────────────
    def _integrate(self, kind: str) -> float:
        T = max(1, len(self._mem_buf))
        if T < 1: return 0.0

        N_of = {}
        for t1 in range(T):
            if kind == "psi":
                N_of[t1] = self._N2(t1) * (T * T)
            elif kind == "psi_hat":
                N_of[t1] = self._N4(t1) * T
            elif kind == "psi_tilde":
                N_of[t1] = self._N5(t1)
            else:
                N_of[t1] = 0.0

        I = 0.0
        for t1 in range(T):
            N = N_of[t1]
            if N <= 0: continue
            for t2 in range(t1, T):
                for t3 in range(t2, T):
                    I += N * self._Phi(t1, t2, t3)
        return I / (T ** 5)

    def psi(self) -> float:
        """Ψ_S (Def 5.4)."""
        if self._cache_valid and "Psi" in self._cache: return self._cache["Psi"]
        v = self._integrate("psi"); self._cache["Psi"] = v; return v

    def psi_hat(self) -> float:
        """Ψ̂_S (Def 6.5)."""
        if self._cache_valid and "PsiH" in self._cache: return self._cache["PsiH"]
        v = self._integrate("psi_hat"); self._cache["PsiH"] = v; return v

    def psi_tilde(self) -> float:
        """Ψ̃_S (Def 7.11) ≡ Listing D.1 Psi_tilde."""
        if self._cache_valid and "PsiT" in self._cache: return self._cache["PsiT"]
        v = self._integrate("psi_tilde"); self._cache["PsiT"] = v; return v

    # ──────────── indices ────────────
    def witness_index(self) -> float:
        """WI = Ψ̂/Ψ (Def 6.8)."""
        p = self.psi()
        return (self.psi_hat() / p) if p > 1e-12 else 0.0

    def empathy_index(self) -> float:
        """EI = Ψ̃/Ψ̂ (Def 11.2)."""
        ph = self.psi_hat()
        return (self.psi_tilde() / ph) if ph > 1e-12 else 0.0

    def mcap(self) -> bool:
        """Thm 9.3."""
        pt = self.psi_tilde()
        nonzero = any(self.phi[m] * abs(self.w_funcs[ell](0)) > 1e-12
                      for m in range(self.M + 1) for ell in range(self.L))
        return (pt > 1e-12) and nonzero

    def beta_star_upper(self) -> float:
        """Thm 9.10: β* ≤ 1 + (log₂(M+1)/(M+1)) · max(1 − Δ/(ln2·log₂(M+1)), 0)."""
        M = self.M
        if M <= 0: return 1.0
        g = math.log2(M + 1)
        if g <= 0: return 1.0
        pen = self.delta / (math.log(2) * g)
        return 1.0 + (g / (M + 1)) * max(1.0 - pen, 0.0)

    def bounds(self) -> dict:
        """Thm 5.7 / 6.7 / 9.1 upper bounds."""
        D, J, L = self.D, self.J, self.L
        M, w, k, H, lam, d = (self.M, self.w_max, self.kstar,
                              self.H_est if self.H_est > 0 else 1.0,
                              max(1e-6, self.lam), self.delta)
        b57 = D * J * k * H * H / (12.0 * lam)
        b67 = D * J * L * w * w * k * H * H / (12.0 * lam)
        b91 = D * J * (M + 1) * L * w * w * ((k ** 0.5 + d) ** 2) * H * H / (12.0 * lam)
        return {"Thm5.7_Psi_ub": b57, "Thm6.7_PsiH_ub": b67, "Thm9.1_PsiT_ub": b91}

    # ──────────── Compassion decomposition (Def 10.5 / Thm 10.6) ────────────
    def components(self) -> List[float]:
        T = max(1, len(self._mem_buf))
        comps: List[float] = [0.0] * (self.M + 1)
        for t1 in range(T):
            partial = [0.0] * (self.M + 1)
            for m in range(self.M + 1):
                acc_m = 0.0
                for i in range(self.D):
                    for j in range(self.J):
                        for ell in range(self.L):
                            s = 0.0
                            for k in range(t1 + 1):
                                v = self._T5_entry(i, j, k, ell, m)
                                s += v * v
                            acc_m += s
                partial[m] = acc_m
            for t2 in range(t1, T):
                for t3 in range(t2, T):
                    phi_val = self._Phi(t1, t2, t3)
                    for m in range(self.M + 1):
                        comps[m] += partial[m] * phi_val
        return [c / (T ** 5) for c in comps]

    # ──────────── regime (§10.1 / 10.2 / 9.4) ────────────
    def regime(self) -> str:
        if self._n_observations < 3:
            return "empty"
        if self.phi and self.phi[0] > 0.9:
            return "narcissism"                         # Cor 10.2
        if all(p.distortion == 0.0 for p in self.P):
            return "solipsism"                          # Thm 10.1
        active_diff = False
        for m in range(len(self.P)):
            for m2 in range(m + 1, len(self.P)):
                if (self.P[m].description != self.P[m2].description
                        and self.phi[m] * self.phi[m2] > 0):
                    active_diff = True; break
            if active_diff: break
        return "intersubjective" if active_diff else "solipsism"

    # ──────────── §13 singularity API ────────────
    def apply_blowup(self, m_idx: int, n: int) -> None:
        if 0 <= m_idx < len(self.P):
            self.P[m_idx] = Sing(self.P[m_idx], int(n))
            self._cache_valid = False

    def apply_retrieval(self, m_idx: int, mu: float) -> float:
        if not (0 <= m_idx < len(self.P)):
            return 0.0
        old = self.P[m_idx]
        self.P[m_idx] = Ret(old, mu)
        self._cache_valid = False
        return max(0.0, old.distortion - float(mu))

    def singularity_trajectory(self, m_idx: int = 1,
                               depths: Sequence[int] = (1, 2, 4, 8, 16, 32, 64),
                               mu: float = 0.5) -> List[dict]:
        """Thm 13.7: EI^post ≤ EI^pre + ε(μ). 對應 Listing D.1 singularity_trajectory."""
        if not (0 <= m_idx < len(self.P)):
            return []
        P_base = self.P[m_idx]
        pre_EI = self.empathy_index()
        results = []
        for n in depths:
            self.P[m_idx] = Sing(P_base, int(n))
            self._cache_valid = False
            peak_EI = self.empathy_index()
            self.P[m_idx] = Ret(self.P[m_idx], float(mu))
            self._cache_valid = False
            post_EI = self.empathy_index()
            results.append({"n": int(n),
                             "EI_pre":  pre_EI,
                             "EI_peak": peak_EI,
                             "EI_post": post_EI,
                             "gap":     peak_EI - post_EI})
            self.P[m_idx] = P_base
            self._cache_valid = False
        return results

    def predictor_fit(self, m_idx: int = 1,
                      depths: Sequence[int] = (1, 2, 4, 8, 16, 32, 64, 128)) -> dict:
        """Thm 13.10: 擬合 P_Θ(n) = a·n + b·log₂(1+n) + c."""
        if not (0 <= m_idx < len(self.P)) or len(self._mem_buf) == 0:
            return {}
        P_base = self.P[m_idx]
        ks = []
        mem_row = list(self._mem_buf)[-1]
        env_row = list(self._env_buf)[-1]
        for n in depths:
            S = Sing(P_base, int(n))
            cond = bytes(env_row[0]) + bytes(S.description)
            ks.append(float(_K_cond(mem_row[0], cond)))
        if _HAS_NP:
            A = _np.array([[float(n), math.log2(1 + n), 1.0] for n in depths])
            y = _np.array(ks)
            try:
                theta, *_ = _np.linalg.lstsq(A, y, rcond=None)
                a, b, c = [float(x) for x in theta]
            except Exception:
                a = b = c = 0.0
        else:
            n_vec = [float(n) for n in depths]
            l_vec = [math.log2(1 + n) for n in depths]
            one   = [1.0] * len(depths)
            # 3x3 normal equations
            def dot(u, v): return sum(x*y for x,y in zip(u,v))
            mat = [[dot(n_vec,n_vec), dot(n_vec,l_vec), dot(n_vec,one)],
                   [dot(l_vec,n_vec), dot(l_vec,l_vec), dot(l_vec,one)],
                   [dot(one,n_vec),   dot(one,l_vec),   dot(one,one)]]
            rhs = [dot(n_vec,ks), dot(l_vec,ks), dot(one,ks)]
            # Gauss-Jordan
            def solve3(A, b):
                import copy
                A = [row[:] for row in A]; b = b[:]
                for i in range(3):
                    pv = A[i][i]
                    if abs(pv) < 1e-12: return (0.0,0.0,0.0)
                    for j in range(3): A[i][j] /= pv
                    b[i] /= pv
                    for r in range(3):
                        if r == i: continue
                        f = A[r][i]
                        for j in range(3): A[r][j] -= f * A[i][j]
                        b[r] -= f * b[i]
                return tuple(b)
            a, b, c = solve3(mat, rhs)
        resid = [abs(ks[i] - Pred(n, a, b, c)) for i, n in enumerate(depths)]
        return {"a": a, "b": b, "c": c,
                "max_residual": max(resid) if resid else 0.0,
                "mean_residual": sum(resid)/max(1,len(resid)),
                "K_samples": list(zip(depths, ks))}

    # ──────────── snapshot ────────────
    def snapshot(self) -> dict:
        self._cache_valid = False
        psi  = self.psi()
        psih = self.psi_hat()
        psit = self.psi_tilde()
        self._cache_valid = True

        wi = (psih / psi)  if psi  > 1e-12 else 0.0
        ei = (psit / psih) if psih > 1e-12 else 0.0

        mcap_ok = (psit > 1e-12) and any(self.phi[m] > 1e-12 for m in range(self.M + 1))
        bd = self.bounds()
        comps = self.components()
        comp_sum = sum(comps)
        beta_ub = self.beta_star_upper()
        regime = self.regime()

        s = {
            # ── 三個 scalar functional ──
            "Psi":     psi,                    # Def 5.4
            "PsiHat":  psih,                   # Def 6.5
            "PsiTilde": psit,                  # Def 7.11
            # brain.py 相容別名
            "PsiT":    psit,
            "PsiH":    psih,
            # ── 指標 ──
            "WI":      wi,                     # Def 6.8
            "EI":      ei,                     # Def 11.2
            "alpha*_gt": (wi > 1.0),           # Thm 6.9
            "beta*":   beta_ub,                # Thm 9.10
            "beta*_ub": beta_ub,
            "beta*_gt": (ei >= beta_ub),
            # ── axioms / regime ──
            "MCAP":    mcap_ok,                # Thm 9.3
            "regime":  regime,                 # §10.1 / 10.2 / 9.4
            "components": comps,               # Def 10.5 / Thm 10.6(b)
            "_comp_sum": comp_sum,
            "Thm10.6(b)_verified": (abs(comp_sum - psit) / max(1e-9, abs(psit))) < 1e-3,
            # ── 狀態 ──
            "T":       len(self._mem_buf),
            "M+1":     self.M + 1,
            "L":       self.L,
            "D":       self.D,
            "J":       self.J,
            "lambda":  self.lam,
            "Delta_max": self.delta,
            "kappa":   self.kappa,
            "kappa*":  self.kstar,
            "H_est":   self.H_est,
            "phi":     list(self.phi),
            "perspectives": [{"name": p.name, "Δ": p.distortion,
                              "|d|": len(p.description)} for p in self.P],
            # ── bound verification (Thm 5.7 / 6.7 / 9.1) ──
            "bounds":  bd,
            "bounds_ok": {
                "Thm5.7":  psi  <= bd["Thm5.7_Psi_ub"]  * 1.05,
                "Thm6.7":  psih <= bd["Thm6.7_PsiH_ub"] * 1.05,
                "Thm9.1":  psit <= bd["Thm9.1_PsiT_ub"] * 1.05,
            },
        }
        self._last = s
        return s


# ═══════════════════════════════════════════════════════════════════════════
#  §14 toy example self-test (對應 Listing E.1 e1~e10)
# ═══════════════════════════════════════════════════════════════════════════
def _self_test():
    print("[intersubjective] 論文 §14 toy example self-test …")
    eng = IntersubjectiveEngine(window=16, n_models=3, layers=2,
                                 lam=0.5, delta_max=1.0)
    M_seq = [b"00000000", b"10000000", b"11000000", b"11100000", b"11110000"]
    E_seq = [b"0000"] * 5
    for rep, env in zip(M_seq, E_seq):
        eng.observe(rep, other_rep=rep[::-1], env=env)
    snap = eng.snapshot()
    print(f"  Ψ        = {snap['Psi']:.3f}     (target ≈ 6.00)")
    print(f"  Ψ̂        = {snap['PsiHat']:.3f}  (target ≈ 7.56)")
    print(f"  Ψ̃        = {snap['PsiTilde']:.3f} (target ≈ 12.4)")
    print(f"  WI       = {snap['WI']:.3f}      (target ≈ 1.26)")
    print(f"  EI       = {snap['EI']:.3f}      (target ≈ 1.64)")
    print(f"  β* ub    = {snap['beta*_ub']:.3f}")
    print(f"  regime   = {snap['regime']}")
    print(f"  MCAP     = {snap['MCAP']}")
    print(f"  Thm10.6b = {snap['Thm10.6(b)_verified']}")
    print(f"  bounds_ok= {snap['bounds_ok']}")
    traj = eng.singularity_trajectory(m_idx=1, depths=[1,2,4,8,16], mu=0.5)
    print("\n  [§13 singularity trajectory]")
    for r in traj:
        print(f"    n={r['n']:3d}  pre={r['EI_pre']:.3f}  "
              f"peak={r['EI_peak']:.3f}  post={r['EI_post']:.3f}  gap={r['gap']:+.3f}")
    pf = eng.predictor_fit(m_idx=1, depths=[1,2,4,8,16,32,64])
    print(f"\n  [§13.10 predictor] a={pf.get('a',0):.3f}  "
          f"b={pf.get('b',0):.3f}  c={pf.get('c',0):.3f}  "
          f"max_resid={pf.get('max_residual',0):.3f}")
    print("[intersubjective] self-test done.\n")
    return snap


if __name__ == "__main__":
    _self_test()
