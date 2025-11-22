#!/usr/bin/env python3

import re
from datetime import datetime, timedelta

def debug_missing_fields(response):
    """Debug missing fields in Amazon product pages"""
    
    print("=== DEBUGGING MISSING AMAZON FIELDS ===")
    print(f"URL: {response.url}")
    print(f"Status: {response.status}")
    print("=" * 50)
    
    # Extract ASIN for reference
    asin_match = re.search(r'/dp/([A-Z0-9]{10})', response.url)
    asin = asin_match.group(1) if asin_match else "Unknown"
    print(f"ASIN: {asin}")
    print("=" * 50)
    
    # 1. BestSellerRank
    print("\n1. BEST SELLER RANK")
    print("-" * 30)
    
    # Multiple selectors for Best Seller Rank
    rank_selectors = [
        '#SalesRank::text',
        '#detailBullets_feature_div li:contains("Best Sellers Rank")::text',
        '#productDetails_detailBullets_sections1 tr:contains("Best Sellers Rank") td::text',
        '#productDetails_db_sections tr:contains("Best Sellers Rank") td::text',
        'li:contains("Best Sellers Rank")::text',
        'span:contains("Best Sellers Rank")::text',
        'tr:contains("Best Sellers Rank")::text'
    ]
    
    for selector in rank_selectors:
        try:
            result = response.css(selector).get()
            if result:
                print(f"✓ Found with: {selector}")
                print(f"  Result: {result.strip()}")
                rank_match = re.search(r'#([\d,]+)', result)
                if rank_match:
                    print(f"  Extracted rank: {rank_match.group(1)}")
                break
        except:
            continue
    else:
        print("✗ Best Seller Rank not found")
        # Let's check what's in the details section
        details = response.css('#productDetails_detailBullets_sections1').get()
        if details:
            print("  Found product details section, checking content...")
            print(f"  Details preview: {details[:200]}...")
    
    # 2. CustomerServiceProvider
    print("\n2. CUSTOMER SERVICE PROVIDER")
    print("-" * 30)
    
    csp_selectors = [
        '#merchant-info span:contains("Customer service")::text',
        'tr:contains("Customer service") td::text',
        'span:contains("Customer service")::text',
        '#tabular-buybox tr:contains("Customer service") td::text'
    ]
    
    for selector in csp_selectors:
        try:
            result = response.css(selector).get()
            if result:
                print(f"✓ Found with: {selector}")
                print(f"  Result: {result.strip()}")
                break
        except:
            continue
    else:
        print("✗ Customer Service Provider not found")
    
    # 3. Delivery Information
    print("\n3. DELIVERY INFORMATION")
    print("-" * 30)
    
    delivery_selectors = [
        '#mir-layout-DELIVERY_BLOCK',
        '#deliveryBlockMessage',
        '#availability',
        '#ddmDeliveryMessage',
        '[data-feature-name="delivery"]',
        '#shippingMessageInsideBuyBox_feature_div',
        '#fast-track-message',
        '#contextualIngressPt',
        '#contextualIngressPt_feature_div'
    ]
    
    print("Delivery sections found:")
    for selector in delivery_selectors:
        try:
            result = response.css(selector).get()
            if result:
                print(f"✓ {selector}: Found")
                # Extract text content
                text_content = response.css(f"{selector} *::text").getall()
                clean_text = ' '.join([t.strip() for t in text_content if t.strip()])
                print(f"  Text: {clean_text[:100]}...")
                
                # Look for specific delivery patterns
                if any(word in clean_text.lower() for word in ['tomorrow', 'today', 'delivery', 'shipping']):
                    print(f"  🎯 Contains delivery info!")
        except:
            continue
    
    # 4. Shipping Cost
    print("\n4. SHIPPING COST")
    print("-" * 30)
    
    shipping_selectors = [
        '#mir-layout-DELIVERY_BLOCK span:contains("FREE")::text',
        '#deliveryBlockMessage span:contains("FREE")::text',
        '#shippingMessageInsideBuyBox_feature_div span:contains("FREE")::text',
        'span:contains("shipping")::text',
        'span:contains("delivery")::text',
        '#contextualIngressPt span:contains("FREE")::text'
    ]
    
    for selector in shipping_selectors:
        try:
            result = response.css(selector).get()
            if result:
                print(f"✓ Found with: {selector}")
                print(f"  Result: {result.strip()}")
                if 'FREE' in result.upper():
                    print(f"  🎯 Free shipping detected!")
                break
        except:
            continue
    else:
        print("✗ Shipping cost not found")
    
    # 5. Seller Information
    print("\n5. SELLER INFORMATION")
    print("-" * 30)
    
    seller_selectors = [
        '#merchant-info',
        '#tabular-buybox',
        '#buybox',
        '#apex_desktop',
        '#soldByThirdParty',
        '#merchant-info a::text',
        'span:contains("Sold by")::text',
        'span:contains("Ships from")::text',
        'span:contains("Dispatches from")::text'
    ]
    
    print("Seller sections found:")
    for selector in seller_selectors:
        try:
            result = response.css(selector).get()
            if result:
                print(f"✓ {selector}: Found")
                if selector.endswith('::text'):
                    print(f"  Text: {result.strip()}")
                else:
                    # Extract text content
                    text_content = response.css(f"{selector} *::text").getall()
                    clean_text = ' '.join([t.strip() for t in text_content if t.strip()])
                    print(f"  Text: {clean_text[:100]}...")
        except:
            continue
    
    # 6. Product Details Section
    print("\n6. PRODUCT DETAILS SECTION")
    print("-" * 30)
    
    details_selectors = [
        '#productDetails_detailBullets_sections1',
        '#productDetails_db_sections',
        '#detailBullets_feature_div',
        '#productDetails_techSpec_section_1',
        '#feature-bullets'
    ]
    
    print("Product details sections found:")
    for selector in details_selectors:
        try:
            result = response.css(selector).get()
            if result:
                print(f"✓ {selector}: Found")
                # Look for specific fields
                fields_to_check = ['Date first available', 'ASIN', 'Item model number', 'Manufacturer']
                for field in fields_to_check:
                    field_result = response.css(f"{selector} *:contains('{field}')").get()
                    if field_result:
                        print(f"  🎯 Contains '{field}'")
        except:
            continue
    
    # 7. Availability and Stock
    print("\n7. AVAILABILITY AND STOCK")
    print("-" * 30)
    
    availability_selectors = [
        '#availability',
        '#availability span::text',
        '#availability-brief',
        '#quantityDropdown',
        '#quantity'
    ]
    
    for selector in availability_selectors:
        try:
            result = response.css(selector).get()
            if result:
                print(f"✓ Found with: {selector}")
                if selector.endswith('::text'):
                    print(f"  Text: {result.strip()}")
                else:
                    text_content = response.css(f"{selector} *::text").getall()
                    clean_text = ' '.join([t.strip() for t in text_content if t.strip()])
                    print(f"  Text: {clean_text[:100]}...")
        except:
            continue
    
    print("\n" + "=" * 50)
    print("DEBUG COMPLETE")
    print("=" * 50)

