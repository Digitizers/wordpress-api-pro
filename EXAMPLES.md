# Usage Examples

## Setup

```bash
# 1. Copy config template
cp config/sites.example.json config/sites.json

# 2. Add your sites (edit config/sites.json)
{
  "sites": {
    "digitizer-studio": {
      "url": "https://www.digitizer.studio",
      "username": "benkalsky",
      "app_password": "xxxx xxxx xxxx xxxx xxxx xxxx"
    },
    "digitizer-hebrew": {
      "url": "https://www.digitizer.co.il",
      "username": "benkalsky",
      "app_password": "yyyy yyyy yyyy yyyy yyyy yyyy"
    }
  },
  "groups": {
    "digitizer": ["digitizer-studio", "digitizer-hebrew"],
    "all": ["digitizer-studio", "digitizer-hebrew"]
  }
}
```

## Single Site Operations

```bash
# Update a post
./wp digitizer-studio update-post \
  --id 123 \
  --title "New Title" \
  --content "Updated content" \
  --status "publish"

# Create a new post
./wp digitizer-studio create-post \
  --title "My New Post" \
  --content "<p>Post content here</p>" \
  --status "draft"

# Get post details
./wp digitizer-studio get-post --id 123

# List recent posts
./wp digitizer-studio list-posts --per-page 10 --status "publish"

# Update with content from file
./wp digitizer-studio update-post \
  --id 123 \
  --content-file "./content/article.html" \
  --status "publish"
```

## Multi-Site Operations

```bash
# Update same post on all Digitizer sites
./wp digitizer update-post \
  --id 456 \
  --status "publish"

# List sites
./wp --list-sites

# List groups
./wp --list-groups
```

## Batch Operations

```bash
# Publish multiple posts across all sites
python3 scripts/batch_update.py \
  --group all \
  --post-ids 123,456,789 \
  --status "publish"

# Update SEO score meta on specific sites
python3 scripts/batch_update.py \
  --sites "digitizer-studio,digitizer-hebrew" \
  --post-ids 100,200 \
  --meta-key "seo_score" \
  --meta-value "95"

# Dry run (preview changes)
python3 scripts/batch_update.py \
  --group all \
  --post-ids 123 \
  --status "draft" \
  --dry-run
```

## Advanced: Direct Script Usage

```bash
# Single site with environment variables
export WP_URL="https://example.com"
export WP_USERNAME="admin"
export WP_APP_PASSWORD="xxxx xxxx xxxx xxxx"

python3 scripts/update_post.py --id 123 --content "Updated"

# Or with command-line args
python3 scripts/update_post.py \
  --url "https://example.com" \
  --username "admin" \
  --app-password "xxxx xxxx xxxx" \
  --id 123 \
  --content "Updated content"
```

## Real-World Scenarios

### Scenario 1: Publish an article to multiple sites

```bash
# Content in file: article.html
./wp digitizer update-post \
  --id 123 \
  --content-file "article.html" \
  --status "publish"
```

### Scenario 2: Update meta across 50 sites

```bash
# Add all 50 sites to config
# Then:
python3 scripts/batch_update.py \
  --group all \
  --post-ids 100 \
  --meta-key "last_updated" \
  --meta-value "2026-03-02"
```

### Scenario 3: Migration - set all posts to draft

```bash
python3 scripts/batch_update.py \
  --sites "old-site" \
  --post-ids 1,2,3,4,5,6,7,8,9,10 \
  --status "draft" \
  --dry-run  # Check first

# If OK, run without --dry-run
python3 scripts/batch_update.py \
  --sites "old-site" \
  --post-ids 1,2,3,4,5,6,7,8,9,10 \
  --status "draft"
```

## Tips

- **Always test with --dry-run first** for batch operations
- **Use groups** to manage related sites (staging + production, brands, languages)
- **Store config outside git** - config/sites.json is in .gitignore
- **Backup before batch updates** - WordPress exports or database snapshots
- **Check credentials** - `./wp --list-sites` shows auth status (✓/✗)
