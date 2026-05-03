import re

FILE = r"F:\christine\christine_final.py"
with open(FILE, "r", encoding="utf-8") as f:
    content = f.read()

# Check batch markers
print("Has batch3 marker (復健醫學):", "復健醫學" in content)
print("Has batch4 marker (中國傳統戲曲包括京劇):", "中國傳統戲曲包括京劇" in content)
print("Has batch4 alt marker (國劇臉譜):", "國劇臉譜" in content)
print("Has batch4 alt2 (mahjong/麻將):", "麻將" in content)

# Count entries
end_marker = content.find("class V57AutonomousKnowledgeEngine")
if end_marker == -1:
    print("ERROR: Cannot find V57 class!")
else:
    kb_section = content[:end_marker]
    count = len(re.findall(r'\(\s*"[^"]+",\s*"[^"]+",\s*"[^"]+"', kb_section))
    print(f"Total COMPRESSED_KB entries: {count}")

# Find last few entries
last_bracket = content.rfind("]", 0, end_marker)
if last_bracket > 0:
    snippet = content[max(0, last_bracket-300):last_bracket+10]
    print("\n--- Last part of COMPRESSED_KB ---")
    print(snippet)
