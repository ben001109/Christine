"""
column.py — 皮質微柱 (Mountcastle 1978 / Hawkins HTM)
====================================================

一個 column = 6 層 × N_per_layer 個 LIF，層間依已知解剖學連接：

  L4  ← thalamus (feedforward input)
  L4  → L2/3
  L2/3 → L2/3 of next column (horizontal)
  L2/3 → L5 (output to sub-cortical / other areas)
  L5  → L6  → thalamus (corticothalamic feedback)
  L6  → L4  (gain control)

抑制性中間神經元 (L2/3 PV+SST) 另外一池，比例 ~20%（Markram 2004）。

沒做完所有解剖細節——只抓「影響計算的骨架」。
"""
from __future__ import annotations
from .neuron import LIFPopulation
from .synapse import STDPMatrix

try:
    import numpy as _np
    _HAS_NP = True
except Exception:
    _HAS_NP = False


class CorticalColumn:
    LAYERS = ("L23", "L4", "L5", "L6")

    def __init__(self, n_per_layer=64, inh_ratio=0.2, seed=0):
        self.n = n_per_layer
        self.seed = seed
        self.pops = {}
        self.inh_pops = {}
        for i, layer in enumerate(self.LAYERS):
            n_exc = int(n_per_layer * (1 - inh_ratio))
            n_inh = n_per_layer - n_exc
            self.pops[layer]     = LIFPopulation(n_exc, seed=seed*10 + i)
            self.inh_pops[layer] = LIFPopulation(n_inh, tau=10.0, seed=seed*10 + i + 100)

        # 層間連線（用 STDP matrix）
        self.syn = {}
        def mk(src, dst, sparsity=0.15):
            self.syn[(src,dst)] = STDPMatrix(
                self.pops[src].N, self.pops[dst].N,
                sparsity=sparsity, seed=seed + hash((src,dst)) & 0xFFFF,
            )
        mk("L4",  "L23", 0.20)
        mk("L23", "L5",  0.15)
        mk("L5",  "L6",  0.10)
        mk("L6",  "L4",  0.08)
        mk("L23", "L23", 0.05)   # recurrent

        # 抑制反饋（L2/3 inh → L2/3 exc）
        self.inh_syn = STDPMatrix(
            self.inh_pops["L23"].N, self.pops["L23"].N,
            sparsity=0.3, w_init=-0.4, A_plus=0.0, A_minus=0.0,
            seed=seed + 999,
        )

        self._last = {layer: ([False]*p.N if not _HAS_NP
                               else _np.zeros(p.N, dtype=bool))
                       for layer,p in self.pops.items()}

    # ── forward 一個時間片（dt 毫秒） ──
    def step(self, input_current_L4, dt=0.5, feedback=None):
        """input_current_L4: len=n_exc(L4)；feedback: optional len=n_exc(L6)"""
        feedback = feedback or ([0.0]*self.pops["L6"].N if not _HAS_NP
                                 else _np.zeros(self.pops["L6"].N, _np.float32))

        # 1. 匯集輸入
        I = {layer: self._zero(self.pops[layer].N) for layer in self.LAYERS}
        I["L4"] = self._add(I["L4"], input_current_L4)

        # 2. 層間投射（用上一步的 spikes）
        for (src,dst), syn in self.syn.items():
            post = syn.project(self._last[src])
            I[dst] = self._add(I[dst], post)

        # 3. inhibition on L2/3
        inh_post = self.inh_syn.project(
            self._last.get("_inh_L23", [False]*self.inh_pops["L23"].N))
        I["L23"] = self._add(I["L23"], inh_post)

        # 4. step 所有 pops
        spikes = {}
        for layer,p in self.pops.items():
            spikes[layer] = p.step(I[layer], dt=dt)

        # 5. 抑制池也跑（輸入 = L2/3 exc）
        inh_in = self._excitatory_to_inh("L23", spikes["L23"])
        inh_spikes = self.inh_pops["L23"].step(inh_in, dt=dt)
        self._last["_inh_L23"] = inh_spikes

        # 6. STDP 更新
        for (src,dst), syn in self.syn.items():
            syn.step(self._last[src], spikes[dst], dt=dt)
        self.inh_syn.step(self._last["_inh_L23"], spikes["L23"], dt=dt)

        self._last = {**self._last, **spikes}

        # 7. 輸出：L5 是皮質投射出去的軸突
        return spikes["L5"], spikes  # (output, all_layers)

    def get_output_rate(self):
        """最近一步 L5 的 firing rate 當 'column activation'。"""
        out = self._last.get("L5")
        if out is None: return 0.0
        if _HAS_NP and hasattr(out, "mean"):
            return float(out.mean())
        return sum(1 for s in out if s) / max(1, len(out))

    # helpers
    def _zero(self, n):
        return _np.zeros(n, _np.float32) if _HAS_NP else [0.0]*n
    def _add(self, a, b):
        if _HAS_NP: return a + _np.asarray(b, _np.float32)
        return [a[i]+b[i] for i in range(len(a))]
    def _excitatory_to_inh(self, layer, spikes):
        # 非常簡化：exc spike 直接當驅動
        if _HAS_NP:
            s = _np.asarray(spikes, _np.float32)
            # random fixed projection
            n_inh = self.inh_pops[layer].N
            n_exc = len(s)
            # 均勻映射
            k = max(1, n_exc // n_inh)
            out = _np.zeros(n_inh, _np.float32)
            for i in range(n_inh):
                out[i] = s[i*k:(i+1)*k].sum() * 3.0
            return out
        n_inh = self.inh_pops[layer].N
        n_exc = len(spikes); k = max(1, n_exc // n_inh)
        return [sum(spikes[i*k:(i+1)*k])*3.0 for i in range(n_inh)]
