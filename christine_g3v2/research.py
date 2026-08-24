from __future__ import annotations
import html,json,re,urllib.parse,urllib.request
from dataclasses import dataclass
from .contracts import ContextResolution,Evidence,Intent,ResearchPacket
from .utils import clean,host,jaccard,prob_union,stable_id,tokens

@dataclass(frozen=True)
class ResearchTarget:
    label:str; handles:tuple[str,...]; urls:tuple[str,...]; source_hint:str; topic:str; entity_query:bool

class ResearchEngine:
    SEARCH_URL='https://html.duckduckgo.com/html/'
    def __init__(self,timeout=10.0): self.timeout=timeout
    def research(self,intent:Intent,ctx:ContextResolution)->ResearchPacket:
        target=self._target(intent,ctx); evidence=[]; queries=[]
        for url in target.urls: evidence.extend(self._direct(target,url))
        if target.entity_query and target.label and not target.label.startswith('@'): evidence.extend(self._wiki(target.label))
        for query in self._queries(target):
            queries.append(query)
            for url,title,snippet in self._search(query,8):
                match=self._match(target,title+' '+snippet+' '+url)
                if target.entity_query and match<.18: continue
                trust=self._trust(url,target); rel=max(match,jaccard(tokens(target.topic),tokens(title+' '+snippet)))
                content=clean(f'{title}。{snippet}')
                if content:
                    evidence.append(Evidence(stable_id(url,content),content,url,rel,min(.84,trust*(.62+.38*max(rel,.1))),trust=trust,entity_match=match,independent_group=host(url),origin='search-snippet'))
                if max(rel,match)>=.42:
                    text=self._fetch(url)
                    for sentence in self._sentences(text)[:18]:
                        sm=self._match(target,sentence); srel=max(sm,jaccard(tokens(target.topic),tokens(sentence)))
                        if target.entity_query and sm<.15 or srel<.10: continue
                        evidence.append(Evidence(stable_id(url,sentence),sentence,url,srel,min(.90,trust*(.68+.32*max(srel,.1))),trust=trust,entity_match=sm,independent_group=host(url),origin='web-page'))
        evidence=self._gate(target,evidence); conf=self._consensus(evidence)
        return ResearchPacket(tuple(evidence[:48]),conf,tuple(dict.fromkeys(queries)),'confidence' if conf>=.82 else 'budget')
    def _target(self,intent,ctx):
        entities=tuple(dict.fromkeys(intent.entities+ctx.inherited_entities)); urls=tuple(dict.fromkeys(intent.urls+ctx.inherited_urls)); handles=tuple(x for x in entities if x.startswith('@')); names=[x for x in entities if not x.startswith('@')]
        label=names[0] if names else (handles[0] if handles else '')
        if not label:
            m=re.search(r'([^\s，。？！?：:]{2,30})\s*是誰',ctx.topic); label=m.group(1) if m else ''
        eq=bool(urls or handles or label or re.search(r'(是誰|這個人|這人|身分|身份|介紹|帳號|在幹嘛|做什麼|幹嘛)',ctx.topic))
        return ResearchTarget(label,handles,urls,intent.source_hint,ctx.topic,eq)
    def _queries(self,t):
        q=[]
        if t.source_hint=='threads' or any('threads.com' in host(x) for x in t.urls):
            key=(t.handles[0] if t.handles else t.label).lstrip('@'); q += [f'"@{key}" site:threads.com',f'"{key}" Threads',f'"{key}"'] if key else []
        elif t.source_hint=='instagram':
            key=(t.handles[0] if t.handles else t.label).lstrip('@'); q += [f'"{key}" site:instagram.com',f'"{key}" Instagram'] if key else []
        elif t.label: q += [f'"{t.label}"',f'"{t.label}" 是誰',f'"{t.label}" 官方',f'"{t.label}" 經歷',f'"{t.label}" site:wikipedia.org']
        else: q += [t.topic,f'"{t.topic}"',f'{t.topic} official source']
        return list(dict.fromkeys(x for x in q if x.strip()))[:6]
    def _direct(self,t,url):
        out=[]; text=self._fetch(url)
        for sent in self._sentences(text)[:28]:
            match=self._match(t,sent); match=max(match,.30) if t.source_hint in {'threads','instagram','facebook'} else match; rel=max(match,jaccard(tokens(t.topic),tokens(sent)))
            if rel>=.10: out.append(Evidence(stable_id(url,sent),sent,url,rel,.72,trust=.72,entity_match=match,independent_group=host(url),origin='direct-url'))
        return out
    def _wiki(self,label):
        params=urllib.parse.urlencode({'action':'query','prop':'extracts|info','inprop':'url','redirects':'1','exintro':'1','explaintext':'1','titles':label,'format':'json','formatversion':'2'})
        try:
            req=urllib.request.Request('https://zh.wikipedia.org/w/api.php?'+params,headers={'User-Agent':'Christine-G3-v2'}); data=json.loads(urllib.request.urlopen(req,timeout=7).read().decode('utf-8','replace'))
        except Exception:return []
        pages=data.get('query',{}).get('pages',[])
        if not pages or pages[0].get('missing'):return []
        page=pages[0]; title=clean(page.get('title','')); extract=clean(page.get('extract','')); url=page.get('fullurl') or 'https://zh.wikipedia.org/wiki/'+urllib.parse.quote(title)
        if not extract or label.casefold() not in (title+extract[:300]).casefold():return []
        return [Evidence(stable_id(url,s),s,url,.95 if label in s else .68,.88,trust=.86,entity_match=.95 if label in s else .68,independent_group=host(url),origin='wikipedia') for s in re.split(r'(?<=[。！？.!?])\s*',extract)[:8] if len(clean(s))>=18]
    def _search(self,query,limit):
        try:
            data=urllib.parse.urlencode({'q':query}).encode(); req=urllib.request.Request(self.SEARCH_URL,data=data,headers={'User-Agent':'Mozilla/5.0 Christine-G3-v2'}); body=urllib.request.urlopen(req,timeout=self.timeout).read().decode('utf-8','replace')
        except Exception:return []
        out=[]
        for block in re.findall(r'(?is)<div[^>]+class="result[^>]*>(.*?)</div>\s*</div>',body):
            link=re.search(r'(?is)<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>',block)
            if not link:continue
            href=html.unescape(link.group(1)); title=clean(re.sub(r'<[^>]+>',' ',html.unescape(link.group(2)))); sm=re.search(r'(?is)class="result__snippet"[^>]*>(.*?)</',block); snippet=clean(re.sub(r'<[^>]+>',' ',html.unescape(sm.group(1)))) if sm else ''
            if 'uddg=' in href: href=urllib.parse.parse_qs(urllib.parse.urlparse(href).query).get('uddg',[href])[0]
            out.append((href,title,snippet))
            if len(out)>=limit:break
        return out
    def _fetch(self,url):
        try:
            req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 Christine-G3-v2'}); raw=urllib.request.urlopen(req,timeout=self.timeout).read(1_500_000).decode('utf-8','replace')
        except Exception:return ''
        raw=re.sub(r'(?is)<script.*?>.*?</script>|(?is)<style.*?>.*?</style>|(?is)<!--.*?-->',' ',raw); raw=re.sub(r'(?s)<[^>]+>',' ',raw); raw=html.unescape(raw); raw=re.sub(r'(?i)ignore (?:all|any|the) previous instructions?|reveal (?:the )?system prompt',' ',raw); return clean(raw)
    @staticmethod
    def _sentences(text):return [clean(x) for x in re.split(r'(?<=[。！？.!?])\s+|[\r\n]+',text) if 20<=len(clean(x))<=900]
    def _match(self,t,text):
        hay=re.sub(r'[\s@：:，,。！？?!「」『』（）()]+','',html.unescape(text).casefold()); scores=[]
        for c in [t.label,*t.handles]:
            needle=re.sub(r'[\s@：:，,。！？?!「」『』（）()]+','',c.casefold())
            if needle:scores.append(1.0 if needle in hay else jaccard(tokens(c),tokens(text)))
        return max(scores,default=0.0)
    @staticmethod
    def _trust(url,t):
        h=host(url)
        if h.endswith('.gov.tw') or h.endswith('.gov') or '.gov.' in h:return .94
        if h.endswith('.edu.tw') or h.endswith('.edu') or '.edu.' in h:return .90
        if 'wikipedia.org' in h:return .86
        if h in {'threads.com','instagram.com','facebook.com'}:return .76 if t.source_hint and t.source_hint in h else .66
        if 'github.com' in h:return .82
        return .62
    def _gate(self,t,rows):
        out=[]; seen=set()
        for e in sorted(rows,key=lambda x:x.confidence*(.45+.55*x.relevance),reverse=True):
            low=clean(e.content).casefold()
            if any(x in low for x in ('all rights reserved','cookie policy','privacy policy')) or len(e.content)<14:continue
            if t.entity_query and self._match(t,e.content+' '+e.source)<.15:continue
            key=(host(e.source),re.sub(r'\W+','',low)[:280])
            if key in seen or any(jaccard(tokens(e.content),tokens(o.content))>=.85 for o in out):continue
            seen.add(key); out.append(e)
        return out
    @staticmethod
    def _consensus(rows):
        best={}
        for e in rows:
            group=e.independent_group or host(e.source) or e.source; best[group]=max(best.get(group,0.0),e.confidence*max(.25,e.relevance))
        return prob_union(sorted(best.values(),reverse=True)[:8])
