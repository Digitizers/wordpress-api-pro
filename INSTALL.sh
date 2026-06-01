#!/usr/bin/env bash
# =============================================================================
# WordPress API Pro — Claude Code Installer (Mac / Linux)
#
# Copies the skill payload into ~/.claude/skills/wordpress-api-pro/ so Claude
# Code discovers it automatically. The same payload also works as an OpenClaw
# skill (see README) — this installer only wires up the Claude Code path.
#
# Safe to re-run (asks before overwriting an existing install).
# =============================================================================

set -euo pipefail

BOLD=$'\033[1m'; GREEN=$'\033[32m'; CYAN=$'\033[36m'; YELLOW=$'\033[33m'
RED=$'\033[31m'; DIM=$'\033[2m'; RESET=$'\033[0m'

ok()   { printf "  ${GREEN}✓${RESET} %s\n" "$*"; }
warn() { printf "  ${YELLOW}⚠${RESET} %s\n" "$*"; }
fail() { printf "  ${RED}✗${RESET} %s\n" "$*"; }
step() { printf "\n${BOLD}${CYAN}▸ %s${RESET}\n" "$*"; }

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="$HERE/wordpress-api-pro"

[ -d "$SRC" ] || { fail "Cannot find $SRC — run this from the repo root."; exit 1; }
[ -f "$SRC/SKILL.md" ] || { fail "Missing SKILL.md in $SRC."; exit 1; }

cat <<'BANNER'

  ╭───────────────────────────────────────────────╮
  │   WordPress API Pro — Claude Code Installer   │
  │   ─────────────────────────────────────       │
  │   Installs the skill into ~/.claude/skills/   │
  │   so Claude Code can find and run it.         │
  ╰───────────────────────────────────────────────╯

BANNER

DEST="$HOME/.claude/skills/wordpress-api-pro"

step "Installing to $DEST"
if [ -d "$DEST" ]; then
  warn "An install already exists at $DEST"
  printf "    Overwrite? [y/N] "
  read -r ans
  if [[ ! "$ans" =~ ^[Yy]$ ]]; then
    warn "Left existing install untouched. Nothing changed."
    exit 0
  fi
  rm -rf "$DEST"
fi

mkdir -p "$DEST"
# Copy the payload contents (SKILL.md, scripts/, references/, config/, wp.sh,
# requirements.txt) to the skill root so relative `scripts/*.py` paths resolve.
cp -R "$SRC"/. "$DEST"/
chmod +x "$DEST/wp.sh" 2>/dev/null || true
ok "Installed skill payload"

step "Python dependency (optional)"
printf "  ${DIM}The ACF / SEO / JetEngine / plugin-detection scripts need 'requests'.\n  The core post/page/media/WooCommerce/batch scripts use the stdlib only.${RESET}\n"
if python3 -c "import requests" >/dev/null 2>&1; then
  ok "'requests' already available"
else
  warn "'requests' not installed. Install it when you need the plugin scripts:"
  printf "      ${CYAN}python3 -m pip install -r \"$DEST/requirements.txt\"${RESET}\n"
  printf "    ${DIM}(or use a venv: python3 -m venv .venv && .venv/bin/pip install -r requirements.txt)${RESET}\n"
fi

cat <<EOF

  ${BOLD}${GREEN}✓ Install complete${RESET}

  ${BOLD}Installed at:${RESET}
    ${DIM}$DEST/SKILL.md${RESET}

  ${BOLD}Next steps:${RESET}

    1. Restart Claude Code so it picks up the new skill.

    2. Provide credentials for the target site (one of):
       ${CYAN}export WP_URL="https://your-site.example"${RESET}
       ${CYAN}export WP_USERNAME="wp-api-user"${RESET}
       ${CYAN}export WP_APP_PASSWORD="xxxx xxxx xxxx xxxx xxxx xxxx"${RESET}
       ${DIM}— or set up config/sites.json for multi-site (see SKILL.md).${RESET}

    3. Ask Claude to use it, e.g.:
       ${DIM}"use wordpress-api-pro to list draft posts on my site"${RESET}
       ${DIM}"upload this image to the media library and set it as featured"${RESET}

  ${BOLD}Safety:${RESET} writes default to drafts / dry-run. Review before --execute.

EOF
