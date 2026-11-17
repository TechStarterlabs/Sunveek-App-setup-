import json, time, urllib.request, urllib.parse, re
from pathlib import Path
import wpapi

wpapi.preflight()

# cleanup verify json + deactivate snippet permanently-ish
cleanup = Path(r"C:\Users\abhis\Desktop\SUNVIK STEEL\_tmp_cleanup2.php")
cleanup.write_text(
    "\n".join([
        "$uploads = wp_upload_dir();",
        "$base = trailingslashit( $uploads['basedir'] );",
        "foreach ( array( 'sunvik-lead-email-verify-v1.json', 'sunvik-lead-email-setup-v1.json' ) as $f ) {",
        "  $p = $base . $f;",
        "  if ( file_exists( $p ) ) { @unlink( $p ); }",
        "}",
        "delete_option( 'sunvik_lead_email_setup_v1' );",
        "",
    ]),
    encoding="utf-8",
)
code = cleanup.read_text(encoding="utf-8")
assert "$uploads" in code
wpapi.call("PUT", "/code-snippets/v1/snippets/13", {
    "name": "TEMP Sunvik cleanup lead dumps",
    "code": code,
    "active": True,
    "scope": "global",
})
urllib.request.urlopen(urllib.request.Request("https://sunviksteels.com/?c=" + str(int(time.time())), headers={"User-Agent": "Mozilla/5.0"}), timeout=45).read(40)
wpapi.call("PUT", "/code-snippets/v1/snippets/13", {"active": False})
print("cleanup done")

# Live form submit test
import http.cookiejar
cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
UA = {"User-Agent": "Mozilla/5.0"}
page = opener.open(urllib.request.Request("https://sunviksteels.com/tmt-bars/", headers=UA), timeout=60).read().decode("utf-8", "replace")
token = re.search(r'name="wpforms\[id\]"[^>]*>|<input type="hidden" name="wpforms\[id\]" value="11835">', page)
tok = re.search(r'data-token="([^"]+)"', page)
tokt = re.search(r'data-token-time="([^"]+)"', page)
# find ajax url / localized
loc = re.search(r'var wpforms_settings = (\{.*?\});', page, re.S)
print("has settings", bool(loc), "token", tok.group(1)[:20] if tok else None)

# WPForms modern ajax posts to same page or admin-ajax
# Try POST to page with wpforms fields
boundary_fields = {
    "wpforms[fields][1]": "Lead Setup Test",
    "wpforms[fields][2]": "leadtest+" + str(int(time.time())) + "@sunviksteels.com",
    "wpforms[fields][4]": "9999999999",
    "wpforms[fields][10][]": "Sunvik TMT Bars",
    "wpforms[fields][3]": "Automated setup verification submit - please ignore.",
    "wpforms[id]": "11835",
    "wpforms[post_id]": "6408",
    "page_title": "TMT Bars",
    "page_url": "https://sunviksteels.com/tmt-bars/",
    "page_id": "6408",
    "url_referer": "",
    "action": "wpforms_submit",
}
if tok:
    # some versions need token in POST
    pass

# Prefer admin-ajax with action
data = urllib.parse.urlencode({
    **boundary_fields,
    "wpforms[token]": tok.group(1) if tok else "",
}).encode()

# Actually include proper structure for AJAX
import urllib.parse
ajax_data = urllib.parse.urlencode([
    ("action", "wpforms_submit"),
    ("wpforms[id]", "11835"),
    ("wpforms[post_id]", "6408"),
    ("wpforms[token]", tok.group(1) if tok else ""),
    ("wpforms[fields][1]", "Lead Setup Test"),
    ("wpforms[fields][2]", f"leadtest+{int(time.time())}@example.com"),
    ("wpforms[fields][4]", "9999999999"),
    ("wpforms[fields][10][]", "Sunvik TMT Bars"),
    ("wpforms[fields][3]", "Automated setup verification - ignore this test lead."),
    ("page_title", "TMT Bars"),
    ("page_url", "https://sunviksteels.com/tmt-bars/"),
    ("page_id", "6408"),
]).encode()

req = urllib.request.Request(
    "https://sunviksteels.com/wp-admin/admin-ajax.php",
    data=ajax_data,
    headers={**UA, "Content-Type": "application/x-www-form-urlencoded", "Referer": "https://sunviksteels.com/tmt-bars/", "X-Requested-With": "XMLHttpRequest"},
    method="POST",
)
try:
    resp = opener.open(req, timeout=60)
    body = resp.read().decode("utf-8", "replace")
    print("AJAX status", resp.status, body[:800])
except Exception as e:
    if hasattr(e, "read"):
        print("AJAX err", e, e.read().decode("utf-8", "replace")[:800])
    else:
        print("AJAX err", e)
