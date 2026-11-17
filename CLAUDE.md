# Sunvik Steels website — AI runbook

Read this fully before touching anything. This folder is **not** the website's code. It is a toolkit
that edits the **live** WordPress sites remotely. Every change here is a production change, and
there is no staging site.

- **sunviksteels.com**: main site (Elementor + ThemeREX theme). Most tasks are here.
- **sunviksteels.shop**: second WordPress install on the same cPanel host. Has its own forms and SMTP.

---

## 1. Fast path: change text on a page (about 3 commands)

Use [sunvik_edit.py](sunvik_edit.py). Do not write a new one-off script for a text change.

```bash
cd "/c/Users/abhis/Desktop/SUNVIK STEEL"
export WP_USER=... WP_APP_PW=...          # see §3

python -I sunvik_edit.py find "Old text" --id 621          # where is it? (read-only)
python -I sunvik_edit.py find "Old text"                   # search all published pages
python -I sunvik_edit.py replace --id 621 "Old text" "New text"
```

`replace` does everything in one run. It never saves if anything looks off.
1. It backs up the page's Elementor data and post content to `_wp_backups/pages-<id>-before-replace-<stamp>.json`.
2. It changes only the setting strings that contain the old text. It stops if the number of matches isn't exactly `--count` (default 1).
3. It saves, re-reads the page, and confirms only those fields changed.
4. It clears that page's caches (Elementor element cache + WP Fastest Cache).
5. It loads the live URL as a real visitor on desktop and mobile, and prints `VERIFY: PASS` or `FAIL`.

The other commands:
- `purge --id N` clears that one page's caches.
- `verify --id N "must be present" ["must be gone"]` checks the live page.
- `--type posts` works on blog posts instead of pages.

`find` matching ignores case. `replace` matching is exact and case-sensitive. Copy the exact
string that `find` printed, because CSS often shows text in capitals that is stored in mixed case.

Tell the user the result in plain words, and include the backup file path.

---

## 2. Rules (each one comes from a real incident)

1. **Back up before every write.** Save the original data in `_wp_backups/` before saving anything.
   `sunvik_edit.py replace` already does this.
2. **Never call `\Elementor\Plugin::$instance->files_manager->clear_cache()`.** On 2026-10-28 it caused
   an HTTP 500 on the request that ran it, and it deletes every Elementor CSS file across the site.
   Clear the cache for one page only: `delete_post_meta($id, '_elementor_element_cache')` plus
   `wpfc_clear_post_cache_by_id($id)`.
3. **Don't reuse `_tmp_clear_el.php`.** It forces `_elementor_version` to `3.0.0`, which is wrong.
4. **Gate temporary PHP so visitors never run it.** Wrap the code in `if (isset($_GET['sunvik_xyz']))`
   and run it on `init`. `sunvik_edit.run_snippet()` does this for you.
5. **Always switch snippet #13 off in a `finally` block,** even if the request fails.
   Before using it, check that it is inactive. If it's already active, stop and ask.
6. **Check the live site with the plain URL, not only `?v=123`.** A query string skips WP Fastest
   Cache, so a cache-busted URL can show the new text while real visitors still see the old one.
   This happened on 2026-10-28.
7. **Don't load the page between saving and clearing the cache.** That request makes WP Fastest Cache
   save a fresh copy of the stale page.
8. **After any change, run a health check:** the changed page, the home page, and a couple of key
   pages should return HTTP 200, contain no "critical error", and end with `</html>`.
   If anything returns 500, check snippet #13 first and switch it off.
9. **Only change what was asked.** Don't tidy up, reformat, or "improve" nearby content, plugins or settings.
10. **Ask before:** deleting anything, changing plugins or themes, editing `.htaccess` or `wp-config.php`,
    touching email/SMTP or form recipients, or making changes that cover the whole site.

---

## 3. Credentials and environment

- Copy [`.env.example`](.env.example) → `.env` and fill real values (private team channel only).
  `.env` is gitignored. Never commit it or paste secrets into chat/PRs.
- [wpapi.py](wpapi.py) auto-loads `.env` and reads `WP_USER` / `WP_APP_PW` / `WP_SITE`
  (and `SHOP_WP_USER` / `SHOP_WP_PASSWORD` / `SHOP_SITE` for shop cookie-login scripts).
- You can still export the same vars in the shell; existing env wins over `.env`.
- **Don't hardcode credentials** in scripts, docs, or new files. Rotate if anything leaked.
- Python 3.10+ (this PC has 3.14). Run with `python -I` from this folder. `-I` means the current
  folder isn't on the import path, so scripts must `sys.path.insert(0, <this folder>)` before
  `import wpapi`. `sunvik_edit.py` already does.

