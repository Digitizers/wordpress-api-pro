#!/bin/bash
# Quick publish to ClawHub

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "📦 Publishing wordpress-api to ClawHub..."
echo ""

# Check if logged in
if ! clawhub whoami &>/dev/null; then
    echo "❌ Not logged in to ClawHub"
    echo "Run: clawhub login"
    exit 1
fi

echo "✓ Logged in to ClawHub"
echo ""

# Publish from current directory
clawhub publish "$SCRIPT_DIR" \
  --slug wordpress-api \
  --name "WordPress API" \
  --version 2.0.1 \
  --changelog "Multi-site management system with batch operations, site groups, and dry-run mode. Full CRUD support for WordPress REST API with Gutenberg blocks. Zero dependencies, pure Python stdlib."

echo ""
echo "✅ Published!"
echo "🔗 https://clawhub.com/skills/wordpress-api"
echo ""
echo "Users can install with:"
echo "  clawhub install wordpress-api"
