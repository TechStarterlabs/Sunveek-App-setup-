import time, urllib.request
from pathlib import Path
import wpapi

wpapi.preflight()
code = Path(r"C:\Users\abhis\Desktop\SUNVIK STEEL\_tmp_cleanup_all.php").read_text(encoding="utf-8")
wpapi.call("PUT", "/code-snippets/v1/snippets/13", {
    "name": "TEMP Sunvik cleanup reports",
    "code": code,
    "active": True,
    "scope": "global",
})
urllib.request.urlopen(urllib.request.Request("https://sunviksteels.com/?x=" + str(int(time.time())), headers={"User-Agent": "Mozilla/5.0"}), timeout=45).read(40)
wpapi.call("PUT", "/code-snippets/v1/snippets/13", {"active": False})
print("cleaned")
