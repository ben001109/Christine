# -*- coding: utf-8 -*-
"""
Mass_Fix.py  —  christine_final.py 大量語法修復工具
================================================
策略：
  1. 讀檔（UTF-8，錯誤忽略）
  2. 移除已知亂碼字元（ㄍ 等注音、連續分號 ;;;;; ）
  3. 修復空 block：try:/if:/for:/while:/with:/def:/class:/else:/elif:/except:
     只要下一個「有字」的行縮排 <= 該行縮排，就插入 `    pass` 佔位
  4. 用 ast.parse 反覆 compile，每失敗一次就用 errormsg 的 lineno 做單行修復
     - 重複 400 次上限，避免無限迴圈
  5. 備份原檔 -> christine_final.py.bak.YYYYMMDD_HHMMSS
  6. 寫出修復後的檔案 + _fix_report.txt
"""
import os, sys, re, ast, io, shutil, datetime, traceback

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "christine_final.py")
REPORT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_fix_report.txt")

def log(msg, rep):
    print(msg)
    rep.append(msg)

def main():
    rep = []
    if not os.path.isfile(SRC):
        print("[ERR] 找不到", SRC); return 1

    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    bak = SRC + f".bak.{ts}"
    shutil.copy2(SRC, bak)
    log(f"[1] 已備份 -> {bak}", rep)

    with open(SRC, "r", encoding="utf-8", errors="replace") as f:
        text = f.read()
    log(f"[2] 讀入 {len(text):,} chars / {text.count(chr(10)):,} lines", rep)

    orig = text

    # --- Pass A: 移除已知亂碼 ---
    junk_chars = ["ㄍ", "ㄅ", "ㄆ", "ㄇ", "ㄈ", "ㄉ", "ㄊ", "ㄋ", "ㄌ"]
    removed = 0
    for ch in junk_chars:
        c = text.count(ch)
        if c:
            text = text.replace(ch, "")
            removed += c
            log(f"    - 移除注音字元 '{ch}' x{c}", rep)
    # 連續 4+ 個分號 -> 變空字串（前面保留一個分號）
    text2 = re.sub(r";{4,}", ";", text)
    if text2 != text:
        log(f"    - 折疊連續分號 ;;;;;", rep)
        text = text2
    log(f"[3] Pass A 完成，清除 {removed} 個亂碼字元", rep)

    # --- Pass B: 按行掃描，為空 block 插入 pass ---
    lines = text.split("\n")
    BLOCK_RE = re.compile(
        r"^(\s*)(try|if|elif|else|for|while|with|def|class|except|finally)\b.*:\s*(#.*)?$"
    )
    inserted = 0
    i = 0
    out = []
    while i < len(lines):
        ln = lines[i]
        out.append(ln)
        m = BLOCK_RE.match(ln)
        if m:
            indent = len(m.group(1))
            # 找下一行非空非純註解
            j = i + 1
            need_pass = True
            while j < len(lines):
                nxt = lines[j]
                stripped = nxt.strip()
                if stripped == "" or stripped.startswith("#"):
                    j += 1
                    continue
                nxt_indent = len(nxt) - len(nxt.lstrip())
                if nxt_indent > indent:
                    need_pass = False
                break
            if need_pass:
                out.append(" " * (indent + 4) + "pass")
                inserted += 1
        i += 1
    text = "\n".join(out)
    log(f"[4] Pass B 完成，插入 {inserted} 個 pass 佔位", rep)

    # --- Pass C: 反覆 ast.parse，用單行註解修復剩餘錯誤 ---
    MAX_ITER = 400
    fixed_syntax = 0
    for it in range(MAX_ITER):
        try:
            ast.parse(text)
            log(f"[5] Pass C: 第 {it} 輪 ast.parse 通過 ✓", rep)
            break
        except SyntaxError as e:
            ln_no = e.lineno or 1
            cur = text.split("\n")
            if 0 < ln_no <= len(cur):
                bad = cur[ln_no - 1]
                # 策略：若該行是 `try:` 或其他 block 開頭後空，補 pass
                bm = BLOCK_RE.match(bad)
                if bm:
                    indent = len(bm.group(1))
                    cur.insert(ln_no, " " * (indent + 4) + "pass")
                    text = "\n".join(cur)
                    fixed_syntax += 1
                    continue
                # 否則：註解該行
                cur[ln_no - 1] = "# [MASS_FIX_DISABLED] " + bad
                text = "\n".join(cur)
                fixed_syntax += 1
                if it < 20 or it % 50 == 0:
                    log(f"    - line {ln_no}: {e.msg}  -> 註解化", rep)
            else:
                log(f"    - 無法修復 line {ln_no}: {e.msg}", rep)
                break
    else:
        log(f"[5] Pass C: 達到 {MAX_ITER} 上限仍未通過", rep)

    log(f"[6] Pass C 修復 {fixed_syntax} 個語法錯誤", rep)

    # --- 最終檢查 ---
    try:
        ast.parse(text)
        log("[7] 最終檢查：ast.parse 通過 ✓", rep)
        status = "OK"
    except SyntaxError as e:
        log(f"[7] 最終檢查：仍有錯 line {e.lineno}: {e.msg}", rep)
        status = "PARTIAL"

    # 寫出
    if text != orig:
        with open(SRC, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        log(f"[8] 已寫回 {SRC}", rep)
    else:
        log("[8] 檔案無變動", rep)

    with open(REPORT, "w", encoding="utf-8") as f:
        f.write("\n".join(rep))
    log(f"[9] 報告 -> {REPORT}", rep)
    log(f"\n=== RESULT: {status} ===", rep)
    return 0 if status == "OK" else 2

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        traceback.print_exc()
        input("按 Enter 結束...")
        sys.exit(1)
