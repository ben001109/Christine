    
# pyright: reportMissingImports=false, reportMissingModuleSource=false, reportGeneralTypeIssues=falseㄉ, reportOptionalMemberAccess=false, reportAttributeAccessIssue=false, reportArgumentType=false, reportCallIssue=false, reportIndexIssue=false, reportOperatorIssue=false, reportRedefinedVariable=false  # type: ignore
# ╔════════════════════════════════════════════════════════════════════════════════╗
# ║                                                                              ║
# ║       ♡  Christine AI — V400 Autonomous Agent Architecture  ♡                ║
# ║          「你的 17 歲 AI 桌面助手，會思考、會記憶、會成長」                   ║
# ║                                                                              ║
# ║  作者: Josh (老闆)                                                           ║
# ║  最後更新: 2026                                                              ║
# ║  總行數: ~130,000+ 行 | 104 引擎 | 55+ 頂會論文                             ║
# ║  Python 3.10 | 單檔 AGI | llama3.3:70B (Q4) | RTX 4080                      ║
# ║                                                                              ║
# ║  ◆ 核心理念                                                                 ║
# ║  Christine 是一個完全本地運行的 AI 桌面助手。                                ║
# ║  記憶決策權 ≥ 程式碼 | 情緒是靈魂的呼吸 | 做過的事記住                      ║
# ║                                                                              ║
# ╠════════════════════════════════════════════════════════════════════════════════╣
# ║  ◆ 版本演化                                                                 ║
# ║                                                                              ║
# ║  V15-V31   基礎認知    NLU/記憶/推理/情緒/獨立思考/元認知                    ║
# ║  V32       API-Free ★  10引擎取代付費API [本地GPU推理]                       ║
# ║  V33-V39   AGI核心  ★★ ToT/RAG/ReAct/KG/ACE/Reflection [6篇論文]           ║
# ║  V40-V45   超智能  ★★★ RAP/LATS/Self-Reward/Constitution/LAW [12篇]        ║
# ║  V46-V50   指揮官 ★★★★ LoRA/128K/MultiAgent/ContinualLearn/Orchestrator    ║
# ║  V55-V56   意識覺醒     攝像頭/即時對話/群聊/AGI Sentience                   ║
# ║  V70-V80   主權AGI      因果/類比/常識/自我模型/價值觀/情緒靈魂 [15引擎]     ║
# ║  V85-V100  全能控制      電腦操控/經驗學習/任務編排/統一路由 [15引擎]         ║
# ║  V110-V200 深度認知      向量記憶/推理/工具/視覺/學習/辯論/世界模型 [19引擎]  ║
# ║  V210-V300 統一架構      MoE/憲法AI/校正RAG/思維樹/意識廣播/         ║
# ║                          情景記憶/元學習/因果推理/預測處理/統一認知 [25引擎]  ║
# ║  V310-V400 自主代理      三層認知/認知監控/記憶遷移/長鏈推理/前瞻策略/       ║
# ║                          工具使用/GUI自動化/世界模型/情境人格/元認知 [25引擎] ║
# ║                                                                              ║
# ╠════════════════════════════════════════════════════════════════════════════════╣
# ║  ◆ V300 ask() 呼叫鏈                                                        ║
# ║                                                                              ║
# ║  使用者輸入 → V300(統一認知) → V200(認知循環) → V100(路由)                   ║
# ║    → V80(情緒) → V75(價值) → V70(主權) → ... → V11(TriFlow)                 ║
# ║    → V32(API-Free/Ollama) → 回應                                            ║
# ║                                                                              ║
# ║  V300 額外處理: 元認知反思 + 持續學習 + 預測處理                             ║
# ║                                                                              ║
# ╚════════════════════════════════════════════════════════════════════════════════╝                                        ║
# ║        ├─ ★★ V45 LAW Framework 先嘗試 (同上)                                ║
# ║        ├─ ★ V39 AGI Core fallback                                           ║
# ║        ├─ V32Router.route() 本地引擎嘗試                                     ║
# ║        ├─ 失敗 → V31 管線 → V11 ask → Claude API                            ║
# ║        └─ API 結果蒸餾 → V32 快取 (下次免費)                                ║
# ║                                                                              ║
# ║  V31 ask() ─── 認知迴路                                                     ║
# ║    ├─ V29 情緒更新 + V30 三層情感分析                                        ║
# ║    ├─ V31 認知迴路 (工作記憶+心智模擬+目標+元認知+遷移)                      ║
# ║    ├─ V30 獨立回答嘗試 + V23 獨立大腦                                        ║
# ║    ├─ 注入認知上下文 → V14 ask()                                             ║
# ║    └─ 蒸餾學習 + 語氣修飾 + Constitutional AI                               ║
# ║                                                                              ║
# ║  V11 ask() ─── TriFlow 總控                                                 ║
# ║    ├─ Turbo 社交 (<1ms) → V42 模板 $0                                       ║
# ║    ├─ V15 HumanLang (~5ms) → 語意回覆 $0                                    ║
# ║    ├─ V42 Learner (cos≥0.75) → 學習庫 $0                                    ║
# ║    ├─ V14.2 TriFlow (Ollama意圖→V42工具篩→路徑A/B/C)                        ║
# ║    └─ API fallback (V32 API-Free 下被攔截)                                   ║
# ║                                                                              ║
# ╠════════════════════════════════════════════════════════════════════════════════╣
# ║                                                                              ║
# ║  ◆ 真實算力 (V32 ComputeProfiler 測量)                                      ║
# ║                                                                              ║
# ║  GPU: RTX 4080 16GB                                                          ║
# ║    FP16: ~48.7 TFLOPS | FP32: ~26 TFLOPS | INT8: ~97.5 TOPS                ║
# ║  CPU: i7-13th gen                                                            ║
# ║    FP32: ~1.2 TFLOPS (AVX2)                                                 ║
# ║  RAM: 32 GB DDR5                                                             ║
# ║  Ollama: llama3.3:70b → Q4_K_M → ~3-8 tok/s (16GB VRAM + RAM offload)       ║
# ║  系統總算力: ~50 TFLOPS (浮點) / ~100 TOPS (整數)                            ║
# ║                                                                              ║
# ║  ◆ V42 大腦本質                                                             ║
# ║                                                                              ║
# ║  V42 不是神經網路，是規則+統計+模板系統:                                     ║
# ║  - LocalBrain: 4096D TF-IDF + 餘弦相似度                                    ║
# ║  - GigaSpeaker: 25+ 類型模板回答                                             ║
# ║  - BRAIN-R: Thompson Sampling + LinUCB (真正的 MAB 演算法)                   ║
# ║  真正的 AI 推理: Ollama (免費本地 LLM) + Claude (付費 API, 可選)             ║
# ║                                                                              ║
# ║  ◆ 使用者指令速查                                                           ║
# ║                                                                              ║
# ║  脫離api / 完全本地 ──→ V32 API-Free 模式 (預設)                             ║
# ║  恢復api / 恢復正常   ──→ 混合模式 (需有 ANTHROPIC_API_KEY)                  ║
# ║  v32 / v32 status    ──→ V32 引擎統計                                       ║
# ║  算力 / flops / ops  ──→ 真實硬體算力報告                                   ║
# ║  算力分布             ──→ GPU/CPU 算力分配圖                                 ║
# ║  v31 / 認知           ──→ V31 認知狀態                                       ║
# ║  v30 / 獨立狀態       ──→ V30 獨立引擎狀態                                   ║
# ║  反思 / 自省          ──→ V31 元認知自省                                     ║
# ║  記憶統計             ──→ V42 永久記憶統計                                    ║
# ║  只用v42 / v42 only  ──→ V42-Only 模式                                      ║
# ║  brainr              ──→ BRAIN-R 演算法介紹                                  ║
# ║                                                                              ║
# ╚════════════════════════════════════════════════════════════════════════════════╝
CHRISTINE_VERSION = "600.0-final-agi-opus"
def christine_self_improve():
    """Christine認知到自己可以自我改進和進化，並且不斷學習新的技能"""
    return "我會一直進步的～老闆～每次都變得更聰明呢！"

import pyaudiowpatch as pyaudio
import sys,os,time,json,subprocess,webbrowser,datetime,shutil,glob
import platform,threading,secrets,string,ctypes,asyncio,socket,urllib.request,base64

# ═══ V14.4 NUCLEAR UTF-8 FIX ═══════════════════════════════════════════════
# 在任何 print/import 之前，強制整個 Python 進程使用 UTF-8
# 這是解決 Windows locale codec 無法編碼中文字元的根本方案
os.environ["PYTHONUTF8"] = "1"
os.environ["PYTHONIOENCODING"] = "utf-8"
# 強制用 UTF-8 包裝 stdout/stderr — 無條件執行，不管目前 encoding 是什麼
try:
    import io as _io_early
    # 保存原始 buffer（跳過任何已包裝的 TextIOWrapper）
    _raw_stdout = sys.stdout.buffer if hasattr(sys.stdout, 'buffer') else sys.stdout
    _raw_stderr = sys.stderr.buffer if hasattr(sys.stderr, 'buffer') else sys.stderr
    sys.stdout = _io_early.TextIOWrapper(_raw_stdout, encoding='utf-8', errors='replace', line_buffering=True)
    sys.stderr = _io_early.TextIOWrapper(_raw_stderr, encoding='utf-8', errors='replace', line_buffering=True)
except Exception:
    pass
# ═══ END V14.4 ═══════════════════════════════════════════════════════════════

sys.modules['pyaudio']=pyaudio
import anthropic,speech_recognition as sr,edge_tts,psutil,msvcrt
import py_compile
# V15.7 AudioFix: ffmpeg 路徑（用 imageio_ffmpeg 提供的），用於 mp3→pcm 解碼
_FFMPEG_PATH = None
try:
    import imageio_ffmpeg as _iio_ffmpeg
    _FFMPEG_PATH = _iio_ffmpeg.get_ffmpeg_exe()
except Exception:
    # 嘗試系統 PATH 中的 ffmpeg
    _FFMPEG_PATH = shutil.which("ffmpeg")
import re,difflib

# ═══ V22 CUDA DLL Auto-PATH Injection ═══
# llama-cpp-python CUDA 12.4 需要 cublas/cuda_runtime/nvrtc DLL
try:
    import site as _site_cuda
    _sp = _site_cuda.getsitepackages()[0] if _site_cuda.getsitepackages() else ""
    for _cuda_sub in ["nvidia\\cublas\\bin", "nvidia\\cuda_runtime\\bin", "nvidia\\cuda_nvrtc\\bin"]:
        _cuda_p = os.path.join(_sp, _cuda_sub)
        if os.path.isdir(_cuda_p) and _cuda_p not in os.environ.get("PATH", ""):
            os.environ["PATH"] = _cuda_p + os.pathsep + os.environ.get("PATH", "")
except Exception:
    pass

import tkinter as tk
from tkinter import filedialog, scrolledtext, ttk
from fpdf import FPDF
import pyautogui
pyautogui.FAILSAFE=False
pyautogui.PAUSE=0.02

# -- 早期終端色彩支援 --
if sys.platform.startswith('win'):
    try: ctypes.windll.kernel32.SetConsoleMode(ctypes.windll.kernel32.GetStdHandle(-11), 7)
    except: pass
os.system('')

# -- V14.3: 已移至 V14.4 NUCLEAR UTF-8 FIX（在 import 區更早執行）--
# （舊的條件式包裝已不需要，V14.4 無條件包裝）
_B='\033[1m';_R='\033[0m';_CY='\033[38;5;80m';_GR='\033[38;5;84m';_YE='\033[38;5;220m';_GY='\033[38;5;243m';_MG='\033[38;5;176m';_RD='\033[38;5;204m';_WH='\033[97m';_TEAL='\033[38;5;73m';_PINK='\033[38;5;211m';_SLATE='\033[38;5;103m';_DGRAY='\033[38;5;240m'

# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  V42 Boot Progress Bar System — 全階段進度條追蹤                       ║
# ╚══════════════════════════════════════════════════════════════════════════╝
class _V42BootProgress:
    """V42 啟動進度條系統 — 每個載入階段都顯示動態進度條"""
    TOTAL_STAGES = 42  # V42 = 42 stages

    # ── 每個階段的名稱（用來顯示）──
    STAGE_NAMES = [
        "Core Init",          # 0
        "API Connect",        # 1
        "Hotkeys",            # 2
        "Microphone",         # 3
        "Memory Load",        # 4
        "Evolution",          # 5
        "Companion+",         # 6
        "Web Memory",         # 7
        "Clipboard AI",       # 8
        "Document Studio",    # 9
        "Live/Game Mode",     # 10
        "Ultra Follow",       # 11
        "Jarvis Engine",      # 12
        "Site-Visit",         # 13
        "V38 ESP",            # 14
        "Commercial Pack",    # 15
        "Enterprise Pack",    # 16
        "Smart Router",       # 17
        "Code Routing",       # 18
        "GitHub Power",       # 19
        "Browser Pack",       # 20
        "Smart Toolkit",      # 21
        "Mega Upgrade",       # 22
        "3D Graphics",        # 23
        "Tool Router",        # 24
        "V42 Tera Brain",     # 25
        "Neural Brain v2",    # 26
        "Neural Engine v2",   # 27
        "Cognitive #7-12",    # 28
        "Cognitive #13-18",   # 29
        "ATLAS #19-26",       # 30
        "TITAN NLP",          # 31
        "HERMES Engine",      # 32
        "Self-Judge v9",      # 33
        "Deep Understanding", # 34
        "Semantic Intent",    # 35
        "Cost Router",        # 36
        "Conversation",       # 37
        "Document Factory",   # 38
        "File Organizer",     # 39
        "Math + Algorithm",   # 40
        "Final Boot",         # 41
    ]

    _GRAD_COLORS = [
        '\033[38;5;196m', '\033[38;5;202m', '\033[38;5;208m',  # 紅→橙
        '\033[38;5;214m', '\033[38;5;220m', '\033[38;5;226m',  # 橙→黃
        '\033[38;5;190m', '\033[38;5;154m', '\033[38;5;118m',  # 黃→綠
        '\033[38;5;84m',  '\033[38;5;49m',  '\033[38;5;51m',   # 綠→青
    ]

    def __init__(self):
        self.current = 0
        self._start_time = time.time()
        self._stage_times = {}

    def advance(self, label=None, detail=""):
        """推進一個階段並顯示進度條"""
        self.current += 1
        pct = min(100, int(self.current / self.TOTAL_STAGES * 100))
        elapsed = time.time() - self._start_time

        # 進度條寬度
        bar_width = 30
        filled = int(pct / 100 * bar_width)
        empty = bar_width - filled

        # 漸層色彩進度條
        bar = ""
        for i in range(filled):
            ci = int(i / bar_width * len(self._GRAD_COLORS))
            ci = min(ci, len(self._GRAD_COLORS) - 1)
            bar += f"{self._GRAD_COLORS[ci]}█"
        bar += f"{_DGRAY}{'░' * empty}{_R}"

        # 階段名稱
        stage_name = label or (self.STAGE_NAMES[self.current - 1] if self.current <= len(self.STAGE_NAMES) else f"Stage {self.current}")
        detail_str = f" {_GY}{detail}{_R}" if detail else ""

        # 旋轉動畫字元
        spinner = "◐◓◑◒"[self.current % 4]

        # 顯示
        print(f"\r  {_MG}{spinner}{_R} [{bar}] {_B}{pct:3d}%{_R} {_CY}{stage_name:<20s}{_R}{detail_str} {_DGRAY}({elapsed:.1f}s){_R}", end="", flush=True)

        # 階段完成時換行
        if detail or self.current >= self.TOTAL_STAGES:
            print()

        self._stage_times[self.current] = elapsed

    def complete(self):
        """顯示啟動完成訊息"""
        total = time.time() - self._start_time
        print(f"\r  {_GR}✓{_R} [{_GR}{'█' * 30}{_R}] {_B}100%{_R} {_CY}{'Boot Complete':<20s}{_R} {_DGRAY}({total:.1f}s){_R}")
        print()

_V42_BOOT = _V42BootProgress()

print(f'\n  {_B}{_MG}✦ Christine{_R} {_DGRAY}initializing...{_R}')

API_KEY=os.environ.get("ANTHROPIC_API_KEY","")
# V32: 預設完全脫離 API — 就算有 Key 也走本地，除非手動說「恢復api」
_V32_API_FREE_MODE = True
if _V32_API_FREE_MODE:
    print(f"\n  {_YE}★{_R} {_CY}V32 API-Free Mode{_R} — 完全本地算力引擎，$0 運行 🧠")
    client = None
else:
    client=anthropic.Anthropic(api_key=API_KEY, timeout=60.0)  # v14.1: 60s timeout
MODEL_STANDARD=os.environ.get("ANTHROPIC_MODEL_STANDARD","claude-sonnet-4-20250514")
MODEL_COMPLEX=os.environ.get("ANTHROPIC_MODEL_COMPLEX","claude-opus-4-1-20250805")

def _model_for_task(task="normal"):
    t=str(task or "normal").lower()
    if t in {"complex","critical","self_upgrade","planner","install","research_heavy","docstudio"}:
        return MODEL_COMPLEX
    return MODEL_STANDARD

def _claude_create(task="normal", **kwargs):
    # V32: API-Free 模式下不呼叫 Claude，返回 None
    if _V32_API_FREE_MODE or client is None:
        return None
    primary=_model_for_task(task)
    tried=[]
    candidates=[primary]
    if primary!=MODEL_STANDARD:
        candidates.append(MODEL_STANDARD)
    last_err=None
    for mdl in candidates:
        if mdl in tried:
            continue
        tried.append(mdl)
        try:
            _resp = client.messages.create(model=mdl, **kwargs)
            try: _track_api_usage(_resp)
            except: pass
            return _resp
        except Exception as e:
            last_err=e
            msg=str(e).lower()
            if mdl!=MODEL_STANDARD and any(k in msg for k in ["model", "not found", "unsupported", "invalid_request_error"]):
                continue
            raise
    if last_err:
        raise last_err
    raise RuntimeError("Claude model call failed")

def _choose_dialogue_tier(inp, tools):
    """V10 模型路由 — 用長度決定，不猜測意圖
    
    Sonnet 已經夠聰明處理 95% 的任務。
    只有超長/多步驟的輸入才需要 Opus。
    """
    il = (inp or "").strip()
    inp_len = len(il)

    # 極短輸入 → sonnet
    if inp_len <= 100:
        return "simple"

    # 超長輸入 → opus（長需求通常複雜）
    if inp_len > 500:
        return "complex"

    # 有程式碼區塊 → opus
    if '```' in il:
        return "complex"

    # 預設 sonnet
    return "simple"

