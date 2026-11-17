import time, urllib.request, re
from pathlib import Path
import wpapi

wpapi.preflight()
# list snippets find id 13
st, snippets = wpapi.call("GET", "/code-snippets/v1/snippets?per_page=50")
print("snippets", [(s.get("id"), s.get("name"), s.get("active")) for s in (snippets or [])][:15])

code = Path(r"C:\Users\abhis\Desktop\SUNVIK STEEL\_tmp_clear_el.php").read_text(encoding="utf-8")
assert "$post_id" in code
# use snippet 13 if exists else create
sid = 13
st, u = wpapi.call("PUT", f"/code-snippets/v1/snippets/{sid}", {
    "name": "TEMP clear elementor cache about",
    "code": code,
    "active": True,
    "scope": "global",
})
print("update", st, u.get("active") if isinstance(u, dict) else u, u.get("code_error") if isinstance(u, dict) else None)

urllib.request.urlopen(urllib.request.Request("https://sunviksteels.com/?elc=" + str(int(time.time())), headers={"User-Agent": "Mozilla/5.0"}), timeout=60).read(40)
time.sleep(2)
# deactivate
wpapi.call("PUT", f"/code-snippets/v1/snippets/{sid}", {"active": False})

# verify live
html = urllib.request.urlopen(urllib.request.Request("https://sunviksteels.com/about-us/?nocache=" + str(int(time.time())), headers={"User-Agent": "Mozilla/5.0", "Cache-Control": "no-cache"}), timeout=60).read().decode("utf-8", "replace")
print("new jpg present?", "GreenPro-Renewal-Sunvik-Flyash-Bricks-Blocks-2027" in html)
print("old 2026/09 present?", "cii-greenpro-certificate-sunvik-flyash-bricks-blocks-valid-december-2027" in html)
idx = html.lower().find("our certifications")
chunk = html[idx:idx+5000] if idx >= 0 else ""
urls = re.findall(r'/wp-content/uploads/[^\"\']+\.(?:jpg|jpeg|png|webp)', chunk, re.I)
# unique preserve order
seen = []
for u in urls:
    if u not in seen and ("Green" in u or "Mybuild" in u or "MyBuild" in u or "greenpro" in u.lower() or "certificate" in u.lower()):
        seen.append(u)
print("cert-ish urls:", seen[:15])

# cleanup json
cleanup = (
    "$uploads = wp_upload_dir();\n"
    "$p = trailingslashit($uploads['basedir']).'sunvik-el-clear.json';\n"
    "if (file_exists($p)) @unlink($p);\n"
)
Path(r"C:\Users\abhis\Desktop\SUNVIK STEEL\_tmp_cl_el.php").write_text(cleanup, encoding="utf-8")
wpapi.call("PUT", f"/code-snippets/v1/snippets/{sid}", {"code": Path(r"C:\Users\abhis\Desktop\SUNVIK STEEL\_tmp_cl_el.php").read_text(encoding="utf-8"), "active": True, "scope": "global"})
urllib.request.urlopen(urllib.request.Request("https://sunviksteels.com/?cl=" + str(int(time.time())), headers={"User-Agent": "Mozilla/5.0"}), timeout=45).read(20)
wpapi.call("PUT", f"/code-snippets/v1/snippets/{sid}", {"active": False})
print("done")
