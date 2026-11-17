# Sunvik Steels — live WordPress toolkit

Remote toolkit for **sunviksteels.com** and **sunviksteels.shop**. This is not the website source; scripts edit the live sites via WordPress REST / Code Snippets.

Read **[CLAUDE.md](CLAUDE.md)** fully before changing anything. Every write is a production change (no staging).

## First-time setup (team)

1. Clone this repo.
2. Copy `.env.example` → `.env`.
3. Paste the real values from the private team channel into `.env` (never commit `.env`).
4. Use Python 3.10+ from this folder.

```bash
cd "/path/to/Sunveek-App-setup-"
# Windows PowerShell example:
# Copy-Item .env.example .env
# then edit .env
```

`wpapi.py` and `sunvik_edit.py` load `.env` automatically.

## Fast path — text change on a page

```bash
python -I sunvik_edit.py find "Old text" --id 621
python -I sunvik_edit.py replace --id 621 "Old text" "New text"
```

## Prompt your AI teammate can paste

```
You are working in the Sunvik Steels WordPress toolkit repo.
Read CLAUDE.md fully before any change.
Load credentials from .env only (never hardcode secrets).
Only change what was asked. Back up before every write (sunvik_edit.py replace does this).
After changes: purge that page's cache, verify the plain URL (desktop + mobile), health-check home + changed page, ensure snippet #13 is inactive.
Report in plain words: what changed, backup path, VERIFY pass/fail.
```

## What is gitignored

`.env`, `_wp_backups/`, temp JSON dumps, image upload originals. Historical `_run_*.py` scripts may remain as reference — they must not contain live passwords (use env vars).
