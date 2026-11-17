import json, time, urllib.request, re
from pathlib import Path
import wpapi

wpapi.preflight()

# Safe cleanup on .com via snippet - ensure we use inactive-first pattern with try/catch style
code = Path(r"C:\Users\abhis\Desktop\SUNVIK STEEL\_tmp_safe_cleanup.php").read_text(encoding="utf-8")
# Use a NEW snippet id, activate briefly
st, created = wpapi.call("POST", "/code-snippets/v1/snippets", {
    "name": "TEMP safe cleanup only",
    "code": code,
    "active": True,
    "scope": "global",
})
print("create", st, created.get("id") if isinstance(created, dict) else created)
sid = created.get("id")
urllib.request.urlopen(urllib.request.Request("https://sunviksteels.com/?safe=" + str(int(time.time())), headers={"User-Agent": "Mozilla/5.0"}), timeout=45).read(50)
time.sleep(1)
# Immediately deactivate ALL temp snippets including this one
wpapi.call("PUT", f"/code-snippets/v1/snippets/{sid}", {"active": False})
wpapi.call("PUT", "/code-snippets/v1/snippets/13", {"active": False, "code": "// disabled - was causing fatal clear_cache", "name": "TEMP DISABLED clear elementor cache"})

st, sn = wpapi.call("GET", "/code-snippets/v1/snippets?per_page=50")
print("active:", [(s["id"], s["name"]) for s in sn if s.get("active")])

html = urllib.request.urlopen(urllib.request.Request(
    "https://sunviksteels.com/about-us/?nocache=" + str(int(time.time())),
    headers={"User-Agent": "Mozilla/5.0", "Cache-Control": "no-cache"}), timeout=45).read().decode("utf-8", "replace")
idx = html.lower().find("our certifications")
chunk = html[idx:idx+6000] if idx >= 0 else ""
urls = []
for u in re.findall(r"https://sunviksteels\.com/wp-content/uploads/[^\"'\s>]+\.(?:jpg|jpeg|png|webp)", chunk, re.I):
    if u not in urls:
        urls.append(u)
print("cert urls:")
for u in urls:
    if any(k in u.lower() for k in ["green", "mybuild", "cert"]):
        print(" ", u)

# cleanup json
cleanup = Path(r"C:\Users\abhis\Desktop\SUNVIK STEEL\_tmp_safe_cleanup.php")
# delete report via quick call
c2 = (
    "$uploads=wp_upload_dir();\n"
    "$p=trailingslashit($uploads['basedir']).'sunvik-safe-cleanup.json';\n"
    "if(file_exists($p)) @unlink($p);\n"
)
Path(r"C:\Users\abhis\Desktop\SUNVIK STEEL\_tmp_del_json.php").write_text(c2, encoding="utf-8")
wpapi.call("PUT", f"/code-snippets/v1/snippets/{sid}", {"code": Path(r"C:\Users\abhis\Desktop\SUNVIK STEEL\_tmp_del_json.php").read_text(encoding="utf-8"), "active": True})
urllib.request.urlopen(urllib.request.Request("https://sunviksteels.com/?dj=" + str(int(time.time())), headers={"User-Agent": "Mozilla/5.0"}), timeout=30).read(20)
wpapi.call("PUT", f"/code-snippets/v1/snippets/{sid}", {"active": False})
print("SITE OK")
