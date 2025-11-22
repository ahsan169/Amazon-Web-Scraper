#!/usr/bin/env python3
# run_scraper.py - Amazon Scraper Runner Script

import os
import sys
import subprocess
import argparse
from datetime import datetime
import config

def main():
    parser = argparse.ArgumentParser(description='Run Amazon UK Product Scraper')
    
    # Add command line arguments
    parser.add_argument('--keywords', '-k', type=str, 
                       help='Comma-separated list of keywords to scrape')
    parser.add_argument('--pages', '-p', type=int, default=config.MAX_PAGES_PER_KEYWORD,
                       help='Number of pages to scrape per keyword')
    parser.add_argument('--output', '-o', type=str, default='csv',
                       choices=['csv', 'json', 'both'],
                       help='Output format (csv, json, or both)')
    parser.add_argument('--delay', '-d', type=int, default=config.DELAY_BETWEEN_REQUESTS,
                       help='Delay between requests in seconds')
    parser.add_argument('--concurrent', '-c', type=int, default=config.CONCURRENT_REQUESTS,
                       help='Number of concurrent requests')
    parser.add_argument('--log-level', '-l', type=str, default='INFO',
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       help='Log level')
    parser.add_argument('--use-cache', action='store_true',
                       help='Enable caching')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be scraped without running')
    parser.add_argument('--domain', '-dm', type=str, default=config.DEFAULT_DOMAIN,
                   choices=list(config.AMAZON_DOMAINS.keys()),
                   help='Amazon domain to scrape (us, uk, de, fr, etc.)')
    
    args = parser.parse_args()
    
    # Prepare keywords
    if args.keywords:
        keywords = args.keywords
    else:
        keywords = ','.join(config.KEYWORDS)
    
    # Show dry run information
    if args.dry_run:
        print("=== Amazon Scraper Dry Run ===")
        print(f"Keywords: {keywords}")
        print(f"Pages per keyword: {args.pages}")
        print(f"Output format: {args.output}")
        print(f"Delay between requests: {args.delay}s")
        print(f"Concurrent requests: {args.concurrent}")
        print(f"Log level: {args.log_level}")
        print(f"Estimated products: {len(keywords.split(',')) * args.pages * 16}")
        print("\nRun without --dry-run to start scraping")
        return
    
    # Prepare output filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Prepare scrapy command
    cmd = [
        'scrapy', 'crawl', 'amazon_spider',
        '-a', f'keywords={keywords}',
        '-a', f'max_pages={args.pages}',
        '-s', f'DOWNLOAD_DELAY={args.delay}',
        '-s', f'CONCURRENT_REQUESTS={args.concurrent}',
        '-s', f'LOG_LEVEL={args.log_level}',
    ]
    
    # Add caching if enabled
    if args.use_cache:
        cmd.extend(['-s', 'HTTPCACHE_ENABLED=True'])
    
    # Configure output
    if args.output in ['csv', 'both']:
        cmd.extend(['-o', f'amazon_products_{timestamp}.csv'])
    
    if args.output in ['json', 'both']:
        cmd.extend(['-o', f'amazon_products_{timestamp}.json'])

    if args.domain:
        cmd.extend(['-a', f'domain={args.domain}'])

    
    # Print run information
    print("=== Starting Amazon Scraper ===")
    print(f"Keywords: {keywords}")
    print(f"Pages per keyword: {args.pages}")
    print(f"Output format: {args.output}")
    print(f"Timestamp: {timestamp}")
    print("=" * 40)
    
    # Change to the scrapy project directory
    scrapy_dir = os.path.join(os.getcwd(), 'amazon_scraper')
    if os.path.exists(scrapy_dir):
        os.chdir(scrapy_dir)
    
    # Run the scraper
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        print("\n=== Scraping Completed Successfully ===")
        print(f"Output files created with timestamp: {timestamp}")
        
    except subprocess.CalledProcessError as e:
        print(f"\n=== Scraping Failed ===")
        print(f"Error: {e}")
        sys.exit(1)
    
    except KeyboardInterrupt:
        print("\n=== Scraping Interrupted ===")
        print("Scraping was interrupted by user")
        sys.exit(1)


def setup_project():
    """Set up the Scrapy project if it doesn't exist"""
    if not os.path.exists('amazon_scraper'):
        print("Creating Scrapy project...")
        subprocess.run(['scrapy', 'startproject', 'amazon_scraper'], check=True)
        print("Project created successfully!")
    else:
        print("Scrapy project already exists.")


def check_dependencies():
    """Check if required dependencies are installed"""
    required_packages = ['scrapy', 'requests', 'beautifulsoup4', 'lxml']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"Missing required packages: {', '.join(missing_packages)}")
        print("Please install them using: pip install -r requirements.txt")
        return False
    
    return True


if __name__ == '__main__':
    print("Amazon UK Product Scraper")
    print("=" * 40)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Set up project if needed
    if len(sys.argv) > 1 and sys.argv[1] == 'setup':
        setup_project()
        sys.exit(0)
    
    # Run the scraper
    main()