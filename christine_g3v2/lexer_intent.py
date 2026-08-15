from __future__ import annotations

import re
import urllib.parse

from .contracts import Intent
from .utils import clean, clamp01

URL_RE = re.compile(
    r"https?://[A-Za-z0-9.-]+(?::\d+)?(?:/[A-Za-z0-9._~:/?#\[\]@!$&'()*+,;=%-]*)?",
    re.I,
)


def split_urls(raw: str) -> tuple[tuple[str, ...], str]:
    text = str(raw or "")
    urls, spans = [], []
    for m in URL_RE.finditer(text):
        url = m.group(0).rstrip(".,;:!?)]}")
        if url:
            urls.append(url); spans.append((m.start(), m.start()+len(url)))
    chars = list(text)
    for a,b in spans:
        for i in range(a,b): chars[i] = " "
    return tuple(dict.fromkeys(urls)), clean("".join(chars))


def handle_from_url(url: str) -> str:
    try: path = urllib.parse.urlparse(url).path
    except Exception: return ""
    m = re.search(r"/@([A-Za-z0-9_.-]{1,64})(?:/|$)", path)
    return "@"+m.group(1) if m else ""


def source_hint(urls: tuple[str, ...], residual: str) -> str:
    combined = " ".join(urls).casefold()+" "+residual.casefold()
    for name, aliases in {
        "threads":("threads.com","threads"), "instagram":("instagram.com","instagram"),
        "facebook":("facebook.com","facebook"), "github":("github.com","github"),
        "reddit":("reddit.com","reddit"), "youtube":("youtube.com","youtu.be","youtube"),
    }.items():
        if any(a in combined for a in aliases): return name
    return ""


