"""Deploy security-headers Code Snippet on .com and .shop, then verify live headers."""
from __future__ import annotations

import http.cookiejar
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import wpapi  # noqa: E402

SNIPPET = (ROOT / "_tmp_security_headers_snippet.php").read_text(encoding="utf-8").strip()
TITLE = "Sunvik Security Headers (audit)"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) SunvikHeaderAudit/1.0"}


def check_headers(url: str) -> dict:
    req = urllib.request.Request(url, method="GET", headers=UA)
    with urllib.request.urlopen(req, timeout=40) as resp:
        h = {k.lower(): v for k, v in resp.headers.items()}
        body = resp.read(8000)
        lower = body.lower()
        return {
            "url": url,
            "status": resp.status,
            "x-content-type-options": h.get("x-content-type-options"),
            "x-frame-options": h.get("x-frame-options"),
            "referrer-policy": h.get("referrer-policy"),
            "strict-transport-security": h.get("strict-transport-security"),
            "content-security-policy": (h.get("content-security-policy") or "")[:160],
            "critical_error": b"critical error" in lower,
            "body_ok": b"<html" in lower or b"<!doctype" in lower,
        }


def deploy_com() -> dict:
    if not os.environ.get("WP_USER") or not os.environ.get("WP_APP_PW"):
        raise SystemExit("Set WP_USER / WP_APP_PW in .env (see .env.example)")
    wpapi.preflight()
    st, snips = wpapi.call("GET", "/code-snippets/v1/snippets?per_page=100")
    if st != 200 or not isinstance(snips, list):
        return {"ok": False, "error": f"list failed {st} {snips}"}
    match = next((s for s in snips if s.get("name") == TITLE), None)
    body = {"name": TITLE, "code": SNIPPET, "active": True, "scope": "global"}
    if match:
        st2, resp = wpapi.call("PUT", f"/code-snippets/v1/snippets/{match['id']}", body)
        return {"ok": st2 in (200, 201), "action": "updated", "id": match["id"], "status": st2, "code_error": (resp or {}).get("code_error") if isinstance(resp, dict) else None}
    st2, resp = wpapi.call("POST", "/code-snippets/v1/snippets", body)
    sid = resp.get("id") if isinstance(resp, dict) else None
    return {"ok": st2 in (200, 201) and sid, "action": "created", "id": sid, "status": st2, "code_error": (resp or {}).get("code_error") if isinstance(resp, dict) else None, "resp": {k: resp.get(k) for k in ("id", "active", "message", "code_error")} if isinstance(resp, dict) else resp}


def shop_rest():
    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

    def get(url):
        return opener.open(urllib.request.Request(url, headers=UA), timeout=60).read().decode("utf-8", "replace")

    def post_form(url, data):
        body = urllib.parse.urlencode(data).encode()
        req = urllib.request.Request(
            url,
            data=body,
            headers={**UA, "Content-Type": "application/x-www-form-urlencoded"},
            method="POST",
        )
        return opener.open(req, timeout=60)

    shop_user = os.environ.get("SHOP_WP_USER") or wpapi.SHOP_USER
    shop_pw = os.environ.get("SHOP_WP_PASSWORD") or wpapi.SHOP_PASSWORD
    if not shop_user or not shop_pw:
        raise RuntimeError("Set SHOP_WP_USER / SHOP_WP_PASSWORD in .env")
    shop = (os.environ.get("SHOP_SITE") or wpapi.SHOP_SITE).rstrip("/")
    get(shop + "/wp-login.php")
    r = post_form(
        shop + "/wp-login.php",
        {
            "log": shop_user,
            "pwd": shop_pw,
            "wp-submit": "Log In",
            "redirect_to": shop + "/wp-admin/",
            "testcookie": "1",
        },
    )
    admin = get(shop + "/wp-admin/")
    nonce_m = re.search(r'wpApiSettings\s*=\s*\{[^}]*"nonce":"([^"]+)"', admin) or re.search(
        r'"nonce":"([^"]+)"', admin
    )
    if not nonce_m:
        raise RuntimeError("shop nonce not found")
    nonce = nonce_m.group(1)

    def rest(method, path, payload=None):
        url = shop + "/wp-json" + path
        data = json.dumps(payload).encode() if payload is not None else None
        headers = {**UA, "Accept": "application/json", "X-WP-Nonce": nonce}
        if data:
            headers["Content-Type"] = "application/json"
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with opener.open(req, timeout=90) as resp:
                return resp.status, json.loads(resp.read().decode() or "{}")
        except urllib.error.HTTPError as e:
            raw = e.read().decode("utf-8", "replace")
            try:
                return e.code, json.loads(raw)
            except Exception:
                return e.code, {"raw": raw[:400]}

    return rest, r.geturl()


def deploy_shop() -> dict:
    rest, login_url = shop_rest()
    st, snips = rest("GET", "/code-snippets/v1/snippets?per_page=100")
    if st != 200 or not isinstance(snips, list):
        return {"ok": False, "login": login_url, "error": f"list failed {st} {snips}"}
    match = next((s for s in snips if s.get("name") == TITLE), None)
    body = {"name": TITLE, "code": SNIPPET, "active": True, "scope": "global"}
    if match:
        st2, resp = rest("PUT", f"/code-snippets/v1/snippets/{match['id']}", body)
        return {"ok": st2 in (200, 201), "action": "updated", "id": match["id"], "status": st2, "code_error": (resp or {}).get("code_error") if isinstance(resp, dict) else None}
    st2, resp = rest("POST", "/code-snippets/v1/snippets", body)
    sid = resp.get("id") if isinstance(resp, dict) else None
    return {"ok": st2 in (200, 201) and sid, "action": "created", "id": sid, "status": st2, "code_error": (resp or {}).get("code_error") if isinstance(resp, dict) else None}


def main():
    results = {"com": None, "shop": None, "checks": [], "errors": []}
    try:
        results["com"] = deploy_com()
    except Exception as e:
        results["errors"].append({"stage": "com", "error": str(e)})
    try:
        results["shop"] = deploy_shop()
    except Exception as e:
        results["errors"].append({"stage": "shop", "error": str(e)})

    time.sleep(2)
    urls = [
        "https://sunviksteels.com/",
        "https://www.sunviksteels.com/",
        "https://sunviksteels.com/about-us/",
        "https://sunviksteels.com/tmt-bars/",
        "https://sunviksteels.shop/",
        "https://sunviksteels.shop/contact-us/",
    ]
    for u in urls:
        try:
            results["checks"].append(check_headers(u + ("&" if "?" in u else "?") + "t=" + str(int(time.time()))))
        except Exception as e:
            results["errors"].append({"url": u, "error": str(e)})

    out = ROOT / "_security_headers_result.json"
    out.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
