import json, time, urllib.request, urllib.parse, re, http.cookiejar
from pathlib import Path
import wpapi

wpapi.preflight()
code = Path(r"C:\Users\abhis\Desktop\SUNVIK STEEL\_tmp_lead_reconfig_v2.php").read_text(encoding="utf-8")
assert "manjunath@sunvik.in" in code and "divya.nikam@thestarterlabs.com" in code

st, u = wpapi.call("PUT", "/code-snippets/v1/snippets/13", {
    "name": "TEMP Sunvik lead reconfig v2",
    "code": code,
    "active": True,
    "scope": "global",
})
print("update", st, "active", u.get("active") if isinstance(u, dict) else u, "err", u.get("code_error") if isinstance(u, dict) else None)

urllib.request.urlopen(
    urllib.request.Request("https://sunviksteels.com/?reconfig=" + str(int(time.time())), headers={"User-Agent": "Mozilla/5.0"}),
    timeout=120,
).read(50)
time.sleep(2)

raw = urllib.request.urlopen(
    urllib.request.Request(
        "https://sunviksteels.com/wp-content/uploads/sunvik-lead-reconfig-v2.json?t=" + str(int(time.time())),
        headers={"User-Agent": "Mozilla/5.0"},
    ),
    timeout=60,
).read().decode()
Path(r"C:\Users\abhis\Desktop\SUNVIK STEEL\_tmp_lead_reconfig_v2.json").write_text(raw, encoding="utf-8")
data = json.loads(raw)
print("errors", data.get("errors"))
print("com wpforms", len(data.get("com", {}).get("wpforms") or []), "all ok", all(x.get("ok") for x in (data.get("com", {}).get("wpforms") or [])))
print("shop wpforms", len(data.get("shop", {}).get("wpforms") or []), "all ok", all(x.get("ok") for x in (data.get("shop", {}).get("wpforms") or [])))
print("com smtp test", data.get("tests"))
print("com smtp cfg", data.get("com", {}).get("smtp"))
print("shop smtp cfg", data.get("shop", {}).get("smtp"))
print("sample to", (data.get("com", {}).get("wpforms") or [{}])[0].get("to"))

wpapi.call("PUT", "/code-snippets/v1/snippets/13", {"active": False})

UA = {"User-Agent": "Mozilla/5.0"}

def submit_com():
    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    page = opener.open(urllib.request.Request("https://sunviksteels.com/tmt-bars/", headers=UA), timeout=60).read().decode("utf-8", "replace")
    tok = re.search(r'data-token="([^"]+)"', page)
    stamp = str(int(time.time()))
    pairs = [
        ("action", "wpforms_submit"),
        ("wpforms[id]", "11835"),
        ("wpforms[post_id]", "6408"),
        ("wpforms[token]", tok.group(1) if tok else ""),
        ("wpforms[fields][1]", "Lead Reconfig Test COM"),
        ("wpforms[fields][2]", f"comtest+{stamp}@example.com"),
        ("wpforms[fields][4]", "9999999999"),
        ("wpforms[fields][10][]", "Sunvik TMT Bars"),
        ("wpforms[fields][3]", "Automated reconfig verification .com - ignore."),
        ("page_title", "TMT Bars"),
        ("page_url", "https://sunviksteels.com/tmt-bars/"),
        ("page_id", "6408"),
    ]
    req = urllib.request.Request(
        "https://sunviksteels.com/wp-admin/admin-ajax.php",
        data=urllib.parse.urlencode(pairs).encode(),
        headers={**UA, "Content-Type": "application/x-www-form-urlencoded", "Referer": "https://sunviksteels.com/tmt-bars/", "X-Requested-With": "XMLHttpRequest"},
        method="POST",
    )
    resp = opener.open(req, timeout=60)
    body = resp.read().decode()
    print("COM SUBMIT", resp.status, body[:400])
    return "success\":true" in body or '"success":true' in body

def submit_shop():
    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    page = opener.open(urllib.request.Request("https://sunviksteels.shop/sunvik-gold-tmt-bar/", headers=UA), timeout=60).read().decode("utf-8", "replace")
    tok = re.search(r'data-token="([^"]+)"', page)
    formid = re.search(r'data-formid="(\d+)"', page)
    post_id = re.search(r'name="wpforms\[post_id\]" value="(\d+)"', page) or re.search(r'name="page_id" value="(\d+)"', page)
    containers = re.findall(r'id="wpforms-\d+-field_(\d+)-container" class="wpforms-field ([^"]+)"', page)
    type_map = {c[0]: c[1] for c in containers}
    stamp = str(int(time.time()))
    pairs = [
        ("action", "wpforms_submit"),
        ("wpforms[id]", formid.group(1) if formid else "1866"),
        ("wpforms[post_id]", post_id.group(1) if post_id else "2429"),
        ("wpforms[token]", tok.group(1) if tok else ""),
    ]
    for fid, cls in type_map.items():
        key = f"wpforms[fields][{fid}]"
        if "email" in cls:
            pairs.append((key, f"shoptest+{stamp}@example.com"))
        elif "name" in cls:
            pairs.append((key, "Lead Reconfig Test SHOP"))
        elif "phone" in cls or "number" in cls:
            pairs.append((key, "9999999999"))
        elif "textarea" in cls:
            pairs.append((key, "Automated reconfig verification .shop - ignore."))
        elif "checkbox" in cls:
            m = re.search(rf'name="wpforms\[fields\]\[{fid}\]\[\]" value="([^"]+)"', page)
            if m:
                pairs.append((f"wpforms[fields][{fid}][]", m.group(1)))
        elif "address" in cls:
            # skip complex address; may be optional
            pass
    req = urllib.request.Request(
        "https://sunviksteels.shop/wp-admin/admin-ajax.php",
        data=urllib.parse.urlencode(pairs).encode(),
        headers={**UA, "Content-Type": "application/x-www-form-urlencoded", "Referer": "https://sunviksteels.shop/sunvik-gold-tmt-bar/", "X-Requested-With": "XMLHttpRequest"},
        method="POST",
    )
    resp = opener.open(req, timeout=60)
    body = resp.read().decode()
    print("SHOP SUBMIT", resp.status, body[:500])
    return "success\":true" in body or '"success":true' in body

ok_com = submit_com()
ok_shop = submit_shop()
print("RESULT com_submit", ok_com, "shop_submit", ok_shop)

# cleanup report json
cleanup = (
    "$uploads = wp_upload_dir();\n"
    "$base = trailingslashit( $uploads['basedir'] );\n"
    "foreach ( array( 'sunvik-lead-reconfig-v2.json', 'sunvik-final-check-v1.json' ) as $f ) {\n"
    "  $p = $base . $f; if ( file_exists( $p ) ) { @unlink( $p ); }\n"
    "}\n"
)
Path(r"C:\Users\abhis\Desktop\SUNVIK STEEL\_tmp_cleanup_reconfig.php").write_text(cleanup, encoding="utf-8")
# dollars already in write via Path from this .py file - good
c = Path(r"C:\Users\abhis\Desktop\SUNVIK STEEL\_tmp_cleanup_reconfig.php").read_text(encoding="utf-8")
wpapi.call("PUT", "/code-snippets/v1/snippets/13", {"name": "TEMP cleanup", "code": c, "active": True, "scope": "global"})
urllib.request.urlopen(urllib.request.Request("https://sunviksteels.com/?cln=" + str(int(time.time())), headers=UA), timeout=45).read(20)
wpapi.call("PUT", "/code-snippets/v1/snippets/13", {"active": False})
print("cleaned")
