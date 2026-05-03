import re
FILE = r"F:\christine\christine_final.py"
LOG = r"F:\christine\kb_count_result.txt"

with open(FILE, "r", encoding="utf-8") as f:
    content = f.read()

# Find COMPRESSED_KB section
kb_start = content.find("COMPRESSED_KB = [")
kb_init = content.find("def __init__(self):", kb_start)
kb_section = content[kb_start:kb_init]

# Count entries - each entry ends with "),
entry_count = kb_section.count('"),')

# Count lines
line_count = kb_section.count('\n')

# Find last entry text (just first 80 chars of last answer)
last_entry_pos = kb_section.rfind('"),')
if last_entry_pos > 0:
    snippet_start = max(0, last_entry_pos - 200)
    last_snippet = kb_section[snippet_start:last_entry_pos+3]
else:
    last_snippet = "NOT FOUND"

result = f"COMPRESSED_KB section: {line_count} lines\nEntry count (by closing pattern): {entry_count}\nFile total lines: {content.count(chr(10))+1}\n\nLast entry snippet:\n{last_snippet}\n"

with open(LOG, "w", encoding="utf-8") as f:
    f.write(result)

print("Done. Check " + LOG)
