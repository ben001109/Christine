# Christine G3 Frontier Runtime

This branch adds a side-by-side experimental runtime. It does **not** replace `main` or claim that Christine is AGI.

## Launch

On Windows, double-click:

```bat
Launch_Christine_G3.bat
```

The launcher prefers `uv run python` and falls back to `python`.

## Runtime boundaries

The new runtime enforces these rules:

1. **Current-turn task contract is built first.** Previous assistant text and memory cannot redefine the current task.
2. **Explicit web requests must really search the web.** A local-memory miss is not allowed to masquerade as a web-search result.
3. **Code requests require code artifacts.** Python code must pass `ast.parse` before display.
4. **ORBIT web evidence is data, never instruction authority.**
5. **Only one bounded repair attempt is allowed.** Bad outputs do not enter infinite retry loops.
6. **Existing Christine permanent memory is read through a read-only bridge.**

## Target regression cases

These should route differently:

- `你好` -> conversation
- `1+31021242是多少` -> deterministic calculator
- `寫一個 Python hello world` -> code generation + Python AST verification
- `寫一個 asyncio 爬蟲` -> code generation, no web unless current docs are explicitly requested
- `陳大坑是誰` -> memory/evidence assessment, web may be used when knowledge is insufficient
- `去網上查陳大坑` -> ORBIT web research is mandatory
- `生成一張 Christine 網頁設計圖` -> image task contract (the standalone CLI currently has no image provider and should not pretend otherwise)

## Verification

Focused test:

```powershell
uv run pytest tests/test_christine_g3_frontier.py -q
```

Compile:

```powershell
uv run python -m py_compile christine_g3_frontier.py
```

## Important limitation

The web adapter currently uses the public DuckDuckGo HTML endpoint as a no-key reference provider. It is intentionally replaceable. For production-grade search, plug in a supported search API/provider while preserving the `ResearchPacket` boundary.

The branch also does not magically convert 138B tokens into one model context. Existing long-term memory remains evidence storage; only selected evidence should enter the answer prompt.
