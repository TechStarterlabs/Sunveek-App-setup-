import time, urllib.request, json
from pathlib import Path
import wpapi

wpapi.preflight()
code = Path(r"C:\Users\abhis\Desktop\SUNVIK STEEL\_tmp_leads_sep.php").read_text(encoding="utf-8")
wpapi.call("PUT", "/code-snippets/v1/snippets/13", {
    "name": "TEMP Sunvik leads sep dump",
    "code": code,
    "active": True,
    "scope": "global",
})
urllib.request.urlopen(urllib.request.Request("https://sunviksteels.com/?leads=" + str(int(time.time())), headers={"User-Agent": "Mozilla/5.0"}), timeout=120).read(40)
time.sleep(2)
raw = urllib.request.urlopen(urllib.request.Request(
    "https://sunviksteels.com/wp-content/uploads/sunvik-leads-sep-days-v1.json?t=" + str(int(time.time())),
    headers={"User-Agent": "Mozilla/5.0"},
), timeout=60).read().decode()
Path(r"C:\Users\abhis\Desktop\SUNVIK STEEL\_tmp_leads_sep.json").write_text(raw, encoding="utf-8")
data = json.loads(raw)
print("com sept counts:", json.dumps(data.get("com_sept_counts"), indent=2))
print("\n=== COM CONFIRMATIONS ===")
print(json.dumps(data.get("com_confirmations"), indent=2)[:2000])
print("\n=== SNIPPETS WA ===")
print(json.dumps(data.get("snippets_whatsapp"), indent=2)[:2000])
for d in ["2026-09-14", "2026-09-17", "2026-09-20"]:
    print(f"\n===== COM {d} count={data.get('com_entries',{}).get(d,{}).get('count')} =====")
    for r in data.get("com_entries", {}).get(d, {}).get("rows") or []:
        print(json.dumps(r, ensure_ascii=False))
    print(f"\n===== SHOP {d} count={data.get('shop_entries',{}).get(d,{}).get('count')} =====")
    for r in data.get("shop_entries", {}).get(d, {}).get("rows") or []:
        print(json.dumps(r, ensure_ascii=False))
print("\n=== SHOP CONF ===")
print(json.dumps(data.get("shop_confirmations"), indent=2)[:1500])

wpapi.call("PUT", "/code-snippets/v1/snippets/13", {"active": False})
# cleanup
cleanup = (
    "$uploads=wp_upload_dir();\n"
    "$p=trailingslashit($uploads['basedir']).'sunvik-leads-sep-days-v1.json';\n"
    "if(file_exists($p)) @unlink($p);\n"
)
Path(r"C:\Users\abhis\Desktop\SUNVIK STEEL\_tmp_cl_leads.php").write_text(cleanup, encoding="utf-8")
wpapi.call("PUT", "/code-snippets/v1/snippets/13", {"code": Path(r"C:\Users\abhis\Desktop\SUNVIK STEEL\_tmp_cl_leads.php").read_text(encoding="utf-8"), "active": True, "scope": "global"})
urllib.request.urlopen(urllib.request.Request("https://sunviksteels.com/?cll=" + str(int(time.time())), headers={"User-Agent": "Mozilla/5.0"}), timeout=45).read(20)
wpapi.call("PUT", "/code-snippets/v1/snippets/13", {"active": False})
print("cleaned")