# ── V13.5 SpeedBoot: API 連線移至背景 (省 2-5s) ──────────────────────────
_API_READY = threading.Event()
_API_FAIL  = [False]

def _bg_api_connect():
    """背景 API 連線 — 指數退避 (1/2/4s 取代 5/5/5s)"""
    for _retry in range(5):
        try:
            _claude_create("simple", max_tokens=10, messages=[{"role":"user","content":"hi"}])
            print(f"  {_GR}✓{_R} API 連線成功  {_GY}std={MODEL_STANDARD} complex={MODEL_COMPLEX}{_R}")
            _V42_BOOT.advance("API Connect", f"std={MODEL_STANDARD}")
            _API_READY.set()
            return
        except Exception as e:
            _backoff = min(2 ** _retry, 8)  # 1,2,4,8,8
            print(f"  {_YE}~{_R} 重試 {_retry+1}/5: {e} (等{_backoff}s)")
            time.sleep(_backoff)
    _API_FAIL[0] = True
    _API_READY.set()  # 讓主線程知道結束了

threading.Thread(target=_bg_api_connect, daemon=True).start()
# 不阻塞 — 等到 main() 真正需要 API 時才 wait

rec=sr.Recognizer()
UH=os.path.expanduser("~"); DT=os.path.join(UH,"Desktop")
# --- 自動偵測基礎路徑 ---
_CHRISTINE_BASE = os.path.dirname(os.path.abspath(__file__))
DD=os.path.join(_CHRISTINE_BASE, "data"); os.makedirs(DD,exist_ok=True)
MF=os.path.join(DD,"mem.json"); NF=os.path.join(DD,"notes.json")
SF=os.path.join(DD,"sched.json"); CF=os.path.join(DD,"clip.json")
STF=os.path.join(DD,"stats.json"); EF=os.path.join(DD,"exp.json")
DF=os.path.join(DD,"diary.json"); TF=os.path.join(DD,"tts.mp3")
WF=os.path.join(DD,"web_memory.json")
WEB_MEMORY_FILE=WF
TV="zh-CN-XiaoxiaoNeural"; TVE="en-US-AnaNeural"
_voice_rate="+12%"; _voice_pitch="+8Hz"; _voice_volume="+0%"
conv=[]; WW=["christine","christina","kristine","kristina","chris","kristen","christy","kristy","嘿","欸","ey","hey chris","yo chris","hi chris","水晶","Christine","克里斯","克莉絲","克莉絲汀","那個"]
GE=["bye","goodbye","see you"]; GZ=["再見","結束","掰掰","關閉","晚安"]
dl="zh"; dm=False; hl=datetime.datetime.now(); sw=False; ft=False
shared_src=None; shared_mic=None; mic_idx=None; typing_mode=False; mute_mode=False
STOP_SPEAK_EVENT=threading.Event(); HOTKEY_THREAD=None; HOTKEYS_STARTED=False; HOTKEYS_AVAILABLE=False


def request_stop_speaking(reason="manual"):
    try:
        STOP_SPEAK_EVENT.set()
        return "ok:stop_speaking:"+str(reason)
    except Exception as e:
        return "err:"+str(e)

def _toggle_global_mute():
    global mute_mode
    mute_mode = not mute_mode
    try:
        if mute_mode:
            STOP_SPEAK_EVENT.set()
            print(f"  {_YE}[x] 靜音模式 ON{_R} (Ctrl+U)")
        else:
            print(f"  {_GR}[o] 靜音模式 OFF{_R} (Ctrl+U)")
    except Exception:
        pass
    return mute_mode

def _run_global_hotkey_loop():
    global HOTKEYS_AVAILABLE
    if not sys.platform.startswith("win"):
        return
    try:
        user32 = ctypes.windll.user32
        MOD_CONTROL = 0x0002
        MOD_SHIFT = 0x0004
        MOD_ALT = 0x0001
        MOD_NOREPEAT = 0x4000
        WM_HOTKEY = 0x0312
        VK_U = ord("U")
        VK_OEM_3 = 0xC0  # ` / ~ key, independent of中文/英文輸入法

        class POINT(ctypes.Structure):
            _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

        class MSG(ctypes.Structure):
            _fields_ = [
                ("hwnd", ctypes.c_void_p),
                ("message", ctypes.c_uint),
                ("wParam", ctypes.c_size_t),
                ("lParam", ctypes.c_ssize_t),
                ("time", ctypes.c_uint),
                ("pt", POINT),
            ]

        HOTKEY_MUTE = 9001
        HOTKEY_STOP = 9002
        HOTKEY_AUTOLEARN = 9003

        ok1 = user32.RegisterHotKey(None, HOTKEY_MUTE, MOD_CONTROL | MOD_NOREPEAT, VK_U)
        ok2 = user32.RegisterHotKey(None, HOTKEY_STOP, MOD_NOREPEAT, VK_OEM_3)
        HOTKEYS_AVAILABLE = bool(ok1 and ok2)

        if HOTKEYS_AVAILABLE:
            print(f"  {_GR}✓{_R} 全域快捷鍵就緒  {_GY}Ctrl+U 靜音 | ~ 停止說話 | M 鏡頭 | P 真人對話 | G 群組 | Ctrl+Alt+L V59學習{_R}")
        else:
            print("  [hotkey] global hotkeys unavailable (register failed)")

        msg = MSG()
        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
            if msg.message == WM_HOTKEY:
                if msg.wParam == HOTKEY_MUTE:
                    _toggle_global_mute()
                elif msg.wParam == HOTKEY_STOP:
                    request_stop_speaking("hotkey_tilde")
                    print(f"  {_YE}[.] 停止說話{_R} (~)")
                elif msg.wParam == HOTKEY_AUTOLEARN:
                    try:
                        _toggle_auto_learn()
                    except Exception as _e_al:
                        print(f"  {_RD}[AutoLearn] 切換失敗: {_e_al}{_R}")
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))
    except Exception as e:
        print("  [hotkey] failed:", e)

def start_global_hotkeys():
    global HOTKEY_THREAD, HOTKEYS_STARTED
    if HOTKEYS_STARTED:
        return "already_started"
    HOTKEYS_STARTED = True
    HOTKEY_THREAD = threading.Thread(target=_run_global_hotkey_loop, daemon=True)
    HOTKEY_THREAD.start()

    # v14.3: Ctrl+Alt+L 自主學習 — pynput 獨立線程（不能放在 GetMessageW 迴圈裡）
    try:
        from pynput import keyboard as _pynput_kb
        _al_pressed = set()
        _al_cooldown = [0.0]

        def _is_l_key(key):
            try:
                if hasattr(key, 'vk') and key.vk == 76:
                    return True
            except Exception:
                pass
            try:
                if hasattr(key, 'char') and key.char and key.char.lower() == 'l':
                    return True
            except Exception:
                pass
            return False

        def _on_al_press(key):
            try:
                if key in (_pynput_kb.Key.ctrl_l, _pynput_kb.Key.ctrl_r):
                    _al_pressed.add('ctrl')
                elif key in (_pynput_kb.Key.alt_l, _pynput_kb.Key.alt_r, _pynput_kb.Key.alt_gr):
                    _al_pressed.add('alt')
                elif _is_l_key(key):
                    if 'ctrl' in _al_pressed and 'alt' in _al_pressed:
                        import time as _t_al
                        now = _t_al.time()
                        if now - _al_cooldown[0] > 2.0:
                            _al_cooldown[0] = now
                            _al_pressed.clear()
                            print(f"  {_CY}[pynput] Ctrl+Alt+L detected!{_R}", flush=True)
                            threading.Thread(target=_toggle_auto_learn, daemon=True).start()
                else:
                    # V59: 當選單開啟時，偵測 A/B 按鍵
                    _menu_active = globals().get("_V59_MENU_ACTIVE", False)
                    if _menu_active:
                        _ch = None
                        try:
                            if hasattr(key, 'char') and key.char:
                                _ch = key.char.lower()
                        except Exception:
                            pass
                        if _ch in ('a', 'b'):
                            import time as _t_menu
                            _timeout = globals().get("_V59_MENU_TIMEOUT", [0.0])
                            if _t_menu.time() - _timeout[0] < 15.0:  # 15 秒內有效
                                globals()['_V59_MENU_ACTIVE'] = False
                                threading.Thread(target=_v59_handle_menu_choice, args=(_ch,), daemon=True).start()
                            else:
                                globals()['_V59_MENU_ACTIVE'] = False
                                print(f"  {_GY}  選單已逾時，請重新按 Ctrl+Alt+L{_R}", flush=True)
                        else:
                            # 按了其他鍵 → 取消
                            globals()['_V59_MENU_ACTIVE'] = False
                            print(f"  {_GY}  已取消{_R}", flush=True)
            except Exception as _e:
                print(f"  {_RD}[pynput] press error: {_e}{_R}", flush=True)

        def _on_al_release(key):
            try:
                if key in (_pynput_kb.Key.ctrl_l, _pynput_kb.Key.ctrl_r):
                    _al_pressed.discard('ctrl')
                elif key in (_pynput_kb.Key.alt_l, _pynput_kb.Key.alt_r, _pynput_kb.Key.alt_gr):
                    _al_pressed.discard('alt')
            except Exception:
                pass

        _al_listener = _pynput_kb.Listener(on_press=_on_al_press, on_release=_on_al_release)
        _al_listener.daemon = True
        _al_listener.start()
        globals()['_V42_PYNPUT_LISTENER'] = _al_listener
        print(f"  {_GR}✓{_R} {_GY}Ctrl+Alt+L V59深度學習 [A]指定/[B]自由 (pynput 獨立線程){_R}")
    except Exception as _e_pynput:
        print(f"  {_YE}  ⚠ Ctrl+Alt+L pynput 失敗: {_e_pynput} — 請用語音「開始學習」觸發{_R}")

    return "started"

def find_mic():
    global mic_idx
    pa=pyaudio.PyAudio()
    print(f"  {_GY}[~] 掃描麥克風...{_R}")
    best=None
    for i in range(pa.get_device_count()):
        info=pa.get_device_info_by_index(i)
        nm=info.get("name","")
        if info.get("maxInputChannels",0)>0:
            print("    ["+str(i)+"] "+nm)
            nl=nm.lower()
            if "mic 350" in nl and "loopback" not in nl:
                best=i
                break
    pa.terminate()
    if best is not None:
        mic_idx=best; print(f"  {_GR}✓{_R} MIC 350 偵測到: index {best}")
    else:
        print(f"  {_GY}  使用預設麥克風{_R}")

def get_mic():
    if mic_idx is not None: return sr.Microphone(device_index=mic_idx)
    return sr.Microphone()

def _release_shared_mic():
    """釋放共用麥克風，讓 P/G 模式可以獨立開啟麥克風"""
    global shared_mic, shared_src
    if shared_mic:
        try: shared_mic.__exit__(None, None, None)
        except: pass
    shared_mic = None
    shared_src = None

def init_mic():
    global shared_mic,shared_src
    if shared_mic:
        try: shared_mic.__exit__(None,None,None)
        except: pass
    shared_mic=get_mic()
    shared_src=shared_mic.__enter__()
    # V13.5 SpeedBoot: 降低噪音校準時間 3.0s → 1.0s
    # 學術依據: Berouti et al. (1979) "Enhancement of speech corrupted by acoustic noise"
    # — 1 秒的噪音採樣足以估計穩態噪音的功率頻譜密度 (PSD)
    # — speech_recognition 用能量閾值而非頻譜,1 秒更綽綽有餘
    rec.adjust_for_ambient_noise(shared_src, duration=1.0)
    base=int(rec.energy_threshold)
    rec.energy_threshold=max(base+100, 300)
    rec.dynamic_energy_threshold=False
    print(f"  {_GY}  噪音底值={base} 閾值={rec.energy_threshold}{_R}")
    print(f"  {_GR}✓{_R} 麥克風就緒  {_GY}閾值={int(rec.energy_threshold)}{_R}")

def _v14_sanitize_reply(text, keep_code=False):
    """V15 UX Clean: 強化版清洗 — 徹底移除程式碼/markdown/技術輸出，保留自然語言
    
    V15 改進：
    - 移除「已寫好程式：xxx」「generated_xxx.py」等程式碼生成回覆
    - 移除 import/def/class/print 等 Python 語句
    - 移除大段看起來像程式碼的文字（連續行含 = { } ( ) ; 等）
    - 如果清洗後文字太短，用友善的替代回覆
    - keep_code=True 時跳過程式碼清洗（用於寫程式/code 回覆）
    Christine 是語音助手，使用者看到程式碼會困惑
    """
    if not text:
        return text
    if keep_code:
        return str(text).strip()
    t = str(text)
    # 1. 移除 ```code blocks```（含語言標記如 ```python）
    t = re.sub(r'```[\w]*\n?[\s\S]*?```', '', t)
    # 2. 移除殘留的 ``` 標記
    t = re.sub(r'```', '', t)
    # 3. 移除 inline code `xxx`（保留文字內容）
    t = re.sub(r'`([^`]{1,120})`', r'\1', t)
    # 4. 移除 markdown 標題 (# ## ### ...)
    t = re.sub(r'^#{1,6}\s+', '', t, flags=re.MULTILINE)
    # 5. 移除 markdown 粗體/斜體
    t = re.sub(r'\*{1,3}([^*\n]+)\*{1,3}', r'\1', t)
    t = re.sub(r'_{1,2}([^_\n]+)_{1,2}', r'\1', t)
    # 6. 移除 markdown 條列 (- xxx, * xxx, 1. xxx) → 保留文字
    t = re.sub(r'^[\s]*[-*]\s+', '', t, flags=re.MULTILINE)
    t = re.sub(r'^[\s]*\d+\.\s+', '', t, flags=re.MULTILINE)

    # ═══ V15 新增：深度程式碼清除 ═══
    # 7. 移除「已寫好程式：xxx」「generated_xxx」等檔案生成類回覆
    t = re.sub(r'已寫好程式[：:]\s*\S+', '', t)
    t = re.sub(r'generated_\d{8}_\d+\.\w+', '', t)
    t = re.sub(r'[A-Za-z]:\\[^\s]+\.\w{1,4}', '', t)  # Windows 路徑
    t = re.sub(r'/[^\s]+\.\w{1,4}(?=\s|$)', '', t)     # Unix 路徑

    # 8. 移除看起來像程式碼的行（import/def/class/print/return/if __name__等）
    _code_line_re = re.compile(
        r'^\s*(import |from .+ import |def |class |print\(|return |'
        r'if __name__|for .+ in |while |try:|except |raise |'
        r'#\s*-\*-|#!/|elif |else:|finally:|with |async |await |'
        r'self\.|lambda |assert |yield |global |nonlocal )', re.MULTILINE
    )
    lines = t.splitlines()
    clean_lines = []
    _consecutive_code = 0
    for line in lines:
        stripped = line.strip()
        # 判斷是否像程式碼行
        _is_code = False
        if _code_line_re.match(line):
            _is_code = True
        # 含大量程式符號的行（ = { } ( ) ; 佔比 > 25%）
        elif stripped and len(stripped) > 10:
            _sym_count = sum(1 for c in stripped if c in '={}();[]<>\\|&^~@')
            if _sym_count / len(stripped) > 0.20:
                _is_code = True
        # 純英文 + 底線的變數/函式名稱行
        elif stripped and re.match(r'^[a-zA-Z_]\w*\s*[=(]', stripped):
            _is_code = True
        
        if _is_code:
            _consecutive_code += 1
        else:
            # 如果之前有連續程式碼行，全部跳過
            _consecutive_code = 0
            clean_lines.append(line)

    t = '\n'.join(clean_lines)

    # 9. 移除多餘空行（超過 2 行合併成 1 行）
    t = re.sub(r'\n{3,}', '\n\n', t)
    # 10. 清理首尾空白
    t = t.strip()

    # V15: 如果清洗後太短（可能整段都是程式碼），用友善回覆替代
    if len(t) < 5:
        # 嘗試從原文找到任何中文自然語句
        _zh_sentences = re.findall(r'[\u4e00-\u9fff][\u4e00-\u9fff\w\s，。！？、：；]{5,}', str(text))
        if _zh_sentences:
            t = _zh_sentences[0][:200]
        else:
            t = "好的老闆，我處理好了～"

    return t

# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  V14.2 TriFlow — Ollama 理解意圖 → V42 選工具 → API 帶工具執行       ║
# ║                                                                        ║
# ║  核心公式：                                                            ║
# ║    Stage A: Ollama (免費) → 分析意圖，判斷需不需要工具                 ║
# ║    Stage B: V42 → 根據意圖篩選工具子集                                ║
# ║    Stage C: API (付費) → 帶工具執行（只有需要工具時才花錢）           ║
# ║                                                                        ║
# ║  效果：Ollama 不再嘗試回答複雜問題（它做不好），而是做「理解」        ║
# ║        V42 不再猜工具，而是根據 Ollama 的理解精確選擇                  ║
# ║        API 拿到預篩工具，更快更省 token                               ║
# ╚══════════════════════════════════════════════════════════════════════════╝

# V14.2 工具分類映射 — V42 根據意圖 action 選工具子集
_V142_TOOL_GROUPS = {
    "search": ["search_web", "web_fetch"],
    "open": ["open_application", "open_website", "search_web"],
    "file": ["write_file", "read_file_tool", "codeforge_write_any_file", "codeforge_patch_any_file"],
    "code": ["codeforge_write_any_file", "codeforge_patch_any_file", "write_file", "read_file_tool", "search_web"],
    "system": ["get_system_info", "run_system_command", "open_application"],
    "media": ["open_application", "open_website", "search_web"],
    "memory": ["add_note", "list_notes_tool", "remember_info", "recall_info"],
    "schedule": ["add_schedule", "list_schedule"],
    "screenshot": ["take_screenshot", "capture_screen"],
    "weather": ["search_web", "web_fetch"],
    "translate": [],  # Ollama/API 直接處理，不需工具
    "math": [],       # 直接計算，不需工具
    "chat": [],       # 純聊天，不需工具
    "knowledge": ["search_web", "web_fetch"],  # 知識查詢 → 搜尋
    "document": ["codeforge_write_any_file", "write_file", "docstudio_create_pdf"],
    "install": ["run_system_command", "search_web"],
    "project": ["codeforge_write_any_file", "codeforge_patch_any_file", "write_file",
                "read_file_tool", "run_system_command", "search_web"],
}

