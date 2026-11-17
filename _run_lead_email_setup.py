import json, time, urllib.request
from pathlib import Path
import wpapi

wpapi.preflight()
code = Path(r"C:\Users\abhis\Desktop\SUNVIK STEEL\_tmp_lead_email_setup.php").read_text(encoding="utf-8")
assert "$client_email" in code

# reuse snippet 13
st, u = wpapi.call("PUT", "/code-snippets/v1/snippets/13", {
    "name": "TEMP Sunvik lead email setup (delete after)",
    "desc": "Enable/harden WPForms+CF7 lead emails to client; send SMTP test. Delete after.",
    "code": code,
    "active": True,
    "scope": "global",
    "tags": ["temp", "sunvik-leads"],
})
print("update", st, "active", u.get("active") if isinstance(u, dict) else u, "err", u.get("code_error") if isinstance(u, dict) else None)
print("stored ok", "$client_email" in (u.get("code") or ""))

urllib.request.urlopen(
    urllib.request.Request(
        "https://sunviksteels.com/?leadsetup=" + str(int(time.time())),
        headers={"User-Agent": "Mozilla/5.0"},
    ),
    timeout=90,
).read(100)
time.sleep(2)

url = "https://sunviksteels.com/wp-content/uploads/sunvik-lead-email-setup-v1.json?t=" + str(int(time.time()))
raw = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=45).read().decode()
Path(r"C:\Users\abhis\Desktop\SUNVIK STEEL\_tmp_lead_email_setup.json").write_text(raw, encoding="utf-8")
print(raw)

# deactivate
wpapi.call("PUT", "/code-snippets/v1/snippets/13", {"active": False})
print("deactivated")
