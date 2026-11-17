import json, time, urllib.request, re
from pathlib import Path
import wpapi

wpapi.preflight()
code = Path(r"C:\Users\abhis\Desktop\SUNVIK STEEL\_tmp_final_check.php").read_text(encoding="utf-8")
wpapi.call("PUT", "/code-snippets/v1/snippets/13", {
    "name": "TEMP Sunvik final check",
    "code": code,
    "active": True,
    "scope": "global",
})
urllib.request.urlopen(urllib.request.Request("https://sunviksteels.com/?fc=" + str(int(time.time())), headers={"User-Agent": "Mozilla/5.0"}), timeout=60).read(40)
time.sleep(1)
raw = urllib.request.urlopen(urllib.request.Request(
    "https://sunviksteels.com/wp-content/uploads/sunvik-final-check-v1.json?t=" + str(int(time.time())),
    headers={"User-Agent": "Mozilla/5.0"},
), timeout=30).read().decode()
print(raw)
wpapi.call("PUT", "/code-snippets/v1/snippets/13", {"active": False})

# cleanup file
cleanup = Path(r"C:\Users\abhis\Desktop\SUNVIK STEEL\_tmp_cleanup_all.php").read_text(encoding="utf-8")
# extend cleanup to include final check
cleanup2 = cleanup.replace(
    "sunvik-lead-email-setup-v1.json'",
    "sunvik-lead-email-setup-v1.json', 'sunvik-final-check-v1.json'",
)
if "sunvik-final-check-v1.json" not in cleanup2:
    cleanup2 = (
        "$uploads = wp_upload_dir();\n"
        "$base = trailingslashit( $uploads['basedir'] );\n"
        "foreach ( array( 'sunvik-final-check-v1.json' ) as $f ) {\n"
        "\t$p = $base . $f;\n"
        "\tif ( file_exists( $p ) ) { @unlink( $p ); }\n"
        "}\n"
    )
wpapi.call("PUT", "/code-snippets/v1/snippets/13", {"code": cleanup2, "active": True, "scope": "global"})
urllib.request.urlopen(urllib.request.Request("https://sunviksteels.com/?cl=" + str(int(time.time())), headers={"User-Agent": "Mozilla/5.0"}), timeout=45).read(20)
wpapi.call("PUT", "/code-snippets/v1/snippets/13", {"active": False})

# Live WhatsApp + form presence
for url in [
    "https://sunviksteels.com/tmt-bars/",
    "https://sunviksteels.shop/sunvik-gold-tmt-bar/",
]:
    html = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=45).read().decode("utf-8", "replace")
    ctc = "ht_ctc" in html or "ht_ctc_chat_var" in html
    num = re.search(r'"number"\s*:\s*"(\d+)"', html)
    wpforms = "wpforms-form" in html
    print(url, "wpforms", wpforms, "whatsapp_float", ctc, "number", num.group(1) if num else None)
