"""Safe text edits on sunviksteels.com Elementor pages.

Usage (from the project folder, WP_USER / WP_APP_PW set):
  python -I sunvik_edit.py find "<text>" [--type pages|posts] [--id N]
  python -I sunvik_edit.py replace --id N "<old>" "<new>" [--count K]
  python -I sunvik_edit.py purge --id N
  python -I sunvik_edit.py verify --id N "<must be present>" ["<must be gone>"]

replace = backup -> change -> save -> diff check -> purge caches -> live verify.
"""
import json, re, sys, time, urllib.error, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import wpapi  # noqa: E402

BK = ROOT / "_wp_backups"
SNIPPET_ID = 13
DESKTOP_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/130 Safari/537.36"
MOBILE_UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148 Safari/604.1"


def die(msg):
    raise SystemExit("STOP: " + msg)


def get_item(kind, pid):
    st, item = wpapi.call("GET", "/wp/v2/%s/%d?context=edit" % (kind, pid))
    if st != 200:
        die("GET %s %d -> %s %s" % (kind, pid, st, item))
    return item


def elementor_data(item):
    raw = (item.get("meta") or {}).get("_elementor_data") or ""
    return raw, (json.loads(raw) if raw else [])


def walk_strings(node, fn, trail=()):
    """Call fn(trail, value) for every string under widget settings; fn returns new value or None."""
    if isinstance(node, list):
        for i, x in enumerate(node):
            walk_strings(x, fn, trail + (i,))
    elif isinstance(node, dict):
        settings = node.get("settings")
        if isinstance(settings, (dict, list)):
            _walk_settings(settings, fn, (node.get("id"), node.get("widgetType") or node.get("elType")))
        walk_strings(node.get("elements") or [], fn, trail)


def _walk_settings(obj, fn, widget, path=()):
    items = obj.items() if isinstance(obj, dict) else enumerate(obj)
    for k, v in list(items):
        if isinstance(v, str):
            new = fn(widget, path + (k,), v)
            if new is not None:
                obj[k] = new
        elif isinstance(v, (dict, list)):
            _walk_settings(v, fn, widget, path + (k,))


def leaf_diff(a, b, path=()):
    if type(a) is not type(b):
        return [(path, a, b)]
    if isinstance(a, dict):
        out = []
        for k in set(a) | set(b):
            out += leaf_diff(a.get(k), b.get(k), path + (k,))
        return out
    if isinstance(a, list):
        if len(a) != len(b):
            return [(path, "len %d" % len(a), "len %d" % len(b))]
        out = []
        for i, (x, y) in enumerate(zip(a, b)):
            out += leaf_diff(x, y, path + (i,))
        return out
    return [] if a == b else [(path, a, b)]


def cmd_find(text, kind="pages", pid=None):
    wpapi.preflight()
    if pid:
        items = [get_item(kind, pid)]
    else:
        st, items = wpapi.call("GET", "/wp/v2/%s?per_page=100&context=edit&status=publish" % kind)
        if st != 200:
            die("list %s -> %s" % (kind, st))
    rx = re.compile(re.escape(text), re.I)
    total = 0
    for item in items:
        _, data = elementor_data(item)
        hits = []
        walk_strings(data, lambda w, p, v: hits.append((w, p, v)) if rx.search(v) else None)
        in_content = len(rx.findall((item.get("content") or {}).get("raw") or ""))
        if hits or in_content:
            print("\n#%s %s  (%s)" % (item["id"], item.get("link"), (item.get("title") or {}).get("raw")))
            for (wid, wtype), path, v in hits:
                print("   widget %s [%s] %s = %r" % (wid, wtype, "/".join(map(str, path)), v[:200]))
            print("   post_content fallback copies: %d" % in_content)
            total += len(hits)
    print("\nelementor matches: %d (searched %d %s)" % (total, len(items), kind))
    if not total:
        print("Not found in %s. Also try --type posts; header/footer text lives in ThemeREX layouts / Elementor templates." % kind)


def run_snippet(code, trigger_param, label):
    """Run PHP once via Code Snippet #13, gated on a query param so visitors never execute it."""
    st, s = wpapi.call("GET", "/code-snippets/v1/snippets/%d" % SNIPPET_ID)
    if st != 200:
        die("snippet %d not readable: %s" % (SNIPPET_ID, st))
    if s.get("active"):
        die("snippet %d is already active (%s) - someone else may be using it" % (SNIPPET_ID, s.get("name")))
    gated = "if ( isset( $_GET['%s'] ) ) {\n\tadd_action( 'init', function () {\n%s\n\t}, 99 );\n}\n" % (
        trigger_param, "\n".join("\t\t" + line for line in code.strip().splitlines()))
    st, u = wpapi.call("PUT", "/code-snippets/v1/snippets/%d" % SNIPPET_ID,
                       {"name": "TEMP " + label, "code": gated, "active": True, "scope": "global"})
    if st != 200 or (isinstance(u, dict) and u.get("code_error")):
        wpapi.call("PUT", "/code-snippets/v1/snippets/%d" % SNIPPET_ID, {"active": False})
        die("snippet rejected: %s %s" % (st, u.get("code_error") if isinstance(u, dict) else u))
    try:
        url = "%s/?%s=1&t=%d" % (wpapi.SITE, trigger_param, time.time())
        r = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": DESKTOP_UA}), timeout=90)
        print("snippet ran: HTTP", r.status)
    finally:
        st, u = wpapi.call("PUT", "/code-snippets/v1/snippets/%d" % SNIPPET_ID,
                           {"name": "TEMP DISABLED " + label, "active": False})
        print("snippet %d deactivated: %s" % (SNIPPET_ID, not u.get("active")))


