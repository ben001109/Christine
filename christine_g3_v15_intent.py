from __future__ import annotations

import re
import urllib.parse
from dataclasses import dataclass, field

import christine_g3_frontier as g3

URL_RE = re.compile(r"https?://[^\s<>()]+", re.I)

def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()

def _tokens(text: str) -> set[str]:
    return g3._tokens(_clean(text))

def _jaccard(a: set[str], b: set[str]) -> float:
    return g3._jaccard(a, b)

def _host(url: str) -> str:
    try:
        return urllib.parse.urlparse(url).netloc.casefold().removeprefix("www.")
    except Exception:
        return ""

@dataclass(frozen=True)
class IntentFrame:
    mode: str
    operation: str
    output_kind: str
    goal: str
    requires_web: bool = False
    requires_facts: bool = False
    emotional_support: bool = False
    urls: tuple[str, ...] = ()
    source_hint: str = ""
    entities: tuple[str, ...] = ()
    missing_slots: tuple[str, ...] = ()
    scores: dict[str, float] = field(default_factory=dict)

class IntentKernel:
    """Feature-scored current-turn intent kernel. It runs before context inheritance."""

    WEB_SOURCES = {
        "threads": ("threads", "threads.com", "thread"),
        "instagram": ("instagram", "ig"),
        "facebook": ("facebook", "fb"),
        "github": ("github",),
        "reddit": ("reddit",),
        "youtube": ("youtube", "yt", "影片"),
    }

    def analyze(self, raw: str) -> IntentFrame:
        text = _clean(raw)
        low = text.casefold()
        urls = tuple(URL_RE.findall(text))
        source_hint = self._source_hint(low, urls)
        f = {
            "compute": self._compute_score(text),
            "code": self._code_score(text),
            "research": self._research_score(text, urls, source_hint),
            "support": self._support_score(text),
            "conversation": self._conversation_score(text),
            "factual": self._factual_score(text),
        }
        entities = self._entities(text, urls)

        if f["compute"] >= 0.92:
            return IntentFrame("compute", "compute", "text", text, entities=entities, scores=f)

        if urls:
            question_like = bool(re.search(r"(誰|什麼|在幹嘛|做什麼|怎麼|如何|內容|分析|看看|查|介紹|這個人|這是)", text, re.I))
            mode = "research" if question_like or len(text) > sum(len(u) for u in urls) + 4 else "inspect_url"
            return IntentFrame(mode, "research", "text", text, requires_web=True, requires_facts=True,
                               urls=urls, source_hint=source_hint, entities=entities, scores=f)

        if f["support"] >= 0.58:
            return IntentFrame("support", "converse", "text", text, emotional_support=True,
                               requires_facts=False, entities=entities, scores=f)

        if f["code"] >= 0.62:
            missing = self._code_missing_slots(text)
            return IntentFrame("clarify" if missing else "create_code", "create", "code", text,
                               requires_web=self._explicit_web(text), requires_facts=False,
                               entities=entities, missing_slots=tuple(missing), scores=f)

        if f["research"] >= 0.62:
            return IntentFrame("research", "research", "text", text, requires_web=True,
                               requires_facts=True, source_hint=source_hint, entities=entities, scores=f)

        if f["conversation"] >= 0.60:
            return IntentFrame("conversation", "converse", "text", text, entities=entities, scores=f)

        if f["factual"] >= 0.55:
            return IntentFrame("answer", "answer", "text", text, requires_facts=True, entities=entities, scores=f)

        return IntentFrame("conversation", "converse", "text", text, entities=entities, scores=f)

    @staticmethod
    def _compute_score(text: str) -> float:
        if re.fullmatch(r"\s*[0-9().+\-*/% ]+\s*(?:是多少|等於多少|=?\??)?\s*", text):
            return 1.0
        return 0.95 if re.search(r"(算一下|計算)\s*[0-9(]", text) else 0.0

    @staticmethod
    def _code_score(text: str) -> float:
        create = len(re.findall(r"(寫|做|建立|生成|實作|開發|create|build|implement)", text, re.I))
        tech = len(re.findall(r"(python|javascript|typescript|java|rust|go|程式|腳本|外掛|plugin|addon|api|爬蟲|bot|函式|演算法|asyncio|aiohttp)", text, re.I))
        debug = len(re.findall(r"(debug|除錯|修.*bug|程式碼)", text, re.I))
        return min(1.0, 0.34 * create + 0.38 * tech + 0.35 * debug)

    def _research_score(self, text: str, urls: tuple[str, ...], source_hint: str) -> float:
        explicit = len(re.findall(r"(上網|網路|網上|搜尋|搜索|查一下|幫我查|去查|上查|查查|查\b|search|look up)", text, re.I))
        current = len(re.findall(r"(最新|今天|現在|目前|即時|最近)", text, re.I))
        return min(1.0, 0.58 * min(1, explicit) + 0.24 * min(1, current) + 0.22 * bool(source_hint) + 0.5 * bool(urls))

    @staticmethod
    def _support_score(text: str) -> float:
        reflection = len(re.findall(r"(支撐著現在的我|影響我|改變我|我很感謝|非常感謝|其實我|我也有同樣|我困惑|我不懂為什麼|我一直在想)", text))
        distress = len(re.findall(r"(女朋友|伴侶|性侵|侵害|僵住|不反抗|不逃|害怕|創傷|難受|自責|愧疚|痛苦)", text))
        personal = len(re.findall(r"(我|我的|我們)", text))
        explanatory = len(re.findall(r"(為什麼|怎麼會|其實|但其實)", text))
        return min(1.0, 0.46 * min(2, reflection) + 0.30 * min(2, distress) + 0.12 * min(2, personal) + 0.10 * min(2, explanatory))

    @staticmethod
    def _conversation_score(text: str) -> float:
        greet = bool(re.search(r"^(你好|嗨|哈囉|hi|hello)", text, re.I))
        social = bool(re.search(r"(@[\w\u3400-\u9fff]+|斗內|donate|感謝他|謝謝他|我想跟他說|可以幫我@)", text, re.I))
        opinion = bool(re.search(r"(我覺得|我想|我希望|我都想|真的很)", text))
        return min(1.0, 0.65 * greet + 0.62 * social + 0.25 * opinion)

    @staticmethod
    def _factual_score(text: str) -> float:
        q = len(re.findall(r"(是誰|是什麼|為什麼|怎麼|如何|哪裡|何時|多少|有沒有|在幹嘛|做什麼|幹嘛|嗎|？|\?)", text))
        return min(1.0, 0.58 * min(1, q) + 0.18 * (len(text) > 8))

    @staticmethod
    def _explicit_web(text: str) -> bool:
        return bool(re.search(r"(上網|網路|網上|搜尋|查一下|幫我查|最新|目前|threads|instagram|github|reddit)", text, re.I))

    def _source_hint(self, low: str, urls: tuple[str, ...]) -> str:
        for url in urls:
            host = _host(url)
            for name, aliases in self.WEB_SOURCES.items():
                if any(a in host for a in aliases):
                    return name
        for name, aliases in self.WEB_SOURCES.items():
            if any(a in low for a in aliases):
                return name
        return ""

    @staticmethod
    def _entities(text: str, urls: tuple[str, ...]) -> tuple[str, ...]:
        entities: list[str] = []
        for url in urls:
            p = urllib.parse.urlparse(url)
            m = re.search(r"@([A-Za-z0-9_.-]+)", p.path)
            if m:
                entities.append("@" + m.group(1))
        entities += re.findall(r"@([A-Za-z0-9_.\-\u3400-\u9fff]+)", text)
        m = re.search(r"([^\s，。？！?]{2,20})是誰", text)
        if m:
            entities.append(m.group(1))
        for key in re.findall(r"(錫蘭|PUA\s*影片|PUA影片|花栗鼠🍋?)", text, re.I):
            entities.append(key)
        return tuple(dict.fromkeys(str(e) for e in entities))

    @staticmethod
    def _code_missing_slots(text: str) -> list[str]:
        low = text.casefold()
        objective_terms = re.findall(r"(抓取|下載|分析|排序|搜尋|監控|轉換|讀取|寫入|連線|api|網頁|網站|檔案|資料|影像|圖片|遊戲|minecraft|discord|瀏覽器|chrome|自動|asyncio|aiohttp|伺服器|server|bot|計算|模擬)", low, re.I)
        vague_only = bool(re.fullmatch(r".{0,8}(寫|做|建立|生成|開發).{0,8}(程式|腳本|外掛|plugin|addon).{0,4}", text, re.I))
        missing = []
        if not objective_terms or vague_only:
            missing.append("purpose")
        if re.search(r"(外掛|plugin|addon)", text, re.I) and not re.search(r"(minecraft|chrome|瀏覽器|遊戲|discord|vscode|wordpress|網站|app|應用|平台)", text, re.I):
            missing.append("target_platform")
        return list(dict.fromkeys(missing))