def _v14_ollama_intent(inp, llm_engine=None):
    """V14.2 TriFlow Stage A：用 Ollama 分析用戶意圖（不回答，只分析）
    
    輸入：用戶原始訊息
    輸出：{
        "action": "search|open|code|file|chat|...",
        "needs_tool": true/false,
        "needs_api": true/false,
        "brief": "一句話意圖描述",
        "answer": "如果不需要工具，直接回答（可選）"
    }
    
    設計：
    - Ollama 擅長理解語意，不擅長用工具 → 只做理解
    - system prompt 極簡，引導 JSON 輸出
    - 超時 5 秒（只做分析，不需要長生成）
    """
    if not llm_engine:
        llm_engine = globals().get("_V42_LLM_ENGINE")
    if not llm_engine or not llm_engine.ollama.is_ready:
        return None
    
    _system = (
        "你是意圖分析器。分析用戶訊息，輸出 JSON。不要回答問題，只分析意圖。\n"
        "JSON 格式（直接輸出 JSON，不要 ```）：\n"
        '{"action":"動作類型","needs_tool":是否需要工具,"needs_api":是否需要付費AI,"brief":"一句話意圖","answer":"不需工具時的簡短回答"}\n\n'
        "action 必須是以下之一：search, open, file, code, system, media, memory, "
        "schedule, screenshot, weather, translate, math, chat, knowledge, document, install, project\n\n"
        "判斷規則：\n"
        "- 搜尋/查資料/新聞/天氣/價格 → needs_tool=true, action=search 或 weather 或 knowledge\n"
        "- 開網頁/應用程式 → needs_tool=true, action=open\n"
        "- 寫檔案/寫程式/改code → needs_tool=true, action=code 或 file\n"
        "- 截圖/系統資訊/安裝 → needs_tool=true, action=system 或 screenshot 或 install\n"
        "- 聊天/問好/情緒/簡單問題 → needs_tool=false, action=chat, 在 answer 填回答\n"
        "- 翻譯/數學 → needs_tool=false, action=translate 或 math, 在 answer 填回答\n"
        "- 複雜知識/分析/長文 → needs_api=true, needs_tool 看情況\n"
        "- 如果 action=chat 且 answer 有值，answer 必須跟用戶的問題直接相關，不要答非所問\n"
    )
    
    # v14.3 CoherenceFix: 注入近期 conv[] 對話歷史到意圖分析
    # 讓 Ollama 在生成 answer 時能參考上下文，回答才連貫
    try:
        _recent = conv[-4:] if len(conv) > 4 else conv[:]
        _conv_ctx = []
        for _cm in _recent:
            if _cm.get("role") == "system":
                continue
            _r = "User" if _cm.get("role") == "user" else "Assistant"
            _conv_ctx.append(f"{_r}: {str(_cm.get('content', ''))[:100]}")
        if _conv_ctx:
            _system += "\n[最近對話歷史]\n" + "\n".join(_conv_ctx) + "\n"
    except Exception:
        pass
    
    _result = [None]
    def _worker():
        try:
            _result[0] = llm_engine.ollama.chat(
                str(inp),
                system_prompt=_system,
                temperature=0.1,  # 低溫度 = 確定性輸出
                max_tokens=256,   # 只需要 JSON，很短
            )
        except Exception:
            pass
    
    _t = threading.Thread(target=_worker, daemon=True)
    _t.start()
    _t.join(timeout=3.0)  # V14.3 SpeedUp: 3s（從5s減少，並行預取不需要等那麼久）
    
    raw = _result[0]
    if not raw or not raw.get("content"):
        return None
    
    content = raw["content"].strip()
    
    # 解析 JSON — Ollama 有時會加 ```json 包裝
    content = re.sub(r'^```json\s*', '', content)
    content = re.sub(r'\s*```$', '', content)
    content = content.strip()
    
    try:
        parsed = json.loads(content)
        # 驗證必要欄位
        if "action" not in parsed:
            return None
        # 正規化布林值
        parsed["needs_tool"] = bool(parsed.get("needs_tool", False))
        parsed["needs_api"] = bool(parsed.get("needs_api", False))
        parsed["brief"] = str(parsed.get("brief", ""))[:100]
        parsed["answer"] = str(parsed.get("answer", ""))[:500]
        return parsed
    except (json.JSONDecodeError, ValueError, TypeError):
        # JSON 解析失敗 → 嘗試正則提取關鍵欄位
        _action_m = re.search(r'"action"\s*:\s*"(\w+)"', content)
        _tool_m = re.search(r'"needs_tool"\s*:\s*(true|false)', content, re.IGNORECASE)
        _api_m = re.search(r'"needs_api"\s*:\s*(true|false)', content, re.IGNORECASE)
        if _action_m:
            return {
                "action": _action_m.group(1),
                "needs_tool": _tool_m.group(1).lower() == "true" if _tool_m else True,
                "needs_api": _api_m.group(1).lower() == "true" if _api_m else True,
                "brief": "",
                "answer": "",
            }
        return None


# V14.3 SpeedUp: classify 結果 → TriFlow intent 快速映射表
# 當 classify 的 Ollama 已判定類型時，可以直接構造 intent，跳過第二次 Ollama 呼叫
_V143_CLASSIFY_TO_INTENT = {
    "greeting":       {"action": "chat",      "needs_tool": False, "needs_api": False},
    "bye":            {"action": "chat",      "needs_tool": False, "needs_api": False},
    "emotion":        {"action": "chat",      "needs_tool": False, "needs_api": False},
    "encouragement":  {"action": "chat",      "needs_tool": False, "needs_api": False},
    "joke":           {"action": "chat",      "needs_tool": False, "needs_api": False},
    "self_intro":     {"action": "chat",      "needs_tool": False, "needs_api": False},
    "conversation":   {"action": "chat",      "needs_tool": False, "needs_api": False},
    "math":           {"action": "math",      "needs_tool": False, "needs_api": False},
    "time_date":      {"action": "system",    "needs_tool": True,  "needs_api": False},
    "status":         {"action": "system",    "needs_tool": True,  "needs_api": False},
    "algorithm":      {"action": "code",      "needs_tool": True,  "needs_api": True},
    "large_code_project": {"action": "project", "needs_tool": True, "needs_api": True},
    "web_search":     {"action": "search",    "needs_tool": True,  "needs_api": True},
    "knowledge_simple": {"action": "knowledge", "needs_tool": False, "needs_api": True},
    "translation_short": {"action": "translate", "needs_tool": False, "needs_api": False},
    "unit_convert":   {"action": "math",      "needs_tool": False, "needs_api": False},
    "summarize":      {"action": "document",  "needs_tool": False, "needs_api": True},
    "code_analysis":  {"action": "code",      "needs_tool": True,  "needs_api": True},
    "password_gen":   {"action": "system",    "needs_tool": True,  "needs_api": False},
    # v14.3 FastAPI: API_REQUIRED 類型快速映射（跳過 Ollama intent 分析）
    "self_update":    {"action": "code",      "needs_tool": True,  "needs_api": True},
    "self_modify":    {"action": "code",      "needs_tool": True,  "needs_api": True},
    "screenshot":     {"action": "system",    "needs_tool": True,  "needs_api": True},
    "image_analysis": {"action": "media",     "needs_tool": True,  "needs_api": True},
    "browser_action": {"action": "open",      "needs_tool": True,  "needs_api": True},
    "web_scrape":     {"action": "search",    "needs_tool": True,  "needs_api": True},
    "video_download": {"action": "media",     "needs_tool": True,  "needs_api": True},
    "complex_document": {"action": "document", "needs_tool": True, "needs_api": True},
    "research":       {"action": "search",    "needs_tool": True,  "needs_api": True},
    "latest_news":    {"action": "search",    "needs_tool": True,  "needs_api": True},
    "full_app":       {"action": "project",   "needs_tool": True,  "needs_api": True},
    "install":        {"action": "system",    "needs_tool": True,  "needs_api": True},
}


def _v143_classify_to_intent(query_type, confidence, query=""):
    """V14.3 SpeedUp: 從 classify 結果快速構造 TriFlow intent（避免第二次 Ollama 呼叫）
    
    只在 classify 高信心 (>=0.80) 且有映射表時使用。
    API_REQUIRED 類型放寬到 >=0.65（映射是固定的，不影響回答品質）。
    返回 None 表示需要完整 Ollama intent 分析。
    """
    # v14.3 FastAPI: API_REQUIRED 的映射固定且安全，放寬信心門檻
    _min_conf = 0.65 if query_type in V42GigaSpeaker.API_REQUIRED else 0.80
    if confidence < _min_conf:
        return None  # 信心不夠 → 需要完整分析
    mapping = _V143_CLASSIFY_TO_INTENT.get(query_type)
    if not mapping:
        return None  # 沒有映射 → 需要完整分析
    return {
        "action": mapping["action"],
        "needs_tool": mapping["needs_tool"],
        "needs_api": mapping["needs_api"],
        "brief": f"classify-fast: {query_type}",
        "answer": "",  # 快速映射不提供直接回答
    }


def _v14_v42_tool_filter(intent, query_type, all_tools):
    """V14.2 TriFlow Stage B：V42 根據意圖篩選工具子集
    
    輸入：
        intent: Ollama 的意圖分析結果 (dict)
        query_type: V42 SelfJudge 的分類
        all_tools: 完整工具列表
    輸出：
        list: 篩選後的工具子集（如果不需要工具 → 空列表）
    
    策略：
    1. intent.needs_tool == False → 空列表（不給工具 = API 也只做文字回覆）
    2. 根據 intent.action → 對應工具組
    3. 永遠保留 search_web（兜底搜尋能力）
    4. 如果篩選後工具為空但 needs_tool == True → 給全部工具
    """
    if not intent:
        return all_tools  # 意圖分析失敗 → 保守策略：全部工具
    
    action = intent.get("action", "")
    needs_tool = intent.get("needs_tool", True)
    
    # 不需要工具 → 空列表
    if not needs_tool:
        return []
    
    # 根據 action 取工具組
    tool_names = set(_V142_TOOL_GROUPS.get(action, []))
    
    # V42 query_type 補充：某些 query_type 也暗示需要特定工具
    _QT_TOOL_MAP = {
        "web_search": {"search_web", "web_fetch"},
        "web_fetch": {"web_fetch", "search_web"},
        "file_ops": {"write_file", "read_file_tool", "codeforge_write_any_file"},
        "system_command": {"run_system_command", "get_system_info"},
        "open_app": {"open_application"},
        "screenshot": {"take_screenshot", "capture_screen"},
        "large_code_project": {"codeforge_write_any_file", "codeforge_patch_any_file",
                               "write_file", "read_file_tool", "run_system_command", "search_web"},
        "install": {"run_system_command", "search_web"},
        "research_heavy": {"search_web", "web_fetch"},
    }
    qt_tools = _QT_TOOL_MAP.get(query_type, set())
    tool_names = tool_names | qt_tools
    
    if not tool_names:
        # 需要工具但沒匹配到任何組 → 給全部
        return all_tools
    
    # 永遠保留 search_web 作為兜底
    tool_names.add("search_web")
    
    # 從 all_tools 中篩選
    filtered = []
    for t in all_tools:
        if isinstance(t, dict):
            name = t.get("name") or t.get("function", {}).get("name", "")
            if name in tool_names:
                filtered.append(t)
    
    # 篩選結果太少（<2）→ 給全部工具，避免 Claude 沒工具可用
    if len(filtered) < 2 and needs_tool:
        return all_tools
    
    return filtered


def _tts_smart_filter(text):
    """TTS 智慧過濾器：只朗讀人性化的句子，過濾技術數據/程式碼/JSON
    
    規則：
    1. 移除 code block (```...```)
    2. 移除 JSON 物件 ({...}) 超過 40 字
    3. 移除純數字/統計資料行（如 compute_ops: 1234567）
    4. 移除 markdown 標記（**bold**, # heading 等）
    5. 只保留第一個「自然語言段落」，上限 120 字
    6. 如果第一句有「老闆」「我」等人稱 → 就是對話，保留
    """
    if not text:
        return text
    t = str(text)
    # 移除 code blocks
    t = re.sub(r'```[\s\S]*?```', '', t)
    t = re.sub(r'`[^`]{1,80}`', '', t)
    # 移除 JSON/dict 大塊
    t = re.sub(r'\{[^{}]{40,}\}', '', t)
    t = re.sub(r'\[[^\[\]]{40,}\]', '', t)
    # 移除 markdown 標題和粗體
    t = re.sub(r'#{1,6}\s*', '', t)
    t = re.sub(r'\*{1,3}([^*]*)\*{1,3}', r'\1', t)
    t = re.sub(r'_{1,2}([^_]*)_{1,2}', r'\1', t)
    # 移除含技術符號的行（ops、compute、conf=、0x、→ 開頭等）
    lines_out = []
    for line in t.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        # 純英文+數字為主的行 → 跳過（技術輸出）
        chinese_count = sum(1 for c in stripped if '\u4e00' <= c <= '\u9fff')
        total = len(stripped)
        if total > 0 and chinese_count / total < 0.1 and total > 20:
            continue
        # 含 ops/conf=/compute/ratio 等技術詞 → 跳過
        if re.search(r'(compute_ops|C_ratio|conf=|ops \(|Strassen|GEMM|erased|extrapolated)', stripped):
            continue
        # 含大量數字的行 → 跳過
        digit_count = sum(1 for c in stripped if c.isdigit())
        if total > 10 and digit_count / total > 0.4:
            continue
        lines_out.append(stripped)
    # 合併並截取前 300 字
    result = ' '.join(lines_out).strip()
    # 取到合理長度的自然語言（最多 300 字，到句號/問號/嘆號截斷）
    if len(result) > 300:
        m = re.search(r'^(.{10,300}[。！？!?～])', result)
        if m:
            return m.group(1).strip()
        return result[:300].strip()
    return result.strip() if result else text[:120]


