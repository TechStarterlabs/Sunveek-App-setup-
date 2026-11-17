import time, urllib.request
from pathlib import Path
import wpapi

wpapi.preflight()
code = Path(r"C:\Users\abhis\Desktop\SUNVIK STEEL\_tmp_shop_lead_setup.php").read_text(encoding="utf-8")
assert "$shop_root" in code and "$client" in code
st, u = wpapi.call("PUT", "/code-snippets/v1/snippets/13", {
    "name": "TEMP Sunvik shop lead email setup",
    "code": code,
    "active": True,
    "scope": "global",
})
print("update", st, u.get("active") if isinstance(u, dict) else u, "err", u.get("code_error") if isinstance(u, dict) else None)
urllib.request.urlopen(urllib.request.Request("https://sunviksteels.com/?shopsetup=" + str(int(time.time())), headers={"User-Agent": "Mozilla/5.0"}), timeout=120).read(50)
time.sleep(2)
raw = urllib.request.urlopen(urllib.request.Request(
    "https://sunviksteels.com/wp-content/uploads/sunvik-shop-lead-setup-v1.json?t=" + str(int(time.time())),
    headers={"User-Agent": "Mozilla/5.0"},
), timeout=60).read().decode()
Path(r"C:\Users\abhis\Desktop\SUNVIK STEEL\_tmp_shop_lead_setup.json").write_text(raw, encoding="utf-8")
print(raw[:10000])
wpapi.call("PUT", "/code-snippets/v1/snippets/13", {"active": False})
