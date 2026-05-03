c = open(r'F:\christine\christine_final.py', 'r', encoding='utf-8').read()
i1 = c.find('COMPRESSED_KB = [')
i2 = c.find('def __init__(self):', i1)
chunk = c[i1:i2]
n = chunk.count('(["')
print(f"COMPRESSED_KB entries: {n}")
