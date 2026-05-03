import re

FILE = r"F:\christine\christine_final.py"
OUT = r"F:\christine\kb_status.txt"

with open(FILE, "r", encoding="utf-8") as f:
    content = f.read()

results = []

results.append(f"File size: {len(content)} chars")
results.append(f"Has batch3 marker: {'rehabilitation' in content}")
results.append(f"Has batch4 file marker (mahjong): {'mahjong' in content}")
results.append(f"Has opera keyword: {'Chinese opera' in content}")

end_marker = content.find("class V57AutonomousKnowledgeEngine")
results.append(f"V57 class found at: {end_marker}")

if end_marker > 0:
    kb_section = content[:end_marker]
    count = len(re.findall(r'\(\s*"[^"]+",\s*"[^"]+",\s*"[^"]+"', kb_section))
    results.append(f"Total COMPRESSED_KB entries: {count}")

    # Find last entry
    last_bracket_pos = kb_section.rfind("]")
    if last_bracket_pos > 0:
        snippet = kb_section[max(0, last_bracket_pos-500):last_bracket_pos+5]
        results.append(f"\nLast 500 chars before closing bracket:\n{snippet}")

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(results))

print(f"Output written to {OUT}")
