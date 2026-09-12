# Changelog

## 3.9.0 — 2026-09-12

Security release, from the ClawHub 3.8.2 audit. Two defaults change; both have an
escape hatch.

Fixed:

- **Credential leak on cross-host redirects.** The nine scripts that send an
  `Authorization` header with `urllib` called `urllib.request.urlopen` directly,
  and CPython's `HTTPRedirectHandler` copies every header except
  `content-length`/`content-type` onto a redirected request — so a redirect to
  another host carried the site's app password with it. All of them now go
  through `security.urlopen_authenticated`, which strips `Authorization` when a
  redirect leaves the origin (scheme, host or effective port). The four scripts
  that authenticate through `requests` were never affected: its
  `rebuild_auth` already does this.
- **SSRF through the unauthenticated site audit.** `site_audit` accepted any URL
  and opened a TLS connection to whatever host came back, so
  `site_audit http://192.168.1.1/` — or a public site answering `302
  http://169.254.169.254/` — reached whatever the agent's host can reach. It now
  opens through `security.urlopen_probe`, which validates the URL *and* the
  target of every redirect against the address rule; the TLS expiry check
  validates its hostname the same way. An address must be globally reachable
  (`is_global`) *and* none of private/loopback/link-local/multicast/reserved/
  unspecified — enumerating only the second half missed RFC 6598 shared address
  space (`100.64.0.0/10`), which Python reports as none of them and which is
  routable on any network running CGNAT. `http://` stays permitted here because
  detecting a missing HTTPS redirect is one of the audit's own checks.
- `seed_content` read its `--dataset` with a bare `open()`; it now goes through
  `validate_local_file` with the 2 MB text ceiling, like every other local read.
- The multi-site runners check **every** selected site before the first write.
  Refusing http:// inside the loop would abort a batch partway - earlier sites
  modified, later ones untouched, no summary - so `batch_update` and `wp_cli`
  preflight the whole selection. A dry run reports the same problems without
  exiting, so planning surfaces them (it makes no requests, so there is nothing
  to refuse).
- `describe_cpt` sent Basic credentials without ever checking the URL scheme —
  its `main()` was the one authenticated CLI that never called the guard, so the
  plaintext-http rule below did not apply to it.
- `seo_meta` reported failure as `{"error": ...}` and still exited 0, which CI
  and an agent both read as success. Both result paths exit 1 on an error.
- `jetengine_fields --list-all` was declared but never read, so passing it
  silently returned the same filtered output. It now includes private
  (underscore-prefixed) meta as documented.
- `references/gutenberg-blocks.md`: the table block example closed with
  `<!-- /wp:heading -->`.
- A hostname that does not resolve raises `HostResolutionError` (a `SafetyError`
  subclass) rather than a bare `SafetyError`, so the address validation above did
  not turn a typo'd domain into "refused by the address safety rule". `site_audit`
  still reports it as a site that did not respond, with its JSON intact.

Changed (breaking):

- **Plaintext `http://` to a non-local host is refused**, where it previously
  printed a warning and sent the app password in the clear anyway. Set
  `WP_ALLOW_HTTP=1` to restore the warn-and-continue behaviour;
  `WP_REQUIRE_HTTPS=1` still refuses and wins over it. `localhost` and the
  `.local` / `.test` / `.localhost` suffixes are exempt exactly as before.
- **A SEO meta key outside the Rank Math / Yoast allowlist is refused**, where it
  was previously written as raw postmeta with a warning — a typo'd friendly name
  silently created a junk meta row, or overwrote a key another plugin owns. Set
  `WP_ALLOW_RAW_META=1` for the old behaviour; `WP_REQUIRE_ALLOWLIST=1` still
  refuses and wins over it.
- `warn_insecure_wp_url` is now `require_secure_wp_url` (the pure, raising half
  is `check_wp_url_scheme`). The old name described the old behaviour.

Disclosure:

- `SKILL.md` declared `shell: "none (Python only; no shell-out)"`, which was
  false: `wp_cli.py` spawns `python3 <script>` subprocesses (argv list, never
  `shell=True`) and `wp.sh` is a bash wrapper around it. The declaration now says
  so, and the network/env blocks cover the audit's egress and the new variables.
- `SKILL.md` told users to run `bash INSTALL.sh` from the skill directory, but
  that installer lives in the git repo and is not part of the packaged skill.
- `requests` is now pinned: `requirements.txt` ships inside the skill with
  `requests>=2.32.3` (2.32.0 fixed CVE-2024-35195, where a `Session` that made
  one `verify=False` request silently skipped certificate verification for later
  requests to that host).

## 3.8.2 — 2026-06-12

Codex review fixes:

