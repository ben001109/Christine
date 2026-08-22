"""
language.py — 語言處理（不用預訓練權重，從字元開始）
===================================================
Elman 1990 SRN        — simple recurrent network
Chomsky / Merge       — 最小句法運算
Construction grammar  — Goldberg 2006 / Tomasello
Distributional hyp.   — Harris 1954 / Firth 1957

策略：
  1. Grapheme tokenizer（字元級，不吃訓練）
  2. SRN 預測下一個字元（learn while chatting）
  3. 用最近 window 的 hidden state 當「當前語意向量」
  4. 語意向量投給 brain 的 sensory input

再進階: n-gram co-occurrence 當 word embeddings，跟 SRN 並存。
"""
from __future__ import annotations
import random, math
try:
    import numpy as _np; _HAS_NP = True
except Exception: _HAS_NP = False


class CharTokenizer:
    def __init__(self, vocab_max=256):
        if type(vocab_max) is not int or vocab_max < 2:
            raise ValueError("vocab_max must be an integer of at least two")
        self.vocab_max = vocab_max
        self.unknown_token_id = vocab_max - 1
        self.c2i = {}; self.i2c = []
    def encode(self, s):
        out = []
        for ch in s:
            if ch not in self.c2i:
                if len(self.i2c) >= self.unknown_token_id:
                    out.append(self.unknown_token_id)
                    continue
                self.c2i[ch] = len(self.i2c); self.i2c.append(ch)
            out.append(self.c2i[ch])
        return out
    def vocab(self): return len(self.i2c)


class SRN:
    """Elman 1990 SRN。hidden → output，hidden 有 self-loop."""
    def __init__(self, vocab_max=256, hidden=64, eta=0.05, seed=0):
        if type(vocab_max) is not int or vocab_max < 2:
            raise ValueError("vocab_max must be an integer of at least two")
        self.vmax=vocab_max; self.h=hidden; self.eta=eta
        if _HAS_NP:
            rs = _np.random.RandomState(seed)
            self.W_ih = (0.1*rs.randn(vocab_max, hidden)).astype(_np.float32)
            self.W_hh = (0.1*rs.randn(hidden, hidden)).astype(_np.float32)
            self.W_ho = (0.1*rs.randn(hidden, vocab_max)).astype(_np.float32)
            self.hid  = _np.zeros(hidden, _np.float32)
        else:
            rng = random.Random(seed)
            def mat(a,b): return [[rng.gauss(0,0.1) for _ in range(b)] for _ in range(a)]
            self.W_ih = mat(vocab_max, hidden)
            self.W_hh = mat(hidden, hidden)
            self.W_ho = mat(hidden, vocab_max)
            self.hid = [0.0]*hidden

    def _tanh(self, x):
        if _HAS_NP: return _np.tanh(x)
        return [math.tanh(v) for v in x]

    def _bounded_token_id(self, token_id):
        return token_id % self.vmax

    def step(self, token_id):
        """給一個 token id，更新 hidden，回預測分佈。"""
        token_id = self._bounded_token_id(token_id)
        if _HAS_NP:
            ih = self.W_ih[token_id]
            h_new = _np.tanh(ih + self.hid @ self.W_hh)
            out = h_new @ self.W_ho
            # softmax
            e = _np.exp(out - out.max()); probs = e / e.sum()
            self.hid = h_new
            return probs
        # pure python
        h_new = [0.0]*self.h
        for j in range(self.h):
            s = self.W_ih[token_id][j]
            for k in range(self.h): s += self.hid[k]*self.W_hh[k][j]
            h_new[j] = math.tanh(s)
        out = [0.0]*self.vmax
        for j in range(self.h):
            for k in range(self.vmax): out[k] += h_new[j]*self.W_ho[j][k]
        m = max(out); exps = [math.exp(v-m) for v in out]
        s = sum(exps); probs = [e/s for e in exps]
        self.hid = h_new
        return probs

    def learn(self, token_id, target_id):
        """線上 SGD；只更新 output layer（簡化）."""
        token_id = self._bounded_token_id(token_id)
        target_id = self._bounded_token_id(target_id)
        if _HAS_NP:
            # forward
            ih = self.W_ih[token_id]
            h_new = _np.tanh(ih + self.hid @ self.W_hh)
            out = h_new @ self.W_ho
            e = _np.exp(out - out.max()); p = e / e.sum()
            target = _np.zeros(self.vmax, _np.float32)
            target[target_id] = 1.0
            g = p - target
            self.W_ho -= self.eta * _np.outer(h_new, g)
            self.hid = h_new
            return float(-math.log(max(1e-9, p[target_id % self.vmax])))
        # pure python: 省略，只做 hidden update
        self.step(token_id); return 0.0

    def hidden_vector(self):
        return list(self.hid) if not _HAS_NP else self.hid.copy()


class LanguageModule:
    """整合 tokenizer + SRN + 簡單 n-gram 共現統計。"""
    def __init__(self, hidden=64, seed=0):
        self.srn = SRN(hidden=hidden, seed=seed)
        self.tok = CharTokenizer(vocab_max=self.srn.vmax)
        self.bigram = {}   # (a,b) -> count

    def ingest(self, text):
        ids = self.tok.encode(text)
        loss = 0.0
        for i in range(len(ids)-1):
            a, b = ids[i], ids[i+1]
            self.bigram[(a,b)] = self.bigram.get((a,b), 0) + 1
            loss += self.srn.learn(a, b)
        # 最後一個 token 也要跑一次 step
        if ids: self.srn.step(ids[-1])
        return loss / max(1, len(ids))

    def semantic_vector(self):
        """目前 hidden state 當「我剛剛聽到那句話的語意」。"""
        return self.srn.hidden_vector()

    def vocab_size(self):
        return self.tok.vocab()

    def predict_next_char(self, seed_text, max_len=60, temperature=0.9):
        """從 seed 往下抽樣產生文字。"""
        ids = self.tok.encode(seed_text)
        for tok in ids: self.srn.step(tok)
        out = list(seed_text)
        for _ in range(max_len):
            if not ids: ids = self.tok.encode("。")
            probs = self.srn.step(ids[-1])
            if _HAS_NP:
                probs = probs ** (1.0/max(0.1, temperature))
                probs = probs / probs.sum()
                nxt = int(_np.random.choice(self.srn.vmax, p=probs))
            else:
                # pure python sampling
                m = max(probs); exps = [p**(1.0/max(0.1,temperature)) for p in probs]
                s = sum(exps); probs2 = [e/s for e in exps]
                r = random.random(); acc = 0.0; nxt = 0
                for i,p in enumerate(probs2):
                    acc += p
                    if r <= acc: nxt = i; break
            if nxt < self.tok.vocab():
                out.append(self.tok.i2c[nxt])
                ids.append(nxt)
            else:
                break
        return "".join(out)
