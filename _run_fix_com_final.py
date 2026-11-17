import json, time, urllib.request, urllib.parse, http.cookiejar, re, sys, os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import wpapi  # noqa: E402

UA = {"User-Agent": "Mozilla/5.0"}
cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
SHOP = wpapi.SHOP_SITE
if not wpapi.SHOP_USER or not wpapi.SHOP_PASSWORD:
    raise SystemExit("Set SHOP_WP_USER / SHOP_WP_PASSWORD in .env")

def get(url):
    return opener.open(urllib.request.Request(url, headers=UA), timeout=60).read().decode("utf-8", "replace")

def post_form(url, data):
    body = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(url, data=body, headers={**UA, "Content-Type": "application/x-www-form-urlencoded"}, method="POST")
    return opener.open(req, timeout=60)

get(SHOP + "/wp-login.php")
r = post_form(SHOP + "/wp-login.php", {
    "log": wpapi.SHOP_USER,
    "pwd": wpapi.SHOP_PASSWORD,
    "wp-submit": "Log In",
    "redirect_to": SHOP + "/wp-admin/",
    "testcookie": "1",
})
print("login", r.geturl())
admin = get(SHOP + "/wp-admin/plugin-install.php")  # any admin page for nonce
# wpApiSettings often on admin pages
nonce_m = re.search(r'wpApiSettings\s*=\s*\{[^}]*"nonce":"([^"]+)"', admin)
if not nonce_m:
    admin = get(SHOP + "/wp-admin/")
    nonce_m = re.search(r'"nonce":"([^"]+)"', admin)
nonce = nonce_m.group(1)
print("nonce", nonce)

code = Path(r"C:\Users\abhis\Desktop\SUNVIK STEEL\_shop_fix_com2.php").read_text(encoding="utf-8")

def rest(method, path, payload=None):
    url = SHOP + "/wp-json" + path
    data = json.dumps(payload).encode() if payload is not None else None
    headers = {**UA, "Accept": "application/json", "X-WP-Nonce": nonce}
    if data:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with opener.open(req, timeout=90) as resp:
            return resp.status, json.loads(resp.read().decode() or "{}")
    except Exception as e:
        raw = e.read().decode("utf-8", "replace") if hasattr(e, "read") else str(e)
        try:
            return getattr(e, "code", 0), json.loads(raw)
        except Exception:
            return getattr(e, "code", 0), {"raw": raw[:300]}

st, created = rest("POST", "/code-snippets/v1/snippets", {
    "name": "TEMP fix com outage v2",
    "code": code,
    "active": True,
    "scope": "global",
})
print("create", st, created.get("id") if isinstance(created, dict) else created, created.get("code_error") if isinstance(created, dict) else None, created.get("message") if isinstance(created, dict) else None)

get("https://sunviksteels.shop/?fixv2=" + str(int(time.time())))
time.sleep(2)
try:
    raw = urllib.request.urlopen(urllib.request.Request(
        "https://sunviksteels.shop/wp-content/uploads/sunvik-com-fix2.json?t=" + str(int(time.time())),
        headers=UA), timeout=30).read().decode()
    print("REPORT", raw)
except Exception as e:
    print("report fail", e)

sid = created.get("id") if isinstance(created, dict) else None
if sid:
    rest("PUT", f"/code-snippets/v1/snippets/{sid}", {"active": False})
    print("deactivated", sid)

# Verify .com still up and API
try:
    wpapi.preflight()
    st, sn = wpapi.call("GET", "/code-snippets/v1/snippets?per_page=20")
    print("com snippets API", st, [(x.get("id"), x.get("name"), x.get("active")) for x in (sn or [])] if isinstance(sn, list) else sn)
except Exception as e:
    print("com api", e)

html = urllib.request.urlopen(urllib.request.Request("https://sunviksteels.com/about-us/?t=" + str(int(time.time())), headers=UA), timeout=40).read().decode("utf-8", "replace")
print("about ok", "critical error" not in html.lower(), "GreenPro-Renewal" in html, "cii-greenpro-certificate" in html)
