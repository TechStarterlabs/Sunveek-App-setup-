import json, time, urllib.request
from pathlib import Path
import wpapi

wpapi.preflight()
code = Path(r"C:\Users\abhis\Desktop\SUNVIK STEEL\_tmp_wpforms_entries.php").read_text(encoding="utf-8")
assert "$out" in code

st, u = wpapi.call("PUT", "/code-snippets/v1/snippets/13", {
    "name": "TEMP Sunvik WPForms entries dump",
    "code": code,
    "active": True,
    "scope": "global",
})
print("update", st, u.get("active") if isinstance(u, dict) else u)

urllib.request.urlopen(
    urllib.request.Request(
        "https://sunviksteels.com/?entries=" + str(int(time.time())),
        headers={"User-Agent": "Mozilla/5.0"},
    ),
    timeout=60,
).read(100)
time.sleep(2)

url = "https://sunviksteels.com/wp-content/uploads/sunvik-wpforms-entries-v1.json?t=" + str(int(time.time()))
raw = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=30).read().decode()
Path(r"C:\Users\abhis\Desktop\SUNVIK STEEL\_tmp_wpforms_entries.json").write_text(raw, encoding="utf-8")
print(raw[:6000])
