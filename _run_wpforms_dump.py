import json, time, urllib.request
from pathlib import Path
import wpapi

wpapi.preflight()
code = Path(r"C:\Users\abhis\Desktop\SUNVIK STEEL\_tmp_wpforms_dump.php").read_text(encoding="utf-8")
assert "$out" in code and "$post" in code, "PHP dollars missing in source file"

st, u = wpapi.call("PUT", "/code-snippets/v1/snippets/13", {
    "code": code,
    "active": True,
    "scope": "global",
    "name": "TEMP Sunvik WPForms dump (delete after)",
})
print("update", st, "active", u.get("active") if isinstance(u, dict) else u)
print("stored has $out", "$out" in (u.get("code") or ""))

st, a = wpapi.call("POST", "/code-snippets/v1/snippets/13/activate", {})
print("activate", st, a)

# Confirm stored code
st, s = wpapi.call("GET", "/code-snippets/v1/snippets/13")
print("get active", s.get("active"), "has $out", "$out" in (s.get("code") or ""), "err", s.get("code_error"))

urllib.request.urlopen(
    urllib.request.Request(
        "https://sunviksteels.com/?dump=" + str(int(time.time())),
        headers={"User-Agent": "Mozilla/5.0"},
    ),
    timeout=60,
).read(100)
time.sleep(2)

dump_url = "https://sunviksteels.com/wp-content/uploads/sunvik-wpforms-dump-v1.json?t=" + str(int(time.time()))
raw = urllib.request.urlopen(
    urllib.request.Request(dump_url, headers={"User-Agent": "Mozilla/5.0"}),
    timeout=30,
).read().decode()
print("SUCCESS", len(raw))
Path(r"C:\Users\abhis\Desktop\SUNVIK STEEL\_tmp_wpforms_dump.json").write_text(raw, encoding="utf-8")
print(raw[:8000])
