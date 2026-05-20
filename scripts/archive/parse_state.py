import re

with open("state.json", "r") as f:
    text = f.read()

# Google maps places have ID starting with 0x (like 0x31421...:0x...)
# Or we can look for "The Local Beans" followed shortly by coordinates.
# Let's find all coords
coords = re.findall(r'\[null,null,(16\.\d+),(108\.\d+)\]', text)
print(f"Total coords found: {len(coords)}")
for c in coords[:5]:
    print(c)

# Let's try to find an array containing the name and the coords
matches = re.finditer(r'The Local Beans', text)
for m in matches:
    start = max(0, m.start() - 50)
    end = min(len(text), m.end() + 200)
    print("MATCH:", text[start:end])
