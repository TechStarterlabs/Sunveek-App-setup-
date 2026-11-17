import json, time, urllib.request, urllib.parse, re, http.cookiejar
from pathlib import Path
import wpapi

wpapi.preflight()
code = Path(r"C:\Users\abhis\Desktop\SUNVIK STEEL\_tmp_spam_fix.php").read_text(encoding="utf-8")
wpapi.call("PUT", "/code-snippets/v1/snippets/13", {
    "name": "TEMP Sunvik spam/deliverability fix",
    "code": code,
    "active": True,
    "scope": "global",
})
urllib.request.urlopen(urllib.request.Request("https://sunviksteels.com/?spamfix=" + str(int(time.time())), headers={"User-Agent": "Mozilla/5.0"}), timeout=90).read(40)
time.sleep(2)
raw = urllib.request.urlopen(urllib.request.Request(
    "https://sunviksteels.com/wp-content/uploads/sunvik-spam-fix-v1.json?t=" + str(int(time.time())),
    headers={"User-Agent": "Mozilla/5.0"},
), timeout=30).read().decode()
print(raw)
wpapi.call("PUT", "/code-snippets/v1/snippets/13", {"active": False})

UA = {"User-Agent": "Mozilla/5.0"}

# Live form submits again after mailer change
def submit(url, ajax, form_builder):
    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    page = opener.open(urllib.request.Request(url, headers=UA), timeout=60).read().decode("utf-8", "replace")
    pairs = form_builder(page)
    req = urllib.request.Request(
        ajax,
        data=urllib.parse.urlencode(pairs).encode(),
        headers={**UA, "Content-Type": "application/x-www-form-urlencoded", "Referer": url, "X-Requested-With": "XMLHttpRequest"},
        method="POST",
    )
    resp = opener.open(req, timeout=60)
    body = resp.read().decode()
    ok = '"success":true' in body
    print(url, "OK" if ok else "FAIL", body[:250])
    return ok

stamp = str(int(time.time()))

def com_fields(page):
    tok = re.search(r'data-token="([^"]+)"', page)
    return [
        ("action", "wpforms_submit"),
        ("wpforms[id]", "11835"),
        ("wpforms[post_id]", "6408"),
        ("wpforms[token]", tok.group(1) if tok else ""),
        ("wpforms[fields][1]", "Inbox Deliverability Test"),
        ("wpforms[fields][2]", f"inboxcom+{stamp}@example.com"),
        ("wpforms[fields][4]", "9999999999"),
        ("wpforms[fields][10][]", "Sunvik TMT Bars"),
        ("wpforms[fields][3]", "Please confirm this lead email is IN INBOX not spam."),
        ("page_title", "TMT Bars"),
        ("page_url", "https://sunviksteels.com/tmt-bars/"),
        ("page_id", "6408"),
    ]

def shop_fields(page):
    tok = re.search(r'data-token="([^"]+)"', page)
    formid = re.search(r'data-formid="(\d+)"', page)
    post_id = re.search(r'name="wpforms\[post_id\]" value="(\d+)"', page) or re.search(r'name="page_id" value="(\d+)"', page)
    containers = re.findall(r'id="wpforms-\d+-field_(\d+)-container" class="wpforms-field ([^"]+)"', page)
    pairs = [
        ("action", "wpforms_submit"),
        ("wpforms[id]", formid.group(1) if formid else "1866"),
        ("wpforms[post_id]", post_id.group(1) if post_id else "2429"),
        ("wpforms[token]", tok.group(1) if tok else ""),
    ]
    for fid, cls in {c[0]: c[1] for c in containers}.items():
        if "email" in cls:
            pairs.append((f"wpforms[fields][{fid}]", f"inboxshop+{stamp}@example.com"))
        elif "name" in cls:
            pairs.append((f"wpforms[fields][{fid}]", "Inbox Deliverability Test Shop"))
        elif "phone" in cls or "number" in cls:
            pairs.append((f"wpforms[fields][{fid}]", "9999999999"))
        elif "checkbox" in cls:
            m = re.search(rf'name="wpforms\[fields\]\[{fid}\]\[\]" value="([^"]+)"', page)
            if m:
                pairs.append((f"wpforms[fields][{fid}][]", m.group(1)))
    return pairs

submit("https://sunviksteels.com/tmt-bars/", "https://sunviksteels.com/wp-admin/admin-ajax.php", com_fields)
submit("https://sunviksteels.shop/sunvik-gold-tmt-bar/", "https://sunviksteels.shop/wp-admin/admin-ajax.php", shop_fields)

# cleanup
cleanup = (
    "$uploads = wp_upload_dir();\n"
    "$base = trailingslashit( $uploads['basedir'] );\n"
    "foreach ( array('sunvik-spam-fix-v1.json','sunvik-spam-check-v1.json') as $f ) {\n"
    "  $p = $base . $f; if (file_exists($p)) @unlink($p);\n"
    "}\n"
)
Path(r"C:\Users\abhis\Desktop\SUNVIK STEEL\_tmp_cleanup_spam.php").write_text(cleanup, encoding="utf-8")
c = Path(r"C:\Users\abhis\Desktop\SUNVIK STEEL\_tmp_cleanup_spam.php").read_text(encoding="utf-8")
wpapi.call("PUT", "/code-snippets/v1/snippets/13", {"code": c, "active": True, "scope": "global"})
urllib.request.urlopen(urllib.request.Request("https://sunviksteels.com/?cl=" + stamp, headers=UA), timeout=45).read(20)
wpapi.call("PUT", "/code-snippets/v1/snippets/13", {"active": False})
print("done")
