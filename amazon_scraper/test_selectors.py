#!/usr/bin/env python3
# test_selectors.py - Quick selector testing for missing fields

import re

def test_missing_fields_selectors(response):
    """Test selectors for all missing fields"""
    
    print("=== TESTING MISSING FIELDS SELECTORS ===")
    print(f"URL: {response.url}")
    
    # Test BestSellerRank
    print("\n1. BEST SELLER RANK:")
    print("-" * 30)
    
    best_seller_tests = [
        ('#SalesRank::text', 'SalesRank ID'),
        ('#detailBullets_feature_div li:contains("Best Sellers Rank")::text', 'Detail bullets'),
        ('#productDetails_detailBullets_sections1 tr:contains("Best Sellers Rank") td::text', 'Product details table'),
        ('li:contains("Best Sellers Rank")::text', 'Any list item'),
        ('span:contains("Best Sellers Rank")::text', 'Any span'),
        ('*:contains("Best Sellers Rank")::text', 'Any element')
    ]
    
    for selector, desc in best_seller_tests:
        result = response.css(selector).get()
        if result:
            print(f"✓ {desc}: {result.strip()}")
            rank_match = re.search(r'#([\d,]+)', result)
            if rank_match:
                print(f"  Extracted rank: {rank_match.group(1)}")
        else:
            print(f"✗ {desc}: No result")
    
    # Check for #1 Best Seller badge
    bestseller_badge = response.css('span:contains("#1 Best Seller")::text').get()
    if bestseller_badge:
        print(f"✓ Found #1 Best Seller badge: {bestseller_badge}")
    
    # Test CustomerServiceProvider
    print("\n2. CUSTOMER SERVICE PROVIDER:")
    print("-" * 30)
    
    csp_tests = [
        ('#tabular-buybox tr:contains("Customer service") td::text', 'Tabular buybox'),
        ('span:contains("Customer service")::text', 'Any span'),
        ('tr:contains("Customer service") td::text', 'Any table row'),
        ('*:contains("Customer service")::text', 'Any element')
    ]
    
    for selector, desc in csp_tests:
        result = response.css(selector).get()
        if result:
            print(f"✓ {desc}: {result.strip()}")
        else:
            print(f"✗ {desc}: No result")
    
    # Test DispatchesFrom
    print("\n3. DISPATCHES FROM:")
    print("-" * 30)
    
    dispatch_tests = [
        ('#tabular-buybox tr:contains("Dispatches from") td::text', 'Tabular buybox - Dispatches'),
        ('#tabular-buybox tr:contains("Ships from") td::text', 'Tabular buybox - Ships'),
        ('span:contains("Dispatches from")::text', 'Any span - Dispatches'),
        ('span:contains("Ships from")::text', 'Any span - Ships'),
        ('*:contains("Dispatches from")::text', 'Any element - Dispatches'),
        ('*:contains("Ships from")::text', 'Any element - Ships')
    ]
    
    for selector, desc in dispatch_tests:
        result = response.css(selector).get()
        if result:
            clean_result = result.strip().replace('Dispatches from ', '').replace('Ships from ', '').strip()
            print(f"✓ {desc}: {clean_result}")
        else:
            print(f"✗ {desc}: No result")
    
    # Test ShippingCost
    print("\n4. SHIPPING COST:")
    print("-" * 30)
    
    shipping_tests = [
        ('#mir-layout-DELIVERY_BLOCK', 'Main delivery block'),
        ('#deliveryBlockMessage', 'Delivery message'),
        ('#contextualIngressPt', 'Contextual ingress'),
        ('#shippingMessageInsideBuyBox_feature_div', 'Shipping message buybox')
    ]
    
    for selector, desc in shipping_tests:
        result = response.css(selector).get()
        if result:
            print(f"✓ {desc}: Found")
            # Get text content
            text_content = response.css(f"{selector} *::text").getall()
            clean_text = ' '.join([t.strip() for t in text_content if t.strip()])
            print(f"  Text: {clean_text[:100]}...")
            
            # Check for FREE
            if 'FREE' in clean_text.upper():
                print(f"  🎯 FREE shipping detected!")
            
            # Check for cost
            cost_match = re.search(r'£(\d+\.?\d*)', clean_text)
            if cost_match:
                print(f"  💰 Cost found: £{cost_match.group(1)}")
        else:
            print(f"✗ {desc}: No result")
    
    # Test SellerOffersCount
    print("\n5. SELLER OFFERS COUNT:")
    print("-" * 30)
    
    offers_tests = [
        ('#olp-upd-new-freeshipping a::text', 'OLP new freeshipping'),
        ('#olp_feature_div a::text', 'OLP feature div'),
        ('a:contains("new offers")::text', 'New offers link'),
        ('span:contains("new offers")::text', 'New offers span'),
        ('a:contains("used offers")::text', 'Used offers link'),
        ('*:contains("offers")::text', 'Any offers text')
    ]
    
    for selector, desc in offers_tests:
        result = response.css(selector).get()
        if result:
            print(f"✓ {desc}: {result.strip()}")
            offers_match = re.search(r'(\d+)', result)
            if offers_match:
                print(f"  Offers count: {offers_match.group(1)}")
        else:
            print(f"✗ {desc}: No result")
    
    # Test ListingDate
    print("\n6. LISTING DATE:")
    print("-" * 30)
    
    date_tests = [
        ('#productDetails_detailBullets_sections1 tr:contains("Date first available") td::text', 'Product details - Date'),
        ('#productDetails_db_sections tr:contains("Date first available") td::text', 'Product DB - Date'),
        ('li:contains("Date first available")::text', 'List item - Date'),
        ('span:contains("Date first available")::text', 'Span - Date'),
        ('*:contains("Date first available")::text', 'Any element - Date')
    ]
    
    for selector, desc in date_tests:
        result = response.css(selector).get()
        if result:
            clean_date = result.strip().replace('Date first available:', '').strip()
            print(f"✓ {desc}: {clean_date}")
        else:
            print(f"✗ {desc}: No result")
    
    # Test IsBuyBoxWinner
    print("\n7. BUY BOX WINNER:")
    print("-" * 30)
    
    buybox_tests = [
        ('#merchant-info a::text', 'Merchant info link'),
        ('#soldByThirdParty a::text', 'Sold by third party'),
        ('span:contains("Sold by")::text', 'Sold by span'),
        ('#tabular-buybox tr:contains("Sold by") td a::text', 'Tabular buybox sold by')
    ]
    
    for selector, desc in buybox_tests:
        result = response.css(selector).get()
        if result:
            print(f"✓ {desc}: {result.strip()}")
        else:
            print(f"✗ {desc}: No result")
    
    # Test Delivery Days
    print("\n8. DELIVERY DAYS:")
    print("-" * 30)
    
    # Get all delivery text
    delivery_selectors = [
        '#mir-layout-DELIVERY_BLOCK *::text',
        '#deliveryBlockMessage *::text',
        '#contextualIngressPt *::text',
        '#availability *::text'
    ]
    
    all_delivery_text = []
    for selector in delivery_selectors:
        texts = response.css(selector).getall()
        if texts:
            all_delivery_text.extend(texts)
    
    if all_delivery_text:
        full_text = ' '.join([t.strip() for t in all_delivery_text if t.strip()])
        print(f"Full delivery text: {full_text[:200]}...")
        
        # Test patterns
        if 'tomorrow' in full_text.lower():
            print("✓ Tomorrow delivery detected (1 day)")
        elif 'today' in full_text.lower():
            print("✓ Today delivery detected (0 days)")
        
        days_match = re.search(r'(\d+)[-–]?(\d+)?\s*days?', full_text.lower())
        if days_match:
            fastest = int(days_match.group(1))
            slowest = int(days_match.group(2)) if days_match.group(2) else fastest
            print(f"✓ Delivery days found: {fastest}-{slowest} days")
    else:
        print("✗ No delivery text found")
    
    # Additional debugging
    print("\n9. GENERAL PAGE CHECKS:")
    print("-" * 30)
    
    # Check if common sections exist
    sections_to_check = {
        '#productDetails_detailBullets_sections1': 'Product Details Section 1',
        '#productDetails_db_sections': 'Product DB Sections',
        '#tabular-buybox': 'Tabular Buybox',
        '#merchant-info': 'Merchant Info',
        '#mir-layout-DELIVERY_BLOCK': 'Delivery Block',
        '#availability': 'Availability Section'
    }
    
    for selector, name in sections_to_check.items():
        if response.css(selector).get():
            print(f"✓ {name}: Found")
        else:
            print(f"✗ {name}: Missing")
    
    # Check for common text patterns
    text_patterns = [
        'Best Sellers Rank',
        'Customer service',
        'Dispatches from',
        'Ships from',
        'FREE delivery',
        'Date first available',
        'new offers',
        'Sold by'
    ]
    
    print(f"\nText patterns found in page:")
    for pattern in text_patterns:
        if pattern in response.text:
            print(f"✓ '{pattern}' found in page")
        else:
            print(f"✗ '{pattern}' not found in page")

