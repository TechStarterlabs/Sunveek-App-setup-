import time, urllib.request
from pathlib import Path
import wpapi

wpapi.preflight()
code = Path(r"C:\Users\abhis\Desktop\SUNVIK STEEL\_tmp_cpanel_scan.php").read_text(encoding="utf-8")
assert "$home" in code
wpapi.call("PUT", "/code-snippets/v1/snippets/13", {
    "name": "TEMP Sunvik cPanel folder scan",
    "code": code,
    "active": True,
    "scope": "global",
})
urllib.request.urlopen(urllib.request.Request("https://sunviksteels.com/?scan=" + str(int(time.time())), headers={"User-Agent": "Mozilla/5.0"}), timeout=120).read(50)
time.sleep(2)
raw = urllib.request.urlopen(urllib.request.Request(
    "https://sunviksteels.com/wp-content/uploads/sunvik-cpanel-scan-v1.json?t=" + str(int(time.time())),
    headers={"User-Agent": "Mozilla/5.0"},
), timeout=60).read().decode()
Path(r"C:\Users\abhis\Desktop\SUNVIK STEEL\_tmp_cpanel_scan.json").write_text(raw, encoding="utf-8")
print(raw[:12000])
wpapi.call("PUT", "/code-snippets/v1/snippets/13", {"active": False})
