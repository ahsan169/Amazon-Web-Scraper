#!/bin/bash
# Quick Start Script for Amazon UK Product Scraper

echo "=== Amazon UK Product Scraper - Quick Start ==="
echo ""

# Step 1: Create project directory
echo "Step 1: Creating project directory..."
mkdir -p amazon_scraper_project
cd amazon_scraper_project

# Step 2: Create virtual environment
echo "Step 2: Setting up virtual environment..."
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Step 3: Create requirements.txt
echo "Step 3: Creating requirements.txt..."
cat > requirements.txt << 'EOF'
scrapy==2.11.0
scrapy-user-agents==0.1.1
scrapy-rotating-proxies==0.6.2
scrapeops-scrapy==0.5.13
requests==2.31.0
beautifulsoup4==4.12.2
lxml==4.9.3
itemadapter==0.8.0
twisted==22.10.0
pyopenssl==23.2.0
cryptography==41.0.3
w3lib==2.1.2
parsel==1.8.1
itemloaders==1.1.0
jmespath==1.0.1
cssselect==1.2.0
queuelib==1.6.2
service-identity==23.1.0
zope.interface==6.0
automat==22.10.0
constantly==15.1.0
hyperlink==21.0.0
incremental==22.10.0
packaging==23.1
attrs==23.1.0
six==1.16.0
urllib3==2.0.4
certifi==2023.7.22
charset-normalizer==3.2.0
idna==3.4
EOF

# Step 4: Install dependencies
echo "Step 4: Installing dependencies..."
pip install -r requirements.txt

# Step 5: Create Scrapy project
echo "Step 5: Creating Scrapy project..."
scrapy startproject amazon_scraper
cd amazon_scraper

# Step 6: Display next steps
echo ""
echo "=== Setup Complete! ==="
echo ""
echo "Next steps:"
echo "1. Get your ScrapeOps API key from https://scrapeops.io/"
echo "2. Copy the provided files to their respective locations"
echo "3. Update your API key in settings.py"
echo "4. Run the scraper:"
echo ""
echo "   # Basic usage"
echo "   python run_scraper.py"
echo ""
echo "   # Custom keywords"
echo "   python run_scraper.py --keywords 'laptop,smartphone'"
echo ""
echo "   # Dry run to see what would be scraped"
echo "   python run_scraper.py --dry-run"
echo ""
echo "=== File Structure ==="
echo "amazon_scraper_project/"
echo "├── venv/                    # Virtual environment"
echo "├── requirements.txt         # Python dependencies"
echo "├── config.py               # Configuration file"
echo "├── run_scraper.py          # Runner script"
echo "└── amazon_scraper/         # Scrapy project"
echo "    ├── scrapy.cfg"
echo "    └── amazon_scraper/"
echo "        ├── __init__.py"
echo "        ├── items.py        # Data structure"
echo "        ├── middlewares.py  # Custom middlewares"
echo "        ├── pipelines.py    # Data processing"
echo "        ├── settings.py     # Scrapy settings"
echo "        └── spiders/"
echo "            ├── __init__.py"
echo "            └── amazon_spider.py  # Main spider"
echo ""
echo "=== Important Notes ==="
echo "• Replace 'YOUR_SCRAPEOPS_API_KEY_HERE' with your actual API key"
echo "• Start with small tests (1-2 keywords, few pages)"
echo "• Monitor your scraping in ScrapeOps dashboard"
echo "• Respect Amazon's servers - use appropriate delays"
echo "• Check output files: amazon_products_TIMESTAMP.csv/json"
echo ""
echo "Happy scraping! 🕷️"