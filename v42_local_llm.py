"""
V42 Local LLM Engine v2.0 — 方案B: Ollama 本地大語言模型整合
============================================================
核心設計:
  1. V42OllamaClient  — 純 urllib HTTP 連接 Ollama API (無需 pip)
  2. V42GPUEngine     — GPU/CPU OPS 算力追蹤，持久化累計至 1000T (1P)，含容量上限與警告
  3. V42SelfCodeUnderstanding — LLM 驅動的自我程式碼理解引擎
  4. V42FolderLearner — 掃描 DD 下資料夾，LLM 學習文件
  5. V42SmartRouter   — 知識優先路由：先查知識庫 → 再 ARR 共振路由 → 最後 AI
  6. V42LocalLLMEngine — 統一門面，整合以上所有子系統
  7. V42PermanentFolderMemory — 永久資料夾記憶（跨 session 不遺忘）
  8. V42UserProfile   — 每位使用者獨立的個人化設定與算力配額
  9. V42ComputeSlotManager — 按需算力分配（只用需要的量）
  10. NEXUS v2.0 認知融合引擎 — 13 篇論文 + 5 獨創演算法

v2.0 重大升級:
  ★ 容量: 100T → 1000T (1 Peta OPS)
  ★ NEXUS v2.0: 7 新模組 (共振/碎形/ARR/預測/熵閘/知識庫/工具發現)
  ★ 知識優先路由: 先查內建知識 → 深度學習資料夾 → 記憶 → AI
  ★ 不靠關鍵詞路由: ARR 自適應共振路由 (Grossberg ART 啟發)
  ★ 碎形複雜度分析: 用數學判斷問題難度 (非規則)
  ★ 預測性知識蒸餾: V42 預測下一個問題，預載知識
  ★ 秒開機制: 第二次啟動秒開 (無新知識時)
  ★ 自我工具擴充: V42 判斷需要什麼工具 → 自動建立
  ★ 進度條 UI: 每個載入步驟都有進度條

算力公式 (Kaplan et al. 2020, "Scaling Laws for Neural Language Models"):
  OPS ≈ 2 × N_params × (input_tokens + output_tokens)

1000T OPS 目標:
  - 每次 Ollama 推理 (3B model): ~321B OPS/call
  - 每次嵌入 (137M model): ~13.7B OPS/call
  - NEXUS v2 推理: ~1.83M OPS/query (dim=128)
  - 1000T ÷ 321B = ~3,115 次 Ollama 推理可達標
  - 算力上限 1000T: 接近時警告，滿時節流

判斷邏輯 v2.0 (Knowledge-First + ARR):
  Step 0: V42 NEXUS 碎形複雜度分析 → 判斷問題難度
  Step 1: 內建知識庫查詢 → 有答案就直接回 (0 OPS)
  Step 2: 深度學習資料夾 + 永久記憶搜索 → 有知識就用
  Step 3: ARR 共振路由 (不靠關鍵詞) → 選擇最佳工具
  Step 4: V42 自我能力評估 → 判斷能不能做
  Step 5: Level 1/2/3 路由 → 執行

永久記憶 (市場唯一):
  - 永久記住所有資料夾結構和內容摘要
  - 跨 session 不遺忘
  - 越用越聰明，知識持續累積
  - 不同使用者有不同的記憶空間和效果
"""

import os
import json
import time
import hashlib
import urllib.request
import urllib.error
import threading
import datetime
import uuid

# ── NEXUS v2.0 認知融合引擎 (13 篇論文 + 5 獨創演算法) ──
try:
    from v42_nexus_engine_v2 import V42NexusEngineV2, create_nexus_v2, nexus_encode_text
    _NEXUS_V2_AVAILABLE = True
except ImportError:
    _NEXUS_V2_AVAILABLE = False
try:
    from v42_nexus_engine import V42NexusEngine, nexus_encode_text as _nexus_encode_v1
    _NEXUS_AVAILABLE = True
    if not _NEXUS_V2_AVAILABLE:
        nexus_encode_text = _nexus_encode_v1
except ImportError:
    _NEXUS_AVAILABLE = False
    if not _NEXUS_V2_AVAILABLE:
        # Minimal fallback
        import hashlib as _hlib
        def nexus_encode_text(text, dim=128):
            text = str(text or "")
            vec = []
            for i in range(dim):
                h = _hlib.md5(f"{text}_{i}".encode()).hexdigest()
                val = (int(h[:8],16)/0xFFFFFFFF)*2-1
                vec.append(val)
            import math as _m
            n = _m.sqrt(sum(x*x for x in vec))
            return [x/n for x in vec] if n>1e-12 else vec

# ═══════════════════════════════════════════════════
# 持久化路徑
# ═══════════════════════════════════════════════════
_CHRISTINE_BASE_LLM = os.path.dirname(os.path.abspath(__file__))
_DD = os.path.join(_CHRISTINE_BASE_LLM, "data")
_V42_DIR = os.path.join(_DD, "christine_v42")
_GPU_STATE_PATH = os.path.join(_V42_DIR, "gpu_ops_state.json")
_SELF_UNDERSTANDING_CACHE = os.path.join(_V42_DIR, "self_understanding_cache.json")
_FOLDER_LEARNING_STATE = os.path.join(_V42_DIR, "folder_learning_state.json")
_PERMANENT_FOLDER_MEMORY_PATH = os.path.join(_V42_DIR, "permanent_folder_memory.json")
_USER_PROFILES_PATH = os.path.join(_V42_DIR, "user_profiles.json")
_COMPUTE_SLOTS_PATH = os.path.join(_V42_DIR, "compute_slots.json")
_KNOWLEDGE_GRAPH_PATH = os.path.join(_V42_DIR, "knowledge_graph.json")
os.makedirs(_V42_DIR, exist_ok=True)


