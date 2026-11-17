import json, time, urllib.request, urllib.parse, http.cookiejar, re, sys
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

# login shop
get(SHOP + "/wp-login.php")
post_form(SHOP + "/wp-login.php", {
    "log": wpapi.SHOP_USER,
    "pwd": wpapi.SHOP_PASSWORD,
    "wp-submit": "Log In",
    "redirect_to": SHOP + "/wp-admin/",
    "testcookie": "1",
})
admin = get(SHOP + "/wp-admin/")
nonce = re.search(r'"nonce":"([^"]+)"', admin).group(1)
print("logged in, nonce", nonce[:8])

code = Path(r"C:\Users\abhis\Desktop\SUNVIK STEEL\_shop_fix_com2.php").read_text(encoding="utf-8")
assert "$com_config" in code

def rest(method, path, payload=None):
    url = "https://sunviksteels.shop/wp-json" + path
    data = json.dumps(payload).encode() if payload is not None else None
    headers = {**UA, "Accept": "application/json", "X-WP-Nonce": nonce}
    if data:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with opener.open(req, timeout=90) as r:
            return r.status, json.loads(r.read().decode())
    except Exception as e:
        raw = e.read().decode("utf-8", "replace") if hasattr(e, "read") else str(e)
        try:
            return getattr(e, "code", 0), json.loads(raw)
        except Exception:
            return getattr(e, "code", 0), {"raw": raw[:500]}

# reuse snippet 8 or create new
st, snips = rest("GET", "/code-snippets/v1/snippets?per_page=50")
print("snippets", [(s.get("id"), s.get("name"), s.get("active")) for s in (snips or []) if isinstance(snips, list)])

st, u = rest("PUT", "/code-snippets/v1/snippets/8", {
    "name": "TEMP fix com outage v2",
    "code": code,
    "active": True,
    "scope": "global",
})
print("activate", st, u.get("active") if isinstance(u, dict) else u, u.get("code_error") if isinstance(u, dict) else None)

get("https://sunviksteels.shop/?fix2=" + str(int(time.time())))
time.sleep(2)
raw = urllib.request.urlopen(urllib.request.Request(
    "https://sunviksteels.shop/wp-content/uploads/sunvik-com-fix2.json?t=" + str(int(time.time())),
    headers=UA), timeout=30).read().decode()
print(raw)
rest("PUT", "/code-snippets/v1/snippets/8", {"active": False})

# verify com
html = urllib.request.urlopen(urllib.request.Request("https://sunviksteels.com/?v=" + str(int(time.time())), headers=UA), timeout=30).read().decode("utf-8", "replace")
print("com up", "critical error" not in html.lower(), "len", len(html))

# cleanup report files on shop
rest("PUT", "/code-snippets/v1/snippets/8", {
    "code": "foreach (array('sunvik-com-fix.json','sunvik-com-fix2.json') as $f) { $p='/home/pgf2xcsto0v0/public_html/sunviksteels.shop/wp-content/uploads/'.$f; if(file_exists($p)) @unlink($p);} ",
    "active": True,
    "scope": "global",
})
# wait the dollars will break in this inline - skip cleanup via separate file
rest("PUT", "/code-snippets/v1/snippets/8", {"active": False})
print("done")
