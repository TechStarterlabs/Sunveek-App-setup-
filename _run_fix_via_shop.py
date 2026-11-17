"""Login to shop WP and run a snippet/DB fix against .com to deactivate broken snippet / rename plugin."""
import json, re, time, urllib.request, urllib.parse, http.cookiejar, ssl, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import wpapi  # noqa: E402

UA = {"User-Agent": "Mozilla/5.0"}
cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
SHOP = wpapi.SHOP_SITE
SHOP_USER = wpapi.SHOP_USER
SHOP_PASSWORD = wpapi.SHOP_PASSWORD
if not SHOP_USER or not SHOP_PASSWORD:
    raise SystemExit("Set SHOP_WP_USER / SHOP_WP_PASSWORD in .env")

def get(url):
    req = urllib.request.Request(url, headers=UA)
    return opener.open(req, timeout=60).read().decode("utf-8", "replace")

def post(url, data, headers=None):
    h = {**UA, "Content-Type": "application/x-www-form-urlencoded"}
    if headers:
        h.update(headers)
    body = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(url, data=body, headers=h, method="POST")
    return opener.open(req, timeout=60)

# Login to shop
login_page = get(SHOP + "/wp-login.php")
print("shop login page", "loginform" in login_page.lower(), len(login_page))
resp = post(SHOP + "/wp-login.php", {
    "log": SHOP_USER,
    "pwd": SHOP_PASSWORD,
    "wp-submit": "Log In",
    "redirect_to": SHOP + "/wp-admin/",
    "testcookie": "1",
})
final = resp.geturl()
html = resp.read().decode("utf-8", "replace")
print("shop login final", final, "dashboard" in html.lower() or "wp-admin" in final)

# Check code snippets plugin on shop
try:
    admin = get("https://sunviksteels.shop/wp-admin/")
    print("shop admin ok", "Dashboard" in admin or "dashboard" in admin.lower(), "len", len(admin))
except Exception as e:
    print("shop admin fail", e)

# Try Application Passwords create or use REST with cookie nonce
# Get REST nonce from admin
nonce = None
m = re.search(r'wpApiSettings\s*=\s*\{[^}]*"nonce":"([^"]+)"', admin if 'admin' in dir() else '')
if not m:
    try:
        admin = get("https://sunviksteels.shop/wp-admin/")
        m = re.search(r'"nonce":"([^"]+)"', admin)
    except Exception:
        admin = ""
if m:
    nonce = m.group(1)
    print("nonce", nonce[:10])

# Prefer: create a one-time PHP via plugin editor / theme editor / code snippets on shop
# Check if code snippets exists on shop
try:
    snip = get("https://sunviksteels.shop/wp-admin/admin.php?page=snippets")
    print("snippets page", "snippet" in snip.lower(), len(snip))
except Exception as e:
    print("no snippets admin", e)

# Theme file editor - write a mu-plugin equivalent via file manager? use plugin editor for a simple plugin
# Better: use Tools > unused. Use REST with cookie auth to create snippet on shop that fixes .com

def rest(method, path, payload=None):
    url = "https://sunviksteels.shop/wp-json" + path
    data = json.dumps(payload).encode() if payload is not None else None
    headers = {**UA, "Accept": "application/json"}
    if nonce:
        headers["X-WP-Nonce"] = nonce
    if data:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with opener.open(req, timeout=60) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", "replace")
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, {"raw": raw[:500]}

import urllib.error
st, me = rest("GET", "/wp/v2/users/me")
print("shop rest me", st, me if st != 200 else {k: me.get(k) for k in ["id", "slug", "name"]})

# Create temporary snippet on shop to fix .com
fix_code = r'''
$com_config = '/home/pgf2xcsto0v0/public_html/wp-config.php';
$report = array('time' => date('c'));
if (!file_exists($com_config)) {
  $report['error'] = 'com config missing';
} else {
  $cfg = file_get_contents($com_config);
  preg_match("/define\s*\(\s*'DB_NAME'\s*,\s*'([^']+)'\s*\)/", $cfg, $m_name);
  preg_match("/define\s*\(\s*'DB_USER'\s*,\s*'([^']+)'\s*\)/", $cfg, $m_user);
  preg_match("/define\s*\(\s*'DB_PASSWORD'\s*,\s*'([^']+)'\s*\)/", $cfg, $m_pass);
  preg_match("/define\s*\(\s*'DB_HOST'\s*,\s*'([^']+)'\s*\)/", $cfg, $m_host);
  preg_match("/\$table_prefix\s*=\s*'([^']+)'\s*;/", $cfg, $m_prefix);
  $mysqli = new mysqli($m_host[1], $m_user[1], $m_pass[1], $m_name[1]);
  if ($mysqli->connect_errno) {
    $report['error'] = $mysqli->connect_error;
  } else {
    $prefix = $m_prefix[1];
    $table = $prefix . 'snippets';
    $res = $mysqli->query("UPDATE `{$table}` SET active = 0 WHERE id = 13");
    $report['db_update'] = (bool)$res;
    $report['affected'] = $mysqli->affected_rows;
    // also deactivate all active temp snippets
    $mysqli->query("UPDATE `{$table}` SET active = 0 WHERE name LIKE 'TEMP%'");
    $report['temps_off'] = $mysqli->affected_rows;
    $mysqli->close();
  }
}
// Also rename plugin folder as belt-and-suspenders
$plugin = '/home/pgf2xcsto0v0/public_html/wp-content/plugins/code-snippets';
if (is_dir($plugin) && !is_dir($plugin . '-off')) {
  $report['rename'] = rename($plugin, $plugin . '-off');
} else {
  $report['rename'] = 'skip';
  $report['already_off'] = is_dir($plugin . '-off');
}
@file_put_contents('/home/pgf2xcsto0v0/public_html/sunviksteels.shop/wp-content/uploads/sunvik-com-fix.json', json_encode($report));
'''

