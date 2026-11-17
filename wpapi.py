import base64, json, os, time, urllib.request, urllib.error
from pathlib import Path


def _load_dotenv(path=None):
    """Load KEY=VALUE pairs from .env into os.environ (does not override existing)."""
    env_path = Path(path) if path else Path(__file__).resolve().parent / ".env"
    if not env_path.is_file():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = val


_load_dotenv()

SITE = os.environ.get("WP_SITE", "https://sunviksteels.com").rstrip("/")
USER = os.environ.get("WP_USER", "")
APPPW = os.environ.get("WP_APP_PW", "")
SHOP_SITE = os.environ.get("SHOP_SITE", "https://sunviksteels.shop").rstrip("/")
SHOP_USER = os.environ.get("SHOP_WP_USER", "")
SHOP_PASSWORD = os.environ.get("SHOP_WP_PASSWORD", "")
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) SunvikCert/1.0"


def _auth():
    return "Basic " + base64.b64encode(("%s:%s" % (USER, APPPW)).encode()).decode()


def call(method, path, payload=None, tries=3, timeout=120):
    url = SITE + "/wp-json" + path
    data = json.dumps(payload).encode() if payload is not None else None
    headers = {"User-Agent": UA, "Accept": "application/json", "Authorization": _auth()}
    if data:
        headers["Content-Type"] = "application/json"
    for attempt in range(tries):
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                raw = r.read().decode("utf-8", "replace")
                return r.status, json.loads(raw) if raw else {}
        except urllib.error.HTTPError as e:
            raw = e.read().decode("utf-8", "replace")
            try:
                body = json.loads(raw)
            except Exception:
                body = {"raw": raw[:500]}
            if attempt + 1 < tries and e.code >= 500:
                time.sleep(2)
                continue
            return e.code, body
        except Exception as e:
            if attempt + 1 < tries:
                time.sleep(2)
                continue
            return 0, {"error": str(e)}
    return 0, {"error": "exhausted"}


def upload_media(filepath, filename=None, alt=""):
    import mimetypes

    path = filepath
    filename = filename or os.path.basename(path)
    mime = mimetypes.guess_type(filename)[0] or "application/octet-stream"
    with open(path, "rb") as f:
        content = f.read()
    boundary = "----SunvikBoundary7MA4YWxkTrZu0gW"
    body = b""
    body += ("--%s\r\n" % boundary).encode()
    body += ('Content-Disposition: form-data; name="file"; filename="%s"\r\n' % filename).encode()
    body += ("Content-Type: %s\r\n\r\n" % mime).encode()
    body += content + b"\r\n"
    if alt:
        body += ("--%s\r\n" % boundary).encode()
        body += b'Content-Disposition: form-data; name="alt_text"\r\n\r\n'
        body += alt.encode() + b"\r\n"
    body += ("--%s\r\n" % boundary).encode()
    body += b'Content-Disposition: form-data; name="title"\r\n\r\n'
    body += filename.encode() + b"\r\n"
    body += ("--%s--\r\n" % boundary).encode()
    headers = {
        "User-Agent": UA,
        "Authorization": _auth(),
        "Content-Type": "multipart/form-data; boundary=%s" % boundary,
        "Content-Disposition": 'attachment; filename="%s"' % filename,
        "Accept": "application/json",
    }
    req = urllib.request.Request(SITE + "/wp-json/wp/v2/media", data=body, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=180) as r:
        return r.status, json.loads(r.read().decode())


def preflight():
    st, d = call("GET", "/wp/v2/users/me")
    if st != 200:
        raise SystemExit("auth failed: %s %s" % (st, d))
    print("authenticated as: %s (id=%s)" % (d.get("slug") or d.get("name"), d.get("id")))
    return d