### Tooling quirks seen in this environment
- **Bash heredocs collapse backslashes** (`\\` turns into `\`), which corrupts PHP namespaces and regex.
  Write PHP and Python files with the Write tool, not `cat <<EOF`.
- Bash commands time out after 120s. Checks that cover the whole site (around 60 pages) take longer,
  so set a bigger `timeout` or run them in the background.
- After a Bash call, the shell sometimes goes back to the project folder. Use absolute paths.

---

## 4. Site map (sunviksteels.com)

| Thing | ID / location |
|---|---|
| Home page | page **6166** (front page) |
| About Us | page **621**, `/about-us/` |
| CMD block on About Us | widget `a3b2f8d` (`trx_sc_title`): `subtitle` = "Chairman and Managing Director", title = "Mr. Vivek Kejriwal" |
| Certifications on About Us | image widgets under the "Our Certifications" heading |
| TMT Bars page (enquiry form) | post **6408**, `/tmt-bars/` |
| Main WPForms form | **11835** |
| Code Snippets | **#13** = temporary runner (keep inactive) · **#16** = security headers (keep active) · **#5** = Home Page Schema (keep active) |
| Server path | `/home/pgf2xcsto0v0/public_html/` (cPanel). .shop is at `.../public_html/sunviksteels.shop/` |

Content structure:
- The layout is in post meta `_elementor_data` (JSON), editable through REST `/wp/v2/pages/<id>` with
  `context=edit`. `post_content` is only a plain-HTML copy of it (used for SEO and search).
  Update both.
- The theme is ThemeREX. Its widgets are `trx_sc_*`, e.g. `trx_sc_title` with `title`, `subtitle`
  and `description` settings. Many headings are capitalised by CSS.
- Header and footer are ThemeREX layouts or Elementor templates, not pages. `find` over pages won't see them.
- When the data is saved again, Python may write `\uXXXX` escapes as plain characters, so the JSON
  size changes slightly. That's harmless. Compare the parsed data, not the raw string.

Active plugins worth knowing about:
- **Caching:** WP Fastest Cache. It caches desktop pages only; mobile isn't cached.
- **Layout:** Elementor, Happy Addons, ThemeREX Addons, Slider Revolution.
- **SEO:** Yoast SEO + Premium.
- **Forms and email:** WPForms Lite, Contact Form 7, WP Mail SMTP, Mailchimp for WP, TeleCRM.
- **Other:** Click to Chat (WhatsApp button), Code Snippets, Limit Login Attempts, Temporary Login,
  TinyPNG, Site Kit, "Fetch Product Rate Plugin" (custom; don't touch), All-in-One WP Migration,
  Smash Balloon feeds, DearFlip, MapGeo.

## 5. sunviksteels.shop
- No REST application password. Scripts either log in with cookies (`_run_fix_via_shop*.py`) or
  reach its database from a .com snippet by reading the shop's `wp-config.php`.
- WPForms forms **1866** and **2276**. Security headers are snippet **#10** on .shop.

---

## 6. Running other PHP on the server (snippet #13 pattern)

For anything that REST can't do:
1. Write the PHP to a file with the Write tool.
2. Call `sunvik_edit.run_snippet(code, "sunvik_<task>", "<label>")`. It checks #13 is inactive,
   gates the code behind the query parameter, runs it once, and switches #13 off again.
3. To return data, write JSON to `wp-content/uploads/sunvik-<task>.json`, fetch it, and then
   **delete it** with a second gated run. Those files are publicly readable.

The older `_run_*.py` / `_tmp_*.php` scripts in this folder are a record of past work. Read them
for reference, but don't re-run them blindly: several of them change email and form settings.

---

## 7. Change log
- **2026-10-28:** About Us CMD designation changed from "Our Chief Managing Director" to
  "Chairman and Managing Director". Backup: `_wp_backups/about-621-before-cmd-designation-20261028-120953.json`.
  Afterwards all 59 published pages were checked and returned 200. Added `sunvik_edit.py` and this file.
- **2026-10-14:** security-header snippets deployed (.com #16, .shop #10) and checked on the live sites.
- **2026-10-01:** GreenPro flyash certificate (valid to 2027) added to About Us certifications.
- **Sep 2026:** WPForms notifications on both sites go to manjunath@sunvik.in and
  divya.nikam@thestarterlabs.com; SMTP/Brevo set up; spam fix.
- **Aug–Sep 2026:** images compressed after the Zoo Media technical audit, with alt-text updates;
  CSR page banner and year updated.

## 8. Open items
- Four images over 100KB still need compressing: see [Images-Over-100KB-REMAINING.txt](Images-Over-100KB-REMAINING.txt).
- Prefer rotating WP / shop passwords periodically; keep them only in private `.env`, never in git.

## 9. Checklist for every task
- [ ] Confirm the exact page, URL and text with the user. Use `find` to locate it (read-only).
- [ ] Make the change through `sunvik_edit.py` where possible (it backs up automatically).
- [ ] Clear the cache for that page only. Check the plain URL on desktop and mobile.
- [ ] Health-check the home page and the changed page (HTTP 200, no critical error).
- [ ] Snippet #13 is inactive. Temporary JSON files in uploads are deleted.
- [ ] Add a line to §7, and update §4 if any IDs or text changed.
- [ ] Report to the user in plain words: what changed, the backup path, and the verification result.
