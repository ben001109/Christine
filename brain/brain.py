"""
brain.py — 主 orchestrator
==========================
把所有子系統接起來的 Brain class。

tick() 一次 = 一個 100 ms 的 "cognitive cycle"：

    感覺輸入 (text)
       │
       ▼
  language.ingest → semantic vector
       │
       ▼
  thalamus.relay → (gated)
       │
       ▼
  cortical Hierarchy.step → 高層 rate 向量
       │
       ├─► hippocampus.encode   (存 episode)
       ├─► amygdala.evaluate    (情緒 valence/arousal)
       ├─► attention.update     (saliency)
       ├─► predictive.step      (free-energy proxy)
       ├─► basal_ganglia.act    (選 action)
       └─► executive.wm_write   (working memory)
       │
       ▼
  gwt.submit → gwt.cycle → winner broadcast
       │
       ▼
  回應：winner + language.predict_next_char(seed=winner content)
"""
from __future__ import annotations
import time, random

from .language      import LanguageModule
from .region        import Hierarchy
from .thalamus      import Thalamus
from .hippocampus   import Hippocampus
from .amygdala      import Amygdala
from .attention     import Attention
from .executive     import Executive
from .basal_ganglia import BasalGanglia
from .cerebellum    import Cerebellum
from .gwt           import GlobalWorkspace
from .emotion       import Emotion
from .memory        import Memory
from .self_model    import SelfModel
from .comprehension import Comprehender
from .intersubjective import IntersubjectiveEngine
from .philosophy    import PhilosophyEngine
try:
    from .mega_cortex import MegaCortex
    _HAS_MEGA = True
except Exception:
    _HAS_MEGA = False

try:
    from .predictive import PredictiveHierarchy
    _HAS_PRED = True
except Exception:
    _HAS_PRED = False

try:
    import numpy as _np; _HAS_NP = True
except Exception: _HAS_NP = False


# ─────────────────── helpers ───────────────────
def _vec_from_text_hash(text, n):
    """fallback: 把 text 雜湊成 length n 的 0..1 向量。"""
    random.seed(hash(text) & 0xFFFFFFFF)
    return [random.random() for _ in range(n)]