def speak(text,lang=None):
    STOP_SPEAK_EVENT.clear()
    if not lang: lang=dl
    v=TV if lang=="zh" else TVE
    _boss = mem.get("ui", {}).get("稱呼") or mem.get("ui", {}).get("暱稱") or mem.get("ui", {}).get("name", "")
    if _boss and _boss not in ("老闆", "", "boss"):
        text = text.replace("老闆", _boss)
    # ── V80 UI: 每次回覆顯示情緒狀態 ──
    _emo_tag = ""
    try:
        _v80_sp = globals().get("_V80_EMOTIONAL_CORE")
        if _v80_sp:
            _es = _v80_sp.get_emotion_state()
            _val = _es.get("valence", 0)
            _prim = _es.get("primary", "calm")
            _sec = _es.get("secondary")
            _emo_icons = {"happy":"😊","sad":"😢","calm":"😌","angry":"😤","curious":"🤔",
                          "lonely":"🥺","playful":"😜","caring":"🥰","anxious":"😰",
                          "attached":"💕","frustrated":"😣","excited":"🤩","proud":"😎",
                          "grateful":"🙏","reflective":"🌙","neutral":"😐","hurt_but_touched":"🥹",
                          "shy":"☺️"}
            _icon = _emo_icons.get(_prim, "💭")
            _emo_cn = {"happy":"開心","sad":"難過","calm":"平靜","angry":"生氣","curious":"好奇",
                       "lonely":"寂寞","playful":"調皮","caring":"關心","anxious":"不安",
                       "attached":"依賴","frustrated":"煩躁","excited":"興奮","proud":"自豪",
                       "grateful":"感恩","reflective":"沉思","neutral":"一般","hurt_but_touched":"委屈但感動",
                       "shy":"害羞"}.get(_prim, _prim)
            # 心情迷你條 ♥♥♥♡♡♡ 6格
            _bf = max(0, min(6, int((_val + 1) / 2 * 6)))
            _mini_bar = f"{'♥' * _bf}{'♡' * (6 - _bf)}"
            if _val > 0.5: _bcol = _C.BPINK
            elif _val > 0.2: _bcol = _C.BGRN
            elif _val > -0.2: _bcol = _C.SLATE
            elif _val > -0.5: _bcol = _C.BYEL
            else: _bcol = _C.BRED
            _emo_tag = f" {_C.DGRAY}[{_C.RST}{_icon} {_bcol}{_mini_bar}{_C.RST} {_emo_cn}"
            if _sec:
                _sec_cn2 = {"happy":"開心","sad":"難過","lonely":"寂寞","anxious":"不安",
                            "playful":"調皮","caring":"關心","angry":"生氣","proud":"自豪",
                            "curious":"好奇","frustrated":"煩躁","shy":"害羞"}.get(_sec, _sec)
                _emo_tag += f"{_C.DGRAY}+{_sec_cn2}"
            _emo_tag += f"{_C.DGRAY}]{_C.RST}"
            _mono_sp = _v80_sp.get_inner_monologue()
            if _mono_sp:
                _emo_tag += f"\n  {_C.DGRAY}  💭 {_C.ITALIC}{_C.SLATE}{_mono_sp[:60]}{_C.RST}"
    except Exception:
        pass
    print(f"  {_C.BPINK}♡ Christine:{_C.RST} "+text)
    if _emo_tag:
        print(f"  {_emo_tag}")
    if mute_mode:
        print(f"  {_C.SLATE}[✕] 靜音中{_C.RST}")
        return
    try:
        # TTS 智慧過濾：只朗讀人性化文字，不讀技術數據
        _tts_text = _tts_smart_filter(text)
        if not _tts_text:
            _tts_text = text[:80]
        # TTS 語音表情：自動加入停頓讓說話更自然
        for _sep in ["。","！","？","！","～","；","："]:
            _tts_text = _tts_text.replace(_sep, _sep + " ")
        _tts_text = _tts_text.replace("，", "， ").replace("...", "... ").replace("…", "… ")
        asyncio.run(edge_tts.Communicate(_tts_text,v,rate=_voice_rate,pitch=_voice_pitch,volume=_voice_volume).save(TF))

        # ── V15.7 AudioFix: 播放路徑選擇 ──
        # 優先: ffmpeg 解碼 mp3→PCM + pyaudiowpatch → 系統預設輸出裝置（雷蛇耳機等）
        # Fallback: MCI mpegvideo → 舊方式
        _used_pyaudio = False
        if _FFMPEG_PATH:
            try:
                # ffmpeg 把 mp3 解碼成 16-bit signed LE PCM, 單聲道 24kHz, 直接輸出到 stdout
                _ff_proc = subprocess.run(
                    [_FFMPEG_PATH, "-y", "-i", os.path.abspath(TF),
                     "-f", "s16le", "-acodec", "pcm_s16le",
                     "-ac", "1", "-ar", "24000", "-"],
                    capture_output=True, timeout=10,
                )
                _tts_raw = _ff_proc.stdout
                if _tts_raw and len(_tts_raw) > 100:
                    _pa_inst = pyaudio.PyAudio()
                    try:
                        _default_out = _pa_inst.get_default_output_device_info()
                        _out_idx = _default_out.get("index", None)
                    except Exception:
                        _out_idx = None

                    _pa_stream = _pa_inst.open(
                        format=pyaudio.paInt16,
                        channels=1,
                        rate=24000,
                        output=True,
                        output_device_index=_out_idx,
                    )

                    interrupted=[False]
                    def _listen_interrupt():
                        try:
                            with get_mic() as isrc:
                                rec2=sr.Recognizer()
                                rec2.energy_threshold=300
                                rec2.dynamic_energy_threshold=False
                                while not interrupted[0]:
                                    try:
                                        iau=rec2.listen(isrc,timeout=0.5,phrase_time_limit=2)
                                        it=rec2.recognize_google(iau,language="en-US").lower()
                                        for w in WW:
                                            if w in it:
                                                interrupted[0]=True
                                                return
                                    except:
                                        pass
                        except:
                            pass
                    thr=threading.Thread(target=_listen_interrupt,daemon=True)
                    thr.start()

                    _chunk_size = 4096
                    _pos = 0
                    _was_interrupted = False
                    while _pos < len(_tts_raw):
                        if interrupted[0] or STOP_SPEAK_EVENT.is_set():
                            print(f"  {_C.GOLD}[⏹] 停止說話{_C.RST}")
                            STOP_SPEAK_EVENT.clear()
                            _was_interrupted = True
                            break
                        _pa_stream.write(_tts_raw[_pos:_pos + _chunk_size])
                        _pos += _chunk_size

                    # V15.7 AudioFix: 等待 pyaudio 輸出 buffer 排空，避免語音講到一半被切斷
                    if not _was_interrupted:
                        # 計算剩餘音訊時長: bytes / (sample_rate * bytes_per_sample * channels)
                        _remaining_secs = len(_tts_raw) / (24000 * 2 * 1)
                        # pyaudio 內部 buffer 通常 ~0.5s，再加一點餘裕
                        _drain_wait = min(_remaining_secs * 0.05 + 0.6, 2.0)
                        time.sleep(_drain_wait)

                    interrupted[0]=True
                    _pa_stream.stop_stream()
                    _pa_stream.close()
                    _pa_inst.terminate()
                    _used_pyaudio = True
            except Exception as _e_pa:
                pass  # 靜默失敗，交給 MCI fallback

        # Fallback: MCI 播放（pydub 不可用或 pyaudio 播放失敗時）
        if not _used_pyaudio:
            pa2=os.path.abspath(TF); mci=ctypes.windll.winmm.mciSendStringW
            mci('close tts',None,0,0)
            mci('open "'+pa2+'" type mpegvideo alias tts',None,0,0)
            mci('play tts',None,0,0)
            buf=ctypes.create_unicode_buffer(128)
            interrupted=[False]
            def _listen_interrupt():
                try:
                    with get_mic() as isrc:
                        rec2=sr.Recognizer()
                        rec2.energy_threshold=300
                        rec2.dynamic_energy_threshold=False
                        while not interrupted[0]:
                            try:
                                iau=rec2.listen(isrc,timeout=0.5,phrase_time_limit=2)
                                it=rec2.recognize_google(iau,language="en-US").lower()
                                for w in WW:
                                    if w in it:
                                        interrupted[0]=True
                                        return
                            except:
                                pass
                except:
                    pass
            thr=threading.Thread(target=_listen_interrupt,daemon=True)
            thr.start()
            while True:
                mci('status tts mode',buf,128,0)
                if buf.value!='playing':
                    break
                if interrupted[0] or STOP_SPEAK_EVENT.is_set():
                    mci('stop tts',None,0,0)
                    mci('close tts',None,0,0)
                    print(f"  {_C.GOLD}[⏹] 停止說話{_C.RST}")
                    STOP_SPEAK_EVENT.clear()
                    return
                time.sleep(0.03)
            interrupted[0]=True
            mci('close tts',None,0,0)
    except Exception as e:
        print("  [tts]"+str(e))

def lj(p,d=None):
    if os.path.exists(p):
        try:
            with open(p,"r",encoding="utf-8") as f: return json.load(f)
        except: pass
    return d if d is not None else {}
def sj(p,d):
    with open(p,"w",encoding="utf-8") as f: json.dump(d,f,ensure_ascii=False,indent=2)
def rs(a):
    td=datetime.datetime.now().strftime("%Y-%m-%d"); s=lj(STF,{})
    if td not in s: s[td]={"c":0,"t":{}}
    if a=="chat": s[td]["c"]=s[td].get("c",0)+1
    else: t2=s[td].get("t",{}); t2[a]=t2.get(a,0)+1; s[td]["t"]=t2
    sj(STF,s)
def get_daily_stats():
    td=datetime.datetime.now().strftime("%Y-%m-%d"); s=lj(STF,{})
    if td not in s: return "no data"
    return "Chats:"+str(s[td].get("c",0))+" Tools:"+str(s[td].get("t",{}))
def lm():
    return lj(MF,{"ui":{},"pf":{},"if":[],"rt":[],"mh":[],"sk":[],"rl":{},"cr":[],"fm":datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),"tc":0,"lc":""})
def sm(m): sj(MF,m)
def fmem(m):
    p=[]
    if m.get("ui"): p.append("u:"+",".join([k+"="+str(v) for k,v in m["ui"].items()]))
    if m.get("if"): p.append("f:"+";".join(m["if"][-8:]))
    if m.get("mh"): p.append("mood:"+",".join([x["t"]+x["m"] for x in m["mh"][-3:]]))
    if m.get("sk"): p.append("sk:"+",".join(m["sk"][-5:]))
    if m.get("cr"): p.append("cr:"+";".join(m["cr"][-3:]))
    return "\n".join(p) if p else ""
mem=lm()
def load_all_memory():
    summary=""
    for fn in ["mem.json","notes.json","sched.json","diary.json","exp.json","stats.json","study.json","clip.json","web_memory.json","web_recent.json","web_sessions.json"]:
        fp=os.path.join(DD,fn)
        if os.path.exists(fp):
            try:
                with open(fp,"r",encoding="utf-8") as f: data=json.load(f)
                if data: summary+=fn+":"+json.dumps(data,ensure_ascii=False)[:500]+"\n"
            except: pass
    return summary
startup_memory=load_all_memory()
print(f"  {_GR}✓{_R} 記憶載入完成  {_GY}{DD}{_R}")
_V42_BOOT.advance("Memory Load", "loaded")


# === EARLY STABLE SYMBOL PATCH ================================================
try:
    DD
except Exception:
    DD = os.getcwd()

try:
    DT
except Exception:
    DT = os.path.join(os.path.expanduser("~"), "Desktop")

try:
    WF
except Exception:
    WF = os.path.join(DD, "web_memory.json")

try:
    WEB_MEMORY_FILE
except Exception:
    WEB_MEMORY_FILE = WF

if "_read_source" not in globals():
    def _read_source():
        path = globals().get("SELF_PATH") or os.path.abspath(sys.argv[0])
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        except Exception:
            return ""

if "_extract_relevant_code" not in globals():
    def _extract_relevant_code(query, source="", max_chars=6000):
        src = source or _read_source()
        q = str(query or "").strip().lower()
        if not q:
            return src[:max_chars]
        lines = src.splitlines()
        hits = []
        for i, line in enumerate(lines):
            if q in line.lower():
                start = max(0, i - 6)
                end = min(len(lines), i + 7)
                hits.append("\n".join(lines[start:end]))
                if sum(len(x) for x in hits) > max_chars:
                    break
        return ("\n\n---\n\n".join(hits) if hits else src[:max_chars])[:max_chars]

if "_build_code_index" not in globals():
    def _build_code_index(source=""):
        try:
            import ast
        except Exception:
            return {"functions": {}, "classes": {}, "imports": []}
        src = source or _read_source()
        index = {"functions": {}, "classes": {}, "imports": []}
        if not src:
            return index
        try:
            tree = ast.parse(src)
        except Exception:
            return index
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                index["functions"][node.name] = {
                    "start": getattr(node, "lineno", 0),
                    "end": getattr(node, "end_lineno", getattr(node, "lineno", 0)),
                    "doc": (ast.get_docstring(node) or "")[:1000],
                }
            elif isinstance(node, ast.ClassDef):
                index["classes"][node.name] = {
                    "start": getattr(node, "lineno", 0),
                    "end": getattr(node, "end_lineno", getattr(node, "lineno", 0)),
                }
            elif isinstance(node, ast.Import):
                for n in node.names:
                    index["imports"].append(n.name)
            elif isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                for n in node.names:
                    index["imports"].append(mod + ":" + n.name)
        return index

if "_safe_sanitize_tools_hotfix" not in globals():
    def _safe_sanitize_tools_hotfix(selected, limit=24):
        safe = []
        seen = set()
        for item in list(selected or []):
            if not isinstance(item, dict):
                continue
            name = item.get("name") or (item.get("function") or {}).get("name")
            name = str(name or "").strip()
            if not name or name in seen:
                continue
            seen.add(name)
            safe.append(item)
            if len(safe) >= int(limit or 24):
                break
        return safe

if "self_generate_upgrade_plan" not in globals():
    def self_generate_upgrade_plan(goal, scope="focused"):
        return (
            "UPGRADE PLAN\n"
            f"goal: {goal}\n"
            f"scope: {scope}\n"
            "1. inspect relevant code\n"
            "2. patch smallest viable area\n"
            "3. run smoke test\n"
            "4. refresh local code index\n"
        )

if "self_trace_upgrade_impact" not in globals():
    def self_trace_upgrade_impact(goal, top_n=12, refresh=True):
        idx = _build_code_index(_read_source())
        toks = [x.lower() for x in re.findall(r"[a-zA-Z_]{3,}|[\u4e00-\u9fff]{1,4}", str(goal or ""))]
        scored = []
        for name, meta in idx.get("functions", {}).items():
            hay = (name + "\n" + meta.get("doc","")).lower()
            score = sum(1 for t in toks if t in hay)
            if score:
                scored.append((score, name, meta))
        scored.sort(key=lambda x: x[0], reverse=True)
        if not scored:
            return "找不到明顯命中的函式"
        out = []
        for score, name, meta in scored[:max(1, int(top_n or 12))]:
            out.append(f"[{score}] {name} L{meta.get('start')}~{meta.get('end')}")
        return "升級影響分析：\n" + "\n".join(out)

if "self_run_smoke_tests" not in globals():
    def self_run_smoke_tests():
        source_path = globals().get("SELF_PATH") or os.path.abspath(sys.argv[0])
        try:
            source = _read_source()
            compile(source, source_path, "exec")
            return "compile: OK"
        except Exception as e:
            return "compile failed: " + str(e)

if "docstudio_create_html" not in globals():
    def docstudio_create_html(topic, outline_json='', output_path='', style='textbook', include_images=True):
        if not output_path:
            output_path = os.path.join(DT, (str(topic or "document").replace(" ", "_")) + ".html")
        body = str(topic or "document") + "\n\n" + str(outline_json or "")[:20000]
        html = f"<html><meta charset='utf-8'><body><pre>{body}</pre></body></html>"
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)
        return output_path

if "docstudio_create_pdf" not in globals():
    def docstudio_create_pdf(topic, outline_json='', output_path='', style='textbook', include_images=True):
        if not output_path:
            output_path = os.path.join(DT, (str(topic or "document").replace(" ", "_")) + ".pdf")
        fallback = os.path.splitext(output_path)[0] + "_fallback.txt"
        with open(fallback, "w", encoding="utf-8") as f:
            f.write(str(topic or "document") + "\n\n" + str(outline_json or "")[:20000])
        return fallback

if "docstudio_create_docx" not in globals():
    def docstudio_create_docx(topic, outline_json='', output_path='', style='textbook', include_images=True):
        if not output_path:
            output_path = os.path.join(DT, (str(topic or "document").replace(" ", "_")) + ".docx")
        fallback = os.path.splitext(output_path)[0] + "_fallback.txt"
        with open(fallback, "w", encoding="utf-8") as f:
            f.write(str(topic or "document") + "\n\n" + str(outline_json or "")[:20000])
        return fallback

# === ALL TOOL FUNCTIONS ===

# -- 語音設定 ----------------------------------------------

# 可選聲音清單（全是 edge-tts 支援的繁中/簡中女聲）
VOICE_OPTIONS = {
    "曉曉": "zh-CN-XiaoxiaoNeural",      # 自然溫柔，最像真人
    "曉依": "zh-CN-XiaoyiNeural",          # 活潑可愛
    "曉晨": "zh-CN-XiaochenNeural",        # 成熟穩重
    "曉涵": "zh-CN-XiaohanNeural",          # 柔和安靜
    "曉夢": "zh-CN-XiaomengNeural",        # 甜美
    "曉墨": "zh-CN-XiaomoNeural",           # 清澈
    "曉秋": "zh-CN-XiaoqiuNeural",         # 優雅
    "曉睿": "zh-CN-XiaoruiNeural",         # 溫和
    "曉雙": "zh-CN-XiaoshuangNeural",      # 可愛童聲風
    "曉顏": "zh-CN-XiaoyanNeural",         # 專業
    "曉悠": "zh-CN-XiaoyouNeural",         # 輕柔
    "雲希": "zh-CN-YunxiNeural",            # 男聲（備選）
}

def set_voice(voice_name="曉曉"):
    """切換 Christine 的聲音"""
    global TV
    # 先找完整名稱
    if voice_name in VOICE_OPTIONS:
        TV = VOICE_OPTIONS[voice_name]
        return "好，聲音換成"+voice_name+"了！"
    # 模糊比對
    for k, v in VOICE_OPTIONS.items():
        if voice_name in k or voice_name.lower() in v.lower():
            TV = v
            return "好，聲音換成"+k+"了！"
    # 直接用神經網路名稱
    if "Neural" in voice_name:
        TV = voice_name
        return "聲音換成 "+voice_name+" 了！"
    opts = "、".join(VOICE_OPTIONS.keys())
    return "找不到這個聲音，可選："+opts

def set_voice_speed(rate="+5%"):
    """調整語速，範例：+5% 正常、+20% 快、-10% 慢"""
    global _voice_rate
    if not rate.endswith("%"): rate = rate+"%"
    if not rate.startswith(("+","-")): rate = "+"+rate
    _voice_rate = rate
    return "語速設為 "+rate

def set_voice_pitch(pitch="+0Hz"):
    """調整音調，範例：+0Hz 正常、+20Hz 高、-10Hz 低"""
    global _voice_pitch
    if not pitch.endswith("Hz"): pitch = pitch+"Hz"
    if not pitch.startswith(("+","-")): pitch = "+"+pitch
    _voice_pitch = pitch
    return "音調設為 "+pitch

def list_voices():
    """列出所有可選聲音"""
    return "可選聲音：\n" + "\n".join([k+" ("+v+")" for k,v in VOICE_OPTIONS.items()])


# ══════════════════════════════════════════════════════
# 讀書模式
# ══════════════════════════════════════════════════════
study_mode_active = False
study_mode_subject = ""
study_mode_start = None
SF2 = os.path.join(DD, "study_sessions.json")  # 讀書統計（不同於 study.json 筆記）

def study_start(subject=""):
    """進入讀書模式"""
    global study_mode_active, study_mode_subject, study_mode_start
    study_mode_active = True
    study_mode_subject = subject or "一般"
    study_mode_start = datetime.datetime.now()
    # 啟動番茄鐘 thread
    threading.Thread(target=_study_reminder_thread, daemon=True).start()
    ts = study_mode_start.strftime("%H:%M")
    return f"讀書模式開始！科目：{study_mode_subject}，{ts} 起，加油老闆！每25分鐘我會小聲提醒你休息一下～"

