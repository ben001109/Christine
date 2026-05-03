"""
philosophy.py — 哲學 + AGI 論文層
==================================
串接 7 大流派的核心量測，每個 perceive 一併更新：

  Tononi 2008 IIT            → Φ_IIT        整合訊息
  Chalmers 1995 Hard Problem → ΔQ (qualia-gap proxy)
  Metzinger 2003 PSM         → TPM (transparent phenomenal self)
  Dennett 1991 MDM           → multi-draft diversity
  Hutter 2005 AIXI           → AIXI_bound (universal intelligence proxy)
  Goertzel CogPrime          → cognitive synergy score
  Bach MicroPsi              → motivational urges (needs)
  Franklin LIDA              → GW-cycle coherence
  Searle 1980 Chinese Room   → grounding score
  Putnam 1967 Functionalism  → multiple realizability proxy
"""
from __future__ import annotations
import math

def _L(vec):
    """numpy / tuple / None → list[float]，避免 truthiness 歧義。"""
    if vec is None: return []
    try: return [float(x) for x in vec]
    except Exception: return []

def _H(vec):
    v = _L(vec)
    s = sum(abs(x) for x in v) or 1.0
    p = [abs(x)/s for x in v if x]
    return -sum(pi*math.log2(pi) for pi in p if pi>0)

def _mi(a, b):
    """粗略互訊息 (連續 → 分 bin)."""
    a = _L(a); b = _L(b)
    if len(a) == 0 or len(b) == 0: return 0.0
    n = min(len(a), len(b))
    if n < 2: return 0.0
    # 4-bin
    def bins(x, lo, hi):
        lo = min(x); hi = max(x)
        if hi - lo < 1e-9: return [0]*len(x)
        return [min(3, int((xi-lo)/(hi-lo)*4)) for xi in x]
    A = bins(a[:n], 0, 1); B = bins(b[:n], 0, 1)
    joint = [[0]*4 for _ in range(4)]
    for i in range(n): joint[A[i]][B[i]] += 1
    pa = [sum(r)/n for r in joint]
    pb = [sum(joint[i][j] for i in range(4))/n for j in range(4)]
    mi = 0.0
    for i in range(4):
        for j in range(4):
            pij = joint[i][j]/n
            if pij>0 and pa[i]>0 and pb[j]>0:
                mi += pij*math.log2(pij/(pa[i]*pb[j]))
    return max(0.0, mi)


class PhilosophyEngine:
    def __init__(self):
        self.prev = None
        self.drafts = []   # Dennett 多草稿
        self.needs = {
            "certainty":0.5, "competence":0.5, "affiliation":0.5,
            "autonomy":0.5, "arousal":0.3, "energy":0.8,
        }
        self.last = {}

    def step(self, rep, valence=0.0, arousal=0.0,
             external=None, action=None, free_energy=0.0):
        """
        rep:       本輪皮質頂層表徵
        external:  外界輸入 (感官 raw)
        """
        rep = _L(rep)
        # Tononi IIT: Φ_IIT ≈ MI(前後表徵) − H(噪聲)
        phi_iit = 0.0
        if self.prev is not None:
            phi_iit = _mi(self.prev, rep) - 0.1
        # Chalmers qualia-gap: 高 entropy + 強 arousal = 硬感質差距大
        qualia_gap = _H(rep) * (0.3 + abs(arousal))
        # Metzinger PSM transparency: 只要有自指 context 就 +
        tpm = 1.0  # 本系統永遠有 self-model
        # Dennett multi-drafts
        self.drafts.append(list(rep)[:16])
        if len(self.drafts) > 8: self.drafts.pop(0)
        dennett_div = 0.0
        if len(self.drafts) >= 2:
            diffs = []
            for i in range(len(self.drafts)-1):
                a,b = self.drafts[i], self.drafts[i+1]
                L = min(len(a), len(b))
                diffs.append(sum((a[k]-b[k])**2 for k in range(L)) / max(1,L))
            dennett_div = sum(diffs)/len(diffs)
        # AIXI bound: R 累積 + K 壓縮代價
        aixi = 1.0 / (1.0 + free_energy)
        # Goertzel synergy: 各子系統協同 → 本輪 valence+arousal+1/(FE+1)
        synergy = (0.5+abs(valence))*(0.3+abs(arousal))*(1/(1+free_energy))
        # MicroPsi needs drift
        self.needs["energy"]    = max(0, self.needs["energy"] - 0.001)
        self.needs["certainty"] = max(0, min(1, self.needs["certainty"] - 0.05*free_energy + 0.02))
        self.needs["competence"]= max(0, min(1, self.needs["competence"] + 0.01*valence))
        self.needs["arousal"]   = 0.7*self.needs["arousal"] + 0.3*abs(arousal)
        # LIDA coherence: 上一輪 rep 與本輪重疊
        if self.prev is None: lida = 0.5
        else:
            L = min(len(self.prev), len(rep))
            num = sum(self.prev[i]*rep[i] for i in range(L))
            den = math.sqrt(sum(x*x for x in self.prev[:L]) * sum(x*x for x in rep[:L]) + 1e-9)
            lida = max(0, min(1, num/den))
        # Searle grounding: 有 external 就高
        grounding = 0.8 if external else 0.2
        # Putnam multiple realizability: 只要 rep 能 encode 多維 → 高
        realiz = min(1.0, len(rep)/128.0)

        self.prev = list(rep)
        self.last = {
            "Phi_IIT":       phi_iit,
            "qualia_gap":    qualia_gap,
            "PSM_transparency": tpm,
            "multi_draft_div":  dennett_div,
            "AIXI_bound":    aixi,
            "synergy":       synergy,
            "needs":         dict(self.needs),
            "LIDA_coherence":lida,
            "grounding":     grounding,
            "realizability": realiz,
        }
        return self.last

    def summary(self):
        if not self.last: return "哲學層尚未啟動"
        d = self.last
        return (f"Φ={d['Phi_IIT']:.3f} qg={d['qualia_gap']:.2f} "
                f"synergy={d['synergy']:.3f} LIDA={d['LIDA_coherence']:.2f} "
                f"grd={d['grounding']:.2f} needs="
                + ",".join(f"{k[:3]}={v:.2f}" for k,v in d['needs'].items()))