# ═══════════════════════════════════════════════════
# 1. V42OllamaClient — Ollama HTTP API 客戶端
# ═══════════════════════════════════════════════════
class V42OllamaClient:
    """純 urllib 連接 Ollama API — 不需要 pip install 任何套件
    
    V52 升級: 雲端 API 後備機制
    ┌─────────────────────────────────────────────────────────────┐
    │ 1. 優先使用本地 Ollama（隱私、免費、無限制）                │
    │ 2. 本地 OOM / 連不上 → 自動切換 Groq Cloud API             │
    │ 3. Groq 提供 llama-3.3-70b @ 280 tok/s（LPU 加速）        │
    │ 4. OpenAI 相容格式 → 無需改動上層程式碼                    │
    │ 5. 支援多雲端後備: Groq → Together → OpenRouter            │
    └─────────────────────────────────────────────────────────────┘
    """

    # ── V52: 雲端 API 設定 ──
    # 支援的雲端提供者（按優先順序）
    CLOUD_PROVIDERS = {
        "groq": {
            "base_url": "https://api.groq.com/openai/v1",
            "env_key": "GROQ_API_KEY",
            "models": {
                "llama-3.3-70b-versatile": 70_000_000_000,
                "llama-3.1-8b-instant": 8_000_000_000,
                "meta-llama/llama-4-scout-17b-16e-instruct": 17_000_000_000,
            },
            "default_model": "llama-3.3-70b-versatile",
            "max_tokens_limit": 32768,
            "label": "Groq LPU Cloud",
        },
        "together": {
            "base_url": "https://api.together.xyz/v1",
            "env_key": "TOGETHER_API_KEY",
            "models": {
                "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo": 70_000_000_000,
                "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo": 8_000_000_000,
            },
            "default_model": "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
            "max_tokens_limit": 4096,
            "label": "Together AI",
        },
        "openrouter": {
            "base_url": "https://openrouter.ai/api/v1",
            "env_key": "OPENROUTER_API_KEY",
            "models": {
                "meta-llama/llama-3.3-70b-instruct": 70_000_000_000,
                "meta-llama/llama-3.1-8b-instruct:free": 8_000_000_000,
            },
            "default_model": "meta-llama/llama-3.3-70b-instruct",
            "max_tokens_limit": 32768,
            "label": "OpenRouter",
        },
    }

    def __init__(self, base_url="http://localhost:11434"):
        self.base_url = base_url
        self._chat_model = None      # 推理模型 (自動選擇)
        self._embed_model = "nomic-embed-text"  # 嵌入模型 (137M params, 768D)
        self._available_models = []
        self._connected = False

        # ── V52: 雲端後備狀態 ──
        self._cloud_provider = None       # 當前使用的雲端提供者名稱
        self._cloud_api_key = None        # API key
        self._cloud_model = None          # 雲端模型名稱
        self._cloud_base_url = None       # 雲端 API base URL
        self._cloud_active = False        # 是否正在使用雲端
        self._cloud_calls = 0             # 雲端呼叫次數
        self._cloud_tokens_used = 0       # 雲端 token 用量
        self._local_oom_count = 0         # 本地 OOM 次數
        self._cloud_errors = []           # 最近的雲端錯誤
        self._init_cloud_fallback()       # 初始化雲端後備

    # ── V52: 雲端後備系統 ────────────────────────────────────────────────

    def _init_cloud_fallback(self):
        """初始化雲端後備 — 掃描環境變數找可用的 API key"""
        for name, cfg in self.CLOUD_PROVIDERS.items():
            key = os.environ.get(cfg["env_key"], "").strip()
            if key and len(key) > 10:
                self._cloud_provider = name
                self._cloud_api_key = key
                self._cloud_base_url = cfg["base_url"]
                self._cloud_model = cfg["default_model"]
                return
        # 也檢查 F:\AI夥伴\記憶資料夾\christine_v42\ 下的 cloud_api_keys.json
        _keys_path = os.path.join(_V42_DIR, "cloud_api_keys.json")
        if os.path.isfile(_keys_path):
            try:
                with open(_keys_path, "r", encoding="utf-8") as f:
                    keys = json.load(f)
                for name, cfg in self.CLOUD_PROVIDERS.items():
                    key = keys.get(cfg["env_key"], "").strip()
                    if key and len(key) > 10:
                        self._cloud_provider = name
                        self._cloud_api_key = key
                        self._cloud_base_url = cfg["base_url"]
                        self._cloud_model = cfg["default_model"]
                        return
            except Exception:
                pass

    def _cloud_request(self, messages, temperature=0.3, max_tokens=2048):
        """V52: 透過 OpenAI-compatible API 呼叫雲端 LLM

        支援 Groq / Together / OpenRouter — 全部都是 OpenAI 格式
        """
        if not self._cloud_api_key or not self._cloud_model:
            return None

        provider_cfg = self.CLOUD_PROVIDERS.get(self._cloud_provider, {})
        _max_limit = provider_cfg.get("max_tokens_limit", 32768)
        max_tokens = min(max_tokens, _max_limit)

        url = f"{self._cloud_base_url}/chat/completions"
        payload = json.dumps({
            "model": self._cloud_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }).encode("utf-8")

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._cloud_api_key}",
            "User-Agent": "Christine-AI/54.0",  # ★ 必須！否則被 Cloudflare 1010 擋
        }
        # OpenRouter 需要額外 header
        if self._cloud_provider == "openrouter":
            headers["HTTP-Referer"] = "https://christine-ai.local"
            headers["X-Title"] = "Christine AI Assistant"

        req = urllib.request.Request(url, data=payload, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                if result and "choices" in result and result["choices"]:
                    choice = result["choices"][0]
                    content = choice.get("message", {}).get("content", "")
                    usage = result.get("usage", {})
                    self._cloud_calls += 1
                    self._cloud_tokens_used += usage.get("total_tokens", 0)
                    return {
                        "content": content,
                        "model": f"☁️{self._cloud_provider}:{self._cloud_model}",
                        "eval_count": usage.get("completion_tokens", 0),
                        "prompt_eval_count": usage.get("prompt_tokens", 0),
                        "total_duration": 0,
                        "cloud": True,
                        "cloud_provider": self._cloud_provider,
                    }
        except urllib.error.HTTPError as e:
            _err_body = ""
            try:
                _err_body = e.read().decode("utf-8", errors="replace")[:300]
            except Exception:
                pass
            self._cloud_errors.append(f"HTTP {e.code}: {_err_body}")
            self._cloud_errors = self._cloud_errors[-10:]  # 只保留最近 10 個
        except Exception as e:
            self._cloud_errors.append(str(e)[:200])
            self._cloud_errors = self._cloud_errors[-10:]
        return None

    def set_cloud_api_key(self, provider, api_key):
        """手動設定雲端 API key（可在對話中設定）"""
        if provider not in self.CLOUD_PROVIDERS:
            return False
        cfg = self.CLOUD_PROVIDERS[provider]
        self._cloud_provider = provider
        self._cloud_api_key = api_key
        self._cloud_base_url = cfg["base_url"]
        self._cloud_model = cfg["default_model"]
        self._cloud_active = False  # 重置，讓它重新嘗試本地
        # 持久化到檔案
        _keys_path = os.path.join(_V42_DIR, "cloud_api_keys.json")
        try:
            existing = {}
            if os.path.isfile(_keys_path):
                with open(_keys_path, "r", encoding="utf-8") as f:
                    existing = json.load(f)
            existing[cfg["env_key"]] = api_key
            with open(_keys_path, "w", encoding="utf-8") as f:
                json.dump(existing, f, indent=2)
        except Exception:
            pass
        return True

    @property
    def cloud_status(self):
        """雲端後備狀態報告"""
        return {
            "cloud_available": bool(self._cloud_api_key),
            "cloud_active": self._cloud_active,
            "provider": self._cloud_provider,
            "model": self._cloud_model,
            "calls": self._cloud_calls,
            "tokens_used": self._cloud_tokens_used,
            "local_oom_count": self._local_oom_count,
            "recent_errors": self._cloud_errors[-3:],
        }

    # ══════════════════════════════════════════════════════════════
    # V54: 🖼️ Cloud Vision Request — Llama-4-Scout Multimodal
    # ══════════════════════════════════════════════════════════════
    VISION_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"

    def _cloud_vision_request(self, text_prompt, image_base64=None, image_url=None,
                               temperature=0.3, max_tokens=2048):
        """V54: 透過 Groq Cloud 呼叫 Llama-4-Scout 視覺模型

        支援兩種圖片輸入:
        - image_base64: base64 編碼的圖片字串 (max 4MB)
        - image_url: 圖片 URL (max 20MB)
        至少需要提供其中一種。

        Returns: dict with 'content', 'model', 'cloud', etc. or None on failure
        """
        if not self._cloud_api_key:
            return None
        if not image_base64 and not image_url:
            return None

        # 構建多模態 content 陣列
        content_parts = []
        content_parts.append({"type": "text", "text": text_prompt or "請描述這張圖片"})

        if image_base64:
            # 自動偵測圖片格式
            _mime = "image/jpeg"
            if image_base64[:4] == "iVBO":
                _mime = "image/png"
            elif image_base64[:4] == "R0lG":
                _mime = "image/gif"
            elif image_base64[:4] == "UklG":
                _mime = "image/webp"
            content_parts.append({
                "type": "image_url",
                "image_url": {"url": f"data:{_mime};base64,{image_base64}"}
            })
        elif image_url:
            content_parts.append({
                "type": "image_url",
                "image_url": {"url": image_url}
            })

        messages = [
            {"role": "system", "content": "你是 Christine AI 的視覺分析模組。請用繁體中文回答，詳細分析圖片內容。"},
            {"role": "user", "content": content_parts}
        ]

        # 使用 Groq base URL（vision 只支援 Groq）
        url = f"{self._cloud_base_url}/chat/completions"
        payload = json.dumps({
            "model": self.VISION_MODEL,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": min(max_tokens, 16384),
            "stream": False,
        }).encode("utf-8")

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._cloud_api_key}",
            "User-Agent": "Christine-AI/54.0",
        }

        req = urllib.request.Request(url, data=payload, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=90) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                if result and "choices" in result and result["choices"]:
                    choice = result["choices"][0]
                    content = choice.get("message", {}).get("content", "")
                    usage = result.get("usage", {})
                    self._cloud_calls += 1
                    self._cloud_tokens_used += usage.get("total_tokens", 0)
                    return {
                        "content": content,
                        "model": f"☁️groq:{self.VISION_MODEL}",
                        "eval_count": usage.get("completion_tokens", 0),
                        "prompt_eval_count": usage.get("prompt_tokens", 0),
                        "total_duration": 0,
                        "cloud": True,
                        "cloud_provider": "groq",
                        "vision": True,
                    }
        except urllib.error.HTTPError as e:
            _err_body = ""
            try:
                _err_body = e.read().decode("utf-8", errors="replace")[:300]
            except Exception:
                pass
            self._cloud_errors.append(f"[Vision] HTTP {e.code}: {_err_body}")
            self._cloud_errors = self._cloud_errors[-10:]
        except Exception as e:
            self._cloud_errors.append(f"[Vision] {str(e)[:200]}")
            self._cloud_errors = self._cloud_errors[-10:]
        return None

    def _request(self, path, data=None, timeout=120):
        """發送 HTTP 請求到 Ollama — V52: 區分 OOM/連不上/正常失敗"""
        url = f"{self.base_url}{path}"
        if data is not None:
            payload = json.dumps(data).encode("utf-8")
            req = urllib.request.Request(url, data=payload,
                                         headers={"Content-Type": "application/json"})
        else:
            req = urllib.request.Request(url)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            # Ollama 500 = 通常是 OOM (model requires more system memory)
            if e.code == 500:
                try:
                    _body = e.read().decode("utf-8", errors="replace")[:500]
                except Exception:
                    _body = ""
                if "memory" in _body.lower() or "oom" in _body.lower() or "not enough" in _body.lower():
                    self._local_oom_count += 1
                    self._cloud_active = True  # ★ 立刻切雲端，不再嘗試本地
                return None
            return None
        except (urllib.error.URLError, ConnectionRefusedError, OSError):
            # Ollama 沒啟動 / 連不上
            return None
        except Exception:
            return None

    def check_ollama(self):
        """檢查 Ollama 是否運行中"""
        try:
            result = self._request("/api/tags", timeout=5)
            if result and "models" in result:
                self._available_models = [m.get("name", "") for m in result["models"]]
                self._connected = True
                return True, self._available_models
        except Exception:
            pass
        self._connected = False
        return False, []

    def auto_select_chat_model(self):
        """自動選擇最佳的聊天模型
        
        V52 SpeedFix: 16GB VRAM 機器上 70B 模型會爆 VRAM → 走 RAM swap → 3-8 tok/s
        改用 qwen2.5:7b 為主（4.7GB 全進 VRAM，穩定 40+ tok/s）
        70B 只在明確要求 heavy 任務時才用（透過 V1210 Router）
        """
        # V52 升級: 優先 7B 等級模型 → 全 VRAM 高速推理
        # 優先順序：qwen2.5:7b > llama3.1:8b > qwen2.5:3b > ... > 70B (最後備援)
        import os as _os
        _force = _os.environ.get("CHRISTINE_CHAT_MODEL", "").strip()
        if _force:
            for available in self._available_models:
                if _force in available or available == _force:
                    self._chat_model = available
                    return available
        preferred = [
            "qwen2.5:7b", "qwen2.5:7b-instruct", "llama3.1:8b", "llama3:8b",
            "mistral:7b", "mistral:latest", "gemma2:9b",
            "qwen2.5:3b", "llama3.2:3b", "qwen2.5:0.5b", "llama3.2:1b",
            "gemma2:2b", "phi3:mini",
            # 巨型模型放最後 — 只在沒有其他選擇時才用（會很慢）
            "llama3.3:70b", "llama3.3:latest", "llama3.1:70b", "qwen2.5:72b",
        ]
        for model in preferred:
            for available in self._available_models:
                if model in available or available.startswith(model.split(":")[0]):
                    self._chat_model = available
                    return available
        # 如果以上都沒有，選第一個可用的非嵌入模型
        for m in self._available_models:
            if "embed" not in m.lower() and "nomic" not in m.lower():
                self._chat_model = m
                return m
        # V52: 本地沒有可用模型 → 如果有雲端 key 就標記雲端模式
        if self._cloud_api_key and self._cloud_model:
            self._cloud_active = True
            self._chat_model = f"cloud:{self._cloud_model}"
            return self._chat_model
        return None

    def ensure_model(self, model_name):
        """確保模型已下載（不阻塞，如果沒有就跳過）"""
        for m in self._available_models:
            if model_name in m or m.startswith(model_name.split(":")[0]):
                return True
        return False

    def embed(self, text, model=None):
        """用 Ollama 生成文字嵌入向量"""
        model = model or self._embed_model
        result = self._request("/api/embeddings", {
            "model": model,
            "prompt": str(text or "")[:8000],
        }, timeout=30)
        if result and "embedding" in result:
            return result["embedding"]  # list[float], 768D for nomic-embed-text
        return None

    def chat(self, prompt, system_prompt=None, model=None, temperature=0.3, max_tokens=2048):
        """用 Ollama 進行聊天推理 — V52: 含雲端後備

        ★ 速度優化流程:
        1. _cloud_active=True → 直接走雲端（不浪費時間嘗試本地）
        2. 本地嘗試 timeout=15s（OOM 秒回 500，不需要等 120s）
        3. 本地失敗 → 快速試一個小模型 → 還是不行 → 雲端
        4. 雲端 Groq 70B @ 280tok/s（比本地 OOM 重試快 100x）
        """
        # 構建 messages（本地和雲端都用得到）
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": str(system_prompt)})
        messages.append({"role": "user", "content": str(prompt)})

        # ── 快速路徑: 已知本地 OOM → 直接雲端 ──
        if self._cloud_active and self._cloud_api_key:
            return self._cloud_request(messages, temperature, max_tokens)

        # ── 嘗試 1: 本地 Ollama (短 timeout) ──
        model = model or self._chat_model
        if model and self._connected and not str(model).startswith("cloud:"):
            result = self._request("/api/chat", {
                "model": model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                },
            }, timeout=60)  # V52.1: 15→60s，小模型寫長 code 也夠用
            if result and "message" in result:
                return {
                    "content": result["message"].get("content", ""),
                    "model": model,
                    "eval_count": result.get("eval_count", 0),
                    "prompt_eval_count": result.get("prompt_eval_count", 0),
                    "total_duration": result.get("total_duration", 0),
                }

        # ── 嘗試 2: 雲端 API ──
        if self._cloud_api_key:
            self._cloud_active = True
            cloud_result = self._cloud_request(messages, temperature, max_tokens)
            if cloud_result:
                return cloud_result

        return None

    def generate(self, prompt, model=None, system=None, temperature=0.3, max_tokens=2048):
        """用 Ollama generate API — V52: 含雲端後備（同 chat 速度優化）"""
        # ── 快速路徑: 已知本地 OOM → 直接雲端 ──
        if self._cloud_active and self._cloud_api_key:
            messages = []
            if system:
                messages.append({"role": "system", "content": str(system)})
            messages.append({"role": "user", "content": str(prompt)})
            return self._cloud_request(messages, temperature, max_tokens)

        # ── 嘗試 1: 本地 Ollama ──
        model = model or self._chat_model
        if model and self._connected and not str(model).startswith("cloud:"):
            data = {
                "model": model,
                "prompt": str(prompt),
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                },
            }
            if system:
                data["system"] = str(system)
            result = self._request("/api/generate", data, timeout=60)
            if result and "response" in result:
                return {
                    "content": result["response"],
                    "model": model,
                    "eval_count": result.get("eval_count", 0),
                    "prompt_eval_count": result.get("prompt_eval_count", 0),
                    "total_duration": result.get("total_duration", 0),
                }

        # ── 嘗試 2: 雲端 API 後備 ──
        if self._cloud_api_key:
            self._cloud_active = True
            messages = []
            if system:
                messages.append({"role": "system", "content": str(system)})
            messages.append({"role": "user", "content": str(prompt)})
            return self._cloud_request(messages, temperature, max_tokens)

        return None

    # ── V53: Streaming 串流輸出 ─────────────────────────────────────────

    def chat_stream(self, prompt, system_prompt=None, model=None, temperature=0.3, max_tokens=2048):
        """V53: 串流聊天 — yield 每個 token chunk

        用法:
            for chunk in ollama.chat_stream("hello"):
                print(chunk, end="", flush=True)
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": str(system_prompt)})
        messages.append({"role": "user", "content": str(prompt)})

        # ── 快速路徑: 已知本地 OOM → 直接雲端串流 ──
        if self._cloud_active and self._cloud_api_key:
            yield from self._cloud_stream(messages, temperature, max_tokens)
            return

        # ── 嘗試 1: 本地 Ollama 串流 ──
        model = model or self._chat_model
        if model and self._connected and not str(model).startswith("cloud:"):
            try:
                url = f"{self.base_url}/api/chat"
                payload = json.dumps({
                    "model": model,
                    "messages": messages,
                    "stream": True,
                    "options": {"temperature": temperature, "num_predict": max_tokens},
                }).encode("utf-8")
                req = urllib.request.Request(url, data=payload,
                                             headers={"Content-Type": "application/json"})
                resp = urllib.request.urlopen(req, timeout=15)
                had_output = False
                for line in resp:
                    if not line.strip():
                        continue
                    try:
                        chunk = json.loads(line.decode("utf-8"))
                        content = chunk.get("message", {}).get("content", "")
                        if content:
                            had_output = True
                            yield content
                        if chunk.get("done"):
                            break
                    except Exception:
                        continue
                resp.close()
                if had_output:
                    return
            except Exception:
                pass

        # ── 嘗試 2: 雲端串流 ──
        if self._cloud_api_key:
            self._cloud_active = True
            yield from self._cloud_stream(messages, temperature, max_tokens)

    def _cloud_stream(self, messages, temperature=0.3, max_tokens=2048):
        """V53: 雲端 SSE 串流"""
        if not self._cloud_api_key or not self._cloud_model:
            return

        provider_cfg = self.CLOUD_PROVIDERS.get(self._cloud_provider, {})
        _max_limit = provider_cfg.get("max_tokens_limit", 32768)
        max_tokens = min(max_tokens, _max_limit)

        url = f"{self._cloud_base_url}/chat/completions"
        payload = json.dumps({
            "model": self._cloud_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }).encode("utf-8")

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._cloud_api_key}",
            "User-Agent": "Christine-AI/54.0",
        }
        if self._cloud_provider == "openrouter":
            headers["HTTP-Referer"] = "https://christine-ai.local"
            headers["X-Title"] = "Christine AI Assistant"

        req = urllib.request.Request(url, data=payload, headers=headers)
        total_tokens = 0
        try:
            resp = urllib.request.urlopen(req, timeout=60)
            for raw_line in resp:
                line = raw_line.decode("utf-8", errors="replace").strip()
                if not line or not line.startswith("data: "):
                    continue
                data_str = line[6:]
                if data_str == "[DONE]":
                    break
                try:
                    chunk = json.loads(data_str)
                    delta = chunk.get("choices", [{}])[0].get("delta", {})
                    content = delta.get("content", "")
                    if content:
                        total_tokens += 1
                        yield content
                except Exception:
                    continue
            resp.close()
            self._cloud_calls += 1
            self._cloud_tokens_used += total_tokens
        except Exception as e:
            self._cloud_errors.append(f"stream: {str(e)[:200]}")
            self._cloud_errors = self._cloud_errors[-10:]

    @property
    def is_ready(self):
        """V52: 本地 Ollama 就緒 OR 雲端 API 可用 → 都算 ready"""
        if self._connected and self._chat_model is not None:
            return True
        if self._cloud_api_key and self._cloud_model:
            return True
        return False

    @property
    def is_cloud_mode(self):
        """V52: 是否正在使用雲端模式"""
        return self._cloud_active


# ═══════════════════════════════════════════════════
# 2. V42GPUEngine — 算力追蹤引擎 (持久化)
# ═══════════════════════════════════════════════════
class V42GPUEngine:
    """追蹤 V42 實際消耗的 GPU/CPU 算力 (OPS)

    公式：OPS = 2 × N_params × tokens  (Kaplan 2020)
    
    算力容量管理 (Compute Capacity Management):
    ┌───────────────────────────────────────────────────────────┐
    │ v13.4 分級制 — Tiered Compute Levels:                     │
    │   Lv.1:     1P (1,000T)   — 基礎算力                     │
    │   Lv.2:    10P (10,000T)  — 進階算力                      │
    │   Lv.3:   100P (100,000T) — 深度算力                      │
    │   Lv.4: 1,000P (1E)       — 超級算力                      │
    │   Lv.5: 10,000P (10E)     — 極限算力                      │
    │ 達到當前等級上限 → 自動升級到下一級                        │
    │ 每級有獨立的 70%/85%/95%/100% 警告門檻                    │
    │                                                           │
    │ 數學基礎:                                                 │
    │   Kaplan et al. 2020: FLOPS ≈ 2 × N × D                 │
    │   Hoffmann et al. 2022: Optimal D/N ratio ≈ 20           │
    │   Clark et al. 2022: E(L) = αN^{-β₁} × D^{-β₂}         │
    │   Rosenfeld et al. 2021: Power-law scaling behavior       │
    └───────────────────────────────────────────────────────────┘

    模型參數量:
      - llama3.2:3b   → 3,210,000,000 params
      - llama3.2:1b   → 1,240,000,000 params
      - nomic-embed-text → 137,000,000 params
      - V42 DU engine → 366,000,000 params
      - V42 NLP core  → 120,000,000 params
    """

    # 常見模型的參數量查找表
    MODEL_PARAMS = {
        "llama3.2:3b": 3_210_000_000,
        "llama3.2:1b": 1_240_000_000,
        "llama3.1:8b": 8_030_000_000,
        "llama3:8b": 8_030_000_000,
        "mistral:7b": 7_240_000_000,
        "mistral:latest": 7_240_000_000,
        "gemma2:9b": 9_240_000_000,
        "gemma2:2b": 2_610_000_000,
        "qwen2.5:7b": 7_620_000_000,
        "qwen2.5:3b": 3_090_000_000,
        "phi3:mini": 3_800_000_000,
        "nomic-embed-text": 137_000_000,
    }

    # V42 內建模型參數量
    V42_DU_PARAMS = 366_000_000
    V42_NLP_PARAMS = 120_000_000

    # ═══ V13.4 分級算力容量 — Tiered Compute Levels ═══
    # 每達到一個里程碑，自動解鎖下一級
    COMPUTE_LEVELS = [
        {"level": 1, "target": 1_000_000_000_000_000,      "name": "基礎算力",   "label": "1P"},
        {"level": 2, "target": 10_000_000_000_000_000,     "name": "進階算力",   "label": "10P"},
        {"level": 3, "target": 100_000_000_000_000_000,    "name": "深度算力",   "label": "100P"},
        {"level": 4, "target": 1_000_000_000_000_000_000,  "name": "超級算力",   "label": "1E"},
        {"level": 5, "target": 10_000_000_000_000_000_000, "name": "極限算力",   "label": "10E"},
    ]
    # CAPACITY_LIMIT 動態計算 — 總是當前等級的 target
    # 初始化時會根據 total_ops 調整
    CAPACITY_LIMIT = 10_000_000_000_000_000  # 預設 10P，__init__ 會更新
    WARN_THRESHOLDS = {
        0.70: "INFO",    # 70% — 算力持續累計中
        0.85: "WARN",    # 85% — 接近上限
        0.95: "ALERT",   # 95% — 即將滿載
        1.00: "FULL",    # 100% — 當前等級已滿（自動升級）
    }

    def __init__(self):
        self.total_ops = 0           # 累計總算力
        self.session_ops = 0         # 本次 session 算力
        self.inference_count = 0     # 推理次數
        self.embed_count = 0         # 嵌入次數
        self.self_code_ops = 0       # 自我程式碼理解消耗的算力
        self.folder_learn_ops = 0    # 資料夾學習消耗的算力
        self.du_train_ops = 0        # DU 訓練消耗的算力
        self._gpu_name = "CPU"
        self._gpu_detected = False
        self._capacity_warnings = []  # 警告歷史
        self._throttle_active = False  # 節流模式
        self._detect_gpu()
        self._load_state()
        self._update_capacity_limit()  # v13.4: 根據 total_ops 動態設定 CAPACITY_LIMIT

    def _update_capacity_limit(self):
        """v13.4: 根據當前 total_ops 動態更新 CAPACITY_LIMIT 到當前等級的 target"""
        for i, lv in enumerate(self.COMPUTE_LEVELS):
            if self.total_ops < lv["target"]:
                self.CAPACITY_LIMIT = lv["target"]
                self._current_level = lv
                self._next_level = self.COMPUTE_LEVELS[i + 1] if i + 1 < len(self.COMPUTE_LEVELS) else None
                return
        # 全部達標
        last = self.COMPUTE_LEVELS[-1]
        self.CAPACITY_LIMIT = last["target"]
        self._current_level = last
        self._next_level = None

    def _detect_gpu(self):
        """偵測 GPU"""
        try:
            import subprocess
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
                self._gpu_name = result.stdout.strip().split(",")[0].strip()
                self._gpu_detected = True
                return
        except Exception:
            pass
        try:
            import torch_directml
            self._gpu_name = "DirectML GPU"
            self._gpu_detected = True
        except Exception:
            pass

    def _load_state(self):
        """從磁碟載入持久化算力狀態"""
        try:
            if os.path.exists(_GPU_STATE_PATH):
                with open(_GPU_STATE_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.total_ops = int(data.get("total_ops", 0))
                self.inference_count = int(data.get("inference_count", 0))
                self.embed_count = int(data.get("embed_count", 0))
                self.self_code_ops = int(data.get("self_code_ops", 0))
                self.folder_learn_ops = int(data.get("folder_learn_ops", 0))
                self.du_train_ops = int(data.get("du_train_ops", 0))
                self._capacity_warnings = data.get("capacity_warnings", [])
        except Exception:
            pass

    def save_state(self):
        """持久化算力狀態到磁碟"""
        try:
            data = {
                "total_ops": self.total_ops,
                "session_ops": self.session_ops,
                "inference_count": self.inference_count,
                "embed_count": self.embed_count,
                "self_code_ops": self.self_code_ops,
                "folder_learn_ops": self.folder_learn_ops,
                "du_train_ops": self.du_train_ops,
                "gpu_name": self._gpu_name,
                "capacity_limit": self.CAPACITY_LIMIT,
                "capacity_used_pct": round(self.progress_pct, 2),
                "capacity_warnings": self._capacity_warnings[-50:],  # 只保留最新 50 條
                "throttle_active": self._throttle_active,
                "last_save": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
            os.makedirs(os.path.dirname(_GPU_STATE_PATH), exist_ok=True)
            with open(_GPU_STATE_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    # ═══ 算力容量管理 ═══

    @property
    def capacity_remaining(self):
        """剩餘算力容量 (OPS)"""
        return max(0, self.CAPACITY_LIMIT - self.total_ops)

    @property
    def capacity_remaining_tops(self):
        """剩餘算力容量 (TOPS)"""
        return self.capacity_remaining / 1e12

    @property
    def is_capacity_exceeded(self):
        """算力是否已超過當前等級上限 — v13.4: 自動升級"""
        if self.total_ops >= self.CAPACITY_LIMIT:
            # 嘗試升級
            self._update_capacity_limit()
            # 升級後如果 CAPACITY_LIMIT 提高了，就不算 exceeded
            return self.total_ops >= self.CAPACITY_LIMIT
        return False

    @property
    def capacity_level(self):
        """當前算力使用等級: 'OK'|'INFO'|'WARN'|'ALERT'|'FULL'"""
        pct = self.total_ops / self.CAPACITY_LIMIT
        for threshold, level in sorted(self.WARN_THRESHOLDS.items(), reverse=True):
            if pct >= threshold:
                return level
        return "OK"

    def check_capacity(self, needed_ops=0):
        """檢查是否有足夠的算力容量執行一個任務
        
        Args:
            needed_ops: 預估需要的 OPS
            
        Returns:
            dict: {
                allowed: bool — 是否允許執行,
                level: str — 容量等級,
                remaining: int — 剩餘 OPS,
                warning: str|None — 警告訊息
            }
        """
        level = self.capacity_level
        remaining = self.capacity_remaining

        if level == "FULL":
            # v13.4: 自動升級到下一級
            if self._next_level:
                old_limit = self.CAPACITY_LIMIT
                self._update_capacity_limit()
                # 如果升級成功（有新的 next level），允許繼續
                if self.CAPACITY_LIMIT > old_limit:
                    new_lv = self._current_level
                    warning = f"⚡ Level Up! Lv.{new_lv['level']} {new_lv['name']} ({new_lv['label']}) — 算力容量已擴充"
                    self._emit_warning(warning, "LEVEL_UP")
                    self._throttle_active = False
                    return {
                        "allowed": True,
                        "level": "OK",
                        "remaining": self.capacity_remaining,
                        "warning": warning,
                        "throttle": False,
                    }
            # 真的全部等級都滿了
            warning = f"⚠️ 算力已達最高等級 ({self.tops:.2f}T)！"
            self._emit_warning(warning, "FULL")
            return {
                "allowed": True,  # v13.4: 即使滿了也允許繼續（不阻塞用戶）
                "level": level,
                "remaining": remaining,
                "warning": warning,
                "throttle": True,
            }

        if needed_ops > remaining:
            warning = f"⚠️ 算力不足！需要 {needed_ops/1e12:.4f}T，剩餘 {remaining/1e12:.2f}T。"
            self._emit_warning(warning, "INSUFFICIENT")
            return {
                "allowed": False,
                "level": level,
                "remaining": remaining,
                "warning": warning,
                "throttle": True,
            }

        warning = None
        if level == "ALERT":
            warning = f"⚡ 算力即將滿載 ({self.progress_pct:.1f}%)，只處理必要任務。剩餘 {self.capacity_remaining_tops:.2f}T"
            self._emit_warning(warning, "ALERT")
            self._throttle_active = True
        elif level == "WARN":
            warning = f"📊 算力使用已達 {self.progress_pct:.1f}%，優先核心任務。剩餘 {self.capacity_remaining_tops:.2f}T"
            self._emit_warning(warning, "WARN")
        elif level == "INFO":
            warning = f"📈 算力持續累計中 ({self.progress_pct:.1f}%)，V42 正在變得更聰明"

        return {
            "allowed": True,
            "level": level,
            "remaining": remaining,
            "warning": warning,
            "throttle": level in ("ALERT", "FULL"),
        }

    def _emit_warning(self, message, level):
        """發出算力警告"""
        self._capacity_warnings.append({
            "ts": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "level": level,
            "message": message,
            "ops": self.total_ops,
            "pct": round(self.progress_pct, 2),
        })
        # 最多保留 50 條
        self._capacity_warnings = self._capacity_warnings[-50:]

    def estimate_ops(self, model_name, input_tokens, output_tokens=0):
        """預估一次操作需要的 OPS（不實際記錄）
        
        用於 V42SmartRouter 的事前判斷
        Formula: OPS = 2 × N_params × (input_tokens + output_tokens)
        Reference: Kaplan et al. 2020, Eq. 1
        """
        params = self._get_model_params(model_name)
        return 2 * params * (input_tokens + output_tokens)

    def record_inference(self, model_name, input_tokens, output_tokens):
        """記錄一次 LLM 推理的算力消耗
        
        Formula: OPS = 2 × N × (T_in + T_out)  [Kaplan 2020]
        v13.4: 不再硬性阻塞 — 達到上限時自動升級
        """
        params = self._get_model_params(model_name)
        ops = 2 * params * (input_tokens + output_tokens)
        self.total_ops += ops
        self.session_ops += ops
        self.inference_count += 1
        # v13.4: 累加後檢查是否需要升級
        if self.total_ops >= self.CAPACITY_LIMIT:
            self._update_capacity_limit()
        return ops

    def record_embedding(self, model_name, tokens):
        """記錄一次嵌入的算力消耗
        
        Formula: OPS = 2 × N_embed × T  [Kaplan 2020]
        """
        params = self._get_model_params(model_name)
        ops = 2 * params * tokens
        self.total_ops += ops
        self.session_ops += ops
        self.embed_count += 1
        if self.total_ops >= self.CAPACITY_LIMIT:
            self._update_capacity_limit()
        return ops

    def record_du_ops(self, ops):
        """記錄 V42 DU (Deep Understanding) 內部計算的算力"""
        self.total_ops += ops
        self.session_ops += ops
        self.du_train_ops += ops
        if self.total_ops >= self.CAPACITY_LIMIT:
            self._update_capacity_limit()
        return ops

    def record_self_code_ops(self, ops):
        """記錄自我程式碼理解消耗的算力"""
        self.total_ops += ops
        self.session_ops += ops
        self.self_code_ops += ops
        if self.total_ops >= self.CAPACITY_LIMIT:
            self._update_capacity_limit()
        return ops

    def record_folder_learn_ops(self, ops):
        """記錄資料夾學習消耗的算力"""
        self.total_ops += ops
        self.session_ops += ops
        self.folder_learn_ops += ops
        if self.total_ops >= self.CAPACITY_LIMIT:
            self._update_capacity_limit()
        return ops

    def reset_capacity(self, confirm_code="V42-RESET"):
        """重置算力容量（需要確認碼）
        
        這是管理員級操作，用於：
        1. 算力已滿時清理
        2. 開始新的算力週期
        """
        if confirm_code != "V42-RESET":
            return False
        old_total = self.total_ops
        self.total_ops = 0
        self.session_ops = 0
        self.inference_count = 0
        self.embed_count = 0
        self.self_code_ops = 0
        self.folder_learn_ops = 0
        self.du_train_ops = 0
        self._throttle_active = False
        self._capacity_warnings.append({
            "ts": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "level": "RESET",
            "message": f"算力已重置 (之前: {old_total/1e12:.2f}T)",
            "ops": 0,
            "pct": 0,
        })
        self.save_state()
        return True

    def _get_model_params(self, model_name):
        """查找模型的參數量"""
        model_name = str(model_name or "").lower()
        for key, params in self.MODEL_PARAMS.items():
            if key in model_name or model_name.startswith(key.split(":")[0]):
                return params
        # 預設 3B
        return 3_000_000_000

    @property
    def tops(self):
        """當前累計算力 (TOPS = Tera OPS)"""
        return self.total_ops / 1e12

    @property
    def target_tops(self):
        return self.CAPACITY_LIMIT / 1e12  # v13.4: 動態目標

    @property
    def progress_pct(self):
        return min(100.0, self.tops / self.target_tops * 100.0)

    def status(self):
        lv = getattr(self, '_current_level', self.COMPUTE_LEVELS[0])
        nxt = getattr(self, '_next_level', None)
        return {
            "total_ops": self.total_ops,
            "session_ops": self.session_ops,
            "tops": round(self.tops, 4),
            "target_tops": self.target_tops,
            "target_readable": f"Lv.{lv['level']} {lv['name']} ({lv['label']})",
            "progress_pct": round(self.progress_pct, 2),
            "current_level": lv["level"],
            "current_level_name": lv["name"],
            "next_level": nxt["level"] if nxt else None,
            "next_level_name": nxt["name"] if nxt else "MAX",
            "inference_count": self.inference_count,
            "embed_count": self.embed_count,
            "self_code_ops": self.self_code_ops,
            "folder_learn_ops": self.folder_learn_ops,
            "du_train_ops": self.du_train_ops,
            "gpu_name": self._gpu_name,
            "gpu_detected": self._gpu_detected,
        }


# ═══════════════════════════════════════════════════
# 3. V42SelfCodeUnderstanding — LLM 驅動的自我程式碼理解
# ═══════════════════════════════════════════════════
class V42SelfCodeUnderstanding:
    """V42 獨一無二的能力：用 LLM 完全理解自己的原始碼

    工作流程:
    1. 讀取 christine_final.py 原始碼
    2. 分段送進 Ollama LLM 分析
    3. 產生每個函式/類別的「能力地圖」
    4. 快取分析結果 (避免重複分析)
    5. 當查詢「你能做什麼」時，從能力地圖檢索
    """

    def __init__(self, ollama_client, gpu_engine):
        self.ollama = ollama_client
        self.gpu = gpu_engine
        self._cache = {}  # {function_name: {summary, capabilities, limitations}}
        self._code_sections = []  # [{name, kind, line, code}]
        self._analyzed = False
        self._load_cache()

    def _load_cache(self):
        try:
            if os.path.exists(_SELF_UNDERSTANDING_CACHE):
                with open(_SELF_UNDERSTANDING_CACHE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._cache = data.get("cache", {})
                self._code_sections = data.get("sections", [])
                if self._cache:
                    self._analyzed = True
        except Exception:
            pass

    def _save_cache(self):
        try:
            data = {
                "cache": self._cache,
                "sections": self._code_sections[:500],
                "last_analysis": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "total_functions": len(self._cache),
            }
            with open(_SELF_UNDERSTANDING_CACHE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def scan_source_code(self, source_path=None):
        """掃描自己的原始碼，提取所有函式和類別"""
        import re
        source_path = source_path or os.path.abspath("christine_final.py")
        if not os.path.exists(source_path):
            # 嘗試其他可能的路徑
            for p in [os.path.join(_CHRISTINE_BASE_LLM, "christine_final.py"), "christine_final.py"]:
                if os.path.exists(p):
                    source_path = p
                    break
            else:
                return []

        try:
            with open(source_path, "r", encoding="utf-8", errors="ignore") as f:
                code = f.read()
        except Exception:
            return []

        lines = code.splitlines()
        sections = []
        func_re = re.compile(r'^(\s*)def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(')
        class_re = re.compile(r'^class\s+([a-zA-Z_][a-zA-Z0-9_]*)')

        for i, line in enumerate(lines):
            cm = class_re.match(line)
            if cm:
                section = "\n".join(lines[max(0, i-2):min(len(lines), i+20)])
                sections.append({
                    "name": cm.group(1),
                    "kind": "class",
                    "line": i + 1,
                    "code": section[:2000],
                })
                continue
            fm = func_re.match(line)
            if fm:
                indent = fm.group(1)
                name = fm.group(2)
                section = "\n".join(lines[max(0, i-2):min(len(lines), i+25)])
                sections.append({
                    "name": name,
                    "kind": "method" if indent else "function",
                    "line": i + 1,
                    "code": section[:2000],
                })

        self._code_sections = sections
        return sections

    def analyze_section(self, section, ollama_client=None):
        """用 LLM 分析一個程式碼段落的能力"""
        client = ollama_client or self.ollama
        if not client or not client.is_ready:
            return None

        name = section.get("name", "unknown")
        if name in self._cache:
            return self._cache[name]

        prompt = f"""分析以下 Python 程式碼段落，用 JSON 格式回答：
