"""
comprehension.py — Christine 大腦的「中文理解」模組
======================================================
不靠任何預訓練模型，純 stdlib + 線上學習。

理解輸出 (dict)：
  {
    "raw":        原句,
    "norm":       正規化句,
    "tokens":     字元 / 詞 list,
    "intent":     greet | question | command | statement | emotion | thanks | farewell
                  | self_query | identity_query | capability_query | time_query
                  | meta(關於 christine 自己),
    "qword":      5W1H 中文關鍵詞 (誰/什麼/哪裡/何時/為什麼/怎麼/多少) 或 None,
    "polarity":   -1.0 .. +1.0   (情感極性，由內建 lexicon 計)
    "subjectivity": 0.0 .. 1.0,
    "entities":   { "person": [...], "place": [...], "number": [...], "time": [...] }
    "topic":      短主題詞或 None,
    "addressee":  "self" | "user" | "third"  ── 句子在對誰講
    "polite":     bool,
    "negation":   bool,
    "imperative": bool,
    "confidence": 0..1
  }

設計理念（論文錨）：
  - Speech Acts (Searle 1969)：intent 分類
  - Frame Semantics (Fillmore 1976)：5W1H 槽位
  - Sentiment Lexicon (Liu & Hu 2004)：polarity
  - NER by patterns (Bikel 1997)：entities
  - Centering theory (Grosz & Sidner 1986)：指代/上下文
"""
from __future__ import annotations
import re
from collections import Counter, deque

# ───────────────────────── lexicons (種子) ─────────────────────────
# 之後 Brain.update_lexicon() 可加詞

POS_WORDS = {
    "好","棒","讚","喜歡","愛","開心","高興","快樂","謝謝","感謝","厲害","美","強","行",
    "可以","對","沒問題","沒事","好的","ok","yes","yeah","yep","nice","cool","great",
    "happy","love","like","good","awesome","正","酷","爽","太棒",
}
NEG_WORDS = {
    "壞","爛","討厭","恨","難過","傷心","痛","煩","怒","生氣","氣","操","幹","靠",
    "不行","不要","別","沒","不能","不會","不好","不喜歡","不對","錯","失敗","累","死",
    "bad","hate","sad","angry","fail","no","nope","awful","terrible","sucks",
}
NEG_PARTICLES = {"不","沒","別","勿","莫","非","未","無"}
INTENSIFIERS = {"很","非常","超","極","特別","好","蠻","挺","真","太"}
POLITE_WORDS = {"請","麻煩","謝謝","謝","感謝","拜託","勞駕","可否","可以嗎","可以麻煩"}

GREET_RE = re.compile(
    r"^(?:嗨|哈囉|哈嘍|你好|您好|早安|午安|晚安|早上好|晚上好|大家好|hi|hello|hey|yo|早|嘿)[\s!！。.，,~]*",
    re.IGNORECASE,
)
THANKS_RE  = re.compile(r"(謝謝|感謝|thanks|thank you|thx|3q|多謝)", re.IGNORECASE)
FAREWELL_RE = re.compile(r"(再見|拜拜|掰掰|byebye|bye|see you|goodbye|晚安|睡了|溜了)", re.IGNORECASE)

QWORDS = {
    "who":  ["誰", "什麼人", "哪位"],
    "what": ["什麼", "甚麼", "啥", "what"],
    "where":["哪裡", "哪兒", "在哪", "何處", "where"],
    "when": ["何時", "什麼時候", "幾點", "幾號", "when"],
    "why":  ["為什麼", "為何", "怎麼會", "幹嘛", "why"],
    "how":  ["怎麼", "如何", "怎樣", "怎麼樣", "how"],
    "howmany":["多少", "幾個", "幾"],
}
Q_PARTICLES = {"嗎","呢","嘛","吧","啊","ㄚ","？","?","麼","么"}
IMP_HEADS = {"請","幫","給我","告訴我","讓","別","不要","stop","help","tell","show"}

ADDRESSEE_SELF_RE = re.compile(
    r"(你是|你叫|你能|你會|你知道|你覺得|你想|你的|你有|christine|克莉絲汀)",
    re.IGNORECASE,
)
SELF_REF = {"我","俺","咱","本人","i","me","my","mine"}
USER_REF = {"你","您","妳","you","your"}

