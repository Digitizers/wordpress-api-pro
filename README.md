# WordPress API Pro — Claude Code & OpenClaw Skill

[![CI](https://github.com/Digitizers/wordpress-api-pro/actions/workflows/ci.yml/badge.svg)](https://github.com/Digitizers/wordpress-api-pro/actions/workflows/ci.yml)
![Claude Code Skill](https://img.shields.io/badge/Claude_Code-Skill-d97757)
![OpenClaw Skill](https://img.shields.io/badge/OpenClaw-Skill-purple)
![WordPress](https://img.shields.io/badge/WordPress-REST_API-21759b)
![License: MIT--0](https://img.shields.io/badge/License-MIT--0-green)
![Version](https://img.shields.io/badge/version-3.8.2-blue)

A production-grade **Claude Code & OpenClaw skill** for managing WordPress content via the REST API — posts, pages, media, WooCommerce, Elementor, SEO meta, ACF, JetEngine — with explicit safety boundaries for agentic use.

This is not just a tool reference. It is an operational playbook for managing WordPress content responsibly: posts, pages, media, WooCommerce products, Elementor content, SEO metadata, and custom fields — with drafts-first, dry-run, and explicit-approval guardrails on every write.

## Part of the Aura Design Engine

These are the free skills behind [**Aura**](https://my-aura.app) — one AI web-agency lifecycle you can run standalone or orchestrate across a whole client fleet from a single dashboard.

| Stage | Skill | Role |
| --- | --- | --- |
| 🎨 Build | [siteagent-elementor-studio](https://github.com/Digitizers/siteagent-elementor-studio) | Design & build sites inside Elementor |
| 🔎 Audit + Content | [**wordpress-api-pro** ← you are here](https://github.com/Digitizers/wordpress-api-pro) | REST content ops, SEO & site audits |
| 🖥 Host | [cloudways-mcp](https://github.com/Digitizers/cloudways-mcp) · [hostinger-mcp](https://github.com/Digitizers/hostinger-mcp) | Provision & operate the infrastructure |

**→ Orchestrate all of it across your client fleet with [Aura](https://my-aura.app)** — governed agent ops with approvals and a full audit trail on top of these skills.

## Seeding, or Aura content ops

This skill can **seed** content over the WordPress REST API — bulk-create posts, pages, and custom-post-type entries from a JSON dataset. It's the operator-side twin of Aura's content tools; which one to use comes down to who owns the site:

- **This skill (seeding)** — for sites you own or throwaway/staging sites: bulk scaffolding, demos, one-shot imports. Note: seeding is **not idempotent** — there's no upsert, so re-running the same seed duplicates content. Track what you've created.
- **Aura content ops** — for **managed client sites**, drive content through [Aura](https://my-aura.app) instead. Aura is the system-of-record: drafts-first and explicit-approval guardrails, a full audit trail, and content state it can reconcile. Seeding a managed site directly forks its content state out from under Aura.

Rule of thumb: seed sites you own; let Aura own content on sites you manage for others.

## Features

- ✅ **Elementor Content** — read and update Elementor page content via `_elementor_data`.
- ✅ **Media Upload** — upload images/files to the WordPress media library.
- ✅ **WooCommerce Products** — list, create, read, and update WooCommerce products.
- ✅ **Full CRUD** — create, read, update, and delete posts/pages.
- ✅ **Gutenberg Support** — native block format and content workflows.
- ✅ **Secure Auth** — WordPress Application Passwords recommended.
- ✅ **Media Management** — local media upload plus explicit opt-in remote HTTPS media.
- ✅ **Batch Operations** — list, filter, dry-run, and bulk update content.
- ✅ **Multi-Site Workflows** — manage named sites and site groups with `wp.sh`.
- ✅ **Plugin Support** — ACF, JetEngine, Rank Math, and Yoast SEO helpers.
- ✅ **Safety Gates** — dry-run defaults, explicit live-write flags, protected local file reads, and private-network URL blocking.
- ✅ **CI Verified** — tested on Python 3.11, 3.12, and 3.13.

## Package Layout

The actual skill payload lives in:

```text
wordpress-api-pro/
```

Repository-only files such as this README, changelog, license, CI, and package metadata intentionally stay outside the skill directory.

ClawHub package directory: `wordpress-api-pro/`.

## Version

Current version: **3.8.2**

## Installation

### Via OpenClaw / ClawHub

```bash
openclaw skills install wordpress-api-pro
```

### Manual Installation

```bash
cp -R wordpress-api-pro ~/.openclaw/workspace/skills/wordpress-api-pro
```

### Via Claude Code

The skill also runs in [Claude Code](https://claude.ai/download). The installer copies the payload into `~/.claude/skills/` so Claude Code discovers it automatically:

```bash
git clone https://github.com/Digitizers/wordpress-api-pro.git
cd wordpress-api-pro
bash INSTALL.sh
```

### Windows note

The plugin ships its skill through a git **symlink** (`skills/` → the in-repo
source). On Windows, enable Developer Mode and set
`git config --global core.symlinks true` **before** cloning or installing —
the plugin cache clone inherits it. Changing the config does not repair an
existing checkout (the repo may have recorded `core.symlinks=false` locally).
To repair one, run these two commands inside it (the second re-materializes
only the `skills/` entry, so nothing else in your working tree is touched):

    git config core.symlinks true
    git checkout -- skills/

Or simply re-clone. WSL also works. macOS/Linux need nothing.
