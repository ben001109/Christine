"""V57 知識庫掃描 — 統計深度學習資料夾"""
import json, os, glob

base = r"F:\AI夥伴\記憶資料夾\深度學習"
topics = set()
total_chars = 0
file_count = 0

for fp in glob.glob(os.path.join(base, "**", "*.json"), recursive=True):
    try:
        with open(fp, "r", encoding="utf-8") as f:
            d = json.load(f)
        t = d.get("topic", "")
        if t:
            topics.add(t)
        total_chars += len(d.get("summary", "")) + len(d.get("raw_text", ""))
        file_count += 1
    except Exception:
        pass

print(f"Files: {file_count}")
print(f"Unique topics: {len(topics)}")
print(f"Total chars: {total_chars:,}")
print(f"Approx MB: {total_chars / 1024 / 1024:.1f}")
print()
for t in sorted(topics):
    print(f"  - {t}")
