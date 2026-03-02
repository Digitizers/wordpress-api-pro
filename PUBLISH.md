# Publishing to ClawHub

## Checklist Before Publishing

- [ ] SKILL.md has proper frontmatter (name, description)
- [ ] All scripts are executable (`chmod +x`)
- [ ] README.md is clear and complete
- [ ] EXAMPLES.md has real-world examples
- [ ] CHANGELOG.md is updated
- [ ] package.json version is correct
- [ ] .gitignore excludes sensitive files
- [ ] Tested on at least one WordPress site
- [ ] Git committed and clean working tree

## Step 1: Login to ClawHub

```bash
clawhub login
```

This opens a browser. Sign in with GitHub/Google/Email.

Verify:
```bash
clawhub whoami
```

## Step 2: Publish

```bash
cd ~/.openclaw/workspace

clawhub publish ./skills/wordpress-api \
  --slug wordpress-api \
  --name "WordPress API" \
  --version 2.0.0 \
  --changelog "Multi-site management system with batch operations, site groups, and dry-run mode. Full CRUD support for WordPress REST API with Gutenberg blocks."
```

### Version Guidelines

- **Major** (x.0.0): Breaking changes
- **Minor** (2.x.0): New features, backward compatible
- **Patch** (2.0.x): Bug fixes

Current version: **2.0.0** (first public release with multi-site)

## Step 3: Verify

After publishing, check:
- Skill page: https://clawhub.com/skills/wordpress-api
- Install test: `clawhub install wordpress-api --dir /tmp/test-skills`

## Future Updates

When you update the skill:

1. Make changes
2. Update CHANGELOG.md
3. Bump version in package.json
4. Git commit
5. Publish new version:

```bash
clawhub publish ./skills/wordpress-api \
  --slug wordpress-api \
  --name "WordPress API" \
  --version 2.1.0 \
  --changelog "Your changes here"
```

Users can update with:
```bash
clawhub update wordpress-api
```

## Unpublishing

To remove (rarely needed):
```bash
clawhub delete wordpress-api
```

Note: This soft-deletes. Contact ClawHub support for permanent removal.

## Tips

- **Clear changelog**: Users decide to update based on this
- **Semantic versioning**: Follow semver.org
- **Test before publish**: Install in a clean directory
- **Document breaking changes**: If any, bump major version
- **Link to GitHub**: Update package.json repository URL

## Support

- ClawHub docs: https://docs.clawhub.com
- Community: https://discord.com/invite/clawd
- Issues: File on GitHub repo
