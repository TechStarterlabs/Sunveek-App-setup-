import wpapi

wpapi.preflight()
# deactivate temp snippet
st, d = wpapi.call("POST", "/code-snippets/v1/snippets/13/deactivate", {})
print("deactivate", st, d)

# also set active false
st, u = wpapi.call("PUT", "/code-snippets/v1/snippets/13", {"active": False})
print("active", u.get("active") if isinstance(u, dict) else u)

# cleanup dump files via a one-shot then deactivate - use snippet 13 once more
cleanup = r"""
$uploads = wp_upload_dir();
$base = trailingslashit( $uploads['basedir'] );
foreach ( array( 'sunvik-wpforms-dump-v1.json', 'sunvik-wpforms-entries-v1.json' ) as $f ) {
	$path = $base . $f;
	if ( file_exists( $path ) ) {
		unlink( $path );
	}
}
delete_option( 'sunvik_wpforms_dump_done_v1' );
"""
# Write won't help - dollars. Load from file.
from pathlib import Path
Path(r"C:\Users\abhis\Desktop\SUNVIK STEEL\_tmp_cleanup.php").write_text(
    "\n".join([
        "$uploads = wp_upload_dir();",
        "$base = trailingslashit( $uploads['basedir'] );",
        "foreach ( array( 'sunvik-wpforms-dump-v1.json', 'sunvik-wpforms-entries-v1.json' ) as $f ) {",
        "\t$path = $base . $f;",
        "\tif ( file_exists( $path ) ) { unlink( $path ); }",
        "}",
        "delete_option( 'sunvik_wpforms_dump_done_v1' );",
        "",
    ]),
    encoding="utf-8",
)
code = Path(r"C:\Users\abhis\Desktop\SUNVIK STEEL\_tmp_cleanup.php").read_text(encoding="utf-8")
st, u = wpapi.call("PUT", "/code-snippets/v1/snippets/13", {"code": code, "active": True, "scope": "global"})
print("cleanup update", st, u.get("active"))
import urllib.request, time
urllib.request.urlopen(urllib.request.Request("https://sunviksteels.com/?cleanup="+str(int(time.time())), headers={"User-Agent":"Mozilla/5.0"}), timeout=60).read(50)
time.sleep(1)
wpapi.call("PUT", "/code-snippets/v1/snippets/13", {"active": False})
print("done cleanup")
