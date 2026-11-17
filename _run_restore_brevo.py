import time, urllib.request, urllib.parse, re, http.cookiejar, json
from pathlib import Path
import wpapi

wpapi.preflight()
code = Path(r"C:\Users\abhis\Desktop\SUNVIK STEEL\_tmp_restore_brevo.php").read_text(encoding="utf-8")
wpapi.call("PUT", "/code-snippets/v1/snippets/13", {"name": "TEMP restore shop Brevo", "code": code, "active": True, "scope": "global"})
urllib.request.urlopen(urllib.request.Request("https://sunviksteels.com/?rb=" + str(int(time.time())), headers={"User-Agent": "Mozilla/5.0"}), timeout=60).read(30)
time.sleep(1)
raw = urllib.request.urlopen(urllib.request.Request(
    "https://sunviksteels.com/wp-content/uploads/sunvik-shop-brevo-restore-v1.json?t=" + str(int(time.time())),
    headers={"User-Agent": "Mozilla/5.0"},
), timeout=30).read().decode()
print(raw)
wpapi.call("PUT", "/code-snippets/v1/snippets/13", {"active": False})

UA = {"User-Agent": "Mozilla/5.0"}
cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
page = opener.open(urllib.request.Request("https://sunviksteels.shop/contact-us/", headers=UA), timeout=60).read().decode("utf-8", "replace")
tok = re.search(r'data-token="([^"]+)"', page)
formid = re.search(r'data-formid="(\d+)"', page)
post_id = re.search(r'name="wpforms\[post_id\]" value="(\d+)"', page) or re.search(r'name="page_id" value="(\d+)"', page)
containers = re.findall(r'id="wpforms-\d+-field_(\d+)-container" class="wpforms-field ([^"]+)"', page)
stamp = str(int(time.time()))
pairs = [
    ("action", "wpforms_submit"),
    ("wpforms[id]", formid.group(1) if formid else "2276"),
    ("wpforms[post_id]", post_id.group(1) if post_id else "666"),
    ("wpforms[token]", tok.group(1) if tok else ""),
]
for fid, cls in {c[0]: c[1] for c in containers}.items():
    if "email" in cls:
        pairs.append((f"wpforms[fields][{fid}]", f"inboxshop+{stamp}@example.com"))
    elif "name" in cls:
        pairs.append((f"wpforms[fields][{fid}]", "Inbox Test Shop"))
    elif "phone" in cls or "number" in cls:
        pairs.append((f"wpforms[fields][{fid}]", "9999999999"))
    elif "textarea" in cls or "text" in cls:
        pairs.append((f"wpforms[fields][{fid}]", "Inbox test after Brevo restore"))

req = urllib.request.Request(
    "https://sunviksteels.shop/wp-admin/admin-ajax.php",
    data=urllib.parse.urlencode(pairs).encode(),
    headers={**UA, "Content-Type": "application/x-www-form-urlencoded", "Referer": "https://sunviksteels.shop/contact-us/", "X-Requested-With": "XMLHttpRequest"},
    method="POST",
)
resp = opener.open(req, timeout=90)
body = resp.read().decode()
print("SHOP SUBMIT", resp.status, body[:400])

cleanup = (
    "$uploads = wp_upload_dir();\n"
    "foreach (array('sunvik-shop-brevo-restore-v1.json','sunvik-shop-smtp-465-v1.json','sunvik-spam-fix-v1.json','sunvik-spam-check-v1.json') as $f) {\n"
    "  $p = trailingslashit($uploads['basedir']).$f; if (file_exists($p)) @unlink($p);\n"
    "}\n"
)
Path(r"C:\Users\abhis\Desktop\SUNVIK STEEL\_tmp_cl2.php").write_text(cleanup, encoding="utf-8")
wpapi.call("PUT", "/code-snippets/v1/snippets/13", {"code": Path(r"C:\Users\abhis\Desktop\SUNVIK STEEL\_tmp_cl2.php").read_text(encoding="utf-8"), "active": True, "scope": "global"})
urllib.request.urlopen(urllib.request.Request("https://sunviksteels.com/?cl3=" + stamp, headers=UA), timeout=45).read(20)
wpapi.call("PUT", "/code-snippets/v1/snippets/13", {"active": False})
print("cleaned")