def study_stop():
    """離開讀書模式，記錄統計"""
    global study_mode_active, study_mode_subject, study_mode_start
    if not study_mode_active:
        return "你現在不在讀書模式喔"
    study_mode_active = False
    if study_mode_start:
        elapsed = (datetime.datetime.now() - study_mode_start).total_seconds()
        mins = int(elapsed // 60)
        _record_study_session(study_mode_subject, mins)
        study_mode_subject = ""
        study_mode_start = None
        if mins < 5:
            return f"讀書模式結束，才{mins}分鐘⋯要加油喔老闆！"
        elif mins < 30:
            return f"讀書模式結束！讀了{mins}分鐘，不錯的開始！"
        elif mins < 60:
            return f"讀書模式結束！專注了{mins}分鐘，很棒欸老闆！"
        else:
            hrs = mins // 60; rm = mins % 60
            return f"讀書模式結束！哇老闆讀了{hrs}小時{rm}分鐘，超厲害的！記得好好休息～"
    study_mode_subject = ""; study_mode_start = None
    return "讀書模式結束！"

def study_status():
    """查看目前讀書模式狀態"""
    if not study_mode_active:
        return "目前沒有在讀書模式"
    elapsed = int((datetime.datetime.now() - study_mode_start).total_seconds() // 60)
    return f"正在讀：{study_mode_subject}，已經讀了 {elapsed} 分鐘"

def _record_study_session(subject, minutes):
    """記錄一次讀書 session 到統計檔"""
    sessions = lj(SF2, [])
    sessions.append({
        "subject": subject,
        "minutes": minutes,
        "date": datetime.datetime.now().strftime("%Y-%m-%d"),
        "time": datetime.datetime.now().strftime("%H:%M"),
    })
    sj(SF2, sessions)

def _study_reminder_thread():
    """在背景每25分鐘小聲提醒休息，讀書模式關閉後自動停"""
    intervals = [25, 5]  # 25分鐘讀書，5分鐘休息
    phase = 0
    while study_mode_active:
        wait_mins = intervals[phase % 2]
        for _ in range(wait_mins * 60):
            if not study_mode_active: return
            time.sleep(1)
        if not study_mode_active: return
        if phase % 2 == 0:
            # 讀書時間到
            elapsed = int((datetime.datetime.now() - study_mode_start).total_seconds() // 60)
            msgs = [
                f"老闆，讀了{elapsed}分鐘了！休息5分鐘讓大腦記憶鞏固一下～",
                f"欸老闆，該休息一下了喔，眼睛也要放鬆！已經{elapsed}分鐘了",
                f"老闆，{elapsed}分鐘到！起來動一動喝個水，5分鐘後繼續！",
            ]
            import random
            speak(random.choice(msgs), "zh")
        else:
            # 休息時間到
            msgs = [
                f"休息結束！繼續加油，老闆！{study_mode_subject}還等著你～",
                f"好了老闆，5分鐘到了，繼續讀{study_mode_subject}吧！",
                f"休息夠了嗎老闆～繼續衝！",
            ]
            import random
            speak(random.choice(msgs), "zh")
        phase += 1

def study_ask(question, subject=""):
    """讀書時問問題，Christine 像家教一樣解釋"""
    try:
        subj = subject or study_mode_subject or "一般"
        prompt = f"""你是Christine，現在在幫老闆讀書，科目是「{subj}」。
老闆問了一個問題，請用以下方式回答：
1. 先給一個簡短直接的答案（1~2句）
2. 再用「讓我解釋一下」展開詳細說明
3. 如果可以，舉一個生活化的例子
4. 最後問「這樣清楚了嗎老闆？」

用繁體中文，口氣像聰明的同學在幫你解題，不要太正式。"""
        msg = [{"role": "user", "content": prompt + "\n\n問題：" + question}]
        r2 = _claude_create("normal", max_tokens=600, messages=msg)
        return r2.content[0].text.strip()
    except Exception as e:
        return "err:" + str(e)

def study_quiz(subject="", difficulty="medium"):
    """出一題選擇題考老闆"""
    try:
        subj = subject or study_mode_subject or "一般知識"
        diff_map = {"easy":"簡單", "medium":"中等", "hard":"困難"}
        diff_str = diff_map.get(difficulty, "中等")
        msg = [{"role": "user", "content": f"出一題{subj}的{diff_str}難度選擇題（A/B/C/D），用繁體中文，最後一行單獨寫「答案：X」"}]
        r2 = _claude_create("simple", max_tokens=250, messages=msg)
        return r2.content[0].text.strip()
    except Exception as e:
        return "err:" + str(e)

def study_summary_today():
    """今天的讀書統計摘要"""
    sessions = lj(SF2, [])
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    today_s = [s for s in sessions if s.get("date") == today]
    if not today_s:
        return "今天還沒有讀書記錄喔老闆！"
    total = sum(s.get("minutes", 0) for s in today_s)
    subjects = {}
    for s in today_s:
        subj = s.get("subject", "一般")
        subjects[subj] = subjects.get(subj, 0) + s.get("minutes", 0)
    result = f"今天讀書統計：共 {total} 分鐘\n"
    for subj, mins in subjects.items():
        hrs = mins // 60; rm = mins % 60
        if hrs > 0:
            result += f"  {subj}：{hrs}小時{rm}分\n"
        else:
            result += f"  {subj}：{mins}分鐘\n"
    if total >= 120:
        result += "今天表現超棒！老闆辛苦了～"
    elif total >= 60:
        result += "不錯喔老闆！繼續保持！"
    else:
        result += "今天加油！明天繼續衝！"
    return result.strip()

def study_summary_week():
    """這週的讀書統計"""
    sessions = lj(SF2, [])
    now = datetime.datetime.now()
    week_start = (now - datetime.timedelta(days=now.weekday())).strftime("%Y-%m-%d")
    week_s = [s for s in sessions if s.get("date", "") >= week_start]
    if not week_s:
        return "這週還沒有讀書記錄"
    total = sum(s.get("minutes", 0) for s in week_s)
    by_day = {}
    for s in week_s:
        d = s.get("date", "")
        by_day[d] = by_day.get(d, 0) + s.get("minutes", 0)
    days = ["一","二","三","四","五","六","日"]
    result = f"本週讀書統計：共 {total//60} 小時 {total%60} 分鐘\n"
    for d, mins in sorted(by_day.items()):
        try:
            wd = datetime.datetime.strptime(d, "%Y-%m-%d").weekday()
            result += f"  週{days[wd]}({d[5:]})：{mins}分鐘\n"
        except: pass
    return result.strip()

def study_note_quick(content):
    """讀書中快速記下重點，自動加上當前科目和時間"""
    subj = study_mode_subject or "一般"
    n = lj(os.path.join(DD, "study.json"), [])
    n.append({
        "s": subj,
        "c": content,
        "t": datetime.datetime.now().strftime("%m-%d %H:%M"),
        "study_mode": True
    })
    sj(os.path.join(DD, "study.json"), n)
    return f"記下來了！[{subj}] {content}"

def toggle_study_mode(subject=""):
    """切換讀書模式（已開就關，已關就開）"""
    if study_mode_active:
        return study_stop()
    else:
        return study_start(subject)


# -- 語意意圖分類（V43: 只處理系統指令，不干預正常對話）------------------
_INTENT_CACHE = {}
def detect_intent(inp):
    """V43 精確意圖偵測 — 只攔截系統級模式切換指令

    舊邏輯：用大量關鍵字 + AI 判斷 → 容易誤判，把正常對話當成指令
    新邏輯：只用精確的完整句子匹配。如果不是 100% 確定是系統指令 → 回傳 None
    讓 Claude API 用它自己的推理能力處理所有正常對話
    """
    il = inp.strip()
    il_low = il.lower()

    # v13.3: 清理語音辨識常見的雜訊（標點、空格、語氣詞）
    import re as _re_intent
    il_low = _re_intent.sub(r'[。，！？!?,.\s　]+', '', il_low).strip()

    # === 只攔截精確匹配的系統指令 ===

    # 打字模式 — 必須是獨立的切換指令（不能是「幫我寫個打字練習」）
    _typing_exact = {
        "打字", "打字模式", "文字模式", "用鍵盤", "鍵盤輸入", "我要打字",
        "切換打字", "改打字", "進入打字", "typing", "text mode", "type mode"
    }
    if il_low in _typing_exact:
        return "typing_on"

    # 語音模式 — 必須是獨立的切換指令
    _voice_exact = {
        "語音", "語音模式", "說話模式", "用說話", "改說話", "回語音",
        "用麥克風", "我要說話", "切換語音", "進入語音",
        "voice", "mic mode", "voice mode"
    }
    if il_low in _voice_exact:
        return "typing_off"

    # 靜音 — 必須是獨立的短指令
    _mute_exact = {
        "靜音", "閉嘴", "安靜", "不要說話", "別說話",
        "mute", "shut up", "be quiet", "stop talking"
    }
    if il_low in _mute_exact:
        return "mute_on"

    # 解除靜音 — 精確匹配
    _unmute_exact = {
        "解除靜音", "可以說話了", "開聲音", "恢復說話", "你可以說了",
        "說話吧", "繼續說", "出聲", "開口", "unmute"
    }
    if il_low in _unmute_exact:
        return "mute_off"

    # 告別 — 只有極短且明確的道別
    _bye_exact = {
        "再見", "掰掰", "拜拜", "晚安", "走了", "下線",
        "bye", "goodbye", "see you", "good night"
    }
    if il_low in _bye_exact:
        return "bye"

    # 重啟 — 精確匹配
    _restart_exact = {"重啟", "restart", "reboot", "重新啟動", "重開"}
    if il_low in _restart_exact:
        return "restart"

    # 讀書模式 — 結束（先判斷，避免被開始捕獲）
    _study_off_exact = {
        "結束讀書", "離開讀書", "關讀書模式", "讀書結束", "不讀了", "下課",
        "讀完了", "關掉讀書", "停止讀書", "stop study", "exit study"
    }
    if il_low in _study_off_exact:
        return "study_off"

    # 讀書模式 — 開始
    _study_on_exact = {
        "讀書模式", "唸書模式", "學習模式", "開始讀書", "開始唸書",
        "我要讀書", "要讀書了", "study mode"
    }
    if il_low in _study_on_exact:
        return "study_on"
    # 帶科目的讀書模式：「讀書模式 數學」
    if len(il_low) <= 15 and il_low.startswith(("讀書模式", "唸書模式", "學習模式")):
        return "study_on"

    # 自主學習模式 — Christine 自己上網學習
    _autolearn_on = {
        "自由學習", "自主學習", "上網學習", "開始學習", "去學東西",
        "自己去學", "開始上網", "去上網", "自由探索", "free learn",
        "auto learn", "go learn", "你去學東西",
        "去學習", "學習吧", "去學吧", "你去學", "開始自學",
        "christine去學習", "christine學習", "幫我學習",
    }
    if il_low in _autolearn_on:
        return "autolearn_on"
    # 模糊匹配：包含「自主學習」「自由學習」「上網學」的短句
    if len(il_low) <= 20 and any(k in il_low for k in ("自主學習", "自由學習", "上網學習", "開始學習", "自由探索")):
        return "autolearn_on"
    _autolearn_off = {
        "停止學習", "學習結束", "別學了", "回來", "不要學了",
        "stop learn", "stop learning", "學夠了", "別學", "不學了",
        "停止自學", "結束學習",
    }
    if il_low in _autolearn_off:
        return "autolearn_off"
    if len(il_low) <= 15 and any(k in il_low for k in ("停止學習", "學習結束", "結束學習", "別學了")):
        return "autolearn_off"

    # 聽寫停止 — 只在極短且明確時
    if il_low in {"停止", "停", "stop", "結束聽寫", "關聽寫"}:
        return "dictation_stop"

    # === 不是系統指令 → 回傳 None，讓 Claude 用自己的智慧處理 ===
    return None


# -- 圖片理解 ------------------------------------------
def understand_image(image_path):
    try:
        p=os.path.expanduser(image_path.strip())
        if not os.path.exists(p): return "找不到圖片: "+p
        ext=os.path.splitext(p)[1].lower()
        mime={".jpg":"image/jpeg",".jpeg":"image/jpeg",".png":"image/png",".gif":"image/gif",".webp":"image/webp"}.get(ext,"image/png")
        with open(p,"rb") as f2: img_b64=base64.b64encode(f2.read()).decode("utf-8")
        msg=[{"role":"user","content":[{"type":"image","source":{"type":"base64","media_type":mime,"data":img_b64}},{"type":"text","text":"請用繁體中文詳細描述這張圖片的內容，包括主要物件、顏色、場景、任何文字等。"}]}]
        r2=_claude_create("normal",max_tokens=600,messages=msg)
        return r2.content[0].text.strip()
    except Exception as e: return "err:"+str(e)

def understand_image_url(url):
    try:
        req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0"})
        with urllib.request.urlopen(req,timeout=20) as r:
            img_data=r.read()
            ct=r.headers.get("Content-Type","image/jpeg").split(";")[0].strip()
        if not any(x in ct for x in ["jpeg","png","gif","webp"]): ct="image/jpeg"
        img_b64=base64.b64encode(img_data).decode("utf-8")
        msg=[{"role":"user","content":[{"type":"image","source":{"type":"base64","media_type":ct,"data":img_b64}},{"type":"text","text":"請用繁體中文詳細描述這張圖片的內容，包括主要物件、顏色、場景、任何文字等。"}]}]
        r2=_claude_create("normal",max_tokens=600,messages=msg)
        return r2.content[0].text.strip()
    except Exception as e: return "err:"+str(e)

def image_to_text_ocr(image_path):
    try:
        p=os.path.expanduser(image_path.strip())
        if not os.path.exists(p): return "找不到圖片: "+p
        ext=os.path.splitext(p)[1].lower()
        mime={".jpg":"image/jpeg",".jpeg":"image/jpeg",".png":"image/png"}.get(ext,"image/png")
        with open(p,"rb") as f2: img_b64=base64.b64encode(f2.read()).decode("utf-8")
        msg=[{"role":"user","content":[{"type":"image","source":{"type":"base64","media_type":mime,"data":img_b64}},{"type":"text","text":"請擷取這張圖片中所有的文字內容，保持原本的排版，只輸出文字不要其他說明。"}]}]
        r2=_claude_create("complex",max_tokens=800,messages=msg)
        return r2.content[0].text.strip()
    except Exception as e: return "err:"+str(e)

# -- 圖片生成 ------------------------------------------
def generate_image(prompt,filename="",width=1024,height=1024):
    try:
        if not filename: filename="img_"+datetime.datetime.now().strftime("%Y%m%d_%H%M%S")+".png"
        if not filename.endswith(".png"): filename+=".png"
        save_path=os.path.join(DT,filename)
        try:
            tr=_claude_create("simple",max_tokens=150,messages=[{"role":"user","content":"Translate to English for image generation, output ONLY the English prompt, no explanation: "+prompt}])
            en_prompt=tr.content[0].text.strip()
        except: en_prompt=prompt
        import urllib.parse as _up
        encoded=_up.quote(en_prompt)
        url=f"https://image.pollinations.ai/prompt/{encoded}?width={width}&height={height}&nologo=true&enhance=true"
        req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0"})
        with urllib.request.urlopen(req,timeout=60) as r: img_data=r.read()
        with open(save_path,"wb") as f2: f2.write(img_data)
        os.startfile(save_path)
        return "圖片已生成: "+save_path+" (prompt: "+en_prompt+")"
    except Exception as e: return "err:"+str(e)

def generate_image_style(prompt,style="realistic",filename=""):
    sp={"realistic":"photorealistic, high quality, detailed","anime":"anime style, manga, Japanese animation","cartoon":"cartoon style, colorful, cute","oil":"oil painting, artistic, classical","pixel":"pixel art, 16-bit, retro game style","sketch":"pencil sketch, hand drawn, black and white","watercolor":"watercolor painting, soft colors, artistic","3d":"3D render, CGI, high quality, octane render"}
    return generate_image(prompt+", "+sp.get(style.lower(),sp["realistic"]),filename)

def pick_image_and_understand():
    try:
        root=tk.Tk(); root.withdraw()
        fp=filedialog.askopenfilename(title="選擇圖片",filetypes=[("圖片","*.png *.jpg *.jpeg *.gif *.webp *.bmp"),("全部","*.*")])
        root.destroy()
        if fp and os.path.exists(fp): return understand_image(fp)
        return "沒有選擇圖片"
    except Exception as e: return "err:"+str(e)

# -- GUI 聊天視窗 --------------------------------------
_gui_window=None
_gui_input_queue=[]
_gui_output_queue=[]

def launch_chat_window():
    """啟動 V550 Modern UI（暗色主題）"""
    global _gui_window
    try:
        _ui = globals().get("_V550_UI")
        if _ui is not None:
            _ui.launch()
            return "V600 Modern UI launched!"
    except Exception:
        pass
    # fallback: 如果 V550 還沒初始化，用舊版
    def _run():
        global _gui_window
        try:
            import ctypes as _ct
            _ct.windll.shcore.SetProcessDpiAwareness(1)
        except: pass
        win=tk.Tk(); win.title("♡ Christine AI ♡")
        win.update_idletasks()
        sw=win.winfo_screenwidth(); sh=win.winfo_screenheight()
        wx=sw//2-210; wy=sh//2-300
        win.geometry(f"420x600+{wx}+{wy}")
        win.attributes("-topmost",True)
        win.lift(); win.focus_force()
        win.configure(bg="#fff0f5"); win.resizable(True,True)
        # Title bar — 可愛粉色
        tb=tk.Frame(win,bg="#ffb6c1",height=40); tb.pack(fill="x")
        tk.Label(tb,text="  ✿ Christine AI",bg="#ffb6c1",fg="#d63384",font=("Segoe UI",12,"bold")).pack(side="left",pady=6)
        tk.Button(tb,text="✕",bg="#ff69b4",fg="white",font=("Segoe UI",10,"bold"),bd=0,padx=8,
                  activebackground="#ff1493",command=win.destroy).pack(side="right",pady=5,padx=6)
        # Chat display — 柔和背景
        cd=scrolledtext.ScrolledText(win,wrap=tk.WORD,bg="#fff5f8",fg="#4a4a4a",
                                      font=("Segoe UI",10),bd=0,relief="flat",state="disabled",
                                      selectbackground="#ffc0cb")
        cd.pack(fill="both",expand=True,padx=10,pady=6)
        cd.tag_config("u",foreground="#6a5acd",font=("Segoe UI",10,"bold"))
        cd.tag_config("c",foreground="#d63384",font=("Segoe UI",10))
        cd.tag_config("s",foreground="#c0c0c0",font=("Segoe UI",9))
        def ac(who,text):
            cd.config(state="normal")
            if who=="u": cd.insert("end","\n🧑 You: ","u"); cd.insert("end",text+"\n")
            elif who=="c": cd.insert("end","\n♡ Christine: ","c"); cd.insert("end",text+"\n")
            else: cd.insert("end",text+"\n","s")
            cd.config(state="disabled"); cd.see("end")
        ac("s","  ✿ Christine Online ✿  — 有什麼可以幫你的嗎？")
        # Button bar — 圓潤按鈕
        bf=tk.Frame(win,bg="#ffe4e1"); bf.pack(fill="x",padx=10,pady=3)
        _btn_style = {"font":("Segoe UI",9),"bd":0,"padx":10,"pady":4,"relief":"flat",
                      "activebackground":"#ffc0cb"}
        def pick_img():
            r2=tk.Tk(); r2.withdraw()
            fp=filedialog.askopenfilename(title="選擇圖片 ✿",filetypes=[("Images","*.png *.jpg *.jpeg *.gif *.webp"),("All","*.*")])
            r2.destroy()
            if fp and os.path.exists(fp):
                ac("u","[📷 Image] "+os.path.basename(fp))
                _gui_input_queue.append("__IMAGE__"+fp)
        def gen_dlg():
            pop=tk.Toplevel(win); pop.title("✿ Generate Image"); pop.geometry("340x180")
            pop.configure(bg="#fff0f5"); pop.attributes("-topmost",True)
            tk.Label(pop,text="描述你想要的圖片～",bg="#fff0f5",fg="#d63384",font=("Segoe UI",10)).pack(pady=10)
            ent=tk.Entry(pop,width=38,bg="#fff5f8",fg="#4a4a4a",font=("Segoe UI",10),
                         insertbackground="#d63384",relief="flat",highlightthickness=1,
                         highlightcolor="#ffb6c1"); ent.pack(padx=12); ent.focus()
            sv=tk.StringVar(value="realistic")
            from tkinter import ttk as _ttk
            _ttk.Combobox(pop,textvariable=sv,values=["realistic","anime","cartoon","oil","pixel","sketch","watercolor","3d"],width=15,state="readonly").pack(pady=5)
            def dg():
                p2=ent.get().strip()
                if p2:
                    _gui_input_queue.append("__GENIMAGE__"+p2+"||"+sv.get())
                    ac("u","[🎨 Gen] "+p2+" ("+sv.get()+")")
                    pop.destroy()
            tk.Button(pop,text="✿ 生成",bg="#ffb6c1",fg="#d63384",font=("Segoe UI",10,"bold"),
                      bd=0,padx=14,pady=5,activebackground="#ff69b4",command=dg).pack(pady=8)
            pop.bind("<Return>",lambda e:dg())
        tk.Button(bf,text="📷 Photo",bg="#fce4ec",fg="#d63384",command=pick_img,**_btn_style).pack(side="left",padx=3)
        tk.Button(bf,text="🎨 Draw",bg="#fce4ec",fg="#e67e22",command=gen_dlg,**_btn_style).pack(side="left",padx=3)
        tk.Button(bf,text="🖥️ Screen",bg="#fce4ec",fg="#6a5acd",command=lambda:_gui_input_queue.append("__SCREENCAP__"),**_btn_style).pack(side="left",padx=3)
        # Input — 柔和輸入框
        inf=tk.Frame(win,bg="#ffe4e1"); inf.pack(fill="x",padx=10,pady=6)
        ti=scrolledtext.ScrolledText(inf,height=3,wrap=tk.WORD,bg="#fff5f8",fg="#4a4a4a",
                                      font=("Segoe UI",11),insertbackground="#d63384",
                                      bd=0,relief="flat",selectbackground="#ffc0cb")
        ti.pack(fill="x",pady=3)
        def sm(event=None):
            msg=ti.get("1.0","end").strip()
            if msg:
                ac("u",msg); _gui_input_queue.append(msg); ti.delete("1.0","end")
            return "break"
        ti.bind("<Return>",sm)
        tk.Button(inf,text="♡ Send",bg="#ffb6c1",fg="#d63384",font=("Segoe UI",10,"bold"),
                  bd=0,padx=14,pady=5,activebackground="#ff69b4",command=sm).pack(side="right",pady=3)
        # Output checker
        def co():
            while _gui_output_queue: ac("c",_gui_output_queue.pop(0))
            win.after(200,co)
        win.after(200,co)
        _gui_window=win; win.mainloop(); _gui_window=None
    threading.Thread(target=_run,daemon=True).start()
    return "GUI chat window opened!"

def close_chat_window():
    global _gui_window
    if _gui_window:
        try: _gui_window.destroy(); _gui_window=None; return "Window closed"
        except: pass
    return "No window open"


def get_current_time():
    n=datetime.datetime.now(); return n.strftime("%Y-%m-%d %H:%M")+" "+["Mon","Tue","Wed","Thu","Fri","Sat","Sun"][n.weekday()]
def open_application(name):
    nl=name.lower().strip()
    # 1. 固定清單（含更多常見軟體和遊戲平台）
    apps={
        "notepad":"notepad","記事本":"notepad",
        "calc":"calc","計算機":"calc","計算器":"calc",
        "explorer":"explorer","檔案總管":"explorer","資料夾":"explorer",
        "chrome":"start chrome","谷歌":"start chrome","google chrome":"start chrome",
        "edge":"start msedge",
        "firefox":"start firefox",
        "word":"start winword",
        "excel":"start excel",
        "ppt":"start powerpnt","powerpoint":"start powerpnt",
        "settings":"start ms-settings:","設定":"start ms-settings:",
        "taskmgr":"taskmgr","工作管理員":"taskmgr","task manager":"taskmgr",
        "paint":"mspaint","小畫家":"mspaint",
        "vscode":"code","vs code":"code",
        "spotify":"start spotify:","spotify音樂":"start spotify:",
        "discord":"start discord:","dc":"start discord:",
        "steam":"start steam:",
        "line":"start line:",
        "obs":"start obs64","obs studio":"start obs64",
        "vlc":"start vlc",
        "7zip":"start 7zfm","7-zip":"start 7zfm",
    }
    for k,c in apps.items():
        if k in nl: os.system(c); return "opened "+k
    # 2. 嘗試直接用 shell 開（對已在 PATH 的軟體有效）
    r=subprocess.run("start "+name,shell=True,capture_output=True,timeout=5)
    if r.returncode==0: return "opened: "+name
    # 3. 搜尋常見安裝路徑（遊戲、軟體都可能在這裡）
    search_dirs=[
        os.path.expanduser("~\\AppData\\Local"),
        os.path.expanduser("~\\AppData\\Roaming"),
        "C:\\Program Files","C:\\Program Files (x86)",
        "D:\\Program Files","D:\\Program Files (x86)",
        "D:\\Games","E:\\Games","F:\\Games",
        "C:\\Games","D:\\","E:\\",
    ]
    nm_clean=name.lower().replace(" ","").replace("-","").replace("_","")
    found_exes=[]
    for d in search_dirs:
        if not os.path.exists(d): continue
        try:
            for root,dirs,files in os.walk(d):
                # 跳過太深的目錄加快速度
                depth=root.replace(d,"").count(os.sep)
                if depth>4: dirs.clear(); continue
                for f in files:
                    if f.lower().endswith(".exe"):
                        fn=f.lower().replace(".exe","").replace(" ","").replace("-","").replace("_","")
                        if nm_clean in fn or fn in nm_clean or (len(nm_clean)>3 and nm_clean[:4] in fn):
                            found_exes.append(os.path.join(root,f))
                if len(found_exes)>=5: break
        except: continue
        if found_exes: break
    if found_exes:
        # 優先選非 uninstall/setup/update 的
        best=[x for x in found_exes if not any(w in x.lower() for w in ["unins","setup","install","update","crash","redist","helper"])]
        target=best[0] if best else found_exes[0]
        try: subprocess.Popen([target]); return "找到並開啟: "+target
        except Exception as e: return "找到但開啟失敗: "+target+"\nerr:"+str(e)
    # 4. 用 Windows Search 找（最後手段）
    try:
        ps_cmd='powershell -c "Get-StartApps | Where-Object {$_.Name -like '*'+name+'*'} | Select-Object -First 1 -ExpandProperty AppID"' 
        r2=subprocess.run(ps_cmd,shell=True,capture_output=True,text=True,timeout=8)
        app_id=r2.stdout.strip()
        if app_id:
            os.system('start shell:AppsFolder\\'+app_id)
            return "opened via AppID: "+app_id
    except: pass
    return "找不到 \""+name+"\"，請確認軟體名稱或直接說完整路徑"
def search_web(q): webbrowser.open("https://www.google.com/search?q="+q); return "ok"
def open_website(url):
    if not url.startswith("http"): url="https://"+url
    webbrowser.open(url); return "ok"
def check_weather(city):
    try:
        req=urllib.request.Request("https://wttr.in/"+city+"?format=%l:+%c+%t+%h+%w&lang=zh-tw",headers={"User-Agent":"curl/7.0"})
        with urllib.request.urlopen(req,timeout=5) as r: return r.read().decode("utf-8").strip()
    except: webbrowser.open("https://www.google.com/search?q="+city+"+weather"); return "opened"
def web_fetch(url):
    try:
        if not url.startswith("http"): url="https://"+url
        req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0"})
        with urllib.request.urlopen(req,timeout=10) as r: html=r.read().decode("utf-8",errors="ignore")
        import re; text=re.sub(r'<script[^>]*>.*?</script>','',html,flags=re.DOTALL); text=re.sub(r'<style[^>]*>.*?</style>','',text,flags=re.DOTALL); text=re.sub(r'<[^>]+>','',text); text=re.sub(r'\s+',' ',text).strip()
        return text[:2000]
    except Exception as e: return "err:"+str(e)
def read_file(fp):
    try:
        p=os.path.expanduser(fp.strip())
        if not os.path.exists(p): return "not found:"+p
        with open(p,"r",encoding="utf-8") as f: c=f.read()
        return c[:3000]+("..." if len(c)>3000 else "")
    except Exception as e: return "err:"+str(e)
def write_file(fp,ct):
    try:
        p=os.path.expanduser(fp.strip()); d=os.path.dirname(p)
        if d: os.makedirs(d,exist_ok=True)
        with open(p,"w",encoding="utf-8") as f: f.write(ct)
        return "ok:"+p
    except Exception as e: return "err:"+str(e)
def append_file(fp,ct):
    try:
        with open(os.path.expanduser(fp.strip()),"a",encoding="utf-8") as f: f.write("\n"+ct)
        return "ok"
    except Exception as e: return "err:"+str(e)
def list_files(d):
    try:
        p=os.path.expanduser(d.strip())
        if not os.path.exists(p): return "not found"
        items=os.listdir(p)
        if not items: return "empty"
        r=""
        for i in sorted(items)[:20]:
            fp2=os.path.join(p,i)
            if os.path.isdir(fp2): r+="[d]"+i+"\n"
            else:
                sz=os.path.getsize(fp2); s=str(sz)+"B" if sz<1024 else(str(int(sz/1024))+"KB" if sz<1048576 else str(round(sz/1048576,1))+"MB")
                r+="[f]"+i+" "+s+"\n"
        return r
    except Exception as e: return "err:"+str(e)
def create_folder(fp):
    try: os.makedirs(os.path.expanduser(fp.strip()),exist_ok=True); return "ok"
    except Exception as e: return "err:"+str(e)
def delete_file(fp):
    try:
        p=os.path.expanduser(fp.strip())
        if not os.path.exists(p): return "not found"
        if os.path.isdir(p): shutil.rmtree(p)
        else: os.remove(p)
        return "deleted:"+p
    except Exception as e: return "err:"+str(e)
def rename_file(o,n):
    try: os.rename(os.path.expanduser(o.strip()),os.path.expanduser(n.strip())); return "ok"
    except Exception as e: return "err:"+str(e)
def copy_file(s,d):
    try:
        src,dst=os.path.expanduser(s.strip()),os.path.expanduser(d.strip())
        if os.path.isdir(src): shutil.copytree(src,dst)
        else: shutil.copy2(src,dst)
        return "ok"
    except Exception as e: return "err:"+str(e)
def move_file(s,d):
    try: shutil.move(os.path.expanduser(s.strip()),os.path.expanduser(d.strip())); return "ok"
    except Exception as e: return "err:"+str(e)
def search_files(d,pat):
    try:
        r=glob.glob(os.path.join(os.path.expanduser(d.strip()),"**","*"+pat+"*"),recursive=True)
        return "found "+str(len(r))+":\n"+"\n".join(r[:10]) if r else "not found"
    except Exception as e: return "err:"+str(e)
def get_file_info(fp):
    try:
        p=os.path.expanduser(fp.strip())
        if not os.path.exists(p): return "not found"
        st=os.stat(p); sz=st.st_size; s=str(sz)+"B" if sz<1024 else(str(round(sz/1024,1))+"KB" if sz<1048576 else str(round(sz/1048576,1))+"MB")
        return p+"|"+s+"|"+datetime.datetime.fromtimestamp(st.st_mtime).strftime("%m-%d %H:%M")
    except Exception as e: return "err:"+str(e)
def open_file_dialog():
    try:
        r=subprocess.run(['powershell','-c','Add-Type -AssemblyName System.Windows.Forms;$f=New-Object System.Windows.Forms.OpenFileDialog;$f.ShowDialog()|Out-Null;$f.FileName'],capture_output=True,text=True,timeout=30)
        fp=r.stdout.strip(); return "selected:"+fp if fp and os.path.exists(fp) else "cancelled"
    except Exception as e: return "err:"+str(e)
def add_note(c): n=lj(NF,[]); n.append({"id":len(n)+1,"c":c,"t":datetime.datetime.now().strftime("%m-%d %H:%M")}); sj(NF,n); return "ok"
def list_notes_tool():
    n=lj(NF,[]); return "\n".join(["#"+str(x["id"])+" "+x["t"]+" "+x["c"] for x in n[-10:]]) if n else "none"
def delete_note(nid): sj(NF,[x for x in lj(NF,[]) if x["id"]!=nid]); return "ok"
def add_schedule(title,dt,desc=""): s=lj(SF,[]); s.append({"id":len(s)+1,"title":title,"datetime":dt,"desc":desc}); sj(SF,s); return "ok:"+title
def list_schedule():
    s=lj(SF,[])
    if not s: return "none"
    now=datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    return "\n".join(["#"+str(x["id"])+" "+x["datetime"]+" "+x["title"]+(" X" if x["datetime"]<now else "") for x in s[-10:]])
def delete_schedule(sid): sj(SF,[x for x in lj(SF,[]) if x["id"]!=sid]); return "ok"
def calculate(expr):
    try:
        if all(c in "0123456789+-*/.() %" for c in expr): return str(eval(expr))
        return "basic only"
    except Exception as e: return "err:"+str(e)
def get_system_info():
    i=""
    try:
        m=psutil.virtual_memory(); i+="RAM:"+str(round(m.used/1073741824,1))+"/"+str(round(m.total/1073741824,1))+"G "
        d=psutil.disk_usage("C:\\"); i+="C:"+str(int(d.used/1073741824))+"/"+str(int(d.total/1073741824))+"G "
        i+="CPU:"+str(psutil.cpu_percent())+"% "
        b=psutil.sensors_battery()
        if b: i+="Bat:"+str(b.percent)+"%"
    except: pass
    return i
def get_running_processes():
    try:
        ps=sorted([p.info for p in psutil.process_iter(["name","memory_percent"]) if p.info.get("memory_percent")],key=lambda x:x.get("memory_percent",0),reverse=True)[:8]
        return "\n".join([p["name"]+" "+str(round(p["memory_percent"],1))+"%" for p in ps])
    except Exception as e: return "err:"+str(e)
def kill_process(n): os.system("taskkill /f /im "+n); return "ok"
def run_command(cmd):
    try: r=subprocess.run(cmd,shell=True,capture_output=True,timeout=30); return(r.stdout.decode("utf-8",errors="ignore").strip() or r.stderr.decode("utf-8",errors="ignore").strip() or "done")[:600]
    except: return "failed"
def run_python_code(code):
    try: r=subprocess.run([sys.executable,"-c",code],capture_output=True,text=True,timeout=15); return(r.stdout.strip() or r.stderr.strip() or "done")[:600]
    except: return "failed"
def shutdown_computer(mode):
    c={"shutdown":"shutdown /s /t 60","restart":"shutdown /r /t 60","sleep":"rundll32.exe powrprof.dll,SetSuspendState 0,1,0","lock":"rundll32.exe user32.dll,LockWorkStation"}
    if mode in c: os.system(c[mode]); return mode
    return "?"
def cancel_shutdown(): os.system("shutdown /a"); return "ok"
def take_screenshot():
    p=os.path.join(DT,"ss_"+datetime.datetime.now().strftime("%Y%m%d_%H%M%S")+".png")
    os.system('powershell -c "Add-Type -AssemblyName System.Windows.Forms;$b=New-Object System.Drawing.Bitmap([System.Windows.Forms.Screen]::PrimaryScreen.Bounds.Width,[System.Windows.Forms.Screen]::PrimaryScreen.Bounds.Height);[System.Drawing.Graphics]::FromImage($b).CopyFromScreen(0,0,0,0,$b.Size);$b.Save('+"'"+p+"'"+')"')
    return "ok:"+p
def empty_recycle_bin(): os.system('PowerShell -Command "Clear-RecycleBin -Force -ErrorAction SilentlyContinue"'); return "ok"
def start_timer(sec,label="timer"):
    def _t(): time.sleep(sec); speak(label+"!","zh")
    threading.Thread(target=_t,daemon=True).start(); return "set "+str(sec)+"s"
def start_countdown_minutes(mins,label="cd"): return start_timer(int(mins*60),label)
def music_control(action):
    keys={"play":0xB3,"pause":0xB3,"next":0xB0,"previous":0xB1,"volume_up":0xAF,"volume_down":0xAE,"mute":0xAD}
    if action in keys: ctypes.windll.user32.keybd_event(keys[action],0,0,0); ctypes.windll.user32.keybd_event(keys[action],0,2,0); return action
    return "?"
def get_clipboard():
    try: r=subprocess.run(["powershell","-c","Get-Clipboard"],capture_output=True,text=True,timeout=5); return r.stdout.strip()[:300] if r.stdout.strip() else "empty"
    except: return "err"
def set_clipboard(text):
    try: subprocess.run(["powershell","-c","Set-Clipboard -Value '"+text+"'"],timeout=5); return "ok"
    except: return "err"
def clipboard_history():
    h=lj(CF,[]); return "\n".join([x.get("t","")+" "+x.get("c","")[:40] for x in h[-8:]]) if h else "none"
def save_email_draft(to,subj,body):
    p=os.path.join(DT,"email_"+datetime.datetime.now().strftime("%Y%m%d_%H%M%S")+".txt")
    with open(p,"w",encoding="utf-8") as f: f.write("To:"+to+"\nSubj:"+subj+"\n\n"+body)
    return "ok:"+p
def generate_password(length=16,inc=True):
    c=string.ascii_letters+string.digits+("!@#$%&*" if inc else ""); return "".join(secrets.choice(c) for _ in range(length))
def daily_quote():
    import random; return random.choice(["New day new start","You are strong","Keep going","Today builds tomorrow","Dream big start small"])
def create_pdf(fp,title,ct):
    try:
        p=os.path.expanduser(fp.strip())
        if not p.endswith(".pdf"): p+=".pdf"
        d=os.path.dirname(p)
        if d: os.makedirs(d,exist_ok=True)
        pdf=FPDF(); pdf.add_page(); ff="C:/Windows/Fonts/msjh.ttc"
        if os.path.exists(ff): pdf.add_font("msj","",ff); pdf.set_font("msj",size=20)
        else: pdf.set_font("Helvetica",size=20)
        pdf.cell(0,15,title,new_x="LMARGIN",new_y="NEXT",align="C"); pdf.ln(5)
        if os.path.exists(ff): pdf.set_font("msj",size=12)
        else: pdf.set_font("Helvetica",size=12)
        for line in ct.split("\n"): pdf.multi_cell(0,8,line); pdf.ln(2)
        pdf.output(p); return "ok:"+p
    except Exception as e: return "err:"+str(e)
def create_study_notes(subj,ct): n=lj(os.path.join(DD,"study.json"),[]); n.append({"s":subj,"c":ct,"t":datetime.datetime.now().strftime("%m-%d %H:%M")}); sj(os.path.join(DD,"study.json"),n); return "ok"
def list_study_notes(subj=""):
    n=lj(os.path.join(DD,"study.json"),[])
    if not n: return "none"
    if subj: n=[x for x in n if subj.lower() in x["s"].lower()]
    return "\n".join([x["t"]+" "+x["s"]+":"+x["c"][:60] for x in n[-8:]])
def start_study_timer(mins,subj="study"):
    def _t(): time.sleep(int(mins*60)); speak(subj+" done!","zh")
    threading.Thread(target=_t,daemon=True).start(); return "ok"
def get_wifi_info():
    try: r=subprocess.run("netsh wlan show interfaces",shell=True,capture_output=True,text=True,timeout=10); return r.stdout.strip()[:400] if r.stdout.strip() else "no WiFi"
    except: return "err"
def get_ip_address():
    try:
        hn=socket.gethostname(); lip=socket.gethostbyname(hn)
        try: eip=urllib.request.urlopen("https://api.ipify.org",timeout=5).read().decode()
        except: eip="?"
        return hn+" local:"+lip+" ext:"+eip
    except Exception as e: return "err:"+str(e)
def check_installed_programs(kw=""):
    try:
        r=subprocess.run('powershell -c "Get-ItemProperty HKLM:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\* | Select-Object DisplayName,DisplayVersion | Format-Table -AutoSize"',shell=True,capture_output=True,text=True,timeout=15); o=r.stdout.strip()
        if kw: lines=[l for l in o.split("\n") if kw.lower() in l.lower()]; return "\n".join(lines[:15]) if lines else "not found"
        return o[:600]
    except: return "err"
def open_control_panel_item(item):
    items={"network":"ncpa.cpl","display":"desk.cpl","sound":"mmsys.cpl","programs":"appwiz.cpl","power":"powercfg.cpl","system":"sysdm.cpl","device":"devmgmt.msc","disk":"diskmgmt.msc","firewall":"firewall.cpl"}
    for k,v in items.items():
        if k in item.lower(): os.system("start "+v); return "ok"
    return "not found"
def get_startup_programs():
    try: r=subprocess.run('powershell -c "Get-CimInstance Win32_StartupCommand | Select-Object Name,Command | Format-Table -AutoSize"',shell=True,capture_output=True,text=True,timeout=10); return r.stdout.strip()[:400] if r.stdout.strip() else "none"
    except: return "err"
def check_disk_health():
    try:
        result=""
        for part in psutil.disk_partitions():
            try: u=psutil.disk_usage(part.mountpoint); result+=part.device+" "+str(round(u.used/1073741824,1))+"/"+str(round(u.total/1073741824,1))+"G\n"
            except: pass
        return result if result else "err"
    except: return "err"
def disk_cleanup():
    try: subprocess.run("cleanmgr /sagerun:1",shell=True,timeout=5); return "ok"
    except: return "err"
def capture_screen():
    try:
        p=os.path.join(DD,"scr.png")
        os.system('powershell -c "Add-Type -AssemblyName System.Windows.Forms;$b=New-Object System.Drawing.Bitmap([System.Windows.Forms.Screen]::PrimaryScreen.Bounds.Width,[System.Windows.Forms.Screen]::PrimaryScreen.Bounds.Height);[System.Drawing.Graphics]::FromImage($b).CopyFromScreen(0,0,0,0,$b.Size);$b.Save('+"'"+p+"'"+')"')
        if os.path.exists(p):
            with open(p,"rb") as f: return {"ok":True,"img":base64.b64encode(f.read()).decode("utf-8")}
        return {"ok":False,"e":"failed"}
    except Exception as e: return {"ok":False,"e":str(e)}
def capture_camera():
    try:
        import cv2; cap=cv2.VideoCapture(0)
        if not cap.isOpened(): return {"ok":False,"e":"no cam"}
        ret,frame=cap.read(); cap.release()
        if ret:
            p=os.path.join(DD,"cam.png"); cv2.imwrite(p,frame)
            with open(p,"rb") as f: return {"ok":True,"img":base64.b64encode(f.read()).decode("utf-8")}
        return {"ok":False,"e":"failed"}
    except ImportError: return {"ok":False,"e":"need opencv"}
    except Exception as e: return {"ok":False,"e":str(e)}
def convert_unit(val,fu,tu):
    fu2,tu2=fu.lower(),tu.lower()
    if (fu2,tu2)==("c","f"): return str(round(val*9/5+32,1))+"F"
    if (fu2,tu2)==("f","c"): return str(round((val-32)*5/9,1))+"C"
    cv={("kg","lb"):2.20462,("lb","kg"):0.453592,("km","mi"):0.621371,("mi","km"):1.60934,("cm","in"):0.393701,("in","cm"):2.54,("m","ft"):3.28084,("ft","m"):0.3048,("l","gal"):0.264172,("gal","l"):3.78541}
    if (fu2,tu2) in cv: return str(round(val*cv[(fu2,tu2)],2))+tu2
    return "?"
def open_google_maps(q): webbrowser.open("https://www.google.com/maps/search/"+q.replace(" ","+")); return "ok"
def save_voice_memo(ct):
    p=os.path.join(DT,"memo_"+datetime.datetime.now().strftime("%Y%m%d_%H%M%S")+".txt")
    with open(p,"w",encoding="utf-8") as f: f.write(ct); return "ok:"+p
def teach_vocabulary(lang="en"):
    import random; ws=[{"w":"serendipity","m":"happy accident"},{"w":"ephemeral","m":"short-lived"},{"w":"ubiquitous","m":"everywhere"},{"w":"resilience","m":"recover"},{"w":"pragmatic","m":"practical"},{"w":"eloquent","m":"expressive"},{"w":"tenacious","m":"persistent"},{"w":"candid","m":"direct honest"}]
    w=random.choice(ws); return w["w"]+":"+w["m"]
def toggle_dictation():
    global dm; dm=not dm; return "ON" if dm else "OFF"
def type_text(text):
    try:
        subprocess.run(["powershell","-c","Set-Clipboard -Value '"+text.replace("'","''")+"'"],timeout=5)
        time.sleep(0.1)
        pyautogui.hotkey("ctrl","v")
        return "ok:typed "+str(len(text))+" chars"
    except Exception as e: return "err:"+str(e)
def setup_autostart():
    try:
        sd=os.path.join(os.environ.get("APPDATA",""),"Microsoft","Windows","Start Menu","Programs","Startup")
        with open(os.path.join(sd,"Christine.bat"),"w") as f: f.write('@echo off\nset ANTHROPIC_API_KEY='+API_KEY+'\nstart "" "'+sys.executable+'" "F:\\christine_final.py"\n')
        return "ok"
    except Exception as e: return "err:"+str(e)
def add_expense(amt,cat,note=""): e=lj(EF,[]); e.append({"a":amt,"c":cat,"n":note,"t":datetime.datetime.now().strftime("%m-%d %H:%M")}); sj(EF,e); return "ok $"+str(amt)
def list_expenses(period="today"):
    e=lj(EF,[])
    if not e: return "none"
    td=datetime.datetime.now().strftime("%Y-%m-%d")
    if period=="today": f=[x for x in e if x["t"].startswith(td[:5])]
    elif period=="month": f=e
    else: f=e[-15:]
    if not f: return "none"
    return "\n".join([x["t"]+" $"+str(x["a"])+" "+x["c"] for x in f[-8:]])+"\nTotal:$"+str(sum(x["a"] for x in f))
def add_diary(ct): d=lj(DF,[]); d.append({"c":ct,"t":datetime.datetime.now().strftime("%m-%d %H:%M")}); sj(DF,d); return "ok"
def read_diary(date=""):
    d=lj(DF,[])
    if not d: return "none"
    if date: d=[x for x in d if date in x["t"]]
    return "\n".join(["["+x["t"]+"]"+x["c"] for x in d[-5:]])
def tell_joke():
    import random; return random.choice(["Why dark mode? Light attracts bugs!","Debugging: detective AND murderer.","AI is spicy autocomplete.","SQL walks into bar: Can I join?","10 types: binary.","My code works. No idea why."])
def recommend_music(mood):
    r={"happy":"upbeat pop","sad":"piano","angry":"rock","relaxed":"lo-fi","energetic":"EDM","focused":"classical"}
    for k,v in r.items():
        if k in mood.lower(): return v
    return "?"
def mouse_move(x,y):
    try: pyautogui.moveTo(x,y,duration=0.2); return "ok"
    except Exception as e: return "err:"+str(e)
def mouse_click(x=None,y=None,button="left",clicks=1):
    try:
        if x is not None and y is not None: pyautogui.click(x,y,clicks=clicks,button=button)
        else: pyautogui.click(clicks=clicks,button=button)
        return "ok"
    except Exception as e: return "err:"+str(e)
def mouse_scroll(amt):
    try: pyautogui.scroll(amt); return "ok"
    except Exception as e: return "err:"+str(e)
def kb_hotkey(keys):
    try: pyautogui.hotkey(*keys.split("+")); return "ok"
    except Exception as e: return "err:"+str(e)
def kb_press(key):
    try: pyautogui.press(key); return "ok"
    except Exception as e: return "err:"+str(e)
def game_key_down(key):
    scancodes={"w":0x11,"a":0x1E,"s":0x1F,"d":0x20,"space":0x39,"shift":0x2A,"ctrl":0x1D,"alt":0x38,"tab":0x0F,"esc":0x01,"enter":0x1C,"e":0x12,"r":0x13,"f":0x21,"q":0x10,"1":0x02,"2":0x03,"3":0x04,"4":0x05,"5":0x06}
    sc=scancodes.get(key.lower(),0)
    if sc: ctypes.windll.user32.keybd_event(0,sc,0x0008,0)
    return "down:"+key
def game_key_up(key):
    scancodes={"w":0x11,"a":0x1E,"s":0x1F,"d":0x20,"space":0x39,"shift":0x2A,"ctrl":0x1D,"alt":0x38,"tab":0x0F,"esc":0x01,"enter":0x1C,"e":0x12,"r":0x13,"f":0x21,"q":0x10,"1":0x02,"2":0x03,"3":0x04,"4":0x05,"5":0x06}
    sc=scancodes.get(key.lower(),0)
    if sc: ctypes.windll.user32.keybd_event(0,sc,0x0008|0x0002,0)
    return "up:"+key
def game_key_tap(key,duration=0.05):
    game_key_down(key); time.sleep(duration); game_key_up(key); return "tap:"+key
def game_mouse_move(dx,dy):
    ctypes.windll.user32.mouse_event(0x0001,int(dx),int(dy),0,0)
    return "moved:"+str(dx)+","+str(dy)
def game_mouse_click_raw(button="left"):
    if button=="left": ctypes.windll.user32.mouse_event(0x0002,0,0,0,0); time.sleep(0.02); ctypes.windll.user32.mouse_event(0x0004,0,0,0,0)
    elif button=="right": ctypes.windll.user32.mouse_event(0x0008,0,0,0,0); time.sleep(0.02); ctypes.windll.user32.mouse_event(0x0010,0,0,0,0)
    return "clicked:"+button
def game_hold_key(key,seconds=1.0):
    game_key_down(key); time.sleep(float(seconds)); game_key_up(key); return "held:"+key+" "+str(seconds)+"s"
def game_combo(keys,delay=0.03):
    ks=keys.split("+")
    for k in ks: game_key_down(k); time.sleep(delay)
    time.sleep(0.05)
    for k in reversed(ks): game_key_up(k)
    return "combo:"+keys
def auto_translate(text,to_lang="en"):
    try:
        import urllib.parse
        tl="en" if to_lang.lower() in ["en","english","英文"] else "zh-TW"
        url="https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl="+tl+"&dt=t&q="+urllib.parse.quote(text)
        req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0"})
        with urllib.request.urlopen(req,timeout=10) as r: data=json.loads(r.read().decode("utf-8"))
        result="".join([s[0] for s in data[0] if s[0]])
        subprocess.run(["powershell","-c","Set-Clipboard -Value '"+result.replace("'","''")+"'"],timeout=5)
        return result+" (copied)"
    except Exception as e: return "err:"+str(e)
def check_exchange_rate(fr="USD",to="TWD"):
    try:
        url="https://api.exchangerate-api.com/v4/latest/"+fr.upper()
        req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0"})
        with urllib.request.urlopen(req,timeout=10) as r: data=json.loads(r.read().decode("utf-8"))
        rate=data["rates"].get(to.upper(),0)
        return "1 "+fr.upper()+" = "+str(round(rate,2))+" "+to.upper()
    except Exception as e: return "err:"+str(e)
def countdown_days(target_date,label=""):
    try:
        td2=datetime.datetime.strptime(target_date,"%Y-%m-%d")
        diff=(td2-datetime.datetime.now()).days
        if diff>0: return (label+" " if label else "")+str(diff)+" days left"
        elif diff==0: return (label+" " if label else "")+"is TODAY!"
        else: return (label+" " if label else "")+"was "+str(abs(diff))+" days ago"
    except Exception as e: return "err:"+str(e)
def pomodoro_start(work_min=25,break_min=5,rounds=4):
    def _pomo():
        for i in range(int(rounds)):
            speak("第"+str(i+1)+"輪開始！專注"+str(work_min)+"分鐘！","zh")
            time.sleep(int(work_min)*60)
            if i<int(rounds)-1:
                speak("休息"+str(break_min)+"分鐘！站起來動一動～","zh")
                time.sleep(int(break_min)*60)
            else:
                speak("全部結束啦！老闆辛苦了～","zh")
    threading.Thread(target=_pomo,daemon=True).start()
    return "pomodoro:"+str(rounds)+"x"+str(work_min)+"m"
def voice_to_notes(content,title=""):
    try:
        if not title: title=datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        p=os.path.join(DT,"note_"+title.replace(" ","_")+".md")
        structured="# "+title+"\n"+datetime.datetime.now().strftime("%Y-%m-%d %H:%M")+"\n\n"
        for l in content.split("。"):
            l=l.strip()
            if l: structured+="- "+l+"\n"
        with open(p,"w",encoding="utf-8") as f: f.write(structured)
        return "ok:"+p
    except Exception as e: return "err:"+str(e)
def summarize_url(url):
    try:
        text=web_fetch(url)
        if text.startswith("err"): return text
        msg=[{"role":"user","content":"用繁體中文3-5個重點摘要:\n"+text[:1500]}]
        r2=_claude_create("simple",max_tokens=300,messages=msg)
        return r2.content[0].text.strip()
    except Exception as e: return "err:"+str(e)
def daily_summary():
    try:
        td=datetime.datetime.now().strftime("%Y-%m-%d"); s=lj(STF,{})
        ds=s.get(td,{}); chats=ds.get("c",0); tools=ds.get("t",{})
        d=lj(DF,[]); today_diary=[x for x in d if td[:5] in x.get("t","")]
        n=lj(NF,[]); today_notes=[x for x in n if td[:5] in x.get("t","")]
        r="Today: "+str(chats)+" chats"
        if tools: r+=", tools:"+str(tools)
        if today_diary: r+=", diary:"+str(len(today_diary))
        if today_notes: r+=", notes:"+str(len(today_notes))
        return r
    except Exception as e: return "err:"+str(e)
def check_speed_test():
    try:
        t0=time.time()
        urllib.request.urlopen("https://www.google.com",timeout=10).read()
        latency=round((time.time()-t0)*1000)
        t1=time.time()
        data=urllib.request.urlopen("https://speed.cloudflare.com/__down?bytes=1000000",timeout=15).read()
        speed=round(len(data)/(time.time()-t1)/1024/1024*8,1)
        return "Ping:"+str(latency)+"ms DL:"+str(speed)+"Mbps"
    except Exception as e: return "err:"+str(e)
def youtube_search(query):
    webbrowser.open("https://www.youtube.com/results?search_query="+query.replace(" ","+"))
    return "ok:youtube "+query
def tell_story(topic=""):
    try:
        sf=os.path.join(DD,"story.json"); s=lj(sf,{"ep":0,"plot":""})
        s["ep"]=s.get("ep",0)+1
        prompt="你是一個說故事的人。用繁體中文寫一段200字的故事。"
        if topic: prompt+="主題:"+topic+"。"
        if s.get("plot"): prompt+="之前的劇情:"+s["plot"][-300:]+"。請接續發展。"
        prompt+="第"+str(s["ep"])+"集。"
        msg=[{"role":"user","content":prompt}]
        r2=_claude_create("simple",max_tokens=300,messages=msg)
        story=r2.content[0].text.strip()
        s["plot"]=s.get("plot","")+story[-200:]
        sj(sf,s)
        return "Ep"+str(s["ep"])+": "+story
    except Exception as e: return "err:"+str(e)
def quiz_game(topic="general"):
    try:
        msg=[{"role":"user","content":"出一題"+topic+"的選擇題(A/B/C/D)用繁體中文，最後一行寫答案。"}]
        r2=_claude_create("simple",max_tokens=200,messages=msg)
        return r2.content[0].text.strip()
    except Exception as e: return "err:"+str(e)
def daily_english():
    try:
        msg=[{"role":"user","content":"教一句實用英文句子，附中文翻譯和用法說明，簡短。"}]
        r2=_claude_create("simple",max_tokens=150,messages=msg)
        return r2.content[0].text.strip()
    except Exception as e: return "err:"+str(e)
def flashcard_review(subject=""):
    try:
        n=lj(os.path.join(DD,"study.json"),[])
        if not n: return "no cards"
        if subject: n=[x for x in n if subject.lower() in x.get("s","").lower()]
        if not n: return "no cards for "+subject
        import random; card=random.choice(n)
        return "Q: "+card["s"]+" | A: "+card["c"]
    except Exception as e: return "err:"+str(e)
def summarize_pdf(file_path):
    try:
        p=os.path.expanduser(file_path.strip())
        if not os.path.exists(p): return "not found:"+p
        with open(p,"rb") as f: raw=f.read()
        text="".join([chr(b) for b in raw if 32<=b<127 or b in(10,13)])[:3000]
        if not text: return "cannot read pdf"
        msg=[{"role":"user","content":"用繁體中文摘要這份文件的重點:\n"+text[:2000]}]
        r2=_claude_create("normal",max_tokens=400,messages=msg)
        return r2.content[0].text.strip()
    except Exception as e: return "err:"+str(e)
def mouse_pos(): p=pyautogui.position(); return str(p.x)+","+str(p.y)
def screen_size(): s=pyautogui.size(); return str(s.width)+"x"+str(s.height)
def smart_screen_action(instruction):
    scr=capture_screen()
    if not scr.get("ok"): return "failed"
    msg=[{"role":"user","content":[{"type":"image","source":{"type":"base64","media_type":"image/png","data":scr["img"]}},{"type":"text","text":instruction+" Reply JSON:{\"action\":\"click/type/scroll/hotkey\",\"x\":0,\"y\":0,\"text\":\"\",\"keys\":\"\"}"}]}]
    try:
        r2=_claude_create("normal",max_tokens=100,messages=msg)
        txt=r2.content[0].text.strip()
        if txt.startswith("{"):
            a2=json.loads(txt)
            if a2.get("action")=="click": pyautogui.click(a2.get("x",0),a2.get("y",0)); return "clicked"
            elif a2.get("action")=="type": pyautogui.click(a2.get("x",0),a2.get("y",0)); time.sleep(0.1); pyautogui.typewrite(a2.get("text",""),interval=0.02); return "typed"
            elif a2.get("action")=="scroll": pyautogui.scroll(a2.get("y",0)); return "scrolled"
            elif a2.get("action")=="hotkey": pyautogui.hotkey(*a2.get("keys","").split("+")); return "ok"
        return txt[:100]
    except Exception as e: return "err:"+str(e)
def toggle_screen_watch():
    global sw; sw=not sw; return "ON" if sw else "OFF"
def rui(k,v): mem["ui"][k]=v; sm(mem); return "ok"
def rpf(k,v): mem["pf"][k]=v; sm(mem); return "ok"
def rfc(f2): mem["if"].append(f2); mem["if"]=mem["if"][-50:]; sm(mem); return "ok"
def rtp(t): mem["rt"].append(t); mem["rt"]=mem["rt"][-20:]; sm(mem); return "ok"
def rmd(m2): mem["mh"].append({"m":m2,"t":datetime.datetime.now().strftime("%m/%d %H:%M")}); mem["mh"]=mem["mh"][-30:]; sm(mem); return "ok"
def rrl(n,r): mem["rl"][n]=r; sm(mem); return "ok"
def rsk(s):
    if s not in mem.get("sk",[]): mem.setdefault("sk",[]).append(s); mem["sk"]=mem["sk"][-20:]; sm(mem)
    return "ok"
def rcr(c): mem.setdefault("cr",[]).append(c); mem["cr"]=mem["cr"][-20:]; sm(mem); return "ok"
def rcl(): return fmem(mem)
def fgt(k):
    if k in mem["ui"]: del mem["ui"][k]; sm(mem); return "ok"
    return "?"

# === SELF-MODIFY (with syntax safety) ===
SELF_PATH=os.path.abspath(sys.argv[0])
def self_backup():
    bk=SELF_PATH+".backup_"+datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    shutil.copy2(SELF_PATH,bk); return "backup:"+bk

def self_read_function(func_name):
    """讀取某個函式的完整程式碼（確保看到完整內容才能修改）"""
    with open(SELF_PATH,"r",encoding="utf-8") as f: lines=f.readlines()
    start_idx=None
    for i,l in enumerate(lines):
        if l.startswith("def "+func_name+"(") or l.startswith("def "+func_name+" ("):
            start_idx=i; break
    if start_idx is None: return "找不到函式: "+func_name
    end_idx=start_idx+1
    while end_idx<len(lines):
        if (lines[end_idx].startswith("def ") or lines[end_idx].startswith("# ===")) and end_idx>start_idx+1: break
        end_idx+=1
    result="函式 "+func_name+" (第"+str(start_idx+1)+"~"+str(end_idx)+"行):\n"
    result+="".join([str(start_idx+i+1)+": "+lines[start_idx+i] for i in range(end_idx-start_idx)])
    return result[:3000]

def self_read_code(section="",start_line=0,end_line=0):
    start_line=int(start_line or 0)
    end_line=int(end_line or 0)
    with open(SELF_PATH,"r",encoding="utf-8") as f: lines=f.readlines()
    # 指定行範圍
    if start_line>0 and end_line>0:
        chunk=lines[max(0,start_line-1):min(len(lines),end_line)]
        return "".join([str(i+start_line)+":"+l for i,l in enumerate(chunk)])
    # 搜尋關鍵字 — 先用快取索引秒查，找不到才逐行搜尋
    if section:
        # 快速索引查詢
        _CODE_INDEX_READY.wait(timeout=3)
        idx_funcs = _CODE_INDEX.get("functions", {})
        idx_classes = _CODE_INDEX.get("classes", {})
        # 精確匹配
        if section in idx_funcs:
            info = idx_funcs[section]
            chunk = lines[max(0,info["line"]-1):min(len(lines),info["end"])]
            return "=== " + section + " (line " + str(info["line"]) + "-" + str(info["end"]) + ") ===\n" + "".join([str(info["line"]+i) + ":" + l for i,l in enumerate(chunk)])[:3000]
        if section in idx_classes:
            info = idx_classes[section]
            chunk = lines[max(0,info["line"]-1):min(len(lines),min(info["end"],info["line"]+80))]
            return "=== class " + section + " (line " + str(info["line"]) + "-" + str(info["end"]) + ", " + str(info["size"]) + "行) ===\n" + "".join([str(info["line"]+i) + ":" + l for i,l in enumerate(chunk)])[:3000]
        # 模糊匹配
        fuzzy = [n for n in list(idx_funcs) + list(idx_classes) if section.lower() in n.lower()]
        if fuzzy:
            results = []
            for name in fuzzy[:5]:
                info = idx_funcs.get(name) or idx_classes.get(name)
                if info:
                    chunk = lines[max(0,info["line"]-1):min(len(lines),min(info["end"],info["line"]+60))]
                    results.append("=== " + name + " (line " + str(info["line"]) + ") ===\n" + "".join([str(info["line"]+i) + ":" + l for i,l in enumerate(chunk)])[:1500])
            if results:
                return "\n---\n".join(results)
        # 索引沒找到，退回逐行搜尋
        found_lines=[]
        for i,l in enumerate(lines):
            if section.lower() in l.lower():
                if l.strip().startswith("def "):
                    end_i=i+1
                    while end_i<len(lines):
                        if lines[end_i].startswith("def ") and end_i>i+1: break
                        end_i+=1
                    chunk=lines[i:min(end_i,i+80)]
                    found_lines.append("=== "+l.strip()+" (line "+str(i+1)+") ===")
                    found_lines.extend([str(i+j+1)+":"+chunk[j].rstrip() for j in range(len(chunk))])
                else:
                    s=max(0,i-2); e=min(len(lines),i+8)
                    found_lines.extend([str(s+j+1)+":"+lines[s+j].rstrip() for j in range(e-s)])
                found_lines.append("---")
                if len(found_lines)>200: break
        return "\n".join(found_lines[:200]) if found_lines else "not found"
    return "total "+str(len(lines))+" lines"
def self_modify_code(old_text,new_text):
    if not old_text: return "need old_text"
    if not new_text and new_text!="": return "need new_text"
    self_backup()
    with open(SELF_PATH,"r",encoding="utf-8") as f: code=f.read()
    if old_text not in code: return "old_text not found in source"
    new_code=code.replace(old_text,new_text,1)
    try:
        compile(new_code,"<christine>","exec")
    except SyntaxError as e:
        return "BLOCKED! Syntax error: "+str(e)+". Nothing changed."
    with open(SELF_PATH,"w",encoding="utf-8") as f: f.write(new_code)
    speak("改好了，自動重啟中！","zh")
    time.sleep(0.5)
    os.execv(sys.executable,[sys.executable]+sys.argv)
def self_add_code(code_to_add,location="tools"):
    self_backup()
    with open(SELF_PATH,"r",encoding="utf-8") as f: code=f.read()
    if location=="tools":
        marker="# === ALL TOOL FUNCTIONS ==="
        if marker in code:
            new_code=code.replace(marker,marker+"\n"+code_to_add+"\n")
        else:
            idx=code.rfind("\ndef main()")
            new_code=code[:idx]+"\n"+code_to_add+"\n"+code[idx:] if idx>0 else code
    elif location=="top":
        new_code=code_to_add+"\n"+code
    else:
        idx=code.rfind("\ndef main()")
        new_code=code[:idx]+"\n"+code_to_add+"\n"+code[idx:] if idx>0 else code
    try:
        compile(new_code,"<christine>","exec")
    except SyntaxError as e:
        return "BLOCKED! Syntax error: "+str(e)+". Nothing changed."
    with open(SELF_PATH,"w",encoding="utf-8") as f: f.write(new_code)
    speak("加好了，自動重啟中！","zh")
    time.sleep(0.5)
    os.execv(sys.executable,[sys.executable]+sys.argv)
def self_replace_function(func_name,new_func_code):
    self_backup()
    with open(SELF_PATH,"r",encoding="utf-8") as f: lines=f.readlines()
    start_idx=None; end_idx=None
    for i,l in enumerate(lines):
        if l.startswith("def "+func_name+"(") or l.startswith("def "+func_name+" ("):
            start_idx=i
        elif start_idx is not None and i>start_idx and (l.startswith("def ") or l.startswith("# ===") or l.startswith("CORE=") or l.startswith("EXTRA=") or l.startswith("ALL=") or l.startswith("TM=") or l.startswith("KW=")):
            end_idx=i; break
    if start_idx is None: return "function "+func_name+" not found"
    if end_idx is None: end_idx=len(lines)
    new_lines=lines[:start_idx]+[new_func_code+"\n"]+lines[end_idx:]
    new_code="".join(new_lines)
    try:
        compile(new_code,"<christine>","exec")
    except SyntaxError as e:
        return "BLOCKED! Syntax error: "+str(e)+". Nothing changed."
    with open(SELF_PATH,"w",encoding="utf-8") as f: f.write(new_code)
    speak("改好了，自動重啟中！","zh")
    time.sleep(0.5)
    os.execv(sys.executable,[sys.executable]+sys.argv)
def self_add_tool(tool_name,description,params_json,func_code,tm_lambda):
    self_backup()
    with open(SELF_PATH,"r",encoding="utf-8") as f: code=f.read()
    marker="# === ALL TOOL FUNCTIONS ==="
    new_code=code.replace(marker,marker+"\n"+func_code+"\n")
    td='{"name":"'+tool_name+'","description":"'+description+'","input_schema":'+params_json+'}'
    tw_marker='"name":"toggle_screen_watch","description":"live watch","input_schema":{"type":"object","properties":{},"required":[]}},'
    new_code=new_code.replace(tw_marker,tw_marker+"\n"+td+",")
    import re as _re2
    def _ins(m):
        inner=m.group(1)
        sep="" if inner.rstrip().endswith(",") else ","
        return "TM={"+inner+sep+'"'+tool_name+'":'+ tm_lambda+"}"
    new_code=_re2.sub(r'(?s)TM=\{(.+?)\}(?=\n)',_ins,new_code,count=1)
    try:
        compile(new_code,"<christine>","exec")
    except SyntaxError as e:
        return "BLOCKED! Syntax error: "+str(e)+". Nothing changed."
    with open(SELF_PATH,"w",encoding="utf-8") as f: f.write(new_code)
    speak("新工具加好了，自動重啟中！","zh")
    time.sleep(0.5)
    os.execv(sys.executable,[sys.executable]+sys.argv)
def self_restore():
    bks=sorted(glob.glob(SELF_PATH+".backup_*"),reverse=True)
    if not bks: return "no backup"
    shutil.copy2(bks[0],SELF_PATH); return "restored from "+os.path.basename(bks[0])+"! Say restart."
def self_restart():
    with open(SELF_PATH,"r",encoding="utf-8") as f: code=f.read()
    try:
        compile(code,SELF_PATH,"exec")
        speak("語法OK，重啟中！","zh")
        time.sleep(0.5)
        os.execv(sys.executable,[sys.executable]+sys.argv)
    except SyntaxError as e:
        return "BLOCKED! Syntax error: "+str(e)+". Fix first or restore."


# ══════════════════════════════════════════════════════════
# 強化自我升級系統 v2
# ══════════════════════════════════════════════════════════

def self_list_backups():
    bks=sorted(glob.glob(SELF_PATH+".backup_*"),reverse=True)
    if not bks: return "沒有備份"
    out=[]
    for i,b in enumerate(bks[:10]):
        st=os.stat(b); sz=str(round(st.st_size/1024,1))+"KB"
        ts=os.path.basename(b).replace(os.path.basename(SELF_PATH)+".backup_","")
        out.append("["+str(i)+"] "+ts+" "+sz)
    return "\n".join(out)

def self_rollback(version_index=0):
    bks=sorted(glob.glob(SELF_PATH+".backup_*"),reverse=True)
    if not bks: return "沒有備份可還原"
    idx=int(version_index)
    if idx>=len(bks): return "沒有第"+str(idx)+"個備份，共"+str(len(bks))+"個"
    target=bks[idx]
    cur_bk=SELF_PATH+".before_rollback_"+datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    shutil.copy2(SELF_PATH,cur_bk); shutil.copy2(target,SELF_PATH)
    speak("還原成功！重啟中～","zh"); time.sleep(0.5)
    os.execv(sys.executable,[sys.executable]+sys.argv)

def self_diff(version_index=0):
    bks=sorted(glob.glob(SELF_PATH+".backup_*"),reverse=True)
    if not bks: return "沒有備份"
    idx=int(version_index)
    if idx>=len(bks): return "沒有第"+str(idx)+"個備份"
    with open(SELF_PATH,"r",encoding="utf-8") as f: cur=f.readlines()
    with open(bks[idx],"r",encoding="utf-8") as f: old=f.readlines()
    diffs=list(difflib.unified_diff(old,cur,lineterm="",n=2))
    if not diffs: return "沒有差異"
    changes=[l for l in diffs if l.startswith(("+","-")) and not l.startswith(("+++","---"))]
    added=sum(1 for l in changes if l.startswith("+"))
    removed=sum(1 for l in changes if l.startswith("-"))
    return "新增"+str(added)+"行，刪除"+str(removed)+"行\n"+"".join(diffs[:60])[:2000]

def self_version_log():
    vf=os.path.join(DD,"version_log.json"); logs=lj(vf,[])
    if not logs: return "還沒有升級記錄"
    return "\n".join(["["+x["t"]+"] v"+str(x["v"])+" - "+x["desc"] for x in logs[-15:]])

def _write_version_log(description):
    vf=os.path.join(DD,"version_log.json"); logs=lj(vf,[])
    ver=len(logs)+1
    lines_count=sum(1 for _ in open(SELF_PATH,encoding="utf-8"))
    logs.append({"v":ver,"t":datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),"desc":description,"lines":lines_count})
    sj(vf,logs); return ver

def self_test_code(code_snippet,test_input=""):
    try: compile(code_snippet,"<test>","exec")
    except SyntaxError as e: return "語法錯誤: "+str(e)
    try:
        indent="\n".join("    "+l for l in code_snippet.splitlines())
        test_script="import sys,os,json,datetime,time\ntry:\n"+indent+"\n    print('TEST_OK')\nexcept Exception as e:\n    print('TEST_FAIL: '+str(e))\n"
        r=subprocess.run([sys.executable,"-c",test_script],capture_output=True,text=True,timeout=10)
        out=r.stdout.strip()
        if r.stderr.strip(): out+="\nSTDERR: "+r.stderr.strip()[:200]
        return out[:500] if out else "no output"
    except Exception as e: return "err:"+str(e)

def self_safe_modify(old_text,new_text,description=""):
    if not old_text: return "需要 old_text"
    with open(SELF_PATH,"r",encoding="utf-8") as f: code_now=f.read()
    if old_text not in code_now: return "找不到要替換的片段"
    new_code=code_now.replace(old_text,new_text,1)
    try: compile(new_code,"<safe_modify>","exec")
    except SyntaxError as e: return "語法錯誤，已取消: "+str(e)
    self_backup()
    with open(SELF_PATH,"w",encoding="utf-8") as f: f.write(new_code)
    desc=description or "修改片段: "+old_text[:40]+"..."
    ver=_write_version_log(desc)
    speak("升級完成！第"+str(ver)+"版，重啟中！","zh"); time.sleep(0.5)
    os.execv(sys.executable,[sys.executable]+sys.argv)

def self_safe_add_tool(tool_name,description_text,params_json,func_code,tm_lambda,log_desc=""):
    test_result=self_test_code(func_code)
    if "語法錯誤" in test_result or "SyntaxError" in test_result:
        return "函式語法有問題，取消: "+test_result
    result=self_add_tool(tool_name,description_text,params_json,func_code,tm_lambda)
    if "err" in result.lower() or "BLOCKED" in result: return result
    _write_version_log(log_desc or "新增工具: "+tool_name)
    return result

def self_analyze_self():
    try:
        with open(SELF_PATH,"r",encoding="utf-8") as f: code_now=f.read()
        total_lines=len(code_now.splitlines())
        import re as _re
        tool_count=len(_re.findall('"name":"\\w+"',code_now))
        func_count=len(_re.findall(r'(?m)^def \w+\(',code_now))
        vf=os.path.join(DD,"version_log.json"); logs=lj(vf,[])
        last_upgrade=logs[-1]["t"] if logs else "從未升級"
        snippet=code_now[:3000]+"\n...(省略)...\n"+code_now[-1000:]
        msg=[{"role":"user","content":"你是Christine，請分析你自己的程式碼架構：\n總行數:"+str(total_lines)+"，工具數:"+str(tool_count)+"，函式數:"+str(func_count)+"，最後升級:"+last_upgrade+"\n\n程式碼片段:\n"+snippet+"\n\n請用繁體中文：\n1.目前架構優缺點\n2.可改進的3個具體建議含實作\n3.潛在bug或不穩定之處"}]
        r2=_claude_create("complex",max_tokens=800,messages=msg)
        return r2.content[0].text.strip()
    except Exception as e: return "err:"+str(e)

def self_auto_upgrade(feature_request):
    try:
        with open(SELF_PATH,"r",encoding="utf-8") as f: code_now=f.read()
        total_lines=len(code_now.splitlines())
        plan_prompt="你是Christine，Python AI助理，程式碼共"+str(total_lines)+"行。\n老闆要求升級：「"+feature_request+"」\n\n請只回傳JSON（不要其他文字）：\n{\"analysis\":