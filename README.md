# WordPress API Pro — OpenClaw Skill

[![CI](https://github.com/Digitizers/wordpress-api-pro/actions/workflows/ci.yml/badge.svg)](https://github.com/Digitizers/wordpress-api-pro/actions/workflows/ci.yml)

WordPress REST API integration skill for OpenClaw. Manage posts, pages, media, WooCommerce products, Elementor content, SEO metadata, ACF, JetEngine fields, and multi-site workflows programmatically — with explicit safety boundaries for agentic use.

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

Current version: **3.5.0**

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

Then restart Claude Code, export `WP_URL` / `WP_USERNAME` / `WP_APP_PASSWORD` (or set up `config/sites.json`), and ask Claude to use it. The ACF / SEO / JetEngine / plugin-detection scripts need `requests` (`pip install -r requirements.txt`); the core post/page/media/WooCommerce/batch scripts use the Python stdlib only.

> Pairs well with the [Elementor MCP kit](https://github.com/Digitizers/claude-elementor-pro): build pages with the MCP, then handle media uploads, SEO meta, custom fields, and WooCommerce with these scripts.

## Quick Start

### Option A: Multi-Site Setup — recommended for 2+ sites ⭐

**1. Copy config template:**

```bash
cd ~/.openclaw/workspace/skills/wordpress-api-pro
cp config/sites.example.json config/sites.json
chmod 600 config/sites.json
```

**2. Edit `config/sites.json`:**

```json
{
  "sites": {
    "client-main": {
      "url": "https://example.com",
      "username": "wp-api-user",
      "app_password": "",
      "description": "Primary client site"
    },
    "client-shop": {
      "url": "https://shop.example.com",
      "username": "wp-api-user",
      "app_password": "",
      "description": "WooCommerce shop"
    }
  },
  "groups": {
    "client": ["client-main", "client-shop"]
  }
}
```

Keep real credentials local only. Do not commit `config/sites.json`.

**3. Use the CLI wrapper:**

```bash
# List configured sites
./wp.sh --list-sites

# Read a post on a specific site
./wp.sh client-main get-post --id 123

# Update a post after approval
./wp.sh client-main update-post --id 123 --status draft

# Group operation requires explicit group execution flag
./wp.sh client --execute-group update-post --id 456 --status draft
```

### Option B: Single Site Setup

**1. Create an Application Password**

1. Open `https://your-site.example/wp-admin/profile.php`.
2. Scroll to **Application Passwords**.
3. Create a password for a dedicated API user.
4. Copy it once and store it in a secret manager or environment variable.

**2. Set environment variables**

```bash
export WP_URL="https://your-site.example"
export WP_USERNAME="wp-api-user"
read -rs WP_APP_PASSWORD
export WP_APP_PASSWORD
```

**3. Use the scripts**

```bash
cd wordpress-api-pro
```

**Update a post:**

```bash
python3 scripts/update_post.py \
  --post-id 123 \
  --title "New Title" \
  --content "Updated content" \
  --status draft
```

**Create a draft:**

```bash
python3 scripts/create_post.py \
  --title "My Post" \
  --content "Post content here" \
  --status draft
```

**Get a post:**

```bash
python3 scripts/get_post.py --post-id 123
```

**List posts:**

```bash
python3 scripts/list_posts.py --per-page 10 --status publish
```

## Batch Operations

Dry-run preview is the default:

```bash
cd wordpress-api-pro
python3 scripts/batch_update.py \
  --group client \
  --post-ids 123,456 \
  --status draft
```

Apply only after review:

```bash
cd wordpress-api-pro
python3 scripts/batch_update.py \
  --group client \
  --post-ids 123,456 \
  --status draft \
  --execute
```

## Scripts

### Core Scripts

| Script | Purpose |
|--------|---------|
| `update_post.py` | Update an existing post/page |
| `create_post.py` | Create a new post/page |
| `get_post.py` | Retrieve a single post/page |
| `list_posts.py` | List and filter posts/pages |
| `batch_update.py` | Dry-run-first batch updates across sites/groups |
| `wp_cli.py` | Multi-site command wrapper backend |
| `security.py` | Local file and remote URL safety helpers |

### Plugin & Commerce Scripts

| Script | Purpose |
|--------|---------|
| `detect_plugins.py` | Auto-detect supported plugins — ACF, Rank Math, Yoast, JetEngine, WooCommerce |
| `acf_fields.py` | Read/write Advanced Custom Fields |
| `seo_meta.py` | Read/write Rank Math and Yoast SEO meta |
| `jetengine_fields.py` | Read/write JetEngine custom fields |
| `elementor_content.py` | Read/update Elementor page content |
| `upload_media.py` | Upload local or explicitly approved remote media |
| `woo_products.py` | Manage WooCommerce products |

## Examples

**Detect supported plugins:**

```bash
python3 scripts/detect_plugins.py
```

**Get ACF fields:**

```bash
python3 scripts/acf_fields.py --post-id 123
```

**Set SEO meta:**

```bash
python3 scripts/seo_meta.py \
  --post-id 123 \
  --set '{"title":"SEO Title","description":"Meta description"}'
```

**Update JetEngine field:**

```bash
python3 scripts/jetengine_fields.py \
  --post-id 123 \
  --field my_field \
  --value "New value"
```

**Elementor content:**

```bash
python3 scripts/elementor_content.py get \
  --post-id 123 \
  --widget-id some_widget_id

python3 scripts/elementor_content.py update \
  --post-id 123 \
  --widget-id some_widget_id \
  --field title \
  --value "New Title"
```

**Media upload:**

```bash
python3 scripts/upload_media.py \
  --file ./media/image.jpg \
  --title "My Image" \
  --caption "A beautiful image"
```

Remote media requires explicit opt-in:

```bash
python3 scripts/upload_media.py \
  --file https://cdn.example.com/image.png \
  --allow-remote-url \
  --set-featured \
  --post-id 123
```

**WooCommerce products:**

```bash
python3 scripts/woo_products.py list --status publish
python3 scripts/woo_products.py get --id 456
python3 scripts/woo_products.py create --name "New Product" --type simple --regular-price 29.99
python3 scripts/woo_products.py update --id 456 --description "Updated product description"
```

## Safety Model

- ✅ Use Application Passwords, not regular account passwords.
- ✅ Prefer a dedicated least-privilege WordPress API user.
- ✅ Always use HTTPS for production sites.
- ✅ Store credentials in environment variables or local untracked config.
- ✅ Keep `config/sites.json` local, untracked, and `chmod 600`.
- ✅ Review dry-runs before live batch updates.
- ❌ Never commit credentials to git.
- ❌ Never publish or update live content without explicit approval.

## Publishing to ClawHub

Releases are published to ClawHub automatically via GitHub Actions ([`.github/workflows/publish-clawhub.yml`](.github/workflows/publish-clawhub.yml)).

**One-time setup:** add a repository secret named `CLAWHUB_TOKEN` (Settings → Secrets and variables → Actions). Get the token from `clawhub login` locally or your ClawHub account.

**Release flow:**
1. Bump the `version:` in `wordpress-api-pro/SKILL.md` (the source of truth ClawHub displays) and add a `CHANGELOG.md` entry.
2. Publish a GitHub Release → the workflow installs the `clawhub` CLI, authenticates with `CLAWHUB_TOKEN`, and runs `clawhub skill publish wordpress-api-pro --version <version>`.

Trigger it manually from the Actions tab (workflow_dispatch) with **dry-run on** to preview the publish plan without uploading.

## Documentation

- **`wordpress-api-pro/SKILL.md`** — full skill instructions for OpenClaw agents.
- **`wordpress-api-pro/references/api-reference.md`** — WordPress REST API reference.
- **`wordpress-api-pro/references/gutenberg-blocks.md`** — Gutenberg block format guide.

## Requirements

- Python 3.8+
- WordPress 5.6+ recommended for built-in Application Passwords
- `requests` for plugin integration scripts: `pip install requests`

## Use Cases

- Publishing and drafting blog posts.
- Content migration between WordPress sites.
- Batch updates across many posts or client sites.
- Automated content workflows with approval gates.
- WooCommerce product maintenance.
- Elementor landing page updates.
- SEO metadata operations.
- Agency multi-site operations.
- Integration with OpenClaw / agentic workflows.

## Links

- **Repository:** https://github.com/Digitizers/wordpress-api-pro
- **ClawHub:** https://clawhub.ai/benkalsky/wordpress-api-pro
- **OpenClaw:** https://openclaw.ai
- **WordPress REST API:** https://developer.wordpress.org/rest-api/
- **Digitizer:** https://www.digitizer.studio

## License

MIT-0 — see [LICENSE.txt](LICENSE.txt)

---

Built with ❤️ for OpenClaw by [Digitizer](https://www.digitizer.studio)