def quick_test_all_fields(response):
    """Quick test of all fields with basic selectors"""
    
    print("\n=== QUICK TEST ALL FIELDS ===")
    
    # Quick field tests
    fields = {
        'ASIN': lambda r: re.search(r'/dp/([A-Z0-9]{10})', r.url).group(1) if re.search(r'/dp/([A-Z0-9]{10})', r.url) else None,
        'Title': lambda r: r.css('#productTitle::text').get(),
        'Price': lambda r: r.css('.a-price .a-offscreen::text').get(),
        'StarRating': lambda r: r.css('[data-hook="average-star-rating"] .a-icon-alt::text').get(),
        'Brand': lambda r: r.css('#bylineInfo::text').get(),
        'Prime': lambda r: 'prime' in r.text.lower(),
        'Availability': lambda r: r.css('#availability span::text').get()
    }
    
    for field, extractor in fields.items():
        try:
            result = extractor(response)
            if result:
                print(f"✓ {field}: {str(result)[:50]}...")
            else:
                print(f"✗ {field}: No result")
        except Exception as e:
            print(f"✗ {field}: Error - {str(e)}")

# Instructions for use
if __name__ == "__main__":
    print("""
    To use this script:
    
    1. Start scrapy shell:
       scrapy shell "https://www.amazon.co.uk/dp/B08N5WRWNW"
    
    2. In the shell, run:
       exec(open('test_selectors.py').read())
       test_missing_fields_selectors(response)
       quick_test_all_fields(response)
    
    3. Try with different products:
       scrapy shell "https://www.amazon.co.uk/dp/ANOTHER_ASIN"
    """)