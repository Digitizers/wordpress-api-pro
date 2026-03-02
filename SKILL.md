---
name: wordpress-api
description: |
  WordPress REST API integration for managing posts, pages, media, and more on self-hosted WordPress sites.
  Use when you need to create, update, or retrieve WordPress content programmatically.
  Supports Gutenberg blocks, custom fields, featured images, and full CRUD operations.
  Works with any WordPress site (self-hosted or managed) that has REST API enabled (WordPress 4.7+).
  Authentication via Application Password (recommended) or Basic Auth.
  Use for publishing articles, updating content, managing media, batch operations, content migration, or any WordPress admin task via API.
---

# WordPress API

Interact with WordPress sites via the REST API. Create, update, and manage posts, pages, media, and more on any WordPress installation.

## Quick Start

### Single Site (Direct)

```bash
# Update a post
python3 scripts/update_post.py \
  --url "https://example.com" \
  --username "admin" \
  --app-password "xxxx xxxx xxxx xxxx" \
  --post-id 123 \
  --content "New content here" \
  --status "publish"
```

### Multi-Site (CLI Wrapper) ⭐

```bash
# Setup: Copy config template and add your sites
cp config/sites.example.json config/sites.json
# Edit config/sites.json with your sites

# List configured sites
./wp.sh --list-sites

# Update post on specific site
./wp.sh digitizer-studio update-post --id 123 --content "New content"

# Run on all sites in a group
./wp.sh digitizer update-post --id 456 --status "publish"

# Batch update across multiple sites
python3 scripts/batch_update.py --group digitizer --post-ids 123,456 --status "publish"
```

## Authentication

WordPress REST API supports two authentication methods:

### 1. Application Password (Recommended) ⭐

**Setup:**
1. Go to: `https://yoursite.com/wp-admin/profile.php`
2. Scroll to "Application Passwords"
3. Name: "OpenClaw API" (or any name)
4. Click "Add New Application Password"
5. Copy the password (shows only once!)

**Format:** `xxxx xxxx xxxx xxxx xxxx xxxx` (24 characters with spaces)

**Usage:** Pass as `--app-password` to scripts or set `WP_APP_PASSWORD` environment variable

### 2. Basic Auth (Legacy)

Requires Basic Auth plugin. Less secure, not recommended for production.

## Environment Variables

Set these to avoid passing credentials every time:

```bash
export WP_URL="https://example.com"
export WP_USERNAME="admin"
export WP_APP_PASSWORD="xxxx xxxx xxxx xxxx xxxx xxxx"
```

## Multi-Site Management

### Configuration

1. Copy the example config:
```bash
cp config/sites.example.json config/sites.json
```

2. Edit `config/sites.json` with your sites:
```json
{
  "sites": {
    "my-site": {
      "url": "https://mysite.com",
      "username": "admin",
      "app_password": "xxxx xxxx xxxx",
      "description": "My WordPress site"
    }
  },
  "groups": {
    "all": ["my-site"]
  }
}
```

### CLI Wrapper (`./wp.sh`)

```bash
# List sites
./wp.sh --list-sites
./wp.sh --list-groups

# Single site operations
./wp.sh my-site update-post --id 123 --content "..."
./wp.sh my-site create-post --title "..." --content "..."
./wp.sh my-site get-post --id 123
./wp.sh my-site list-posts --per-page 10

# Group operations (runs on all sites in group)
./wp.sh all update-post --id 123 --status "publish"
```

### Batch Operations

```bash
# Update multiple posts across multiple sites
python3 scripts/batch_update.py \
  --group digitizer \
  --post-ids 123,456,789 \
  --status "publish"

# Update meta field on all sites
python3 scripts/batch_update.py \
  --sites all \
  --post-ids 100 \
  --meta-key "seo_score" \
  --meta-value "95"

# Dry run (see what would happen)
python3 scripts/batch_update.py \
  --group all \
  --post-ids 123 \
  --status "draft" \
  --dry-run
```

## Individual Scripts

All scripts support both command-line arguments and environment variables.

### Update Post

```bash
python3 scripts/update_post.py \
  --post-id 123 \
  --content "Updated content" \
  --title "New Title" \
  --status "publish"
```

**Supports:**
- Content (HTML or Gutenberg blocks)
- Title
- Status (publish, draft, pending, private)
- Featured image ID
- Custom fields (meta)

### Create Post

```bash
python3 scripts/create_post.py \
  --title "New Post" \
  --content "Post content" \
  --status "draft"
```

### Get Post

```bash
python3 scripts/get_post.py --post-id 123
```

Returns full post data as JSON.

### List Posts

```bash
python3 scripts/list_posts.py --per-page 10 --status "publish"
```

**Options:**
- `--per-page N` - Posts per page (default: 10, max: 100)
- `--page N` - Page number
- `--status STATUS` - Filter by status (publish, draft, pending, private)
- `--author ID` - Filter by author

## Gutenberg Blocks

WordPress uses Gutenberg block format for content. See [references/gutenberg-blocks.md](references/gutenberg-blocks.md) for details.

**Example block:**
```html
<!-- wp:paragraph -->
<p>This is a paragraph.</p>
<!-- /wp:paragraph -->
```

## API Reference

See [references/api-reference.md](references/api-reference.md) for complete WordPress REST API documentation.

**Common endpoints:**
- `/wp-json/wp/v2/posts` - Posts
- `/wp-json/wp/v2/pages` - Pages
- `/wp-json/wp/v2/media` - Media
- `/wp-json/wp/v2/users` - Users
- `/wp-json/wp/v2/categories` - Categories
- `/wp-json/wp/v2/tags` - Tags

## Error Handling

All scripts return:
- Exit code 0 on success
- Exit code 1 on error
- JSON output to stdout
- Error messages to stderr

## Security

- ✅ **DO:** Use Application Passwords
- ✅ **DO:** Use HTTPS only
- ✅ **DO:** Store credentials in environment variables
- ❌ **DON'T:** Hardcode passwords in scripts
- ❌ **DON'T:** Use Basic Auth in production
- ❌ **DON'T:** Commit credentials to git

## Limitations

- Requires WordPress 4.7+ (REST API built-in)
- Requires Application Passwords plugin for WordPress <5.6
- Some endpoints require specific user permissions
- Rate limiting depends on host configuration
