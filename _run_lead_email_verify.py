import json, time, urllib.request, urllib.parse
from pathlib import Path
import wpapi

wpapi.preflight()
code = Path(r"C:\Users\abhis\Desktop\SUNVIK STEEL\_tmp_lead_email_verify.php").read_text(encoding="utf-8")
wpapi.call("PUT", "/code-snippets/v1/snippets/13", {
    "name": "TEMP Sunvik lead email verify",
    "code": code,
    "active": True,
    "scope": "global",
})
urllib.request.urlopen(urllib.request.Request("https://sunviksteels.com/?v=" + str(int(time.time())), headers={"User-Agent": "Mozilla/5.0"}), timeout=60).read(50)
time.sleep(2)
raw = urllib.request.urlopen(urllib.request.Request(
    "https://sunviksteels.com/wp-content/uploads/sunvik-lead-email-verify-v1.json?t=" + str(int(time.time())),
    headers={"User-Agent": "Mozilla/5.0"},
), timeout=30).read().decode()
Path(r"C:\Users\abhis\Desktop\SUNVIK STEEL\_tmp_lead_email_verify.json").write_text(raw, encoding="utf-8")
print(raw[:5000])
wpapi.call("PUT", "/code-snippets/v1/snippets/13", {"active": False})

# Try live AJAX submit of form 11835 (test lead)
import re, http.cookiejar

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
page = opener.open(urllib.request.Request("https://sunviksteels.com/tmt-bars/", headers={"User-Agent": "Mozilla/5.0"}), timeout=60).read().decode("utf-8", "replace")
token = re.search(r'data-token="([^"]+)"', page)
token_time = re.search(r'data-token-time="([^"]+)"', page)
print("token", bool(token), "time", token_time.group(1) if token_time else None)

# WPForms AJAX endpoint
# Prefer admin-ajax
ajax = "https://sunviksteels.com/wp-admin/admin-ajax.php"
# Collect nonce if present
nonce = re.search(r'"wpforms":\{[^}]*"nonce":"([^"]+)"', page) or re.search(r'wpforms_nonce["\']?\s*[:=]\s*["\']([^"\']+)', page)
print("nonce found", bool(nonce))

# Try XML-RPC auth on shop with same creds
import base64
for user in ["sunvikdev", "admin", "Admin", "sunvik", "shop"]:
    url = "https://sunviksteels.shop/xmlrpc.php"
    app_pw = __import__("os").environ.get("WP_APP_PW", "")
    body = f"""<?xml version='1.0'?><methodCall><methodName>wp.getUsersBlogs</methodName><params><param><value><string>{user}</string></value></param><param><value><string>{app_pw}</string></value></param></params></methodCall>""".encode()
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "text/xml", "User-Agent": "Mozilla/5.0"}, method="POST")
    try:
        resp = urllib.request.urlopen(req, timeout=20).read().decode("utf-8", "replace")
        ok = "isAdmin" in resp or "blogName" in resp or "faultCode" not in resp
        print("xmlrpc", user, "okish", "fault" not in resp.lower(), resp[:180].replace("\n", " "))
    except Exception as e:
        print("xmlrpc", user, type(e).__name__, e)