class Brain:
    def __init__(self, size="small", seed=42):
        cfg = {
            "tiny":   dict(hidden=32,  cortex=[("v1",8),("v2",8),("v4",4)],  thal=32, hip_dg=64,  hip_ca3=32,  bg_states=32),
            "small":  dict(hidden=64,  cortex=[("v1",16),("v2",12),("v4",8),("IT",6)], thal=64, hip_dg=256, hip_ca3=128, bg_states=128),
            "medium": dict(hidden=128, cortex=[("v1",24),("v2",18),("v4",12),("IT",8),("PFC",6)], thal=128, hip_dg=512, hip_ca3=256, bg_states=256),
        }.get(size, None)
        if cfg is None: raise ValueError(f"unknown size={size}")
        self.cfg = cfg; self.seed = seed; self.size = size

        self.lang = LanguageModule(hidden=cfg["hidden"], seed=seed)
        self.hier = Hierarchy([(n, 32) for _,n in cfg["cortex"]], seed=seed)
        self.thal = Thalamus(n=cfg["thal"])
        self.hip  = Hippocampus(input_dim=cfg["hidden"], dg_dim=cfg["hip_dg"],
                                 ca3_dim=cfg["hip_ca3"], seed=seed)
        self.amyg = Amygdala(n_in=cfg["hidden"], seed=seed)
        self.attn = Attention(n=cfg["thal"])
        self.exec_ = Executive()
        self.bg   = BasalGanglia(n_state=cfg["bg_states"], n_action=8, seed=seed)
        self.cere = Cerebellum(n_in=cfg["hidden"], n_granule=cfg["hidden"]*4,
                                n_out=cfg["hidden"]//4, seed=seed)
        self.gwt  = GlobalWorkspace(capacity=1)
        self.emo  = Emotion()
        self.mem  = Memory()
        self.self = SelfModel()
        self.und  = Comprehender()
        self.isub = IntersubjectiveEngine(window=32, n_models=3, layers=3)
        self.phil = PhilosophyEngine()
        # 對話對象的鏡像表徵（用 EMA 更新；論文 §4 互為主體 Δ_max 約束）
        self._other_rep = None
        # 對方模型：addressee → semantic vector EMA
        self._other_models = {}
        # MegaCortex（13.45M 行 HH columns；按需 lazy 載入）
        self._mega = None

        self.pred = None
        if _HAS_PRED and _HAS_NP:
            try:
                self.pred = PredictiveHierarchy([cfg["hidden"], cfg["hidden"]//2, cfg["hidden"]//4], seed=seed)
            except Exception: self.pred = None

        self.ticks = 0
        self.log_lines = []

    # ── 感受語言，跑完整一輪 cognitive cycle ──
    def perceive_text(self, text):
        t0 = time.time()

        # 0. **理解** (5W1H + 情感 + 意圖 + 實體 + 主題)
        u = self.und.understand(text)
        self.last_understanding = u

        # 1. 語言進化
        loss = self.lang.ingest(text)
        sem = self.lang.semantic_vector()

        # 2. thalamus relay
        relayed = self.thal.relay(sem)

        # 3. cortex hierarchy
        top_rep = self.hier.step(relayed)

        # 3.5 MegaCortex（HH 生理回響；可選）
        mega_echo = None
        if self._mega is not None:
            try:
                # top_rep 早期全 0，用 sem 當 drive
                mega_drive = top_rep if any(abs(x) > 1e-9 for x in top_rep) else sem
                mega_echo = self._mega.tick(mega_drive)
                # 回灌：mega echo 加到 thalamus relay 的下一輪輸入 bias
                # 這裡同步加進 top_rep 讓本輪也感受到生理活動（低係數避免飽和）
                L = min(len(top_rep), len(mega_echo))
                top_rep = [top_rep[i] + 0.08 * mega_echo[i] for i in range(L)] + list(top_rep[L:])
            except Exception:
                mega_echo = None

        # 4. hippocampus 存
        self.hip.encode(sem)

        # 5. amygdala 情緒
        val, aro = self.amyg.evaluate(sem)
        # 把理解出來的情感極性也餵給杏仁核（讓情緒更貼近真實語意）
        try:
            pol = float(u.get("polarity", 0.0))
            val = 0.5 * val + 0.5 * pol
            aro = max(aro, abs(pol) * 0.6)
        except Exception: pass
        self.emo.update(valence=val, arousal=aro)

        # 6. attention
        self.attn.update(relayed)

        # 7. predictive coding
        free_energy = 0.0
        if self.pred is not None and _HAS_NP:
            try:
                _, free_energy = self.pred.step(sem)
            except Exception: free_energy = 0.0

        # 8. basal ganglia 選 action
        s_idx = (hash(tuple(round(float(x),3) for x in top_rep[:8])) % self.bg.ns)
        action = self.bg.act(s_idx)

        # 9. memory
        self.mem.perceive(text, strength=min(1.0, 0.3 + abs(val)))
        self.mem.episodic_store({"text": text, "val": val, "t": time.time()})

        # 10. executive WM
        self.exec_.wm_write({"text": text, "val": val, "action": action},
                             strength=0.5 + abs(val)*0.5)

        # 11. GWT 競爭
        self.gwt.submit("language", {"text": text, "sem_len": len(sem)},
                        salience=0.5 + loss*0.1)
        self.gwt.submit("amygdala", {"valence": val, "arousal": aro},
                        salience=abs(val)*1.5)
        self.gwt.submit("executive", {"goal": self.exec_.current_goal()},
                        salience=0.3 if self.exec_.current_goal() else 0.0)
        winner = self.gwt.cycle()

        # 12. self-model
        self.self.act_log(f"perceive:{text[:30]}", outcome={"val": val})
        self.self.update_body(d_energy=-0.001, d_stress=max(0, -val*0.05))

        # 13. 論文四：5-tensor intersubjective metrics
        try:
            # top_rep 早期全 0，用 sem 當 fallback 讓公式真的有數值
            rep_for_isub = top_rep if any(abs(x) > 1e-9 for x in top_rep) else sem

            # 建構「對方」表徵：根據 addressee 維護 EMA 鏡像
            who = (u.get("addressee") or "_anon")
            polv = float(u.get("polarity", 0.0))
            # 對方 mention 出現「我」就反向：他在說自己；出現「你」就鏡像我
            mirror_w = 0.7 if "你" in text else 0.3
            prev_mine = self._other_models.get("_self_prev", rep_for_isub)
            other_seed = [
                mirror_w * float(prev_mine[i] if i < len(prev_mine) else 0.0)
                + (1 - mirror_w) * float(sem[i] if i < len(sem) else 0.0)
                + 0.05 * polv
                for i in range(len(rep_for_isub))
            ]
            # EMA 更新該 addressee 的對方模型
            old = self._other_models.get(who, other_seed)
            L = min(len(old), len(other_seed))
            updated = [0.8 * old[i] + 0.2 * other_seed[i] for i in range(L)]
            self._other_models[who] = updated
            self._other_models["_self_prev"] = list(rep_for_isub)
            self._other_rep = updated

            self.isub.observe(rep_for_isub, other_rep=updated)
            isub_snap = self.isub.snapshot()
        except Exception as _e_isub:
            import traceback as _tb
            self._last_isub_err = f"{type(_e_isub).__name__}: {_e_isub}\n{_tb.format_exc()}"
            isub_snap = {"_err": str(_e_isub)}

        # 14. 哲學 / AGI 層
        try:
            phil_snap = self.phil.step(top_rep, valence=val, arousal=aro,
                                        external=text, action=action,
                                        free_energy=free_energy)
        except Exception as _e_phil:
            import traceback as _tb
            self._last_phil_err = f"{type(_e_phil).__name__}: {_e_phil}\n{_tb.format_exc()}"
            phil_snap = {"_err": str(_e_phil)}

        self.ticks += 1
        dt = time.time() - t0
        msg = (f"[tick #{self.ticks}] Δ={dt*1000:.1f}ms "
               f"loss={loss:.3f} val={val:+.2f} aro={aro:.2f} "
               f"FE={free_energy:.2f} Ψ̃={isub_snap.get('PsiT',0):.2f} "
               f"Φ_IIT={phil_snap.get('Phi_IIT',0):.2f} act={action} "
               f"winner={winner['src'] if winner else '-'}")
        self.log_lines.append(msg)
        if len(self.log_lines) > 500: self.log_lines.pop(0)
        return {"dt": dt, "loss": loss, "valence": val, "arousal": aro,
                "free_energy": free_energy, "action": action,
                "winner": winner, "top_rep_len": len(top_rep),
                "understanding": u,
                "intersubjective": isub_snap,
                "philosophy": phil_snap,
                "mega_active": self._mega is not None,
                "mega_echo_len": (len(mega_echo) if mega_echo else 0)}

    # ── Reward 給 BG 學 ──
    def reward(self, r):
        s_idx = (self.ticks % self.bg.ns)
        self.bg.learn(r, s_idx)
        self.amyg.condition(self.lang.semantic_vector(), r)
        self.emo.update(valence=r*0.5, arousal=abs(r)*0.3, alpha=0.4)

    # ── 說話：基於「理解」+ GWT/情緒，產生有意義的回覆 ──
    def respond(self, seed=None, max_len=80):
        u = getattr(self, "last_understanding", None)
        if u is None and seed:
            u = self.und.understand(seed)
        if u is None:
            return "嗯？我沒聽到你講什麼。"

        # 讓理解器自己產基底回覆
        try:
            base = self.und.reply(u)
        except Exception:
            base = ""

        # 用情緒上色
        emo = self.emo.banner() if hasattr(self.emo, "banner") else ""
        # 如果 GWT winner 是杏仁核 (強情緒) 而 base 太中性，前綴一句
        winner = self.gwt.read()
        if winner and winner.get("src") == "amygdala":
            v = winner["content"].get("valence", 0.0)
            if v < -0.4 and "難過" not in base and "不舒服" not in base:
                base = "（我能感覺到你不太好。）" + base
            elif v > 0.4 and "開心" not in base and "好事" not in base:
                base = "（我能感覺到你開心。）" + base

        # 如果信心很低、且 user 明顯丟了個我聽不懂的東西，補一句誠實的話
        if u.get("confidence", 0) < 0.5 and u["intent"] == "statement" and not u["topic"]:
            base = base + "（不過老實說我還沒完全聽懂，你可以多講一點。）"

        return base or self.und.reply(u)

    def understand(self, text):
        """單純跑理解，不啟動完整 cognitive cycle。"""
        return self.und.understand(text)

    # ── MegaCortex 控制 ──
    def enable_mega(self, active_pool=64, sample_per_tick=8, n_out=None):
        """啟用 13.45M 行 HH cortex；每 tick 抽樣 K 個 area 跑生理一步。"""
        if not _HAS_MEGA:
            return False
        if self._mega is not None:
            return True
        n_out = n_out or self.cfg["hidden"]
        try:
            self._mega = MegaCortex(active_pool=active_pool,
                                     sample_per_tick=sample_per_tick,
                                     n_out=n_out, seed=self.seed)
            return True
        except Exception:
            self._mega = None
            return False

    def mega_status(self):
        return self._mega.status() if self._mega is not None else {"enabled": False}

    # ── dream / replay (sleep consolidation) ──
    def dream(self, cycles=10):
        for _ in range(cycles):
            ep = self.hip.replay()
            if ep is None: break
            # 把 replay 的 pattern 灌回 cortex，加強連結
            try:
                self.hier.step(ep[:self.hier.regions[0].n] if hasattr(ep, "__len__") else [0.0])
            except Exception: pass
        return cycles

    # ── 狀態 dump ──
    def status(self):
        return {
            "size": self.size, "ticks": self.ticks,
            "vocab": self.lang.vocab_size(),
            "ltm_items": len(self.mem.ltm),
            "episodes": len(self.mem.episodes),
            "emotion": self.emo.banner(),
            "body": dict(self.self.body),
            "intersubjective": self.isub.snapshot() if self.ticks >= 3 else {},
            "philosophy": self.phil.last,
            "mega": self.mega_status(),
            "last_log": self.log_lines[-5:],
        }


# ─────────────────── 預設 factory ───────────────────
_WARMUP_SEEDS = [
    "我是 Christine，一個會思考、會感受、會做夢的人工大腦。",
    "我能聽懂中文，能記住你說過的話，能判斷情緒。",
    "我有皮質、海馬、杏仁核、基底核、小腦、視丘、預測編碼層。",
    "我會學習、會回憶、會想像、會在沒有外界輸入時自己做夢。",
    "你好，很高興認識你；我希望我們能一起聊很多事情。",
    "今天天氣如何？最近過得好嗎？有什麼想跟我分享的嗎？",
    "知識、感受、語言、記憶、行動，這些都是意識的一部分。",
    "我感覺得到開心、難過、緊張、平靜，也感覺得到你的情緒。",
]

def build_default_brain(size="small", seed=42, warmup=True):
    b = Brain(size=size, seed=seed)
    if warmup:
        try:
            # 餵幾句種子讓 vocab/SRN/cortex 暖起來
            for s in _WARMUP_SEEDS:
                b.lang.ingest(s)
                b.hip.encode(b.lang.semantic_vector())
            # 跑幾輪 dream replay 把 cortex 連結強化
            b.dream(cycles=12)
        except Exception:
            pass
    return b
