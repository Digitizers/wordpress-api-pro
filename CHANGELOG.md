# Changelog

## [2.0.1] - 2026-03-02

### Changed
- Renamed slug from `wordpress-api-skill` to `wordpress-api` (cleaner, follows package manager conventions)
- Updated all documentation to use shorter slug
- Updated GitHub repository URL

## [2.0.0] - 2026-03-02

### Added
- **Multi-site management system**
  - `config/sites.json` - Centralized site configuration
  - `./wp` CLI wrapper - Easy site switching
  - `scripts/wp_cli.py` - Multi-site command router
  - `scripts/batch_update.py` - Batch operations across sites
  - Site groups (e.g., "all", "digitizer")
  - Dry-run mode for safe testing
- `EXAMPLES.md` - Comprehensive usage examples
- `CHANGELOG.md` - This file

### Changed
- Updated `SKILL.md` with multi-site documentation
- Updated `README.md` with multi-site quick start
- Updated `.gitignore` to exclude `config/sites.json`

### Security
- Config file with credentials excluded from git by default
- Template file (`sites.example.json`) provided instead

## [1.0.0] - 2026-03-02

### Added
- Initial release
- WordPress REST API integration
- 4 core scripts:
  - `update_post.py` - Update existing posts
  - `create_post.py` - Create new posts
  - `get_post.py` - Retrieve post data
  - `list_posts.py` - List and filter posts
- Gutenberg block format support
- Application Password authentication
- Reference documentation:
  - `references/api-reference.md`
  - `references/gutenberg-blocks.md`
- `SKILL.md` - Skill definition
- `README.md` - GitHub documentation
- `LICENSE` - MIT License
- `package.json` - ClawHub metadata
- `.gitignore` - Security rules
