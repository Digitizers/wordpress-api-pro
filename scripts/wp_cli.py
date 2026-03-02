#!/usr/bin/env python3
"""
WordPress CLI - Multi-site wrapper

Usage:
    wp_cli.py <site-name> update-post --id 123 --content "..."
    wp_cli.py <site-name> create-post --title "..." --content "..."
    wp_cli.py <site-name> get-post --id 123
    wp_cli.py <site-name> list-posts --per-page 10
    
    wp_cli.py --list-sites
    wp_cli.py --list-groups
    
Environment:
    WP_CONFIG - Path to sites config (default: config/sites.json)
"""

import argparse
import json
import os
import sys
from pathlib import Path

# Import our existing scripts
import subprocess

def load_config(config_path=None):
    """Load sites configuration"""
    if config_path is None:
        script_dir = Path(__file__).parent
        config_path = script_dir.parent / 'config' / 'sites.json'
    
    config_path = Path(config_path)
    
    if not config_path.exists():
        print(f"Error: Config file not found: {config_path}", file=sys.stderr)
        print("Copy config/sites.example.json to config/sites.json and fill in credentials", file=sys.stderr)
        sys.exit(1)
    
    with open(config_path, 'r') as f:
        return json.load(f)

def get_site_config(config, site_name):
    """Get configuration for a specific site"""
    if site_name not in config.get('sites', {}):
        # Check if it's a group
        if site_name in config.get('groups', {}):
            return 'group', config['groups'][site_name]
        
        print(f"Error: Site '{site_name}' not found in config", file=sys.stderr)
        print(f"Available sites: {', '.join(config.get('sites', {}).keys())}", file=sys.stderr)
        print(f"Available groups: {', '.join(config.get('groups', {}).keys())}", file=sys.stderr)
        sys.exit(1)
    
    return 'site', config['sites'][site_name]

def list_sites(config):
    """List all configured sites"""
    print("Configured sites:")
    for name, site in config.get('sites', {}).items():
        desc = site.get('description', '')
        has_pwd = '✓' if site.get('app_password') else '✗'
        print(f"  {name:20} {site['url']:40} {desc:30} [auth: {has_pwd}]")

def list_groups(config):
    """List all configured groups"""
    print("Configured groups:")
    for name, sites in config.get('groups', {}).items():
        print(f"  {name:20} → {', '.join(sites)}")

def run_command(site_config, command, args):
    """Run a WordPress command on a site"""
    script_dir = Path(__file__).parent
    
    # Map commands to scripts
    command_map = {
        'update-post': 'update_post.py',
        'create-post': 'create_post.py',
        'get-post': 'get_post.py',
        'list-posts': 'list_posts.py'
    }
    
    if command not in command_map:
        print(f"Error: Unknown command '{command}'", file=sys.stderr)
        print(f"Available: {', '.join(command_map.keys())}", file=sys.stderr)
        sys.exit(1)
    
    script_path = script_dir / command_map[command]
    
    # Build command args
    cmd = [
        'python3',
        str(script_path),
        '--url', site_config['url'],
        '--username', site_config['username'],
        '--app-password', site_config['app_password']
    ]
    
    # Add remaining args
    cmd.extend(args)
    
    # Run
    result = subprocess.run(cmd)
    return result.returncode

def main():
    parser = argparse.ArgumentParser(description='WordPress Multi-Site CLI')
    parser.add_argument('site', nargs='?', help='Site name or group')
    parser.add_argument('command', nargs='?', help='Command (update-post, create-post, get-post, list-posts)')
    parser.add_argument('--list-sites', action='store_true', help='List configured sites')
    parser.add_argument('--list-groups', action='store_true', help='List configured groups')
    parser.add_argument('--config', default=os.getenv('WP_CONFIG'), help='Config file path')
    
    # Parse known args, pass rest to underlying script
    args, remaining = parser.parse_known_args()
    
    # Load config
    config = load_config(args.config)
    
    # Handle list commands
    if args.list_sites:
        list_sites(config)
        return
    
    if args.list_groups:
        list_groups(config)
        return
    
    # Require site and command
    if not args.site or not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Get site config
    site_type, site_data = get_site_config(config, args.site)
    
    if site_type == 'group':
        # Run on all sites in group
        print(f"Running on group '{args.site}': {', '.join(site_data)}")
        for site_name in site_data:
            site_config = config['sites'][site_name]
            print(f"\n{'='*60}")
            print(f"Site: {site_name} ({site_config['url']})")
            print('='*60)
            run_command(site_config, args.command, remaining)
    else:
        # Run on single site
        run_command(site_data, args.command, remaining)

if __name__ == '__main__':
    main()