- Seeding: featured-image failures raise (were sys.exit) so one bad image no longer aborts the whole batch; ACF/JetEngine field writes and featured media now route through the CPT's rest_base (were silently no-op'ing on custom post types).
- Taxonomy rest_base resolved via /wp/v2/taxonomies (was the post-type endpoint).
- site_audit: HTTP 4xx/5xx pages are audited (status/headers/SEO) instead of reported unreachable; truly unreachable targets exit non-zero.
- Machine-readable stdout: the publish-confirm prompt no longer writes to stdout (stderr only).
- Permissions disclosure notes plaintext-HTTP egress is permitted (warn-only) unless WP_REQUIRE_HTTPS=1.

## 3.8.1 — 2026-06-10

Soft security guards (ClawHub audit follow-up, non-breaking):

- SEO meta: writing a non-allowlisted (raw) postmeta key now emits a warning; set `WP_REQUIRE_ALLOWLIST=1` to refuse instead. ACF/JetEngine custom fields are unaffected (arbitrary keys are their intended API).
- create_post / update_post: interactive confirmation before `--status publish` when run on a TTY; `--yes`/`-y` bypasses. Non-interactive/agent runs are unchanged.

## 3.8.0 — 2026-06-10

Security hardening (ClawHub audit, safe-additive — no breaking changes):

- Warn on plaintext http:// WordPress URLs (Basic-Auth credentials would be sent in cleartext); set WP_REQUIRE_HTTPS=1 to refuse instead. Localhost/dev hosts exempt.
- SKILL.md description now discloses the no-auth site-audit / fingerprinting capability.
- Added an explicit permissions declaration (env / network / filesystem / shell).

## 3.7.1 - 2026-06-04
- ClawHub listing now publishes under the display name **WordPress API Pro** (`--name`) with a pinned slug (`--slug wordpress-api-pro`), instead of an auto-title-cased "Wordpress Api Pro".

## 3.7.0 - 2026-06-02

- Add `site_audit.py` — no-auth Tier-1 website audit (PageSpeed, SSL, security headers, CMS/PHP detection, SEO basics) emitting findings against the audit-engine thresholds. Stdlib-only; the sales-hook quick scan. Pure parsers unit-tested offline + wired into CI.

## 3.6.0 - 2026-06-02

CPT content seeding (Tier-1 dynamic content).

- `create_post.py` gains `--post-type` (resolves rest_base via `/wp/v2/types`) and `--terms` (name→id, create-missing); now importable.
- New `describe_cpt.py` — read-only schema discovery (rest_base, taxonomies, sampled field keys).
- New `seed_content.py` — batch-create CPT entries with ACF/Jet fields, taxonomies, and featured images from a JSON dataset. **Dry-run by default**; `--execute` to write; per-entry errors collected, batch continues. Dry-run/planning is stdlib-only (write-path deps imported lazily).
- `upload_media.py` made importable (`__main__` guard).
- CI runs new unit tests + an offline dry-run smoke.

## 3.5.1 - 2026-06-01

ClawHub packaging compatibility.

- Removed `wordpress-api-pro/requirements.txt` from the published skill payload — the ClawHub package directory ships only `.json` / `.md` / `.py` / `.sh` files, so the single `.txt` is dropped to keep publishing clean.
- The `requests` dependency (ACF / SEO / JetEngine / plugin-detection scripts only) is now installed directly: `pip install requests`. `INSTALL.sh`, README, and SKILL.md updated accordingly. Core scripts remain stdlib-only.

## 3.5.0 - 2026-06-01

Claude Code support.

- Added `INSTALL.sh` to install the skill into `~/.claude/skills/wordpress-api-pro/` for [Claude Code](https://claude.ai/download), alongside the existing OpenClaw path.
- Added `wordpress-api-pro/requirements.txt` (`requests`) — needed only by the ACF / SEO / JetEngine / plugin-detection scripts; the core scripts remain stdlib-only.
- Documented the Claude Code workflow in `README.md` and `SKILL.md`, including local-dev sites and pairing with the Elementor MCP kit.
- Packaging: shipped `INSTALL.sh` + `requirements.txt`, bumped version to `3.5.0`.

## 3.4.0 - 2026-05-05

Security and packaging cleanup for ClawHub publication.

- Moved the publishable skill into the internal `wordpress-api-pro/` directory.
- Added `scripts/security.py` with local file and remote URL safety boundaries.
- Restricted `update_post.py --content-file` to approved local roots.
- Restricted `upload_media.py` local reads to approved roots and made remote URL fetching explicit opt-in.
- Blocked HTTPS remote media URLs that resolve to private, loopback, link-local, multicast, reserved, or unspecified addresses.
- Made `batch_update.py` dry-run by default; live mutation now requires `--execute` and confirmation.
- Added `--allow-all` gate for targeting all configured sites.
- Added `--execute-group` / `--allow-all` gates to the multi-site wrapper.
- Removed admin-style credential examples and hardcoded-looking placeholders from docs/config examples.
- Updated metadata to include repository directory, homepage, and version `3.4.0`.

## 3.3.0 - 2026-05-01

- Previous ClawHub-published version.
- Included WordPress posts/pages/media/WooCommerce/Elementor helper scripts.

## Earlier versions

Earlier versions mixed packaging, documentation, and security changes. Use `git log` for detailed history.