1. summary: 一句話描述這段程式碼的功能
2. capabilities: 這段程式碼能做什麼（列表）
3. limitations: 限制或不能做什麼（列表）
4. category: 屬於哪個類別 (ai/system/ui/network/data/utility/other)

程式碼：
```python
{section.get('code', '')[:1500]}
```

只回答 JSON，不要其他文字。"""

        result = client.chat(prompt, temperature=0.1, max_tokens=500)
        if result and result.get("content"):
            # 記錄算力
            input_tokens = len(prompt) // 4
            output_tokens = result.get("eval_count", len(result["content"]) // 4)
            ops = self.gpu.record_inference(
                client._chat_model, input_tokens, output_tokens
            )
            self.gpu.record_self_code_ops(ops)

            # 嘗試解析 JSON
            content = result["content"]
            try:
                # 嘗試提取 JSON
                import re
                json_match = re.search(r'\{[^{}]*\}', content, re.DOTALL)
                if json_match:
                    parsed = json.loads(json_match.group())
                else:
                    parsed = json.loads(content)
                self._cache[name] = {
                    "summary": parsed.get("summary", content[:200]),
                    "capabilities": parsed.get("capabilities", []),
                    "limitations": parsed.get("limitations", []),
                    "category": parsed.get("category", "other"),
                    "line": section.get("line", 0),
                    "kind": section.get("kind", "unknown"),
                }
            except (json.JSONDecodeError, Exception):
                self._cache[name] = {
                    "summary": content[:300],
                    "capabilities": [],
                    "limitations": [],
                    "category": "other",
                    "line": section.get("line", 0),
                    "kind": section.get("kind", "unknown"),
                }
            return self._cache[name]
        return None

    def analyze_all(self, max_sections=50):
        """分析所有程式碼段落（限制數量避免太慢）"""
        if not self._code_sections:
            self.scan_source_code()

        analyzed = 0
        for section in self._code_sections[:max_sections]:
            if section["name"] not in self._cache:
                result = self.analyze_section(section)
                if result:
                    analyzed += 1
                    # 每分析 10 個存檔一次
                    if analyzed % 10 == 0:
                        self._save_cache()

        self._save_cache()
        self._analyzed = True
        return analyzed

    def query_capability(self, query):
        """查詢 V42 是否有某個能力"""
        query_lower = query.lower()
        results = []
        for name, info in self._cache.items():
            score = 0
            summary = str(info.get("summary", "")).lower()
            caps = " ".join(str(c) for c in info.get("capabilities", [])).lower()
            # 簡單的字元重疊匹配
            q_chars = set(query_lower)
            s_chars = set(summary + " " + caps)
            overlap = len(q_chars & s_chars) / max(len(q_chars), 1)
            if overlap > 0.3:
                score = overlap
                results.append((name, score, info))
        results.sort(key=lambda x: -x[1])
        return results[:10]

    def stats(self):
        return {
            "total_sections_scanned": len(self._code_sections),
            "total_analyzed": len(self._cache),
            "analyzed": self._analyzed,
            "categories": {},
        }


# ═══════════════════════════════════════════════════
# 4. V42FolderLearner — 資料夾學習引擎
# ═══════════════════════════════════════════════════
class V42FolderLearner:
    """掃描 DD 下所有資料夾，用 LLM 學習文件內容

    學習的資料夾:
      - F:\\AI夥伴\\記憶資料夾\\             (記憶資料)
      - F:\\AI夥伴\\記憶資料夾\\深度學習\\    (深度學習資料)
      - F:\\AI夥伴\\記憶資料夾\\projects\\    (專案資料)
      - F:\\AI夥伴\\記憶資料夾\\christine_v42\\ (V42 資料)

    學習方式:
      1. 掃描新增/修改的文件
      2. 用 LLM 生成摘要
      3. 用 Ollama embed 生成向量
      4. 累計算力到 100T 目標
    """

    SUPPORTED_EXTENSIONS = {
        ".txt", ".md", ".json", ".py", ".js", ".ts", ".html", ".css",
        ".csv", ".yaml", ".yml", ".log", ".bat", ".ps1", ".ini", ".cfg",
        ".toml", ".xml", ".pdf",
    }

    def __init__(self, ollama_client, gpu_engine):
        self.ollama = ollama_client
        self.gpu = gpu_engine
        self._learned_files = {}  # {path: {mtime, size, summary_hash}}
        self._summaries = {}      # {path: summary_text}
        self._total_files_learned = 0
        self._total_chars_processed = 0
        self._load_state()

    def _load_state(self):
        try:
            if os.path.exists(_FOLDER_LEARNING_STATE):
                with open(_FOLDER_LEARNING_STATE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._learned_files = data.get("learned_files", {})
                self._total_files_learned = data.get("total_files_learned", 0)
                self._total_chars_processed = data.get("total_chars_processed", 0)
        except Exception:
            pass

    def _save_state(self):
        try:
            data = {
                "learned_files": self._learned_files,
                "total_files_learned": self._total_files_learned,
                "total_chars_processed": self._total_chars_processed,
                "last_learn": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
            with open(_FOLDER_LEARNING_STATE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def scan_new_files(self, folders=None):
        """掃描需要學習的新文件"""
        if folders is None:
            folders = [
                _DD,
                os.path.join(_DD, "深度學習"),
                os.path.join(_DD, "projects"),
            ]

        new_files = []
        for folder in folders:
            if not os.path.exists(folder):
                continue
            try:
                for root, dirs, files in os.walk(folder):
                    dirs[:] = [d for d in dirs if not d.startswith('.')]
                    for fname in files:
                        fpath = os.path.join(root, fname)
                        _, ext = os.path.splitext(fname)
                        if ext.lower() not in self.SUPPORTED_EXTENSIONS:
                            continue
                        try:
                            stat = os.stat(fpath)
                            if stat.st_size == 0 or stat.st_size > 5_000_000:
                                continue
                            # 檢查是否已學習且未修改
                            if fpath in self._learned_files:
                                reg = self._learned_files[fpath]
                                if (reg.get("mtime") == stat.st_mtime and
                                    reg.get("size") == stat.st_size):
                                    continue
                            new_files.append(fpath)
                        except Exception:
                            continue
            except Exception:
                continue
        return new_files

    def learn_file(self, file_path):
        """用 LLM 學習一個文件"""
        if not self.ollama or not self.ollama.is_ready:
            # 沒有 LLM 也可以做基本學習（記錄 OPS）
            return self._learn_without_llm(file_path)

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read(10000)  # 最多讀 10KB
        except Exception:
            return None

        if not text.strip():
            return None

        # 用 LLM 生成摘要
        fname = os.path.basename(file_path)
        prompt = f"用一段簡短的中文摘要描述以下文件的內容和用途 ({fname}):\n\n{text[:3000]}"

        result = self.ollama.chat(prompt, temperature=0.1, max_tokens=200)
        summary = ""
        if result and result.get("content"):
            summary = result["content"]
            input_tokens = len(prompt) // 4
            output_tokens = result.get("eval_count", len(summary) // 4)
            ops = self.gpu.record_inference(
                self.ollama._chat_model, input_tokens, output_tokens
            )
            self.gpu.record_folder_learn_ops(ops)

        # 用 embed API 生成向量
        embed_vec = self.ollama.embed(text[:2000])
        if embed_vec:
            embed_tokens = len(text[:2000]) // 4
            ops = self.gpu.record_embedding(self.ollama._embed_model, embed_tokens)
            self.gpu.record_folder_learn_ops(ops)

        # 記錄學習完成
        try:
            stat = os.stat(file_path)
            self._learned_files[file_path] = {
                "mtime": stat.st_mtime,
                "size": stat.st_size,
                "summary_hash": hashlib.md5(summary.encode()).hexdigest()[:16],
                "ts": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
        except Exception:
            pass

        self._total_files_learned += 1
        self._total_chars_processed += len(text)

        return {
            "file": fname,
            "summary": summary[:200],
            "chars": len(text),
        }

    def _learn_without_llm(self, file_path):
        """沒有 LLM 時的基本學習（用 hash 向量 + OPS 累計）"""
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read(10000)
        except Exception:
            return None

        if not text.strip():
            return None

        # 基本 OPS：模擬 hash 編碼
        ops = len(text) * 4096  # dim=4096 的 hash 向量計算
        self.gpu.record_folder_learn_ops(ops)

        try:
            stat = os.stat(file_path)
            self._learned_files[file_path] = {
                "mtime": stat.st_mtime,
                "size": stat.st_size,
                "summary_hash": hashlib.md5(text[:1000].encode()).hexdigest()[:16],
                "ts": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
        except Exception:
            pass

        self._total_files_learned += 1
        self._total_chars_processed += len(text)
        return {"file": os.path.basename(file_path), "chars": len(text)}

    def learn_all(self, max_files=20):
        """學習所有新文件（限制數量避免阻塞啟動）"""
        new_files = self.scan_new_files()
        if not new_files:
            return {"learned": 0, "total": self._total_files_learned}

        learned = 0
        for fpath in new_files[:max_files]:
            result = self.learn_file(fpath)
            if result:
                learned += 1

        self._save_state()
        return {
            "learned": learned,
            "pending": max(0, len(new_files) - max_files),
            "total": self._total_files_learned,
            "total_chars": self._total_chars_processed,
        }

    def stats(self):
        return {
            "total_files_learned": self._total_files_learned,
            "total_chars_processed": self._total_chars_processed,
            "learned_files_count": len(self._learned_files),
        }


# ═══════════════════════════════════════════════════
# 5. V42SmartRouter — 智慧算力路由判斷 (含自我能力評估)
# ═══════════════════════════════════════════════════
class V42SmartRouter:
    """V42 的大腦決策核心：先自我評估能力，再決定路由
    
    決策流程 (V42 Self-Assessment Pipeline):
    ┌────────────────────────────────────────────────────────────┐
    │ Step 1: 分析查詢複雜度 (query_complexity_score)            │
    │   → 字數、句法深度、專業術語密度、多步驟需求              │
    │                                                            │
    │ Step 2: V42 自我能力評估 (self_capability_assessment)      │
    │   → 檢查知識庫是否涵蓋、算力是否足夠、過去成功率          │
    │                                                            │
    │ Step 3: 算力預算檢查 (compute_budget_check)                │
    │   → 預估 OPS 需求、檢查剩餘容量、是否在節流模式          │
    │                                                            │
    │ Step 4: 路由決策 (routing_decision)                        │
    │   Level 1 — V42 本地直接處理（不消耗 API）                 │
    │   Level 2 — Ollama 本地 LLM 處理（消耗本地算力）           │
    │   Level 3 — 丟給 Claude AI（消耗 API 費用）                │
    │                                                            │
    │ 特色: V42 必須先判斷自己能不能做，不能才往上交             │
    │ 這是 V42 作為「完美控制自己程式的大腦」的核心能力          │
    └────────────────────────────────────────────────────────────┘
    """

    # 各 Level 的類別映射
    LEVEL1_LOCAL = {
        "conversation", "greeting", "emotion", "math", "time_date",
        "status", "joke", "acknowledge", "farewell", "identity",
        "unit_convert", "schedule", "diary",
    }
    LEVEL2_OLLAMA = {
        "code", "algorithm", "translation", "analysis", "summarize",
        "knowledge", "creative", "utility", "password_gen",
    }
    LEVEL3_CLOUD = {
        "browser", "web", "github", "large_code_project",
        "self_update", "media", "document", "circuit",
    }

    # 複雜度權重 (用於自動評估查詢難度)
    COMPLEXITY_KEYWORDS = {
        "high": {"實作", "implement", "完整", "系統", "架構", "design", "multi", "多步",
                 "全部", "所有", "整合", "integrate", "deploy", "部署", "生產環境"},
        "medium": {"分析", "analyze", "翻譯", "translate", "程式", "code", "解釋",
                   "explain", "比較", "compare", "優化", "optimize", "修改", "fix"},
        "low": {"你好", "hello", "早安", "什麼時間", "天氣", "today", "笑話", "joke",
                "謝謝", "thanks", "再見", "bye", "你是誰", "計算", "convert"},
    }

    # 算力門檻
    MIN_OPS_FOR_LOCAL = 1_000_000

    def __init__(self, ollama_client, gpu_engine, self_understanding=None):
        self.ollama = ollama_client
        self.gpu = gpu_engine
        self.self_understanding = self_understanding
        self._route_history = []  # 路由歷史（用於學習）
        self._success_rate = {"level1": 0.95, "level2": 0.80, "level3": 0.99}

    def assess_query_complexity(self, query):
        """Step 1: 分析查詢複雜度
        
        Returns:
            float: 0.0 (極簡) ~ 1.0 (極複雜)
        """
        q = str(query or "").lower()
        q_len = len(q)
        
        # 基礎分數：按長度
        if q_len < 20:
            base_score = 0.1
        elif q_len < 100:
            base_score = 0.3
        elif q_len < 500:
            base_score = 0.5
        elif q_len < 2000:
            base_score = 0.7
        else:
            base_score = 0.9

        # 關鍵字調整
        for kw in self.COMPLEXITY_KEYWORDS["high"]:
            if kw in q:
                base_score = max(base_score, 0.7)
                base_score += 0.05
        for kw in self.COMPLEXITY_KEYWORDS["low"]:
            if kw in q:
                base_score = min(base_score, 0.3)

        # 多步驟指標：問號/逗號/「然後」/「接著」數量
        step_indicators = q.count("?") + q.count("？") + q.count("然後") + q.count("接著") + q.count("and then")
        base_score += step_indicators * 0.05

        return round(min(1.0, max(0.0, base_score)), 3)

    def assess_self_capability(self, query, mode=None):
        """Step 2: V42 自我能力評估 — 我能做這件事嗎？
        
        這是 V42 獨一無二的能力：它能判斷自己能不能勝任一個任務
        
        Returns:
            dict: {
                can_handle: bool,
                confidence: float (0~1),
                reason: str,
                knowledge_coverage: float (0~1),
                past_success_rate: float (0~1),
            }
        """
        mode = str(mode or "general").lower()
        
        # 基本能力判斷
        if mode in self.LEVEL1_LOCAL:
            return {
                "can_handle": True,
                "confidence": 0.95,
                "reason": f"'{mode}' 是 V42 核心能力範圍",
                "knowledge_coverage": 1.0,
                "past_success_rate": self._success_rate.get("level1", 0.95),
            }

        # 從自我理解快取中查詢
        knowledge_coverage = 0.0
        if self.self_understanding and self.self_understanding._analyzed:
            caps = self.self_understanding.query_capability(str(query or ""))
            if caps:
                # 有匹配的能力
                best_score = caps[0][1] if caps else 0
                knowledge_coverage = min(1.0, best_score)

        # 算力評估
        estimated_ops = self._estimate_task_ops(mode, len(str(query or "")))
        capacity_check = self.gpu.check_capacity(estimated_ops)

        can_handle = (
            mode in self.LEVEL2_OLLAMA and
            self.ollama and self.ollama.is_ready and
            capacity_check["allowed"] and
            not capacity_check.get("throttle", False)
        )

        confidence = 0.5
        if can_handle:
            confidence = 0.6 + knowledge_coverage * 0.3
            if self.ollama and self.ollama.is_ready:
                confidence += 0.1
        else:
            confidence = max(0.1, knowledge_coverage * 0.4)

        return {
            "can_handle": can_handle,
            "confidence": round(min(0.99, confidence), 3),
            "reason": f"能力覆蓋 {knowledge_coverage:.0%} | 算力{'充足' if capacity_check['allowed'] else '不足'} | Ollama {'就緒' if self.ollama and self.ollama.is_ready else '離線'}",
            "knowledge_coverage": round(knowledge_coverage, 3),
            "past_success_rate": self._success_rate.get("level2", 0.80),
            "estimated_ops": estimated_ops,
            "capacity_check": capacity_check,
        }

    def _estimate_task_ops(self, mode, query_len):
        """預估任務需要的 OPS
        
        Formula basis: Kaplan et al. 2020, scaled by task complexity
        """
        # 基礎 OPS (根據任務類型)
        base_ops = {
            "conversation": 50_000,
            "greeting": 10_000,
            "math": 100_000,
            "code": 6_000_000_000,  # ~6B (Ollama 3B model)
            "algorithm": 10_000_000_000,
            "translation": 3_000_000_000,
            "analysis": 6_000_000_000,
            "summarize": 4_000_000_000,
            "knowledge": 2_000_000_000,
            "creative": 8_000_000_000,
        }.get(mode, 1_000_000_000)  # 預設 1B

        # 根據查詢長度調整 (longer query ≈ more tokens ≈ more OPS)
        token_multiplier = max(1.0, query_len / 100)
        return int(base_ops * min(token_multiplier, 10.0))

    def route(self, query, mode=None, v42_only=False, user_profile=None):
        """智慧路由決策 — V42 大腦的核心決策函式

        流程:
        1. 分析查詢複雜度
        2. V42 自我能力評估
        3. 算力預算檢查
        4. 做出路由決策
        5. 記錄決策（用於持續學習）

        Args:
            query: 使用者查詢
            mode: 已分類的模式
            v42_only: 是否強制 V42 模式
            user_profile: 使用者設定檔（影響算力分配）

        Returns:
            dict: 完整的路由決策
        """
        mode = str(mode or "general").lower()

        # Step 1: 查詢複雜度
        complexity = self.assess_query_complexity(query)

        # Step 2: 自我能力評估
        self_assessment = self.assess_self_capability(query, mode)

        # Step 3: 算力預算
        estimated_ops = self_assessment.get("estimated_ops", 0)
        capacity_check = self.gpu.check_capacity(estimated_ops)

        # Step 4: 路由決策
        # Level 1: 本地直接處理
        if mode in self.LEVEL1_LOCAL:
            decision = {
                "level": 1,
                "handler": "v42_local",
                "reason": f"簡單查詢 '{mode}' — V42 本地直接處理 (複雜度 {complexity})",
                "can_local": True,
                "estimated_ops": 50_000,
                "complexity": complexity,
                "self_assessment": self_assessment,
                "capacity": capacity_check,
            }
            self._record_route(decision)
            return decision

        # V42_ONLY 模式
        if v42_only:
            if self.ollama and self.ollama.is_ready and capacity_check.get("allowed", True):
                decision = {
                    "level": 2,
                    "handler": "ollama_llm",
                    "reason": "V42_ONLY 模式 — Ollama 本地 LLM",
                    "can_local": True,
                    "estimated_ops": estimated_ops,
                    "complexity": complexity,
                    "self_assessment": self_assessment,
                    "capacity": capacity_check,
                }
            else:
                decision = {
                    "level": 2,
                    "handler": "v42_local",
                    "reason": f"V42_ONLY 模式 — {'算力不足' if not capacity_check.get('allowed', True) else 'Ollama 未連線'}，V42 本地盡力處理",
                    "can_local": True,
                    "estimated_ops": min(estimated_ops, 500_000),
                    "complexity": complexity,
                    "self_assessment": self_assessment,
                    "capacity": capacity_check,
                }
            self._record_route(decision)
            return decision

        # Level 2: V42 先判斷自己能不能做
        if self_assessment["can_handle"] and mode in self.LEVEL2_OLLAMA:
            # V42 判定自己可以做！
            if complexity <= 0.5 and self_assessment["confidence"] >= 0.7:
                decision = {
                    "level": 2,
                    "handler": "ollama_llm",
                    "reason": f"V42 自我評估: 有能力處理 '{mode}' (信心 {self_assessment['confidence']:.0%}, 複雜度 {complexity})",
                    "can_local": True,
                    "estimated_ops": estimated_ops,
                    "complexity": complexity,
                    "self_assessment": self_assessment,
                    "capacity": capacity_check,
                }
                self._record_route(decision)
                return decision
            elif complexity <= 0.7:
                # 中等複雜度，嘗試本地
                decision = {
                    "level": 2,
                    "handler": "ollama_llm",
                    "reason": f"V42 嘗試本地處理 '{mode}' (中等複雜度 {complexity})",
                    "can_local": True,
                    "estimated_ops": estimated_ops,
                    "complexity": complexity,
                    "self_assessment": self_assessment,
                    "capacity": capacity_check,
                }
                self._record_route(decision)
                return decision

        # Level 2 但 Ollama 可用且算力夠（降級場景）
        if mode in self.LEVEL2_OLLAMA and self.ollama and self.ollama.is_ready:
            if capacity_check.get("allowed", True) and complexity <= 0.8:
                decision = {
                    "level": 2,
                    "handler": "ollama_llm",
                    "reason": f"'{mode}' 由 Ollama 處理 (算力允許，複雜度 {complexity})",
                    "can_local": True,
                    "estimated_ops": estimated_ops,
                    "complexity": complexity,
                    "self_assessment": self_assessment,
                    "capacity": capacity_check,
                }
                self._record_route(decision)
                return decision

        # Level 3: 複雜任務 or 能力/算力不足 → Claude
        decision = {
            "level": 3,
            "handler": "claude_api",
            "reason": f"V42 判定: '{mode}' 超出本地能力 (複雜度 {complexity}, 信心 {self_assessment['confidence']:.0%}) — 交由 Claude AI",
            "can_local": False,
            "estimated_ops": 0,
            "complexity": complexity,
            "self_assessment": self_assessment,
            "capacity": capacity_check,
        }
        self._record_route(decision)
        return decision

    def _record_route(self, decision):
        """記錄路由決策（用於持續學習和改進）"""
        self._route_history.append({
            "ts": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "level": decision["level"],
            "handler": decision["handler"],
            "complexity": decision.get("complexity", 0),
        })
        # 只保留最近 200 筆
        self._route_history = self._route_history[-200:]

    def update_success_rate(self, level, success):
        """更新某個 level 的成功率（用於路由學習）"""
        key = f"level{level}"
        old_rate = self._success_rate.get(key, 0.8)
        # 指數移動平均 (EMA, α=0.05)
        alpha = 0.05
        new_rate = old_rate * (1 - alpha) + (1.0 if success else 0.0) * alpha
        self._success_rate[key] = round(new_rate, 4)

    def routing_stats(self):
        """路由統計"""
        level_counts = {}
        for r in self._route_history:
            lv = r.get("level", 0)
            level_counts[lv] = level_counts.get(lv, 0) + 1
        return {
            "total_routes": len(self._route_history),
            "level_distribution": level_counts,
            "success_rates": dict(self._success_rate),
        }


# ═══════════════════════════════════════════════════
# 6. V42PermanentFolderMemory — 永久資料夾記憶
# ═══════════════════════════════════════════════════
class V42PermanentFolderMemory:
    """V42 獨一無二的能力：永久記住資料夾結構和內容

    這是目前 AI 市場上沒有的能力:
    ┌────────────────────────────────────────────────────────────┐
    │ 1. 永久記住所有見過的資料夾和檔案                          │
    │ 2. 記住每個檔案的內容摘要（即使檔案被刪除）                │
    │ 3. 跨 session 不遺忘 — 重啟程式後記憶完整保留              │
    │ 4. 累積式知識圖譜 — 越用越聰明                            │
    │ 5. 資料夾關聯分析 — 理解檔案之間的關係                     │
    │ 6. 不同使用者有獨立的記憶空間                              │
    └────────────────────────────────────────────────────────────┘

    存儲結構:
    {
        "folders": {
            "path": {
                "first_seen": timestamp,
                "last_seen": timestamp,
                "visit_count": int,
                "files": {"filename": {summary, type, size, mtime}},
                "subfolder_count": int,
                "total_size_bytes": int,
                "tags": [str],
                "knowledge_summary": str,
            }
        },
        "knowledge_graph": {
            "nodes": [...],  # 知識節點
            "edges": [...],  # 關係邊
        },
        "stats": {...},
    }
    """

    def __init__(self):
        self._memory = {}       # {folder_path: folder_info}
        self._knowledge = {}    # {topic: knowledge}
        self._file_index = {}   # {file_path: file_info}
        self._total_visits = 0
        self._total_files_remembered = 0
        self._creation_time = None
        self._load()

    def _load(self):
        """載入永久記憶"""
        try:
            if os.path.exists(_PERMANENT_FOLDER_MEMORY_PATH):
                with open(_PERMANENT_FOLDER_MEMORY_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._memory = data.get("folders", {})
                self._knowledge = data.get("knowledge", {})
                self._file_index = data.get("file_index", {})
                self._total_visits = data.get("total_visits", 0)
                self._total_files_remembered = data.get("total_files_remembered", 0)
                self._creation_time = data.get("creation_time")
        except Exception:
            pass
        if not self._creation_time:
            self._creation_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def save(self):
        """持久化永久記憶到磁碟"""
        try:
            data = {
                "folders": self._memory,
                "knowledge": self._knowledge,
                "file_index": self._file_index,
                "total_visits": self._total_visits,
                "total_files_remembered": self._total_files_remembered,
                "creation_time": self._creation_time,
                "last_save": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "version": "v1.0",
            }
            os.makedirs(os.path.dirname(_PERMANENT_FOLDER_MEMORY_PATH), exist_ok=True)
            with open(_PERMANENT_FOLDER_MEMORY_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def remember_folder(self, folder_path, scan_depth=2):
        """永久記住一個資料夾及其內容
        
        Args:
            folder_path: 資料夾路徑
            scan_depth: 掃描深度（預設 2 層）
        """
        folder_path = os.path.abspath(folder_path)
        if not os.path.isdir(folder_path):
            return None

        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 取得或建立資料夾記憶
        if folder_path in self._memory:
            mem = self._memory[folder_path]
            mem["last_seen"] = now
            mem["visit_count"] = mem.get("visit_count", 0) + 1
        else:
            mem = {
                "first_seen": now,
                "last_seen": now,
                "visit_count": 1,
                "files": {},
                "subfolder_count": 0,
                "total_size_bytes": 0,
                "tags": [],
                "knowledge_summary": "",
            }
            self._memory[folder_path] = mem

        self._total_visits += 1

        # 掃描資料夾內容
        try:
            total_size = 0
            subfolder_count = 0
            file_count = 0
            
            for item in os.listdir(folder_path):
                item_path = os.path.join(folder_path, item)
                try:
                    if os.path.isdir(item_path):
                        subfolder_count += 1
                        # 遞迴記住子資料夾（深度控制）
                        if scan_depth > 1:
                            self.remember_folder(item_path, scan_depth - 1)
                    elif os.path.isfile(item_path):
                        stat = os.stat(item_path)
                        total_size += stat.st_size
                        file_count += 1
                        
                        # 記住檔案資訊
                        _, ext = os.path.splitext(item)
                        file_info = {
                            "name": item,
                            "ext": ext.lower(),
                            "size": stat.st_size,
                            "mtime": stat.st_mtime,
                            "last_seen": now,
                        }
                        mem["files"][item] = file_info
                        self._file_index[item_path] = file_info
                        
                        if item_path not in self._file_index:
                            self._total_files_remembered += 1
                except Exception:
                    continue

            mem["subfolder_count"] = subfolder_count
            mem["total_size_bytes"] = total_size
            mem["file_count"] = file_count

        except Exception:
            pass

        return mem

    def remember_file_content(self, file_path, summary=None, tags=None):
        """永久記住一個檔案的內容摘要
        
        即使檔案被刪除，記憶仍然保留
        """
        file_path = os.path.abspath(file_path)
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        info = self._file_index.get(file_path, {})
        info["content_summary"] = summary or info.get("content_summary", "")
        info["content_tags"] = tags or info.get("content_tags", [])
        info["content_remembered_at"] = now
        info["name"] = os.path.basename(file_path)
        self._file_index[file_path] = info

    def add_knowledge(self, topic, content, source=None):
        """添加知識到永久知識庫"""
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if topic in self._knowledge:
            self._knowledge[topic]["content"] = content
            self._knowledge[topic]["updated_at"] = now
            self._knowledge[topic]["update_count"] = self._knowledge[topic].get("update_count", 0) + 1
        else:
            self._knowledge[topic] = {
                "content": content,
                "source": source,
                "created_at": now,
                "updated_at": now,
                "update_count": 1,
            }

    def recall_folder(self, folder_path):
        """回憶一個資料夾（即使它已不存在）"""
        folder_path = os.path.abspath(folder_path)
        return self._memory.get(folder_path)

    def recall_file(self, file_path):
        """回憶一個檔案的資訊和摘要（即使檔案已被刪除）"""
        file_path = os.path.abspath(file_path)
        return self._file_index.get(file_path)

    def search_memory(self, keyword):
        """在永久記憶中搜索"""
        keyword_lower = keyword.lower()
        results = []
        
        # 搜索資料夾
        for path, info in self._memory.items():
            if keyword_lower in path.lower():
                results.append({"type": "folder", "path": path, "info": info})
        
        # 搜索檔案
        for path, info in self._file_index.items():
            name = info.get("name", os.path.basename(path)).lower()
            summary = str(info.get("content_summary", "")).lower()
            if keyword_lower in name or keyword_lower in summary or keyword_lower in path.lower():
                results.append({"type": "file", "path": path, "info": info})

        # 搜索知識
        for topic, info in self._knowledge.items():
            content = str(info.get("content", "")).lower()
            if keyword_lower in topic.lower() or keyword_lower in content:
                results.append({"type": "knowledge", "topic": topic, "info": info})

        return results[:50]

    def scan_all_known_folders(self):
        """重新掃描所有已知資料夾，更新記憶"""
        updated = 0
        for folder_path in list(self._memory.keys()):
            if os.path.isdir(folder_path):
                self.remember_folder(folder_path, scan_depth=1)
                updated += 1
        self.save()
        return updated

    def get_folder_tree(self, root=None):
        """取得資料夾樹狀結構"""
        root = root or _DD
        tree = {}
        for path, info in self._memory.items():
            if path.startswith(root):
                rel = os.path.relpath(path, root)
                tree[rel] = {
                    "files": len(info.get("files", {})),
                    "subfolders": info.get("subfolder_count", 0),
                    "size": info.get("total_size_bytes", 0),
                    "visits": info.get("visit_count", 0),
                }
        return tree

    def stats(self):
        return {
            "total_folders_remembered": len(self._memory),
            "total_files_remembered": len(self._file_index),
            "total_knowledge_entries": len(self._knowledge),
            "total_visits": self._total_visits,
            "creation_time": self._creation_time,
            "memory_persistent": True,
            "unique_feature": "永久記憶 — 跨 session 不遺忘，市場唯一",
        }


# ═══════════════════════════════════════════════════
# 7. V42UserProfile — 使用者個人化設定
# ═══════════════════════════════════════════════════
class V42UserProfile:
    """不同使用者有不同的 V42 效果
    
    功能:
    ┌────────────────────────────────────────────────┐
    │ 1. 每位使用者有獨立的算力配額                  │
    │ 2. 個人化的偏好設定（語言/風格/習慣）          │
    │ 3. 使用歷史和學習記錄                          │
    │ 4. 自訂的知識庫和記憶                          │
    │ 5. 不同的 V42 行為模式                         │
    └────────────────────────────────────────────────┘
    """

    def __init__(self):
        self._profiles = {}  # {user_id: profile}
        self._active_user = "default"
        self._load()

    def _load(self):
        try:
            if os.path.exists(_USER_PROFILES_PATH):
                with open(_USER_PROFILES_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._profiles = data.get("profiles", {})
                self._active_user = data.get("active_user", "default")
        except Exception:
            pass
        # 確保 default 使用者存在
        if "default" not in self._profiles:
            self._profiles["default"] = self._create_default_profile("default")

    def save(self):
        try:
            data = {
                "profiles": self._profiles,
                "active_user": self._active_user,
                "last_save": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
            with open(_USER_PROFILES_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _create_default_profile(self, user_id):
        """建立預設使用者設定"""
        return {
            "user_id": user_id,
            "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "display_name": user_id,
            "language": "zh-tw",
            "style": "friendly",  # friendly|professional|concise|creative
            "compute_quota": 1_000_000_000_000_000,  # 每人 1000T（可自訂）
            "compute_used": 0,
            "preferences": {
                "auto_learn": True,        # 自動學習新檔案
                "verbose_routing": False,  # 是否顯示路由詳情
                "preferred_model": None,   # 偏好的 Ollama 模型
                "max_response_length": 2048,
            },
            "stats": {
                "total_queries": 0,
                "total_sessions": 0,
                "favorite_modes": {},
                "last_active": None,
            },
        }

    def get_profile(self, user_id=None):
        """取得使用者設定"""
        user_id = user_id or self._active_user
        if user_id not in self._profiles:
            self._profiles[user_id] = self._create_default_profile(user_id)
        return self._profiles[user_id]

    def switch_user(self, user_id):
        """切換活躍使用者"""
        if user_id not in self._profiles:
            self._profiles[user_id] = self._create_default_profile(user_id)
        self._active_user = user_id
        p = self._profiles[user_id]
        p["stats"]["total_sessions"] = p["stats"].get("total_sessions", 0) + 1
        p["stats"]["last_active"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.save()
        return p

    def record_query(self, user_id=None, mode=None, ops_used=0):
        """記錄一次查詢"""
        user_id = user_id or self._active_user
        p = self.get_profile(user_id)
        p["stats"]["total_queries"] = p["stats"].get("total_queries", 0) + 1
        p["stats"]["last_active"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if mode:
            fav = p["stats"].setdefault("favorite_modes", {})
            fav[mode] = fav.get(mode, 0) + 1
        p["compute_used"] = p.get("compute_used", 0) + ops_used

    def get_compute_remaining(self, user_id=None):
        """取得使用者剩餘算力"""
        p = self.get_profile(user_id)
        quota = p.get("compute_quota", 1_000_000_000_000_000)
        # 自動升級舊配額 (100T → 1000T)
        if quota <= 100_000_000_000_000:
            quota = 1_000_000_000_000_000
            p["compute_quota"] = quota
        used = p.get("compute_used", 0)
        return max(0, quota - used)

    def list_users(self):
        return list(self._profiles.keys())


# ═══════════════════════════════════════════════════
# 8. V42ComputeSlotManager — 按需算力分配
# ═══════════════════════════════════════════════════
class V42ComputeSlotManager:
    """按需分配算力 — 只用需要的量，不浪費
    
    設計理念:
    ┌────────────────────────────────────────────────────────────┐
    │ 算力不是無限的，V42 必須聰明地分配:                        │
    │                                                            │
    │ 1. 簡單問候: ~50K OPS (幾乎不用算力)                       │
    │ 2. 數學計算: ~100K OPS (純 CPU 計算)                       │
    │ 3. 知識查詢: ~2B OPS (需要嵌入搜索)                        │
    │ 4. 程式碼生成: ~6B OPS (需要 LLM 推理)                     │
    │ 5. 複雜分析: ~10B OPS (多步 LLM + 推理)                    │
    │ 6. 深度學習: ~20B OPS (資料夾掃描 + 學習)                  │
    │                                                            │
    │ 每次任務前先「申請」算力 slot:                              │
    │   slot = allocate(estimated_ops)                           │
    │ 任務完成後「歸還」slot:                                     │
    │   release(slot_id, actual_ops)                             │
    │                                                            │
    │ 這確保算力被精確追蹤，不會超額使用                         │
    └────────────────────────────────────────────────────────────┘
    """

    def __init__(self, gpu_engine):
        self.gpu = gpu_engine
        self._active_slots = {}  # {slot_id: {allocated, started_at, task_type}}
        self._completed_slots = []
        self._total_allocated = 0
        self._total_actually_used = 0
        self._load()

    def _load(self):
        try:
            if os.path.exists(_COMPUTE_SLOTS_PATH):
                with open(_COMPUTE_SLOTS_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._total_allocated = data.get("total_allocated", 0)
                self._total_actually_used = data.get("total_actually_used", 0)
                self._completed_slots = data.get("completed_slots", [])[-100:]
        except Exception:
            pass

    def save(self):
        try:
            data = {
                "total_allocated": self._total_allocated,
                "total_actually_used": self._total_actually_used,
                "active_slots": len(self._active_slots),
                "completed_slots": self._completed_slots[-100:],
                "efficiency": self.efficiency,
                "last_save": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
            with open(_COMPUTE_SLOTS_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def allocate(self, estimated_ops, task_type="general"):
        """申請一個算力 slot
        
        Args:
            estimated_ops: 預估需要的 OPS
            task_type: 任務類型
            
        Returns:
            dict: {slot_id, allocated, allowed, warning}
            或 None（如果不允許）
        """
        # 檢查算力容量
        capacity = self.gpu.check_capacity(estimated_ops)
        
        if not capacity.get("allowed", True):
            return {
                "slot_id": None,
                "allocated": 0,
                "allowed": False,
                "warning": capacity.get("warning", "算力不足"),
            }

        slot_id = str(uuid.uuid4())[:8]
        self._active_slots[slot_id] = {
            "allocated": estimated_ops,
            "started_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "task_type": task_type,
        }
        self._total_allocated += estimated_ops

        return {
            "slot_id": slot_id,
            "allocated": estimated_ops,
            "allowed": True,
            "warning": capacity.get("warning"),
            "capacity_level": capacity.get("level", "OK"),
        }

    def release(self, slot_id, actual_ops=None):
        """歸還算力 slot
        
        Args:
            slot_id: slot ID
            actual_ops: 實際使用的 OPS（如果 None，使用預估值）
        """
        if slot_id not in self._active_slots:
            return False

        slot = self._active_slots.pop(slot_id)
        actual = actual_ops if actual_ops is not None else slot["allocated"]
        self._total_actually_used += actual

        self._completed_slots.append({
            "slot_id": slot_id,
            "allocated": slot["allocated"],
            "actual": actual,
            "efficiency": round(actual / max(1, slot["allocated"]), 4),
            "task_type": slot["task_type"],
            "completed_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        })

        return True

    @property
    def efficiency(self):
        """算力使用效率 (actual / allocated)"""
        if self._total_allocated == 0:
            return 1.0
        return round(self._total_actually_used / self._total_allocated, 4)

    def stats(self):
        return {
            "active_slots": len(self._active_slots),
            "total_allocated": self._total_allocated,
            "total_actually_used": self._total_actually_used,
            "efficiency": self.efficiency,
            "completed_count": len(self._completed_slots),
        }


# ═══════════════════════════════════════════════════
# 9. V42LocalLLMEngine — 統一門面 (V42 的大腦)
# ═══════════════════════════════════════════════════
class V42LocalLLMEngine:
    """V42 本地 LLM 引擎的統一門面 v2.0 — V42 的大腦核心

    整合 11 大子系統:
    ┌──────────────────────────────────────────────────────────┐
    │  1. Ollama 客戶端      — 純 urllib 連接本地 LLM           │
    │  2. GPU 算力追蹤        — 1000T (1P) OPS 容量管理        │
    │  3. 自我程式碼理解      — V42 完全理解自己原始碼           │
    │  4. 資料夾學習          — 深度學習資料夾讓 V42 越來越聰明 │
    │  5. 智慧路由 (含自評)   — 先判斷自己能不能做               │
    │  6. 永久資料夾記憶      — 跨 session 不遺忘（市場唯一）   │
    │  7. 使用者個人化        — 不同人有不同效果                 │
    │  8. 按需算力分配        — 只用需要的算力                   │
    │  9. 知識圖譜            — 累積式知識，越用越聰明           │
    │ 10. NEXUS v2.0          — 13 篇論文 + 5 獨創演算法        │
    │ 11. 自動工具發現        — V42 自我擴充                     │
    └──────────────────────────────────────────────────────────┘

    v2.0 新增能力:
      ★ 1000T (1P) OPS 容量
      ★ 知識優先路由 — 先查知識庫再問 AI
      ★ ARR 共振路由 — 不靠關鍵詞選工具
      ★ 碎形複雜度分析 — 數學判斷問題難度
      ★ 預測性知識蒸餾 — 預測下一個問題
      ★ 秒開機制 — 第二次啟動秒開
      ★ 進度條 UI — 每個步驟都有進度條
      ★ 認知共振 — 多模組超加性效應
    """

    VERSION = "2.0.0"

    def __init__(self):
        self._init_start = time.time()
        self.ollama = V42OllamaClient()
        self.gpu = V42GPUEngine()
        self.self_understanding = V42SelfCodeUnderstanding(self.ollama, self.gpu)
        self.folder_learner = V42FolderLearner(self.ollama, self.gpu)
        self.router = V42SmartRouter(self.ollama, self.gpu, self.self_understanding)
        self.permanent_memory = V42PermanentFolderMemory()
        self.user_profiles = V42UserProfile()
        self.compute_slots = V42ComputeSlotManager(self.gpu)
        self._initialized = False
        self._bg_thread = None
        self._bg_running = False
        self._init_progress = []  # 進度條記錄

        # ── NEXUS v2.0 認知融合引擎 ──
        # 13 篇論文 + 5 獨創演算法 + 7 新模組
        self.nexus = None
        self.nexus_v2 = None
        if _NEXUS_V2_AVAILABLE:
            try:
                self._log_progress("NEXUS v2.0", "載入中...")
                self.nexus_v2 = create_nexus_v2(dim=128)
                self.nexus = self.nexus_v2  # 向下相容
                self._log_progress("NEXUS v2.0", f"完成 ({self.nexus_v2._init_time_ms:.0f}ms)")
            except Exception:
                self.nexus_v2 = None
        if self.nexus is None and _NEXUS_AVAILABLE:
            try:
                self._log_progress("NEXUS v1", "載入中...")
                self.nexus = V42NexusEngine()
                self.nexus.load_state()
                self._log_progress("NEXUS v1", "完成 (v1 fallback)")
            except Exception:
                self.nexus = None

        self._init_time_ms = round((time.time() - self._init_start) * 1000, 2)

    def _log_progress(self, step, status, pct=None):
        """記錄初始化進度 (for UI 進度條)"""
        entry = {
            "step": step,
            "status": status,
            "ts": time.time(),
            "elapsed_ms": round((time.time() - self._init_start) * 1000, 2),
        }
        if pct is not None:
            entry["pct"] = pct
        self._init_progress.append(entry)

    def initialize(self):
        """初始化 v2.0 — 含進度條、秒開機制

        秒開邏輯:
          - 檢查是否有已保存的狀態
          - 檢查深度學習資料夾是否有新文件
          - 如果沒有新知識 → 跳過重新學習 → 秒開
        """
        init_start = time.time()

        # ─ Step 1: Ollama 連線 ─
        self._log_progress("Ollama", "連接中...", 10)
        ok, models = self.ollama.check_ollama()
        if ok:
            self._log_progress("Ollama", f"已連接 ({len(models)} 模型)", 15)
            self.ollama.auto_select_chat_model()
            self.ollama.ensure_model(self.ollama._embed_model)
            if self.ollama._chat_model:
                self.ollama.ensure_model(self.ollama._chat_model)
            self._log_progress("Ollama", f"模型: {self.ollama._chat_model or 'none'}", 20)
        else:
            self._log_progress("Ollama", "離線 (使用本地能力)", 20)

        # ─ Step 2: 永久記憶掃描 ─
        self._log_progress("永久記憶", "載入中...", 30)
        has_new_knowledge = False
        try:
            core_folders = [
                _DD,
                os.path.join(_DD, "深度學習"),
                os.path.join(_DD, "projects"),
                _V42_DIR,
            ]
            for i, folder in enumerate(core_folders):
                if os.path.isdir(folder):
                    self.permanent_memory.remember_folder(folder, scan_depth=2)
            self.permanent_memory.save()
            self._log_progress("永久記憶", f"已記憶 {len(self.permanent_memory._memory)} 個資料夾", 40)
        except Exception:
            self._log_progress("永久記憶", "載入完成 (部分)", 40)

        # ─ Step 3: 秒開檢查 — 有新知識嗎？ ─
        self._log_progress("秒開檢查", "檢查新知識...", 50)
        new_files = self.folder_learner.scan_new_files()
        if new_files:
            has_new_knowledge = True
            self._log_progress("秒開檢查", f"發現 {len(new_files)} 個新文件", 55)
        else:
            self._log_progress("秒開檢查", "無新知識 → 秒開模式 ⚡", 55)

        # ─ Step 4: 知識學習 (僅有新知識時) ─
        if has_new_knowledge:
            self._log_progress("知識學習", f"學習 {min(len(new_files), 10)} 個新文件...", 60)
            learn_result = self.folder_learner.learn_all(max_files=10)
            self._log_progress("知識學習",
                f"學習完成: {learn_result.get('learned', 0)} 個", 70)
        else:
            self._log_progress("知識學習", "跳過 (無新知識) ⚡", 70)

        # ─ Step 5: NEXUS v2 就緒 ─
        self._log_progress("NEXUS v2.0", "檢查狀態...", 80)
        if self.nexus_v2:
            self._log_progress("NEXUS v2.0",
                f"就緒 — {self.nexus_v2._total_queries} 次查詢, "
                f"容量 {self.nexus_v2._total_ops/self.nexus_v2.CAPACITY_LIMIT*100:.4f}%", 85)
        elif self.nexus:
            self._log_progress("NEXUS", "v1 模式運行中", 85)
        else:
            self._log_progress("NEXUS", "未載入 (純本地模式)", 85)

        # ─ Step 6: 使用者設定 ─
        self._log_progress("使用者設定", "載入中...", 90)
        active = self.user_profiles._active_user
        self._log_progress("使用者設定", f"使用者: {active}", 92)

        # ─ Step 7: 完成 ─
        init_ms = round((time.time() - init_start) * 1000, 2)
        self._log_progress("初始化完成", f"耗時 {init_ms:.0f}ms ✓", 100)

        self._initialized = True
        self._init_time_ms = init_ms
        return ok

    def embed(self, text):
        """用 Ollama 生成嵌入向量 (768D)，含按需算力分配"""
        if not self.ollama.is_ready:
            return None
        
        # 按需分配算力
        tokens = len(str(text or "")) // 4
        estimated_ops = self.gpu.estimate_ops(self.ollama._embed_model, tokens)
        slot = self.compute_slots.allocate(estimated_ops, "embedding")
        
        if slot and not slot.get("allowed", True):
            return None  # 算力不足

        vec = self.ollama.embed(text)
        actual_ops = 0
        if vec:
            actual_ops = self.gpu.record_embedding(self.ollama._embed_model, tokens)

        # 歸還算力 slot
        if slot and slot.get("slot_id"):
            self.compute_slots.release(slot["slot_id"], actual_ops)

        return vec

    def chat(self, prompt, system_prompt=None, temperature=0.3):
        """用 Ollama 進行聊天，含 NEXUS v2 知識優先路由 + 按需算力分配

        v2.0 流程:
          1. NEXUS v2 碎形複雜度分析
          2. 內建知識庫查詢 (可能直接回答)
          3. 深度學習資料夾 + 永久記憶搜索
          4. ARR 共振路由 (不靠關鍵詞)
          5. Ollama LLM 推理
          6. 認知共振放大
          7. 預測下一個問題
        """
        if not self.ollama.is_ready:
            # 即使 Ollama 離線，NEXUS v2 仍可提供基本回答
            if self.nexus_v2:
                result = self.nexus_v2.process(str(prompt or ""))
                if result.get("kb_used") and result.get("knowledge_base"):
                    kb = result["knowledge_base"]
                    return {
                        "content": f"{kb.get('desc', '')}: {kb.get('value', '')}",
                        "model": "V42-NEXUS-v2-knowledge",
                        "eval_count": 0,
                        "source": "nexus_v2_knowledge_base",
                    }
            return None

        # ── Step 1: NEXUS v2 前處理 ──
        nexus_result = None
        if self.nexus_v2:
            try:
                nexus_result = self.nexus_v2.process(str(prompt or ""))
                
                # 如果內建知識庫能回答，直接回答 (0 OPS for Ollama)
                if nexus_result.get("kb_used") and nexus_result.get("knowledge_base"):
                    kb = nexus_result["knowledge_base"]
                    # 記錄使用者查詢
                    self.user_profiles.record_query(ops_used=nexus_result.get("total_ops", 0))
                    return {
                        "content": f"{kb.get('desc', '')}: {kb.get('value', '')}",
                        "model": "V42-NEXUS-v2-knowledge",
                        "eval_count": 0,
                        "source": "nexus_v2_knowledge_base",
                        "nexus": nexus_result,
                    }
            except Exception:
                pass

        # ── Step 2: 深度學習資料夾 + 永久記憶搜索 ──
        memory_context = ""
        if self.permanent_memory:
            try:
                memory_results = self.permanent_memory.search_memory(
                    str(prompt or "")[:50]
                )
                if memory_results:
                    ctx_parts = []
                    for r in memory_results[:3]:
                        if r["type"] == "knowledge":
                            ctx_parts.append(str(r["info"].get("content", "")))
                        elif r["type"] == "file":
                            ctx_parts.append(str(r["info"].get("content_summary", "")))
                    memory_context = "\n".join(ctx_parts)[:500]
            except Exception:
                pass

        # ── Step 3: 按需分配算力 ──
        input_tokens = len(str(prompt or "")) // 4
        estimated_ops = self.gpu.estimate_ops(self.ollama._chat_model, input_tokens, input_tokens)
        slot = self.compute_slots.allocate(estimated_ops, "chat")

        if slot and not slot.get("allowed", True):
            return None  # 算力不足

        # ── Step 4: Ollama 推理 (附帶記憶上下文) ──
        actual_prompt = prompt
        if memory_context:
            actual_prompt = f"參考已知資訊:\n{memory_context}\n\n使用者問題: {prompt}"

        result = self.ollama.chat(actual_prompt, system_prompt, temperature=temperature)
        actual_ops = 0
        if result:
            real_input = result.get("prompt_eval_count", input_tokens)
            real_output = result.get("eval_count", len(result.get("content", "")) // 4)
            actual_ops = self.gpu.record_inference(
                self.ollama._chat_model, real_input, real_output
            )
            # 記錄使用者查詢
            self.user_profiles.record_query(ops_used=actual_ops)

            # ── Step 5: NEXUS v2 認知增強 ──
            if self.nexus_v2:
                try:
                    # 觀察 topic (用於預測)
                    if nexus_result:
                        tool = nexus_result.get("routing", {}).get("tool", "general")
                        self.nexus_v2.predictor.observe_topic(tool)
                except Exception:
                    pass

            # 附加 NEXUS 資訊
            if nexus_result:
                result["nexus"] = {
                    "complexity": nexus_result.get("complexity", {}).get("complexity_score", 0),
                    "tier": nexus_result.get("allocation", {}).get("tier", "MEDIUM"),
                    "tool": nexus_result.get("routing", {}).get("tool", "unknown"),
                    "resonance": nexus_result.get("resonance", {}).get("resonance", 0),
                    "beyond_knowledge": nexus_result.get("beyond_knowledge", False),
                }

        if slot and slot.get("slot_id"):
            self.compute_slots.release(slot["slot_id"], actual_ops)

        return result

    def route_query(self, query, mode=None, v42_only=False):
        """智慧路由判斷 — V42 先自我評估再決策"""
        user_profile = self.user_profiles.get_profile()
        return self.router.route(query, mode, v42_only, user_profile)

    def learn_and_remember(self, file_path, summary=None):
        """學習一個檔案並永久記住它"""
        # 先讓 folder_learner 學習
        result = self.folder_learner.learn_file(file_path)
        
        # 再讓 permanent_memory 永久記住
        folder = os.path.dirname(file_path)
        self.permanent_memory.remember_folder(folder, scan_depth=1)
        
        if result and result.get("summary"):
            self.permanent_memory.remember_file_content(
                file_path, 
                summary=result.get("summary", ""),
                tags=[result.get("file", "")]
            )
        elif summary:
            self.permanent_memory.remember_file_content(file_path, summary=summary)
        
        return result

    def deep_learn_folder(self, folder_path=None):
        """深度學習一個資料夾的所有內容
        
        這是 V42 用深度學習資料夾變得更聰明的核心方法
        """
        if folder_path is None:
            folder_path = os.path.join(_DD, "深度學習")
        
        if not os.path.isdir(folder_path):
            return {"error": f"資料夾不存在: {folder_path}"}

        # 記住資料夾
        self.permanent_memory.remember_folder(folder_path, scan_depth=3)
        
        # 學習所有新檔案
        result = self.folder_learner.learn_all(max_files=50)
        
        # 將學習結果加入知識庫
        if result.get("learned", 0) > 0:
            self.permanent_memory.add_knowledge(
                f"深度學習_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}",
                f"學習了 {result['learned']} 個檔案，累計 {result.get('total', 0)} 個",
                source=folder_path,
            )
            self.permanent_memory.save()
        
        # 保存所有狀態
        self.gpu.save_state()
        self.folder_learner._save_state()
        self.compute_slots.save()
        
        return result

    def start_background_learning(self):
        """啟動背景學習線程 — 持續讓 V42 變聰明"""
        if self._bg_running:
            return
        self._bg_running = True
        self._bg_thread = threading.Thread(
            target=self._background_learn_loop,
            daemon=True,
            name="V42-BG-Learn"
        )
        self._bg_thread.start()

    def _background_learn_loop(self):
        """背景學習循環 — 每 5 分鐘掃描一次新文件
        
        包含:
        1. 掃描深度學習資料夾
        2. 更新永久資料夾記憶
        3. 檢查算力容量
        """
        while self._bg_running:
            try:
                # 檢查算力容量 — v13.4: FULL 會自動升級，不再暫停
                capacity = self.gpu.check_capacity(0)
                # 學習新文件（算力分級制下永不阻塞）
                result = self.folder_learner.learn_all(max_files=5)
                if result.get("learned", 0) > 0:
                    self.gpu.save_state()
                    self.folder_learner._save_state()
                
                # 更新永久記憶
                self.permanent_memory.scan_all_known_folders()
            except Exception:
                pass
            # 等待 5 分鐘
            for _ in range(300):
                if not self._bg_running:
                    break
                time.sleep(1)

    def stop_background_learning(self):
        self._bg_running = False

    def save_all(self):
        """持久化所有狀態"""
        self.gpu.save_state()
        self.self_understanding._save_cache()
        self.folder_learner._save_state()
        self.permanent_memory.save()
        self.user_profiles.save()
        self.compute_slots.save()
        # NEXUS v2 認知引擎狀態
        if self.nexus_v2:
            try:
                self.nexus_v2.save_state()
            except Exception:
                pass
        elif self.nexus:
            try:
                self.nexus.save_state()
            except Exception:
                pass

    def capacity_report(self):
        """算力容量報告 — v13.4 分級制"""
        cap = self.gpu.check_capacity(0)
        gpu_st = self.gpu.status()
        return {
            "total_ops": self.gpu.total_ops,
            "capacity_limit": self.gpu.CAPACITY_LIMIT,
            "tops": round(self.gpu.tops, 4),
            "progress_pct": round(self.gpu.progress_pct, 2),
            "remaining_tops": round(self.gpu.capacity_remaining_tops, 4),
            "level": cap["level"],
            "compute_level": gpu_st.get("current_level", 1),
            "compute_level_name": gpu_st.get("current_level_name", "基礎算力"),
            "next_level_name": gpu_st.get("next_level_name", "MAX"),
            "warning": cap.get("warning"),
            "throttle_active": self.gpu._throttle_active,
            "recent_warnings": self.gpu._capacity_warnings[-5:],
            "compute_efficiency": self.compute_slots.efficiency,
        }

    def status(self):
        cap_report = self.capacity_report()

        # NEXUS 報告
        nexus_report = {"status": "not_loaded"}
        if self.nexus_v2:
            try:
                nexus_report = self.nexus_v2.full_report()
            except Exception:
                nexus_report = {"status": "v2_error"}
        elif self.nexus:
            try:
                nexus_report = self.nexus.full_report()
            except Exception:
                nexus_report = {"status": "v1_error"}

        return {
            "engine_version": self.VERSION,
            "init_time_ms": getattr(self, "_init_time_ms", 0),
            "init_progress": getattr(self, "_init_progress", []),
            "ollama_connected": self.ollama._connected,
            "chat_model": self.ollama._chat_model,
            "embed_model": self.ollama._embed_model,
            "available_models": self.ollama._available_models,
            "cloud": self.ollama.cloud_status,  # V52: 雲端後備狀態
            "gpu": self.gpu.status(),
            "capacity": cap_report,
            "self_understanding": self.self_understanding.stats(),
            "folder_learner": self.folder_learner.stats(),
            "permanent_memory": self.permanent_memory.stats(),
            "user_profiles": {
                "active_user": self.user_profiles._active_user,
                "total_users": len(self.user_profiles._profiles),
            },
            "compute_slots": self.compute_slots.stats(),
            "routing": self.router.routing_stats(),
            "background_learning": self._bg_running,
            "initialized": self._initialized,
            "unique_features": [
                "永久資料夾記憶 — 跨 session 不遺忘",
                "自我程式碼理解 — V42 完全理解自己",
                "自我能力評估 — 先判斷能不能做再決策",
                "按需算力分配 — 只用需要的算力",
                "1000T (1P) 容量管理 — 10x 擴容",
                "多使用者個人化 — 不同人不同效果",
                "深度學習資料夾 — 持續變聰明",
                "知識圖譜累積 — 越用越聰明",
                "NEXUS v2.0 認知融合 — 13 篇論文 + 5 獨創演算法",
                "知識優先路由 — 先查知識庫再問 AI",
                "ARR 共振路由 — 不靠關鍵詞選工具",
                "碎形複雜度分析 — 數學判斷問題難度",
                "預測性知識蒸餾 — 預測下一個問題",
                "秒開機制 — 第二次啟動秒開",
                "自動工具發現 — V42 自我擴充",
                "認知連鎖共振 — 多模組超加性效應",
                "熵閘算力分配 — 資訊熵精確分配算力",
            ],
            "nexus_engine": nexus_report,
        }