class IntentKernel:
    """Current-turn intent only. Context is intentionally excluded."""

    def analyze(self, raw: str) -> Intent:
        text = clean(raw)
        urls, residual = split_urls(text)
        hint = source_hint(urls, residual)
        entities = self._entities(residual, urls)
        base = residual or text
        scores = {
            "compute":self._compute(base), "support":self._support(base), "code":self._code(base),
            "image":self._image(base), "research":self._research(base,urls,hint),
            "conversation":self._conversation(base), "factual":self._factual(base),
        }

        if scores["compute"] >= .92:
            return Intent("compute","compute","text",base,scores=scores)
        if urls:
            q = bool(re.search(r"(誰|什麼|在幹嘛|做什麼|幹嘛|怎麼|如何|內容|分析|看看|看一下|查|介紹|這個人|這人|這是)", residual,re.I))
            kind = "research" if q or residual else "inspect_url"
            return Intent(kind,"research","text",residual or " ".join(entities) or urls[0],
                          requires_facts=True,requires_web=True,requires_current=True,
                          source_hint=hint,urls=urls,entities=entities,scores=scores)
        if scores["support"] >= .56:
            return Intent("support","converse","text",text,emotional_support=True,entities=entities,scores=scores)
        if scores["image"] >= .62:
            missing = () if self._image_has_subject(text) else ("subject",)
            return Intent("clarify" if missing else "create_image","create","image",text,
                          missing_slots=missing,entities=entities,scores=scores)
        if scores["code"] >= .62:
            missing = tuple(self._code_missing(text))
            return Intent("clarify" if missing else "create_code","create","code",text,
                          requires_web=self._explicit_web(text),entities=entities,missing_slots=missing,scores=scores)
        if scores["research"] >= .62:
            return Intent("research","research","text",text,requires_facts=True,requires_web=True,
                          requires_current=True,source_hint=hint,entities=entities,scores=scores)
        if scores["conversation"] >= .60:
            return Intent("conversation","converse","text",text,entities=entities,scores=scores)
        if scores["factual"] >= .54:
            return Intent("answer","answer","text",text,requires_facts=True,entities=entities,scores=scores)
        return Intent("conversation","converse","text",text,entities=entities,scores=scores)

    @staticmethod
    def _compute(text):
        if re.fullmatch(r"\s*[0-9().+\-*/% ]+\s*(?:是多少|等於多少|=?\??)?\s*",text): return 1.0
        return .95 if re.search(r"(算一下|計算)\s*[0-9(]",text) else 0.0

    @staticmethod
    def _support(text):
        reflection=len(re.findall(r"(支撐著現在的我|影響我|改變我|很感謝|非常感謝|其實我|我也有同樣|我困惑|我不懂為什麼|我一直在想)",text))
        distress=len(re.findall(r"(女朋友|伴侶|性侵|侵害|僵住|不反抗|不逃|害怕|創傷|難受|自責|愧疚|痛苦)",text))
        personal=len(re.findall(r"(我|我的|我們)",text)); explanatory=len(re.findall(r"(為什麼|怎麼會|其實|但其實)",text))
        return clamp01(.46*min(2,reflection)+.30*min(2,distress)+.12*min(2,personal)+.10*min(2,explanatory))

    @staticmethod
    def _code(text):
        create=len(re.findall(r"(寫|做|建立|生成|實作|開發|create|build|implement)",text,re.I))
        tech=len(re.findall(r"(python|javascript|typescript|java|rust|go|程式|腳本|外掛|plugin|addon|api|爬蟲|bot|函式|演算法|asyncio|aiohttp)",text,re.I))
        return clamp01(.35*create+.42*tech)

    @staticmethod
    def _image(text):
        return .82 if re.search(r"(畫|生成|做|製作|設計|create|generate|draw)",text,re.I) and re.search(r"(圖|圖片|設計圖|logo|插畫|image|picture|封面|角色圖)",text,re.I) else 0.0

    @staticmethod
    def _research(text,urls,hint):
        explicit=bool(re.search(r"(上網|網路|網上|搜尋|搜索|查一下|幫我查|去查|上查|查查|search|look up)",text,re.I))
        current=bool(re.search(r"(最新|今天|現在|目前|即時|最近)",text,re.I))
        return clamp01(.60*explicit+.25*current+.22*bool(hint)+.50*bool(urls))

    @staticmethod
    def _conversation(text):
        greet=bool(re.search(r"^(你好|嗨|哈囉|hi|hello)",text,re.I)); social=bool(re.search(r"(@[\w\u3400-\u9fff]+|斗內|donate|感謝他|謝謝他|我想跟他說|可以幫我@)",text,re.I)); opinion=bool(re.search(r"(我覺得|我想|我希望|我都想|真的很)",text))
        return clamp01(.65*greet+.62*social+.25*opinion)

    @staticmethod
    def _factual(text):
        return .82 if re.search(r"(是誰|是什麼|是啥|啥意思|什麼意思|意思是什麼|為什麼|怎麼|如何|哪裡|何時|多少|有沒有|在幹嘛|做什麼|幹嘛|解釋|說明|介紹|嗎|？|\?)",text) else 0.0

    @staticmethod
    def _entities(residual,urls):
        entities=[]
        for url in urls:
            h=handle_from_url(url)
            if h: entities.append(h)
        for h in re.findall(r"@([A-Za-z0-9_.-]{2,64})",residual): entities.append("@"+h)
        m=re.search(r"([^\s，。？！?：:]{2,40})\s*(?:是誰|是什麼|是啥|啥意思|什麼意思|意思是什麼|是幹嘛的)",residual)
        if m:
            subject=re.sub(r"^(?:看一下|看看|查一下|幫我查|查查|介紹一下|介紹|解釋一下|解釋|說明一下|說明|告訴我)","",m.group(1)).strip()
            if subject and subject not in {"這個人","這人","他","她","這個","這東西"} and not subject.endswith(("這個人","這人")): entities.append(subject)
        m2=re.match(r"^(?:解釋|說明|介紹)(?:一下)?\s*([^，。？！?]{2,40})",residual)
        if m2:
            subject=m2.group(1).strip()
            if subject and subject not in {"這個","這東西"}: entities.append(subject)
        for key in re.findall(r"(錫蘭|PUA\s*影片|PUA影片|花栗鼠🍋?)",residual,re.I): entities.append(key)
        return tuple(dict.fromkeys(entities))

    @staticmethod
    def _code_missing(text):
        objective=bool(re.search(r"(抓取|下載|分析|排序|搜尋|監控|轉換|讀取|寫入|連線|api|網頁|網站|檔案|資料|影像|圖片|遊戲|minecraft|discord|瀏覽器|chrome|自動|asyncio|aiohttp|伺服器|server|bot|計算|模擬)",text,re.I))
        missing=[]
        if not objective: missing.append("purpose")
        if re.search(r"(外掛|plugin|addon)",text,re.I) and not re.search(r"(minecraft|chrome|瀏覽器|遊戲|discord|vscode|wordpress|網站|app|平台)",text,re.I): missing.append("target_platform")
        return list(dict.fromkeys(missing))

    @staticmethod
    def _image_has_subject(text):
        stripped=re.sub(r"(幫我|請|畫|生成|做|製作|設計|一張|圖片|圖|image|picture)"," ",text,flags=re.I)
        return len(clean(stripped))>=2

    @staticmethod
    def _explicit_web(text):
        return bool(re.search(r"(上網|網路|搜尋|最新|目前|threads|instagram|github|reddit)",text,re.I))
