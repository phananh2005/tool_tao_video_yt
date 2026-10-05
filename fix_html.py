with open("web/index.html", "r", encoding="utf-8") as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "Lỗi từ server:" in line:
        lines[i] = '                        if (!response.ok) { const errData = await response.json().catch(() => ({})); throw new Error(errData.detail || `Lỗi từ server: ${response.status}`); }\n                        if (!response.body) throw new Error("ReadableStream không được hỗ trợ.");\n'

with open("web/index.html", "w", encoding="utf-8") as f:
    f.writelines(lines)