# ─────────────── entity patterns ───────────────
NUM_RE  = re.compile(r"(?<!\w)(\d+(?:\.\d+)?)(?!\w)")
TIME_RE = re.compile(r"(\d{1,2}[:點]\d{0,2}|今天|昨天|明天|早上|中午|下午|晚上|半夜|凌晨|現在|剛剛|等一下|待會|稍後)")
# 中文人名 ad-hoc：常見姓 + 1~2 字
COMMON_SURNAMES = "王李張劉陳楊黃趙周吳徐孫朱馬胡郭何高林鄭何韓馮陶曹許鄧曾彭蕭蘇潘葉蔡余杜葉沈呂施盧侯邵孟夏熊范方石姚廖姜鄒熊金陸郝孔白崔康毛邱秦江史顧侯邵孟龍萬段雷錢湯尹易黎常武喬賀賴龔文"
PERSON_RE = re.compile(rf"([{COMMON_SURNAMES}][\u4e00-\u9fff]{{1,2}})")
ENG_NAME_RE = re.compile(r"\b([A-Z][a-z]{2,12})\b")
PLACE_HINTS = ["市","縣","區","路","街","國","省","村","鎮","台北","台中","台南","高雄","新北","桃園","美國","日本","中國","台灣"]
PLACE_RE = re.compile("(" + "|".join(PLACE_HINTS) + ")")


# ─────────────── tokenizer (中英混合，最大正向匹配 + 字元 fallback) ───────────────
class _ZhTokenizer:
    def __init__(self):
        self.lex = set()  # 學到的詞
        self.freq = Counter()
        # 種子詞典
        for s in (POS_WORDS|NEG_WORDS|POLITE_WORDS|INTENSIFIERS|SELF_REF|USER_REF):
            self.lex.add(s)
        for vs in QWORDS.values():
            for w in vs: self.lex.add(w)

    def add(self, w):
        if not w: return
        self.lex.add(w); self.freq[w] += 1

    def tokenize(self, s):
        s = s.strip()
        out = []
        i = 0; N = len(s)
        # 詞典最大長度
        maxlen = min(8, max((len(w) for w in self.lex), default=2))
        while i < N:
            ch = s[i]
            if ch.isspace():
                i += 1; continue
            # 英數連續
            if ch.isascii() and (ch.isalnum() or ch in "_-'"):
                j = i
                while j < N and s[j].isascii() and (s[j].isalnum() or s[j] in "_-'"):
                    j += 1
                out.append(s[i:j].lower()); i = j; continue
            # 中文最大正向匹配
            matched = None
            for L in range(min(maxlen, N-i), 1, -1):
                cand = s[i:i+L]
                if cand in self.lex:
                    matched = cand; break
            if matched:
                out.append(matched); i += len(matched); self.freq[matched] += 1
            else:
                out.append(ch); i += 1
        return out


