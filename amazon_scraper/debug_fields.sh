#!/bin/bash
echo "=== Amazon Field Debugging Script ==="
echo ""

# Function to test a single product
test_product() {
    local asin=$1
    local url="https://www.amazon.co.uk/dp/$asin"
    
    echo "Testing product: $asin"
    echo "URL: $url"
    echo ""
    
    # Create a temporary Python script for scrapy shell
    cat > temp_debug.py << 'EOF'
import re

def quick_debug():
    print("=== QUICK DEBUG RESULTS ===")
    
    # Extract ASIN
    asin_match = re.search(r'/dp/([A-Z0-9]{10})', response.url)
    asin = asin_match.group(1) if asin_match else "Unknown"
    print(f"ASIN: {asin}")
    
    # Check key missing fields
    print("\nMISSING FIELDS CHECK:")
    print("-" * 30)
    
    # Best Seller Rank
    rank_selectors = [
        '#SalesRank::text',
        'li:contains("Best Sellers Rank")::text',
        '*:contains("Best Sellers Rank")::text'
    ]
    
    print("1. Best Seller Rank:")
    for selector in rank_selectors:
        result = response.css(selector).get()
        if result:
            print(f"   ✓ Found: {result.strip()}")
            break
    else:
        print("   ✗ Not found")
        if '#1 Best Seller' in response.text:
            print("   ✓ Found #1 Best Seller badge")
    
    # Delivery info
    print("\n2. Delivery Info:")
    delivery_sections = ['#mir-layout-DELIVERY_BLOCK', '#contextualIngressPt', '#deliveryBlockMessage']
    for section in delivery_sections:
        if response.css(section).get():
            text = response.css(f"{section} *::text").getall()
            clean_text = ' '.join([t.strip() for t in text if t.strip()])
            if clean_text:
                print(f"   ✓ {section}: {clean_text[:100]}...")
                break
    else:
        print("   ✗ No delivery info found")
    
    # Seller info
    print("\n3. Seller Info:")
    seller_sections = ['#merchant-info', '#tabular-buybox', '#soldByThirdParty']
    for section in seller_sections:
        if response.css(section).get():
            text = response.css(f"{section} *::text").getall()
            clean_text = ' '.join([t.strip() for t in text if t.strip()])
            if clean_text:
                print(f"   ✓ {section}: {clean_text[:100]}...")
                break
    else:
        print("   ✗ No seller info found")
    
    # Product details
    print("\n4. Product Details:")
    details_sections = ['#productDetails_detailBullets_sections1', '#productDetails_db_sections']
    for section in details_sections:
        if response.css(section).get():
            print(f"   ✓ {section}: Found")
            # Check for specific fields
            if 'Date first available' in response.css(f"{section} *::text").get():
                print("     ✓ Contains listing date")
            break
    else:
        print("   ✗ No product details found")
    
    # Check text patterns
    print("\n5. Text Pattern Check:")
    patterns = ['Best Sellers Rank', 'FREE delivery', 'Ships from', 'Sold by', 'Date first available']
    for pattern in patterns:
        if pattern in response.text:
            print(f"   ✓ '{pattern}' found in page")
        else:
            print(f"   ✗ '{pattern}' not found")
    
    print("\n" + "="*50)

# Run the debug
quick_debug()
EOF
    
    # Run scrapy shell with the debug script
    echo "exec(open('temp_debug.py').read())" | scrapy shell "$url"
    
    # Clean up
    rm -f temp_debug.py
    echo ""
}

# Default products to test
DEFAULT_PRODUCTS=(
    "B08N5WRWNW"  # Electronics
    "B07VQHZX6H"  # Books
    "B07QFZPQ7V"  # Clothing
    "B07XJZB7Q1"  # Home
)

# Parse command line arguments
if [ $# -eq 0 ]; then
    echo "No ASIN provided. Testing default products..."
    echo ""
    for asin in "${DEFAULT_PRODUCTS[@]}"; do
        test_product "$asin"
        echo "Press Enter to continue to next product..."
        read
    done
else
    echo "Testing provided ASIN: $1"
    test_product "$1"
fi

echo "=== Debug Complete ==="
echo ""
echo "To run manual tests:"
echo "1. scrapy shell \"https://www.amazon.co.uk/dp/YOUR_ASIN\""
echo "2. exec(open('test_selectors.py').read())"
echo "3. test_missing_fields_selectors(response)"
echo ""
echo "Common test ASINs:"
echo "- Electronics: B08N5WRWNW"
echo "- Books: B07VQHZX6H"
echo "- Home: B07XJZB7Q1"
echo "- Clothing: B07QFZPQ7V"