def cmd_purge(pid):
    # Per-page only. Do NOT call Elementor files_manager->clear_cache() here (500'd the site once).
    run_snippet(
        "delete_post_meta( %d, '_elementor_element_cache' );\n"
        "clean_post_cache( %d );\n"
        "if ( function_exists( 'wpfc_clear_post_cache_by_id' ) ) { wpfc_clear_post_cache_by_id( %d ); }" % (pid, pid, pid),
        "sunvik_purge_%d" % pid, "purge cache post %d" % pid)


def fetch(url, ua):
    r = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": ua}), timeout=90)
    return r.status, r.read().decode("utf-8", "replace")


def cmd_verify(pid, present, gone=None, kind="pages"):
    link = get_item(kind, pid)["link"]
    ok = True
    # Plain URL on purpose: a ?query string bypasses WP Fastest Cache and hides stale cache.
    for label, ua in (("desktop", DESKTOP_UA), ("mobile", MOBILE_UA)):
        try:
            st, html = fetch(link, ua)
        except urllib.error.HTTPError as e:
            print(label, "HTTP", e.code, "FAIL")
            ok = False
            continue
        cached = re.search(r"WP Fastest Cache file was created[^>]*?on ([^>]*?)-->", html)
        checks = {
            "http_200": st == 200,
            "has_new": present in html,
            "old_gone": (gone not in html) if gone else True,
            "no_critical_error": "critical error" not in html.lower(),
            "complete_html": "</html>" in html.lower(),
        }
        print(label, link, checks, "| wpfc:", cached.group(1).strip() if cached else "not cached")
        ok = ok and all(checks.values())
    print("VERIFY:", "PASS" if ok else "FAIL")
    return ok


def cmd_replace(pid, old, new, count=1, kind="pages"):
    wpapi.preflight()
    item = get_item(kind, pid)
    ed_raw, data = elementor_data(item)
    content_raw = (item.get("content") or {}).get("raw") or ""
    if not ed_raw:
        die("post %d has no Elementor data" % pid)

    stamp = time.strftime("%Y%m%d-%H%M%S")
    BK.mkdir(exist_ok=True)
    bk = BK / ("%s-%d-before-replace-%s.json" % (kind, pid, stamp))
    bk.write_text(json.dumps({"_elementor_data": ed_raw, "content_raw": content_raw, "modified": item.get("modified"),
                              "old": old, "new": new}, ensure_ascii=False), encoding="utf-8")
    print("backup:", bk)

    before = json.loads(ed_raw)
    hits = []

    def repl(widget, path, v):
        if old in v:
            hits.append((widget, path, v.count(old)))
            return v.replace(old, new)
        return None

    walk_strings(data, repl)
    n = sum(h[2] for h in hits)
    if n != count:
        die("expected %d occurrence(s) of %r, found %d: %s (nothing saved)" % (count, old, n, hits))
    diffs = leaf_diff(before, data)
    if len(diffs) != len(hits):
        die("unexpected diff %s (nothing saved)" % diffs)

    payload = {"meta": {"_elementor_data": json.dumps(data, separators=(",", ":"), ensure_ascii=False)}}
    if old in content_raw:
        payload["content"] = content_raw.replace(old, new)
    st, resp = wpapi.call("POST", "/wp/v2/%s/%d" % (kind, pid), payload)
    if st != 200:
        die("save failed %s %s" % (st, resp))

    stored = json.loads(elementor_data(get_item(kind, pid))[0])
    sdiff = leaf_diff(before, stored)
    print("saved. changed fields:")
    for path, a, b in sdiff:
        print("   %r -> %r" % (a, b))
    if len(sdiff) != len(hits):
        die("stored data differs unexpectedly - restore from %s" % bk)

    cmd_purge(pid)
    time.sleep(2)
    ok = cmd_verify(pid, new, old if new.find(old) < 0 else None, kind)
    if not ok:
        print("Live check failed. Backup:", bk)


def main(argv):
    def opt(name, default=None, cast=str):
        if name in argv:
            i = argv.index(name)
            val = argv[i + 1]
            del argv[i:i + 2]
            return cast(val)
        return default

    kind = opt("--type", "pages")
    pid = opt("--id", None, int)
    count = opt("--count", 1, int)
    if not argv:
        die(__doc__)
    cmd, args = argv[0], argv[1:]
    if cmd == "find" and len(args) == 1:
        cmd_find(args[0], kind, pid)
    elif cmd == "replace" and pid and len(args) == 2:
        cmd_replace(pid, args[0], args[1], count, kind)
    elif cmd == "purge" and pid:
        wpapi.preflight()
        cmd_purge(pid)
    elif cmd == "verify" and pid and len(args) in (1, 2):
        cmd_verify(pid, args[0], args[1] if len(args) == 2 else None, kind)
    else:
        die(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