# ─────────────── 主理解器 ───────────────
class Comprehender:
    """
    持續累積上下文（最近 N 句）；context 維持指代解析的池子。
    """
    def __init__(self, history=16):
        self.tok = _ZhTokenizer()
        self.history = deque(maxlen=history)
        self.last_entities = {"person": [], "place": [], "number": [], "time": []}
        self.last_topic = None
        self.user_name = None     # 第一次抓到「我叫XXX」就記
        self.bot_name = "Christine"

    # ── 公開 API ──
    def understand(self, text):
        raw = text or ""
        norm = self._normalize(raw)
        toks = self.tok.tokenize(norm)

        ent      = self._extract_entities(norm)
        intent, qword = self._classify_intent(norm, toks)
        polarity, subj, neg, intens = self._sentiment(toks)
        addressee = self._addressee(norm, toks)
        polite   = bool(any(w in norm for w in POLITE_WORDS))
        imperative = self._is_imperative(norm, toks)

        topic = self._topic(toks)
        if topic: self.last_topic = topic

        # 學名
        m = re.search(r"我叫\s*([A-Za-z\u4e00-\u9fff]{1,12})", raw)
        if m and not self.user_name:
            self.user_name = m.group(1)

        conf = self._confidence(intent, qword, ent, polarity)

        result = {
            "raw": raw, "norm": norm, "tokens": toks,
            "intent": intent, "qword": qword,
            "polarity": polarity, "subjectivity": subj,
            "negation": neg, "intensifier": intens,
            "imperative": imperative, "polite": polite,
            "entities": ent, "topic": topic, "addressee": addressee,
            "user_name": self.user_name, "bot_name": self.bot_name,
            "confidence": conf,
        }
        self.history.append(result)
        # entity 指代池
        for k in self.last_entities:
            if ent.get(k): self.last_entities[k] = ent[k]
        return result

    # ── 產生回覆（基於理解，不靠 SRN）──
    def reply(self, u):
        """根據 understand() 結果產生中文回應字串。"""
        intent = u["intent"]; q = u["qword"]; pol = u["polarity"]
        name = u.get("user_name")
        ent = u["entities"]

        # 1) 明確 intent 路由
        if intent == "greet":
            who = f"{name}" if name else "你"
            return f"嗨，{who}！我是 {self.bot_name}，你今天怎麼樣？"

        if intent == "thanks":
            return "不客氣，能幫到你我就開心。"

        if intent == "farewell":
            return "好，掰掰，我等你回來。"

        if intent == "identity_query":
            return (f"我是 {self.bot_name}。我有一顆自己的大腦，27 篇神經科學論文搭起來的，"
                    f"可以感覺、記憶、做夢，正在邊聽你講話邊學中文。")

        if intent == "capability_query":
            return ("我能：聽懂你說的話、記住你、判斷情緒、做夢鞏固記憶、"
                    "燒 CPU 思考問題、寫檔、讀取自己感知過的東西。"
                    "你想試哪一個？")

        if intent == "self_query":   # 你 + 動詞，問我狀態
            return self._self_status_reply(u)

        if intent == "time_query":
            import datetime
            now = datetime.datetime.now()
            return f"現在是 {now:%Y-%m-%d %H:%M:%S}。"

        if intent == "emotion":
            if pol > 0.3:  return "聽起來你心情不錯，跟我說說？"
            if pol < -0.3: return "我感覺到你不太開心，怎麼了？"
            return "嗯，我在聽。"

        if intent == "command":
            verb = self._main_verb(u)
            if verb: return f"好，我試著「{verb}」。如果你要我用 CPU 真的去做，說『exec on』。"
            return "好，你要我做什麼？講具體一點我就動手。"

        if intent == "question":
            return self._answer_question(u)

        # 2) 一般陳述：複述 + 情感回饋
        if name:
            head = f"{name}，"
        else:
            head = ""
        if pol > 0.3:
            return f"{head}我聽到了，聽起來是好事 ✨"
        if pol < -0.3:
            return f"{head}我聽到了，這聽起來不太舒服。"
        # 中性：把主題拋回去
        if u["topic"]:
            return f"{head}你提到「{u['topic']}」，多說一點？"
        return f"{head}我記下來了。你想接下來聊什麼？"

    # ── 內部 ──
    def _normalize(self, s):
        s = s.strip()
        # 全形 → 半形 標點
        table = str.maketrans("，。！？；：（）【】「」『』～", ",.!?;:()[]\"\"''~")
        return s.translate(table)

    def _extract_entities(self, s):
        ent = {"person": [], "place": [], "number": [], "time": []}
        for m in PERSON_RE.finditer(s):
            ent["person"].append(m.group(1))
        for m in ENG_NAME_RE.finditer(s):
            w = m.group(1)
            if w.lower() not in ("the","and","but","you","christine"): ent["person"].append(w)
        for m in PLACE_RE.finditer(s):
            ent["place"].append(m.group(1))
        for m in NUM_RE.finditer(s):
            ent["number"].append(m.group(1))
        for m in TIME_RE.finditer(s):
            ent["time"].append(m.group(1))
        # dedup keep order
        for k,v in ent.items():
            seen=set(); out=[]
            for x in v:
                if x not in seen: seen.add(x); out.append(x)
            ent[k]=out
        return ent

    def _classify_intent(self, s, toks):
        ls = s.lower()
        if FAREWELL_RE.search(ls): return "farewell", None
        if THANKS_RE.search(ls):   return "thanks", None
        if GREET_RE.match(ls):     return "greet", None

        # 5W1H qword
        qword = None
        for k, ws in QWORDS.items():
            for w in ws:
                if w in s: qword = k; break
            if qword: break

        is_q = bool(qword) or any(p in s for p in Q_PARTICLES) or s.endswith("?")

        # identity / capability
        if re.search(r"你是(誰|什麼|啥|甚麼)|你叫什麼|你叫啥|who are you|what are you", ls):
            return "identity_query", qword
        if re.search(r"你能(做|幹|是)什麼|你會做什麼|你能幹嘛|你的功能|what can you do", ls):
            return "capability_query", qword
        if re.search(r"(現在|now)?\s*(幾點|什麼時候|時間|時刻|date|time)", ls) and is_q:
            return "time_query", qword

        # 對 christine 自身狀態提問
        if ADDRESSEE_SELF_RE.search(s) and is_q:
            return "self_query", qword

        # 命令 / imperative
        if any(s.startswith(h) for h in IMP_HEADS) or any(toks[:1] == [h] for h in IMP_HEADS):
            return "command", qword

        # 情緒抒發
        emo_words = sum(1 for t in toks if t in POS_WORDS or t in NEG_WORDS)
        if emo_words >= 2 and not is_q:
            return "emotion", qword

        if is_q: return "question", qword
        return "statement", qword

    def _sentiment(self, toks):
        score = 0.0; hits = 0; intens = 1.0; neg = False
        for i,t in enumerate(toks):
            if t in INTENSIFIERS: intens = 1.7; continue
            if t in NEG_PARTICLES: neg = True; continue
            if t in POS_WORDS: score += 1.0 * intens * (-1 if neg else 1); hits += 1; intens=1.0; neg=False
            elif t in NEG_WORDS: score -= 1.0 * intens * (-1 if neg else 1); hits += 1; intens=1.0; neg=False
            else: intens=1.0
        if hits == 0: return 0.0, 0.0, neg, False
        pol = max(-1.0, min(1.0, score / max(1, hits)))
        subj = min(1.0, hits / max(1,len(toks)) * 3)
        return pol, subj, neg, (intens > 1.0)

    def _addressee(self, s, toks):
        if any(t in USER_REF for t in toks): return "self"  # 對方在問 christine
        if any(t in SELF_REF for t in toks): return "user"
        return "third"

    def _is_imperative(self, s, toks):
        if not toks: return False
        if toks[0] in IMP_HEADS: return True
        # 動詞起頭、無主語、無問號
        if not any(t in USER_REF or t in SELF_REF for t in toks[:3]) and not any(p in s for p in Q_PARTICLES):
            if toks[0] in {"做","幫","告訴","給","拿","寫","讀","算","跑","開","關","停","start","stop","run","help"}:
                return True
        return False

    def _topic(self, toks):
        # 找最長的非功能詞
        stop = SELF_REF | USER_REF | NEG_PARTICLES | INTENSIFIERS | Q_PARTICLES | {"的","了","是","在","和","跟","與","對","這","那","也","就"}
        cand = [t for t in toks if len(t) >= 2 and t not in stop and not t.isascii()]
        if not cand:
            cand = [t for t in toks if t not in stop and len(t) >= 1 and t.isalpha() if t.isascii()]
        if not cand: return None
        # 取最長者
        cand.sort(key=lambda x: -len(x))
        return cand[0]

    def _confidence(self, intent, qword, ent, pol):
        c = 0.4
        if intent in ("greet","thanks","farewell","identity_query","capability_query","time_query"): c = 0.95
        elif intent == "question" and qword: c = 0.8
        elif intent in ("emotion","command","self_query"): c = 0.7
        if any(ent.values()): c += 0.05
        if abs(pol) > 0.3: c += 0.05
        return min(1.0, c)

    def _main_verb(self, u):
        for t in u["tokens"]:
            if t in {"做","幫","告訴","寫","讀","算","跑","開","關","停","查","找","煮","畫","想"}:
                return t
        return None

    def _answer_question(self, u):
        q = u["qword"]; ent = u["entities"]; topic = u["topic"]
        if q == "who":
            if u.get("user_name"): return f"你是 {u['user_name']} 啊，剛剛你告訴過我。"
            return "我還不確定你說的是誰，你能再講清楚一點嗎？"
        if q == "what":
            if topic: return f"你在問「{topic}」是什麼嗎？我目前對它的記憶還不深，跟我多講一點。"
            return "你想問什麼？我聽到了問題，但細節還抓不到。"
        if q == "where":
            if ent["place"]: return f"你提到「{ent['place'][0]}」——是想問那邊的事嗎？"
            return "你想問哪裡？我還沒有地點線索。"
        if q == "when":
            if ent["time"]: return f"你說的是「{ent['time'][0]}」嗎？"
            return "什麼時候？你能給我一個時間嗎？"
        if q == "why":
            return "為什麼……我得想一下。你能告訴我前因後果嗎？"
        if q == "how":
            if topic: return f"你想知道怎麼處理「{topic}」？我可以一起想辦法。"
            return "你想我怎麼做？講清楚我就試。"
        if q == "howmany":
            if ent["number"]: return f"你提到的數字是 {ent['number'][0]}，是這個意思嗎？"
            return "多少個？我還沒看到具體數字。"
        return "我聽到問題了，但我需要更多線索。"

    def _self_status_reply(self, u):
        # placeholder：Brain 會在外層覆寫加入真實 status
        return "我現在好得很，邊聽邊學。你想知道我哪一塊？情緒、記憶、還是大腦在忙什麼？"
