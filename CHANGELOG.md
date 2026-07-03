# Changelog

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
