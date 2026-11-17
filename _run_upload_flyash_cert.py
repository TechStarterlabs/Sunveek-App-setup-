import json, copy, shutil, os, time
from pathlib import Path
import wpapi

wpapi.preflight()

IMG = r"C:\Users\abhis\.cursor\projects\c-Users-abhis-Desktop-SUNVIK-STEEL\assets\c__Users_abhis_AppData_Roaming_Cursor_User_workspaceStorage_85f8b39dee22c51b2073fd2ba1cb0387_images_GreenPro_Renewal_Sunvik_Flyash_Blocks.pdf-003ed7c8-8825-4412-bb88-42048d879f4f.png"
ALT = "GreenPro Ecolabel Certificate — Sunvik Flyash Bricks & Blocks, valid until December 2027"

# 1) Inspect live cert widgets
st, page = wpapi.call("GET", "/wp/v2/pages/621?context=edit")
assert st == 200, page
meta = page.get("meta") or {}
ed_raw = meta.get("_elementor_data")
data = json.loads(ed_raw) if isinstance(ed_raw, str) else ed_raw

cert_imgs = []

def walk(nodes, trail=None):
    trail = trail or []
    if isinstance(nodes, list):
        for i, n in enumerate(nodes):
            walk(n, trail + [i])
    elif isinstance(nodes, dict):
        if nodes.get("widgetType") == "image":
            img = (nodes.get("settings") or {}).get("image") or {}
            url = img.get("url") or ""
            if any(k in url.lower() for k in ["greenpro", "mybuild", "cert", "certificate"]) or "Our Certifications" in str(trail):
                cert_imgs.append({"id": nodes.get("id"), "url": url, "media_id": img.get("id"), "trail": trail[:]})
        # also collect any image under section that has Our Certifications sibling - simpler: all greenpro/mybuild
        if "elements" in nodes:
            walk(nodes["elements"], trail)

walk(data)
# broader: all images with greenpro/mybuild in url
cert_imgs = []

def walk2(nodes):
    if isinstance(nodes, list):
        for n in nodes:
            walk2(n)
    elif isinstance(nodes, dict):
        if nodes.get("widgetType") == "image":
            img = (nodes.get("settings") or {}).get("image") or {}
            url = (img.get("url") or "").lower()
            if "greenpro" in url or "mybuild" in url or "certificate" in url:
                cert_imgs.append({"widget_id": nodes.get("id"), "url": img.get("url"), "media_id": img.get("id")})
        if "elements" in nodes:
            walk2(nodes["elements"])

walk2(data)
print("CURRENT CERT IMAGES:")
for c in cert_imgs:
    print(c)

# 2) Backup
bk = Path(r"C:\Users\abhis\Desktop\SUNVIK STEEL\_wp_backups")
bk.mkdir(exist_ok=True)
bk_path = bk / ("about-621-elementor-before-flyash-2027-renewal-%s.json" % time.strftime("%Y%m%d-%H%M%S"))
bk_path.write_text(ed_raw if isinstance(ed_raw, str) else json.dumps(data), encoding="utf-8")
print("backup", bk_path)

# 3) Upload media
st, media = wpapi.upload_media(IMG, filename="GreenPro-Renewal-Sunvik-Flyash-Bricks-Blocks-2027.png", alt=ALT)
print("upload", st, media.get("id"), media.get("source_url"))
assert st in (200, 201), media
media_id = media["id"]
media_url = media["source_url"]

# Update alt via REST if needed
wpapi.call("POST", f"/wp/v2/media/{media_id}", {"alt_text": ALT, "title": "GreenPro Renewal Sunvik Flyash Bricks Blocks 2027"})

# 4) Place as FIRST cert (left of top row) — same as before with 2027 first
# Identify top-left cert widget: historically 21e38f5 was left, 70484f6 right
# Find widgets by live URLs order under Our Certifications section

def find_cert_section(nodes):
    """Return the outer column elements list that contains heading Our Certifications."""
    if isinstance(nodes, list):
        for n in nodes:
            r = find_cert_section(n)
            if r is not None:
                return r
    elif isinstance(nodes, dict):
        # column that has title Our Certifications widget
        els = nodes.get("elements") or []
        for el in els:
            if el.get("widgetType") in ("trx_sc_title", "heading"):
                title = (el.get("settings") or {}).get("title") or ""
                if "Our Certifications" in title:
                    return els
        for el in els:
            r = find_cert_section(el)
            if r is not None:
                return r
            r = find_cert_section(el.get("elements") or [])
            if r is not None:
                return r
    return None

# Mutate: set first image widget that currently shows GreenPro to new media; keep second GreenPro as old if present
changed = []

def replace_first_greenpro(nodes, done=None):
    if done is None:
        done = {"n": 0}
    if isinstance(nodes, list):
        for n in nodes:
            replace_first_greenpro(n, done)
    elif isinstance(nodes, dict):
        if nodes.get("widgetType") == "image" and done["n"] == 0:
            img = (nodes.get("settings") or {}).get("image") or {}
            url = (img.get("url") or "").lower()
            if "greenpro" in url:
                old = img.get("url")
                nodes["settings"]["image"] = {
                    "id": media_id,
                    "url": media_url,
                    "alt": ALT,
                    "source": "library",
                    "size": "",
                }
                changed.append({"widget": nodes.get("id"), "old": old, "new": media_url})
                done["n"] += 1
                return
        if "elements" in nodes:
            replace_first_greenpro(nodes["elements"], done)

replace_first_greenpro(data)
print("changed", changed)

if not changed:
    # fallback: set left widget 21e38f5 if exists
    def set_by_id(nodes, wid):
        if isinstance(nodes, list):
            for n in nodes:
                if set_by_id(n, wid):
                    return True
        elif isinstance(nodes, dict):
            if nodes.get("id") == wid:
                nodes["settings"]["image"] = {
                    "id": media_id,
                    "url": media_url,
                    "alt": ALT,
                    "source": "library",
                    "size": "",
                }
                return True
            if "elements" in nodes and set_by_id(nodes["elements"], wid):
                return True
        return False
    ok = set_by_id(data, "21e38f5")
    print("fallback 21e38f5", ok)
    if ok:
        changed.append({"widget": "21e38f5", "new": media_url})

assert changed, "no cert widget updated"

# 5) Save page
new_ed = json.dumps(data, separators=(",", ":"))
st, updated = wpapi.call("POST", "/wp/v2/pages/621", {"meta": {"_elementor_data": new_ed}})
print("save page", st)
if st != 200:
    print(updated)
    raise SystemExit(1)

# Clear elementor CSS cache if possible - touch modified
wpapi.call("POST", "/wp/v2/pages/621", {"status": "publish"})

# Verify live HTML
import urllib.request, re
html = urllib.request.urlopen(urllib.request.Request("https://sunviksteels.com/about-us/?v=" + str(int(time.time())), headers={"User-Agent": "Mozilla/5.0"}), timeout=60).read().decode("utf-8", "replace")
# find cert image urls near Our Certifications
idx = html.lower().find("our certifications")
chunk = html[idx:idx+8000] if idx >= 0 else html
urls = re.findall(r'https://sunviksteels\.com/wp-content/uploads/[^\"\']+(?:GreenPro|Mybuild|MyBuild|certificate)[^\"\']*', chunk, re.I)
print("LIVE cert urls in section:", urls[:10])
print("new media present?", media_url.split("/")[-1] in html or str(media_id) in html)
print("DONE media_id", media_id, media_url)
