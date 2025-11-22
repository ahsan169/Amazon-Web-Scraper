# Amazon Product Scraper - Complete Setup Guide

## Prerequisites

- Python 3.8 or higher
- pip package manager
- Internet connection
- ScrapeOps account (free tier available)

## Step 1: Initial Setup

### 1.1 Create Project Directory
```bash
mkdir amazon_scraper_project
cd amazon_scraper_project
```

### 1.2 Create Virtual Environment (Recommended)
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 1.3 Install Dependencies
```bash
pip install -r requirements.txt
```

## Step 2: ScrapeOps Setup

### 2.1 Create ScrapeOps Account
1. Go to [https://scrapeops.io/](https://scrapeops.io/)
2. Sign up for a free account
3. Verify your email
4. Login to your dashboard

### 2.2 Get API Key
1. In your ScrapeOps dashboard, go to **Settings** → **API Keys**
2. Copy your API key
3. Replace `YOUR_SCRAPEOPS_API_KEY_HERE` in `settings.py` with your actual API key

### 2.3 Configure ScrapeOps Features
The setup includes:
- **Fake User Agents**: Rotates user agents automatically
- **Fake Headers**: Adds realistic browser headers
- **Monitoring**: Tracks scraping statistics
- **Proxy Support**: (Optional) Premium feature for IP rotation

## Step 3: Create Scrapy Project

### 3.1 Create Project Structure
```bash
scrapy startproject amazon_scraper
cd amazon_scraper
```

### 3.2 Copy Files
Copy all the provided files to their respective locations:

```
amazon_scraper/
├── scrapy.cfg
├── amazon_scraper/
│   ├── __init__.py
│   ├── items.py          # Copy from artifacts
│   ├── middlewares.py    # Copy from artifacts
│   ├── pipelines.py      # Copy from artifacts
│   ├── settings.py       # Copy from artifacts
│   └── spiders/
│       ├── __init__.py
│       └── amazon_spider.py  # Copy from artifacts
├── config.py             # Copy from artifacts
├── run_scraper.py        # Copy from artifacts
└── requirements.txt      # Copy from artifacts
```

## Step 4: Configuration

### 4.1 Update Settings
Edit `amazon_scraper/settings.py`:

```python
# Replace with your actual ScrapeOps API key
SCRAPEOPS_API_KEY = 'your_actual_api_key_here'
```

### 4.2 Configure Keywords
Edit `config.py` to set your target keywords:

```python
KEYWORDS = [
    'wireless headphones',
    'laptop',
    'smartphone',
    # Add your keywords here
]
```

### 4.3 Adjust Scraping Parameters
In `config.py`, modify:
- `MAX_PAGES_PER_KEYWORD`: Number of pages to scrape per keyword
- `DELAY_BETWEEN_REQUESTS`: Delay between requests (seconds)
- `CONCURRENT_REQUESTS`: Number of concurrent requests

## Step 5: Running the Scraper

### 5.1 Basic Usage
```bash
# Navigate to project directory
cd amazon_scraper

# Run with default settings
python ../run_scraper.py

# Or use scrapy directly
scrapy crawl amazon_spider
```

### 5.2 Advanced Usage
```bash
# Custom keywords
python run_scraper.py --keywords "laptop,smartphone,headphones"

# Specify number of pages
python run_scraper.py --pages 10

# Change output format
python run_scraper.py --output json

# Adjust delay and concurrency
python run_scraper.py --delay 3 --concurrent 2

# Dry run (see what would be scraped)
python run_scraper.py --dry-run
```

### 5.3 Command Line Options
```bash
python run_scraper.py -h
```

Options:
- `--keywords, -k`: Comma-separated keywords
- `--pages, -p`: Pages per keyword (default: 5)
- `--output, -o`: Output format (csv, json, both)
- `--delay, -d`: Delay between requests (seconds)
- `--concurrent, -c`: Concurrent requests
- `--log-level, -l`: Log level (DEBUG, INFO, WARNING, ERROR)
- `--use-cache`: Enable caching
- `--dry-run`: Show what would be scraped

## Step 6: Output and Monitoring

### 6.1 Output Files
The scraper creates timestamped files:
- `amazon_products_YYYYMMDD_HHMMSS.csv`
- `amazon_products_YYYYMMDD_HHMMSS.json`

### 6.2 ScrapeOps Dashboard
Monitor your scraping in real-time:
1. Go to [https://scrapeops.io/app](https://scrapeops.io/app)
2. View statistics, errors, and performance metrics
3. Track request/response patterns

### 6.3 Logs
Check `amazon_scraper.log` for detailed logging information.

## Step 7: Troubleshooting

### 7.1 Common Issues

#### "No module named 'scrapy'"
```bash
pip install scrapy
```

#### "403 Forbidden" or "503 Service Unavailable"
- Increase delay between requests
- Check if IP is blocked
- Consider using proxies (ScrapeOps premium feature)

#### "CAPTCHA detected"
- Reduce scraping speed
- Use proxy rotation
- Implement CAPTCHA solving (advanced)

#### Empty results
- Check CSS selectors (Amazon frequently updates their HTML)
- Verify keywords are valid
- Check if region/language settings affect results

### 7.2 Amazon Anti-Bot Measures
Amazon has sophisticated anti-bot systems:
- **Rate limiting**: Respect delays between requests
- **IP blocking**: Use proxy rotation if needed
- **CAPTCHA challenges**: Implement solving or human intervention
- **User agent detection**: Rotate user agents (handled by ScrapeOps)
- **Session tracking**: Clear cookies/sessions periodically

### 7.3 Best Practices
1. **Start small**: Test with 1-2 keywords and few pages
2. **Monitor closely**: Watch ScrapeOps dashboard for errors
3. **Respect robots.txt**: Although set to False, be ethical
4. **Use delays**: Don't overwhelm Amazon's servers
5. **Handle errors gracefully**: Implement retry logic
6. **Store responsibly**: Don't scrape unnecessary data

## Step 8: Advanced Configuration

### 8.1 Proxy Integration
For heavy scraping, consider using proxies:

```python
# In settings.py
DOWNLOADER_MIDDLEWARES = {
    'scrapy_rotating_proxies.middlewares.RotatingProxyMiddleware': 610,
    'scrapy_rotating_proxies.middlewares.BanDetectionMiddleware': 620,
}

ROTATING_PROXY_LIST_PATH = 'proxy_list.txt'
```

### 8.2 Database Storage
To store data in database instead of files:

```python
# Add to pipelines.py
class DatabasePipeline:
    def __init__(self):
        # Initialize database connection
        pass
    
    def process_item(self, item, spider):
        # Save to database
        pass
```

### 8.3 Custom Selectors
Update selectors in `amazon_spider.py` if Amazon changes their HTML structure.

## Step 9: Legal and Ethical Considerations

### 9.1 Terms of Service
- Read Amazon's Terms of Service
- Respect rate limits
- Don't scrape personal data
- Use data responsibly

### 9.2 Best Practices
- Don't overload Amazon's servers
- Use scraped data for legitimate purposes
- Consider Amazon's Product Advertising API for commercial use
- Respect intellectual property rights

## Step 10: Scaling and Production

### 10.1 Scrapyd Deployment
For production deployment:
```bash
pip install scrapyd
scrapyd
```

### 10.2 Monitoring and Alerts
Set up alerts for:
- Scraping failures
- Rate limit hits
- CAPTCHA challenges
- Data quality issues

### 10.3 Data Pipeline
Consider integrating with:
- Data warehouses
- Analytics platforms
- Business intelligence tools

## Support and Resources

- **ScrapeOps Documentation**: [https://scrapeops.io/docs](https://scrapeops.io/docs)
- **Scrapy Documentation**: [https://scrapy.org/](https://scrapy.org/)
- **Amazon Product API**: [https://webservices.amazon.com/paapi5/](https://webservices.amazon.com/paapi5/)

## Example Usage

```bash
# Quick start
python run_scraper.py --keywords "laptop" --pages 3 --output csv

# Production run
python run_scraper.py --keywords "laptop,smartphone,headphones" --pages 10 --delay 3 --output both --use-cache
```

This setup provides a robust foundation for scraping Amazon UK product data with proper monitoring and error handling through ScrapeOps integration.