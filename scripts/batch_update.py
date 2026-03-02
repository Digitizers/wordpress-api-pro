#!/usr/bin/env python3
"""
Batch update posts across multiple sites

Usage:
    # Update meta on all sites
    batch_update.py --sites all --meta-key "seo_score" --meta-value "95"
    
    # Update status on specific group
    batch_update.py --group digitizer --status "publish" --post-ids 123,456,789
    
    # Dry run
    batch_update.py --sites all --status "draft" --dry-run
"""

import argparse
import json
import os
import sys
from pathlib import Path
import urllib.request
import urllib.error
from base64 import b64encode

def load_config(config_path=None):
    """Load sites configuration"""
    if config_path is None:
        script_dir = Path(__file__).parent
        config_path = script_dir.parent / 'config' / 'sites.json'
    
    config_path = Path(config_path)
    
    if not config_path.exists():
        print(f"Error: Config not found: {config_path}", file=sys.stderr)
        sys.exit(1)
    
    with open(config_path, 'r') as f:
        return json.load(f)

def update_post(site, post_id, updates, dry_run=False):
    """Update a post on a site"""
    api_url = f"{site['url'].rstrip('/')}/wp-json/wp/v2/posts/{post_id}"
    
    if dry_run:
        print(f"  [DRY RUN] Would update post {post_id}: {updates}")
        return True
    
    credentials = f"{site['username']}:{site['app_password']}".encode('utf-8')
    auth_header = b64encode(credentials).decode('ascii')
    
    request = urllib.request.Request(
        api_url,
        data=json.dumps(updates).encode('utf-8'),
        method='POST'
    )
    request.add_header('Authorization', f'Basic {auth_header}')
    request.add_header('Content-Type', 'application/json')
    
    try:
        with urllib.request.urlopen(request) as response:
            result = json.loads(response.read().decode('utf-8'))
            print(f"  ✓ Updated post {post_id}")
            return True
    except urllib.error.HTTPError as e:
        error = e.read().decode('utf-8')
        print(f"  ✗ Failed to update post {post_id}: {error}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"  ✗ Error updating post {post_id}: {e}", file=sys.stderr)
        return False

def main():
    parser = argparse.ArgumentParser(description='Batch update WordPress posts')
    parser.add_argument('--sites', help='Site names (comma-separated) or "all"')
    parser.add_argument('--group', help='Group name from config')
    parser.add_argument('--post-ids', help='Post IDs to update (comma-separated)')
    parser.add_argument('--status', choices=['publish', 'draft', 'pending', 'private'])
    parser.add_argument('--meta-key', help='Meta key to update')
    parser.add_argument('--meta-value', help='Meta value to set')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done')
    parser.add_argument('--config', default=os.getenv('WP_CONFIG'))
    
    args = parser.parse_args()
    
    # Load config
    config = load_config(args.config)
    
    # Determine sites to update
    site_names = []
    if args.sites:
        if args.sites == 'all':
            site_names = list(config['sites'].keys())
        else:
            site_names = [s.strip() for s in args.sites.split(',')]
    elif args.group:
        if args.group not in config.get('groups', {}):
            print(f"Error: Group '{args.group}' not found", file=sys.stderr)
            sys.exit(1)
        site_names = config['groups'][args.group]
    else:
        print("Error: Specify --sites or --group", file=sys.stderr)
        sys.exit(1)
    
    # Parse post IDs
    if not args.post_ids:
        print("Error: --post-ids required", file=sys.stderr)
        sys.exit(1)
    
    post_ids = [int(pid.strip()) for pid in args.post_ids.split(',')]
    
    # Build updates
    updates = {}
    if args.status:
        updates['status'] = args.status
    if args.meta_key and args.meta_value:
        updates['meta'] = {args.meta_key: args.meta_value}
    
    if not updates:
        print("Error: No updates specified (--status, --meta-key + --meta-value)", file=sys.stderr)
        sys.exit(1)
    
    # Execute
    print(f"Batch update: {len(site_names)} sites, {len(post_ids)} posts")
    print(f"Updates: {updates}")
    if args.dry_run:
        print("[DRY RUN MODE]")
    print()
    
    total_success = 0
    total_failed = 0
    
    for site_name in site_names:
        if site_name not in config['sites']:
            print(f"Warning: Site '{site_name}' not found in config", file=sys.stderr)
            continue
        
        site = config['sites'][site_name]
        print(f"{site_name} ({site['url']}):")
        
        for post_id in post_ids:
            if update_post(site, post_id, updates, args.dry_run):
                total_success += 1
            else:
                total_failed += 1
        
        print()
    
    print(f"Summary: {total_success} successful, {total_failed} failed")

if __name__ == '__main__':
    main()