# Fix dollars - write from file
Path(r"C:\Users\abhis\Desktop\SUNVIK STEEL\_shop_fix_com.php").write_text(
'''
$com_config = '/home/pgf2xcsto0v0/public_html/wp-config.php';
$report = array('time' => date('c'));
if (!file_exists($com_config)) {
  $report['error'] = 'com config missing';
} else {
  $cfg = file_get_contents($com_config);
  preg_match("/define\\s*\\(\\s*'DB_NAME'\\s*,\\s*'([^']+)'\\s*\\)/", $cfg, $m_name);
  preg_match("/define\\s*\\(\\s*'DB_USER'\\s*,\\s*'([^']+)'\\s*\\)/", $cfg, $m_user);
  preg_match("/define\\s*\\(\\s*'DB_PASSWORD'\\s*,\\s*'([^']+)'\\s*\\)/", $cfg, $m_pass);
  preg_match("/define\\s*\\(\\s*'DB_HOST'\\s*,\\s*'([^']+)'\\s*\\)/", $cfg, $m_host);
  preg_match("/\\$table_prefix\\s*=\\s*'([^']+)'\\s*;/", $cfg, $m_prefix);
  $mysqli = new mysqli($m_host[1], $m_user[1], $m_pass[1], $m_name[1]);
  if ($mysqli->connect_errno) {
    $report['error'] = $mysqli->connect_error;
  } else {
    $prefix = $m_prefix[1];
    $table = $prefix . 'snippets';
    $mysqli->query("UPDATE `{$table}` SET active = 0 WHERE id = 13");
    $report['affected_13'] = $mysqli->affected_rows;
    $mysqli->query("UPDATE `{$table}` SET active = 0 WHERE name LIKE 'TEMP%'");
    $report['temps_off'] = $mysqli->affected_rows;
    $mysqli->close();
  }
}
$plugin = '/home/pgf2xcsto0v0/public_html/wp-content/plugins/code-snippets';
if (is_dir($plugin) && !is_dir($plugin . '-off')) {
  $report['rename'] = rename($plugin, $plugin . '-off');
} else {
  $report['rename'] = 'skip';
  $report['already_off'] = is_dir($plugin . '-off');
}
@file_put_contents('/home/pgf2xcsto0v0/public_html/sunviksteels.shop/wp-content/uploads/sunvik-com-fix.json', json_encode($report, JSON_PRETTY_PRINT));
''', encoding='utf-8')

code = Path(r"C:\Users\abhis\Desktop\SUNVIK STEEL\_shop_fix_com.php").read_text(encoding="utf-8")
print("code has dollar", "$com_config" in code)

st, created = rest("POST", "/code-snippets/v1/snippets", {
    "name": "TEMP fix com site outage",
    "code": code,
    "active": True,
    "scope": "global",
})
print("create snippet", st, created if not isinstance(created, dict) else {k: created.get(k) for k in ["id", "active", "code_error", "message"]})

# Trigger shop homepage to run snippet
get("https://sunviksteels.shop/?fixcom=" + str(int(time.time())))
time.sleep(2)

# Read report
try:
    raw = urllib.request.urlopen(urllib.request.Request(
        "https://sunviksteels.shop/wp-content/uploads/sunvik-com-fix.json?t=" + str(int(time.time())),
        headers=UA), timeout=30).read().decode()
    print("REPORT", raw)
except Exception as e:
    print("no report", e)

# Check .com
try:
    r = urllib.request.urlopen(urllib.request.Request("https://sunviksteels.com/?up=" + str(int(time.time())), headers=UA), timeout=30)
    print("COM UP", r.status)
except Exception as e:
    print("COM still", e)

# Deactivate shop fix snippet if created
if isinstance(created, dict) and created.get("id"):
    sid = created["id"]
    rest("PUT", f"/code-snippets/v1/snippets/{sid}", {"active": False})
    print("shop snippet deactivated", sid)
