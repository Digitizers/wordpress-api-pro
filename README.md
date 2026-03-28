# WordPress API Pro - OpenClaw Skill

WordPress REST API integration skill for OpenClaw. Manage posts, pages, media, and more programmatically.

## Features

- ✅ **Elementor Content** - Read and update Elementor page content via _elementor_data meta field
- ✅ **Media Upload** - Upload images to WordPress media library
- ✅ **WooCommerce Products** - Manage WooCommerce products
- ✅ **Full CRUD** - Create, read, update, delete posts/pages
- ✅ **Gutenberg Support** - Native block format
- ✅ **Secure Auth** - Application Passwords (recommended)
- ✅ **Media Management** - Upload and manage media files
- ✅ **Batch Operations** - List, filter, and bulk actions
- ✅ **Plugin Support** - ACF, JetEngine, Rank Math, Yoast SEO
- ✅ **Minimal Dependencies** - Core scripts use stdlib, plugin scripts use requests

## Installation

### Via ClawHub (Recommended)

```bash
clawhub install wordpress-api-pro
```

### Manual Installation

```bash
cd ~/.openclaw/workspace/skills/
git clone https://github.com/Digitizers/wordpress-api-pro wordpress-api-pro
```

## Quick Start

### Option A: Multi-Site Setup (Recommended for 2+ sites) ⭐

**1. Copy config template:**
```bash
cd ~/.openclaw/workspace/skills/wordpress-api-pro
cp config/sites.example.json config/sites.json
```

**2. Edit config/sites.json:**
```json
{
  "sites": {
    "site1": {
      "url": "https://site1.com",
      "username": "admin",
      "app_password": "xxxx xxxx xxxx",
      "description": "First site"
    },
    "site2": {
      "url": "https://site2.com",
      "username": "admin",
      "app_password": "yyyy yyyy yyyy",
      "description": "Second site"
    }
  },
  "groups": {
    "all": ["site1", "site2"]
  }
}
```

**3. Use the CLI wrapper:**
```bash
# List sites
./wp.sh --list-sites

# Update post on specific site
./wp.sh site1 update-post --id 123 --content "New content"

# Update on all sites
./wp.sh all update-post --id 456 --status "publish"

# Batch update
python3 scripts/batch_update.py --group all --post-ids 123,456 --status "publish"
```

### Option B: Single Site Setup

### 1. Create Application Password

1. Go to: `https://yoursite.com/wp-admin/profile.php`
2. Scroll to "Application Passwords"
3. Name: "OpenClaw API"
4. Click "Add New Application Password"
5. Copy the password

### 2. Set Environment Variables

```bash
export WP_URL="https://yoursite.com"
export WP_USERNAME="your-username"
export WP_APP_PASSWORD="xxxx xxxx xxxx xxxx xxxx xxxx"
```

### 3. Use the Skill

**Update a post:**
```bash
python3 ~/.openclaw/workspace/skills/wordpress-api-pro/scripts/update_post.py \
  --post-id 123 \
  --title "New Title" \
  --content "Updated content" \
  --status "publish"
```

**Create a post:**
```bash
python3 scripts/create_post.py \
  --title "My Post" \
  --content "Post content here" \
  --status "draft"
```

**Get a post:**
```bash
python3 scripts/get_post.py --post-id 123
```

**List posts:**
```bash
python3 scripts/list_posts.py --per-page 10 --status "publish"
```

## Scripts

### Core Scripts
| Script | Purpose |
|--------|---------|
| `update_post.py` | Update existing post |
| `create_post.py` | Create new post |
| `get_post.py` | Retrieve single post |
| `list_posts.py` | List/filter posts |

### Plugin Integration (New in v3.2.0)
| Script | Purpose |
|--------|---------|
| `detect_plugins.py` | Auto-detect installed plugins (ACF, Rank Math, Yoast, JetEngine) |
| `acf_fields.py` | Read/write Advanced Custom Fields |
| `seo_meta.py` | Read/write Rank Math & Yoast SEO meta |
| `jetengine_fields.py` | Read/write JetEngine custom fields |
| `elementor_content.py` | Read/update Elementor page content |
| `upload_media.py` | Upload images to WordPress media library |
| `woo_products.py` | Manage WooCommerce products |

**Examples:**
```bash
# Detect plugins
python3 scripts/detect_plugins.py

# Get ACF fields
python3 scripts/acf_fields.py --post-id 123

# Set SEO meta
python3 scripts/seo_meta.py --post-id 123 --set '{"title": "SEO Title", "description": "Meta desc"}'

# Update JetEngine field
python3 scripts/jetengine_fields.py --post-id 123 --field my_field --value "value"

# Elementor Content
python3 scripts/elementor_content.py get --post-id 123 --widget-id some_widget_id
python3 scripts/elementor_content.py update --post-id 123 --widget-id some_widget_id --field 'title' --value 'New Title'

# Media Upload
python3 scripts/upload_media.py --file-path /path/to/image.jpg --title "My Image" --caption "A beautiful image"
python3 scripts/upload_media.py --url https://example.com/image.png --set-featured --post-id 123

# WooCommerce Products
python3 scripts/woo_products.py list --status 'publish'
python3 scripts/woo_products.py get --id 456
python3 scripts/woo_products.py create --name "New Product" --type 'simple' --regular-price '29.99'
python3 scripts/woo_products.py update --id 456 --description "Updated product description"
```

## Documentation

- **SKILL.md** - Full skill documentation
- **references/api-reference.md** - WordPress REST API reference
- **references/gutenberg-blocks.md** - Gutenberg block format guide

## Requirements

- Python 3.6+
- WordPress 4.7+ (REST API built-in)
- Application Passwords (WordPress 5.6+ or plugin for older versions)
- `requests` library (for plugin integration scripts): `pip install requests`

## Security

- ✅ Use Application Passwords (not regular passwords)
- ✅ Always use HTTPS
- ✅ Store credentials in environment variables
- ❌ Never commit credentials to git

## Use Cases

- Publishing blog posts
- Content migration
- Batch updates
- Automated publishing
- Content management workflows
- Integration with other systems

## License

MIT License - See [LICENSE.txt](LICENSE.txt)

## Links

- **OpenClaw:** https://openclaw.ai
- **ClawHub:** https://clawhub.com
- **WordPress REST API:** https://developer.wordpress.org/rest-api/

---

Built with ❤️ for OpenClaw by [Digitizer](https://www.digitizer.studio)