def test_specific_selectors(response):
    """Test specific selectors for each field"""
    
    print("\n=== TESTING SPECIFIC SELECTORS ===")
    
    # Test cases for each missing field
    test_cases = {
        'BestSellerRank': [
            '#SalesRank::text',
            'li:contains("Best Sellers Rank")::text',
            'tr:contains("Best Sellers Rank") td::text',
            'span:contains("Best Sellers Rank")::text'
        ],
        'CustomerServiceProvider': [
            '#merchant-info span:contains("Customer service")::text',
            'tr:contains("Customer service") td::text'
        ],
        'DispatchesFrom': [
            'span:contains("Dispatches from")::text',
            'span:contains("Ships from")::text',
            '#tabular-buybox tr:contains("Ships from") td::text'
        ],
        'ShippingCost': [
            '#mir-layout-DELIVERY_BLOCK span:contains("FREE")::text',
            '#deliveryBlockMessage span:contains("FREE")::text',
            'span:contains("shipping")::text'
        ],
        'SellerOffersCount': [
            '#olp-upd-new-freeshipping a::text',
            '#olp_feature_div a::text',
            'span:contains("new offers")::text'
        ],
        'IsBuyBoxWinner': [
            '#merchant-info a::text',
            '#soldByThirdParty::text',
            'span:contains("Sold by")::text'
        ],
        'ListingDate': [
            'tr:contains("Date first available") td::text',
            'li:contains("Date first available")::text',
            'span:contains("Date first available")::text'
        ]
    }
    
    for field, selectors in test_cases.items():
        print(f"\n{field}:")
        found = False
        for selector in selectors:
            try:
                result = response.css(selector).get()
                if result:
                    print(f"  ✓ {selector}: {result.strip()}")
                    found = True
                    break
            except:
                continue
        if not found:
            print(f"  ✗ No selector worked for {field}")

# Helper function to extract dates
def extract_delivery_dates(text):
    """Extract delivery dates from text"""
    dates = []
    # Look for patterns like "Get it tomorrow, 15 Jan" or "Tuesday, 16 Jan"
    date_patterns = [
        r'(\w+day,?\s+\d{1,2}\s+\w+)',
        r'(\d{1,2}\s+\w+)',
        r'(tomorrow|today)',
        r'(\d{1,2}-\d{1,2}\s+\w+)'
    ]
    
    for pattern in date_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        dates.extend(matches)
    
    return dates

# Instructions for manual testing
MANUAL_TESTING_INSTRUCTIONS = """
=== MANUAL TESTING INSTRUCTIONS ===

1. Start Scrapy shell:
   scrapy shell "https://www.amazon.co.uk/dp/B08N5WRWNW"

2. In the shell, run:
   exec(open('debug_selectors.py').read())
   debug_missing_fields(response)
   test_specific_selectors(response)

3. Test individual selectors:
   response.css('#SalesRank::text').get()
   response.css('li:contains("Best Sellers Rank")::text').getall()
   response.css('#merchant-info').get()

4. Check page source:
   print(response.text[:1000])  # First 1000 chars

5. Search for specific text:
   'Best Sellers Rank' in response.text
   'Ships from' in response.text
   'FREE delivery' in response.text

6. Test with different products:
   - Electronics: B08N5WRWNW
   - Books: B07VQHZX6H
   - Clothing: B07QFZPQ7V
   - Home & Garden: B07XJZB7Q1
"""

if __name__ == "__main__":
    print("This script is meant to be run inside Scrapy shell")
    print(MANUAL_TESTING_INSTRUCTIONS)