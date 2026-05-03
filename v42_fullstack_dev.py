# ═══════════════════════════════════════════════════════════════════════════════
#  V42 Full-Stack Development Engine — 26 大插件，完整軟體+硬體開發
# ═══════════════════════════════════════════════════════════════════════════════
#
#  功能：工具鏈偵測、架構設計模板、CI/CD 生成、安全掃描、
#        設計模式、Docker 管理、自我程式碼理解
#
#  被 christine_final.py 的 V42HermesWorker._handle_fullstack_dev() 呼叫
# ═══════════════════════════════════════════════════════════════════════════════

import os
import subprocess
import shutil
import json
import re
import ast
import sys
import time
import hashlib


class V42FullStackDevEngine:
    """V42 全棧開發引擎 — 26 大插件，完整軟體+硬體開發能力"""

    VERSION = "1.0.0"

    # ═══ 支援的工具偵測表 ═══
    TOOL_REGISTRY = {
        # ── 語言/編譯器 ──
        "python":     {"cmd": "python --version",       "category": "language"},
        "python3":    {"cmd": "python3 --version",      "category": "language"},
        "node":       {"cmd": "node --version",         "category": "language"},
        "npm":        {"cmd": "npm --version",          "category": "package_manager"},
        "go":         {"cmd": "go version",             "category": "language"},
        "rustc":      {"cmd": "rustc --version",        "category": "language"},
        "cargo":      {"cmd": "cargo --version",        "category": "package_manager"},
        "java":       {"cmd": "java -version",          "category": "language"},
        "javac":      {"cmd": "javac -version",         "category": "language"},
        "gcc":        {"cmd": "gcc --version",          "category": "language"},
        "g++":        {"cmd": "g++ --version",          "category": "language"},
        "dotnet":     {"cmd": "dotnet --version",       "category": "language"},
        "ruby":       {"cmd": "ruby --version",         "category": "language"},
        "php":        {"cmd": "php --version",          "category": "language"},
        "swift":      {"cmd": "swift --version",        "category": "language"},
        "kotlin":     {"cmd": "kotlin -version",        "category": "language"},

        # ── 套件管理器 ──
        "pip":        {"cmd": "pip --version",          "category": "package_manager"},
        "pip3":       {"cmd": "pip3 --version",         "category": "package_manager"},
        "yarn":       {"cmd": "yarn --version",         "category": "package_manager"},
        "pnpm":       {"cmd": "pnpm --version",         "category": "package_manager"},
        "composer":   {"cmd": "composer --version",     "category": "package_manager"},
        "gem":        {"cmd": "gem --version",          "category": "package_manager"},
        "maven":      {"cmd": "mvn --version",          "category": "package_manager"},
        "gradle":     {"cmd": "gradle --version",       "category": "package_manager"},

        # ── DevOps ──
        "docker":     {"cmd": "docker --version",       "category": "devops"},
        "docker-compose": {"cmd": "docker-compose --version", "category": "devops"},
        "kubectl":    {"cmd": "kubectl version --client", "category": "devops"},
        "terraform":  {"cmd": "terraform --version",    "category": "devops"},
        "ansible":    {"cmd": "ansible --version",      "category": "devops"},

        # ── 版本控制 ──
        "git":        {"cmd": "git --version",          "category": "vcs"},

        # ── Linter / Formatter ──
        "flake8":     {"cmd": "flake8 --version",       "category": "linter"},
        "eslint":     {"cmd": "eslint --version",       "category": "linter"},
        "prettier":   {"cmd": "prettier --version",     "category": "formatter"},
        "black":      {"cmd": "black --version",        "category": "formatter"},

        # ── 資料庫 ──
        "mysql":      {"cmd": "mysql --version",        "category": "database"},
        "psql":       {"cmd": "psql --version",         "category": "database"},
        "mongosh":    {"cmd": "mongosh --version",      "category": "database"},
        "redis-cli":  {"cmd": "redis-cli --version",    "category": "database"},
        "sqlite3":    {"cmd": "sqlite3 --version",      "category": "database"},

        # ── 硬體/嵌入式 ──
        "arduino-cli": {"cmd": "arduino-cli version",   "category": "hardware"},
        "platformio":  {"cmd": "pio --version",         "category": "hardware"},
    }

    # ═══ 架構模板 ═══
    ARCHITECTURE_TEMPLATES = {
        "clean_architecture": {
            "desc": "Clean Architecture (Uncle Bob) — 依賴反轉，核心不依賴框架",
            "layers": ["entities", "use_cases", "interface_adapters", "frameworks"],
            "structure": {
                "src/domain/entities/": "業務實體",
                "src/domain/use_cases/": "使用案例（業務邏輯）",
                "src/adapters/controllers/": "控制器（介面轉接）",
                "src/adapters/presenters/": "呈現器",
                "src/adapters/gateways/": "資料庫閘道",
                "src/frameworks/web/": "Web 框架（FastAPI/Flask）",
                "src/frameworks/db/": "資料庫框架（SQLAlchemy）",
                "tests/": "測試",
            },
        },
        "hexagonal": {
            "desc": "Hexagonal Architecture (Ports & Adapters) — 核心與外部完全解耦",
            "layers": ["domain", "ports", "adapters"],
            "structure": {
                "src/domain/models/": "領域模型",
                "src/domain/services/": "領域服務",
                "src/ports/inbound/": "入站端口（用例介面）",
                "src/ports/outbound/": "出站端口（基礎設施介面）",
                "src/adapters/inbound/rest/": "REST API 適配器",
                "src/adapters/inbound/cli/": "CLI 適配器",
                "src/adapters/outbound/persistence/": "持久化適配器",
                "src/adapters/outbound/messaging/": "訊息適配器",
            },
        },
        "ddd": {
            "desc": "Domain-Driven Design — 以領域為中心的架構設計",
            "layers": ["domain", "application", "infrastructure", "presentation"],
            "structure": {
                "src/domain/aggregates/": "聚合根",
                "src/domain/entities/": "實體",
                "src/domain/value_objects/": "值物件",
                "src/domain/repositories/": "倉儲介面",
                "src/domain/events/": "領域事件",
                "src/application/commands/": "命令處理器",
                "src/application/queries/": "查詢處理器",
                "src/infrastructure/persistence/": "持久化實作",
                "src/infrastructure/messaging/": "訊息實作",
                "src/presentation/api/": "API 層",
            },
        },
        "microservice": {
            "desc": "Microservice Architecture — 獨立部署的服務群",
            "layers": ["api_gateway", "services", "shared"],
            "structure": {
                "api-gateway/": "API 閘道（路由、認證）",
                "services/user-service/": "用戶服務",
                "services/order-service/": "訂單服務",
                "services/payment-service/": "支付服務",
                "shared/proto/": "共享 Protobuf 定義",
                "shared/events/": "共享事件定義",
                "infra/docker/": "Docker 配置",
                "infra/k8s/": "Kubernetes 配置",
            },
        },
        "event_driven": {
            "desc": "Event-Driven Architecture — 事件驅動的非同步架構",
            "layers": ["producers", "consumers", "events", "projections"],
            "structure": {
                "src/events/": "事件定義",
                "src/producers/": "事件發布者",
                "src/consumers/": "事件消費者",
                "src/projections/": "讀模型投影",
                "src/sagas/": "Saga 長交易",
                "infrastructure/message_broker/": "訊息代理配置",
            },
        },
    }

    # ═══ GoF 23 設計模式 ═══
    DESIGN_PATTERNS = {
        # 建立型
        "singleton", "factory_method", "abstract_factory", "builder", "prototype",
        # 結構型
        "adapter", "bridge", "composite", "decorator", "facade", "flyweight", "proxy",
        # 行為型
        "chain_of_responsibility", "command", "interpreter", "iterator", "mediator",
        "memento", "observer", "state", "strategy", "template_method", "visitor",
    }

    # ═══ CI/CD 模板 ═══
    CI_TEMPLATES = {
        "github_actions_python": {
            "name": "GitHub Actions — Python",
            "file": ".github/workflows/ci.yml",
            "content": """name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.9', '3.10', '3.11', '3.12']
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - run: pip install -r requirements.txt
      - run: pip install pytest flake8
      - run: flake8 . --max-line-length=120
      - run: pytest tests/ -v
""",
        },
        "github_actions_node": {
            "name": "GitHub Actions — Node.js",
            "file": ".github/workflows/ci.yml",
            "content": """name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        node-version: [18, 20, 22]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node-version }}
      - run: npm ci
      - run: npm run lint
      - run: npm test
""",
        },
        "gitlab_ci_python": {
            "name": "GitLab CI — Python",
            "file": ".gitlab-ci.yml",
            "content": """stages:
  - lint
  - test
  - deploy

lint:
  stage: lint
  image: python:3.11
  script:
    - pip install flake8
    - flake8 . --max-line-length=120

test:
  stage: test
  image: python:3.11
  script:
    - pip install -r requirements.txt
    - pytest tests/ -v --cov
""",
        },
        "docker_python": {
            "name": "Dockerfile — Python (Multi-Stage)",
            "file": "Dockerfile",
            "content": """# Build stage
FROM python:3.11-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .
ENV PATH=/root/.local/bin:$PATH
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
""",
        },
    }

    def __init__(self):
        self._detected_tools = {}
        self._detection_done = False
        self._self_code_cache = None
        self._detect_tools()

    # ═══════════════════════════════════════════════════════════════════════
    #  工具偵測
    # ═══════════════════════════════════════════════════════════════════════

    def _detect_tools(self):
        """偵測系統上已安裝的開發工具"""
        self._detected_tools = {}
        for tool_name, info in self.TOOL_REGISTRY.items():
            try:
                result = subprocess.run(
                    info["cmd"], shell=True, capture_output=True, text=True,
                    timeout=5, encoding="utf-8", errors="replace"
                )
                if result.returncode == 0:
                    version = (result.stdout.strip() or result.stderr.strip()).split("\n")[0][:80]
                    self._detected_tools[tool_name] = {
                        "version": version,
                        "category": info["category"],
                        "available": True,
                    }
            except Exception:
                pass
        self._detection_done = True

    def get_tools_report(self):
        """生成工具偵測報告"""
        if not self._detection_done:
            self._detect_tools()

        lines = [f"🔧 V42 開發工具偵測報告", "═" * 50]

        by_category = {}
        for name, info in self._detected_tools.items():
            cat = info["category"]
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append((name, info["version"]))

        cat_names = {
            "language": "🖥️ 程式語言/編譯器",
            "package_manager": "📦 套件管理器",
            "devops": "🚀 DevOps 工具",
            "vcs": "🔀 版本控制",
            "linter": "🔍 Linter",
            "formatter": "✨ Formatter",
            "database": "🗄️ 資料庫",
            "hardware": "🔌 硬體/嵌入式",
        }

        for cat, cat_label in cat_names.items():
            if cat in by_category:
                lines.append(f"\n{cat_label}:")
                for name, ver in by_category[cat]:
                    lines.append(f"  ✓ {name}: {ver}")

        total = len(self._detected_tools)
        total_possible = len(self.TOOL_REGISTRY)
        lines.append(f"\n{'─' * 50}")
        lines.append(f"已偵測: {total}/{total_possible} 工具")

        return "\n".join(lines)

    # ═══════════════════════════════════════════════════════════════════════
    #  自我程式碼理解
    # ═══════════════════════════════════════════════════════════════════════

    def understand_self(self, mode="overview"):
        """分析 Christine 自身的程式碼"""
        try:
            self_path = os.path.abspath(sys.argv[0]) if sys.argv else None
            if not self_path or not os.path.exists(self_path):
                # 嘗試找 christine_final.py
                for p in [os.path.join(os.path.dirname(os.path.abspath(__file__)), "christine_final.py"), "christine_final.py"]:
                    if os.path.exists(p):
                        self_path = p
                        break

            if not self_path or not os.path.exists(self_path):
                return {"summary": "無法找到自身程式碼", "total_classes": 0, "total_functions": 0, "file_size_mb": 0}

            with open(self_path, "r", encoding="utf-8", errors="replace") as f:
                source = f.read()

            file_size_mb = round(len(source.encode("utf-8")) / (1024 * 1024), 2)
            lines = source.split("\n")
            total_lines = len(lines)

            # AST 分析
            try:
                tree = ast.parse(source)
                classes = [n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
                functions = [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
                imports = [n for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))]
            except SyntaxError:
                classes = []
                functions = []
                imports = []

            return {
                "summary": f"Christine v42 原始碼 — {total_lines:,} 行, {file_size_mb} MB",
                "total_classes": len(classes),
                "total_functions": len(functions),
                "total_imports": len(imports),
                "total_lines": total_lines,
                "file_size_mb": file_size_mb,
                "top_classes": classes[:20],
            }
        except Exception as e:
            return {"summary": f"分析失敗: {str(e)[:60]}", "total_classes": 0, "total_functions": 0, "file_size_mb": 0}

    # ═══════════════════════════════════════════════════════════════════════
    #  智能工具選擇
    # ═══════════════════════════════════════════════════════════════════════

    def auto_select_tool(self, query):
        """根據任務自動推薦工具"""
        ql = query.lower()
        tools_needed = []
        actions = []

        # 語言偵測
        lang_map = {
            "python": ["python", "pip", "flake8", "black"],
            "javascript": ["node", "npm", "eslint", "prettier"],
            "typescript": ["node", "npm", "eslint", "prettier"],
            "rust": ["rustc", "cargo"],
            "go": ["go"],
            "java": ["java", "javac", "maven", "gradle"],
            "c++": ["gcc", "g++"],
            "c#": ["dotnet"],
            "ruby": ["ruby", "gem"],
            "php": ["php", "composer"],
        }
        for lang, tools in lang_map.items():
            if lang in ql:
                tools_needed.extend(tools)
                break

        # 任務偵測
        if any(w in ql for w in ["docker", "容器", "container"]):
            tools_needed.extend(["docker", "docker-compose"])
        if any(w in ql for w in ["部署", "deploy", "k8s", "kubernetes"]):
            tools_needed.extend(["docker", "kubectl"])
        if any(w in ql for w in ["ci", "cd", "pipeline"]):
            tools_needed.extend(["git"])
        if any(w in ql for w in ["資料庫", "database", "sql"]):
            tools_needed.extend(["psql", "mysql", "sqlite3"])
        if any(w in ql for w in ["arduino", "esp32", "嵌入式", "embedded"]):
            tools_needed.extend(["arduino-cli", "platformio"])

        tools_needed = list(set(tools_needed))
        tools_available = [t for t in tools_needed if t in self._detected_tools]
        tools_missing = [t for t in tools_needed if t not in self._detected_tools]

        if tools_missing:
            actions.append(f"建議安裝: {', '.join(tools_missing)}")
        if tools_available:
            actions.append(f"可直接使用: {', '.join(tools_available)}")

        recommendation = "✅ 所有工具就緒" if not tools_missing else f"⚠️ 缺少 {len(tools_missing)} 個工具"

        return {
            "task": query,
            "tools_needed": tools_needed,
            "tools_available": tools_available,
            "tools_missing": tools_missing,
            "actions": "; ".join(actions) if actions else "無特殊需求",
            "recommendation": recommendation,
        }

    # ═══════════════════════════════════════════════════════════════════════
    #  安全掃描
    # ═══════════════════════════════════════════════════════════════════════

    def security_scan(self, path):
        """掃描程式碼安全性"""
        issues = []
        if not os.path.exists(path):
            return {"path": path, "error": "路徑不存在", "issues": []}

        files = []
        if os.path.isfile(path):
            files = [path]
        else:
            for root, _, fnames in os.walk(path):
                for fn in fnames:
                    if fn.endswith((".py", ".js", ".ts", ".java", ".go", ".rs")):
                        files.append(os.path.join(root, fn))

        dangerous_patterns = {
            "eval(": "使用 eval() 可能導致程式碼注入",
            "exec(": "使用 exec() 可能導致程式碼注入",
            "os.system(": "os.system() 容易受到命令注入攻擊",
            "subprocess.call(": "注意: subprocess 需要正確處理輸入",
            "pickle.loads(": "反序列化不受信任的資料可能導致 RCE",
            "yaml.load(": "不安全的 YAML 載入，建議用 yaml.safe_load()",
            "password": "可能包含硬編碼密碼",
            "secret": "可能包含硬編碼密鑰",
            "api_key": "可能包含硬編碼 API 金鑰",
            "SELECT.*FROM": "可能存在 SQL 注入風險",
            "innerHTML": "可能存在 XSS 風險",
        }

        for fp in files[:100]:  # 限制掃描檔案數
            try:
                with open(fp, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
                for i, line in enumerate(content.split("\n"), 1):
                    for pattern, desc in dangerous_patterns.items():
                        if pattern.lower() in line.lower():
                            issues.append({
                                "file": fp,
                                "line": i,
                                "pattern": pattern,
                                "description": desc,
                                "severity": "HIGH" if pattern in ("eval(", "exec(", "pickle.loads(") else "MEDIUM",
                                "code": line.strip()[:100],
                            })
            except Exception:
                pass

        return {
            "path": path,
            "files_scanned": len(files),
            "issues_found": len(issues),
            "issues": issues[:50],
            "summary": f"掃描 {len(files)} 個檔案，發現 {len(issues)} 個潛在安全問題",
        }

    # ═══════════════════════════════════════════════════════════════════════
    #  CI/CD 模板
    # ═══════════════════════════════════════════════════════════════════════

    def list_ci_templates(self):
        """列出可用的 CI/CD 模板"""
        return [f"{k}: {v['name']}" for k, v in self.CI_TEMPLATES.items()]

    def generate_ci(self, template_name, output_dir="."):
        """生成 CI/CD 配置檔案"""
        if template_name not in self.CI_TEMPLATES:
            return {"error": f"未知模板: {template_name}", "available": list(self.CI_TEMPLATES.keys())}

        tmpl = self.CI_TEMPLATES[template_name]
        filepath = os.path.join(output_dir, tmpl["file"])
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(tmpl["content"])

        return {"file": filepath, "template": template_name, "status": "created"}

    # ═══════════════════════════════════════════════════════════════════════
    #  Docker 管理
    # ═══════════════════════════════════════════════════════════════════════

    def docker_ps(self):
        """取得 Docker 容器狀態"""
        if "docker" not in self._detected_tools:
            return "⚠️ Docker 未安裝或未啟動"
        try:
            result = subprocess.run(
                "docker ps --format 'table {{.Names}}\\t{{.Status}}\\t{{.Ports}}'",
                shell=True, capture_output=True, text=True, timeout=10,
                encoding="utf-8", errors="replace"
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
            return "沒有正在運行的容器"
        except Exception as e:
            return f"Docker 查詢失敗: {str(e)[:60]}"

    # ═══════════════════════════════════════════════════════════════════════
    #  架構生成
    # ═══════════════════════════════════════════════════════════════════════

    def generate_architecture(self, arch_name, output_dir="."):
        """根據架構模板生成目錄結構"""
        if arch_name not in self.ARCHITECTURE_TEMPLATES:
            return {"error": f"未知架構: {arch_name}", "available": list(self.ARCHITECTURE_TEMPLATES.keys())}

        arch = self.ARCHITECTURE_TEMPLATES[arch_name]
        created = []
        for dir_path, desc in arch["structure"].items():
            full_path = os.path.join(output_dir, dir_path)
            os.makedirs(full_path, exist_ok=True)
            # 建立 __init__.py (Python 專案)
            init_path = os.path.join(full_path, "__init__.py")
            if not os.path.exists(init_path):
                with open(init_path, "w", encoding="utf-8") as f:
                    f.write(f'"""{desc}"""\n')
            created.append({"path": dir_path, "description": desc})

        return {
            "architecture": arch_name,
            "description": arch["desc"],
            "directories_created": len(created),
            "details": created,
        }

    # ═══════════════════════════════════════════════════════════════════════
    #  狀態報告
    # ═══════════════════════════════════════════════════════════════════════

    def status(self):
        """引擎完整狀態"""
        languages = [t for t, i in self._detected_tools.items() if i["category"] == "language"]
        pkg_mgrs = [t for t, i in self._detected_tools.items() if i["category"] == "package_manager"]
        hardware = [t for t, i in self._detected_tools.items() if i["category"] == "hardware"]

        return {
            "engine": "V42 FullStack Dev Engine",
            "version": self.VERSION,
            "tools_detected": len(self._detected_tools),
            "plugins": 26,
            "architectures": len(self.ARCHITECTURE_TEMPLATES),
            "design_patterns": len(self.DESIGN_PATTERNS),
            "ci_templates": len(self.CI_TEMPLATES),
            "capabilities": {
                "languages": languages if languages else ["(none detected)"],
                "package_managers": pkg_mgrs if pkg_mgrs else ["(none detected)"],
                "hardware": hardware if hardware else ["(none detected)"],
            },
        }
