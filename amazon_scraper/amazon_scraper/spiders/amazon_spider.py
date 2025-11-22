
import scrapy
import json
import re
import config
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlparse, parse_qs
from amazon_scraper.items import AmazonProductItem
from amazon_scraper.database import get_db_manager
from amazon_scraper.keyword_generator import get_keyword_generator

class AmazonSpider(scrapy.Spider):
    name = 'amazon_spider'
    allowed_domains = [config.AMAZON_DOMAINS[config.DEFAULT_DOMAIN]]
    
    # Configuration
    KEYWORDS = config.KEYWORDS
    MAX_PAGES = config.MAX_PAGES_PER_KEYWORD
        
    def __init__(self, keywords=None, max_pages=None, domain=None, generate_keywords=None, 
                categories=None, use_db_keywords=None, *args, **kwargs):
        super(AmazonSpider, self).__init__(*args, **kwargs)
        
        # Initialize database and keyword generator
        self.db_manager = None
        self.keyword_generator = None
        
        if config.MONGODB_ENABLED:
            self.db_manager = get_db_manager()
            self.keyword_generator = get_keyword_generator()
        
        # Set domain
        target_domain = domain if domain in config.AMAZON_DOMAINS else config.DEFAULT_DOMAIN
        self.target_domain = target_domain
        self.allowed_domains = [config.AMAZON_DOMAINS[target_domain]]
        
        # Handle keyword generation
        should_generate = (
            (generate_keywords and generate_keywords.lower() == 'true') or
            (generate_keywords is None and config.KEYWORD_GENERATION_ENABLED and not keywords and not use_db_keywords)
        )
        
        if should_generate and self.keyword_generator:
            self.logger.info("Generating keywords from categories...")
            target_categories = categories.split(',') if categories else config.PRODUCT_CATEGORIES
            
            generated_count = self.keyword_generator.generate_keywords_for_categories(
                target_categories, target_domain
            )
            self.logger.info(f"Generated {generated_count} new keywords")
        
        # Determine keyword source priority:
        # 1. Command line keywords
        # 2. Database keywords (if use_db_keywords=true or no other source)
        # 3. Config keywords
        
        if keywords:
            # Use provided keywords
            self.KEYWORDS = keywords.split(',')
            self.logger.info(f"Using {len(self.KEYWORDS)} keywords from command line")
        elif use_db_keywords == 'true' or (use_db_keywords is None and self.db_manager):
            # Get keywords from database
            if self.db_manager:
                db_keywords = self.keyword_generator.get_keywords_for_scraping(
                    limit=config.MAX_KEYWORDS_PER_RUN,
                    domain=target_domain
                )
                
                if db_keywords:
                    self.KEYWORDS = db_keywords
                    self.logger.info(f"Using {len(db_keywords)} keywords from database")
                else:
                    self.logger.warning("No keywords found in database, using config keywords")
                    self.KEYWORDS = config.KEYWORDS
            else:
                self.logger.warning("Database not available, using config keywords")
                self.KEYWORDS = config.KEYWORDS
        else:
            # Use default keywords from config
            self.KEYWORDS = config.KEYWORDS
            self.logger.info(f"Using {len(self.KEYWORDS)} keywords from config")

        if self.db_manager and hasattr(self, 'KEYWORDS'):
            self.keyword_categories = {}  # Store keyword -> category mapping
            for keyword in self.KEYWORDS:
                keyword_doc = self.db_manager.db[config.get_collection_name('keywords')].find_one({
                    'keyword': keyword,
                    'domain': target_domain
                })
                if keyword_doc:
                    self.keyword_categories[keyword] = keyword_doc.get('category', 'Unknown')
                    self.logger.info(f"Keyword '{keyword}' has category: {keyword_doc.get('category')}")
                else:
                    self.keyword_categories[keyword] = 'Unknown'
        
        # Set other parameters
        if max_pages:
            self.MAX_PAGES = int(max_pages)
        else:
            self.MAX_PAGES = config.MAX_PAGES_PER_KEYWORD
        
    def start_requests(self):
        """Generate initial requests for each keyword"""
        for keyword in self.KEYWORDS:
            domain_name = self.allowed_domains[0]  # e.g., 'amazon.com'
            search_url = f"https://{domain_name}/s?k={keyword.replace(' ', '+')}"
            self.logger.info(f"Starting request for: {search_url}") 
            category = getattr(self, 'keyword_categories', {}).get(keyword, 'Unknown')

            yield scrapy.Request(
                url=search_url,
                callback=self.parse_search_results,
                meta={
                    'keyword': keyword,
                    'page': 1,
                    'domain': self.target_domain,
                    'category': category
                }
            )

    def parse_search_results(self, response):
        """Parse search results page and extract product URLs"""
        keyword = response.meta['keyword']
        page = response.meta['page']
        domain = response.meta['domain']

        # Increment keyword scraping attempts - ADD THIS BACK
        if self.db_manager:
            category = response.meta.get('category', 'Unknown')
            self.db_manager.increment_keyword_attempts(keyword, domain, category)

        # Extract unique product URLs from main search results
        product_urls = []
        unique_links = {}
        
        # Get all result items with ASIN (main products)
        for item in response.css('.s-result-item[data-asin]'):
            asin = item.css('::attr(data-asin)').get()
            
            # Skip empty ASINs and sponsored items
            if not asin or item.css(':contains("Sponsored")'):
                continue
                
            # Get the main product link (first link with /dp/ in this item)
            link = item.css('a[href*="/dp/"]::attr(href)').get()
            
            if link and asin not in unique_links:
                unique_links[asin] = link
                product_urls.append(link)
        
        # # OPTIONAL: Remove variants (uncomment if you want unique products only)
        # # This is already handled above by using unique_links dictionary
        # unique_products = []
        # seen_asins = set()
        # 
        # for url in product_urls:
        #     # Extract ASIN from URL
        #     asin_match = re.search(r'/dp/([A-Z0-9]{10})', url)
        #     if asin_match:
        #         asin = asin_match.group(1)
        #         if asin not in seen_asins:
        #             seen_asins.add(asin)
        #             unique_products.append(url)
        #     else:
        #         # If no ASIN found, include the URL anyway
        #         unique_products.append(url)
        # 
        # product_urls = unique_products
        
        self.logger.info(f"Found {len(product_urls)} unique main products on page {page} for keyword '{keyword}'")
        
        # Process each product URL
        for url in product_urls:
            full_url = urljoin(response.url, url)
            yield scrapy.Request(
                url=full_url,
                callback=self.parse_product,
                meta={
                    'keyword': keyword,
                    'page': page,
                    'domain': domain,
                    'category': response.meta.get('category', 'Unknown')
                }
            )
        
        products_found = len(product_urls)
        if self.db_manager:
            category = response.meta.get('category', 'Unknown')
            should_mark_scraped = False
            
            # Mark as scraped if we've reached max pages OR no next page exists
            if page >= self.MAX_PAGES:
                should_mark_scraped = True
            else:
                # Check if there's actually a next page available
                next_page_url = self.get_next_page_url(response, keyword, page)
                if not next_page_url or not self.has_next_page_results(response):
                    should_mark_scraped = True
            
            if should_mark_scraped:
                self.db_manager.mark_keyword_scraped(keyword, domain, category, products_found)
                self.logger.info(f"Marked keyword '{keyword}' as scraped with {products_found} products")
    
        # Follow pagination if within limit
        if page < self.MAX_PAGES:
            next_page_url = self.get_next_page_url(response, keyword, page)
            if next_page_url:
                yield scrapy.Request(
                    url=next_page_url,
                    callback=self.parse_search_results,
                    meta={
                        'keyword': keyword,
                        'page': page + 1,
                        'domain': self.target_domain,
                        'category': response.meta.get('category', 'Unknown')
                    }
                )
    
    def has_next_page_results(self, response):
        """Check if there are more pages with results"""
        # Check if pagination exists and has next page
        next_page_selectors = [
            '.s-pagination-next:not(.s-pagination-disabled)',
            'a[aria-label="Go to next page"]',
            '.a-pagination .a-last:not(.a-disabled)'
        ]
        
        for selector in next_page_selectors:
            if response.css(selector).get():
                return True
        
        return False
    
    def get_next_page_url(self, response, keyword, current_page):
        """Generate next page URL"""
        next_page = current_page + 1
        base_url = f"https://amazon.com/s?k={keyword.replace(' ', '+')}"
        return f"{base_url}&page={next_page}"
    
    def parse_product(self, response):
        """Parse individual product page"""
        item = AmazonProductItem()
        
        # Extract ASIN from URL
        asin_match = re.search(r'/dp/([A-Z0-9]{10})', response.url)
        item['ASIN'] = asin_match.group(1) if asin_match else None
        
        # Basic product information
        item['Title'] = self.extract_title(response)
        item['ProductURL'] = response.url
        item['Brand'] = self.extract_brand(response)
        
        # Ratings and reviews
        item['StarRating'] = self.extract_star_rating(response)
        item['NumberOfRatings'] = self.extract_number_of_ratings(response)
        
        # Pricing
        item['Price'] = self.extract_price(response)
        item['ShippingCost'] = self.extract_shipping_cost(response)
        
        # Rankings - UPDATED WITH WORKING SELECTORS
        item['BestSellerRank'] = self.extract_best_seller_rank(response)
        item['SalesSubRank'] = self.extract_sales_sub_rank(response)
        item['SalesSubSubRank'] = self.extract_sales_sub_sub_rank(response)
        
        # Delivery information - UPDATED WITH WORKING SELECTORS
        delivery_info = self.extract_delivery_info(response)
        item.update(delivery_info)
        
        # Seller information - UPDATED WITH WORKING SELECTORS
        seller_info = self.extract_seller_info(response)
        item.update(seller_info)
        
        # Prime and availability
        item['IsPrime'] = self.extract_prime_status(response)
        item['Prime'] = item['IsPrime']  # Duplicate field
        item['AvailableQuantity'] = self.extract_available_quantity(response)
        
        # Additional fields - UPDATED WITH WORKING SELECTORS
        item['ListingDate'] = self.extract_listing_date(response)
        item['CustomerServiceProvider'] = self.extract_customer_service_provider(response)
        item['SellerOffersCount'] = self.extract_seller_offers_count(response)
        item['IsBuyBoxWinner'] = self.extract_buy_box_winner(response)
        
        # Metadata
        item['ScrapedAt'] = datetime.now().isoformat()
        item['Keyword'] = response.meta['keyword']
        item['Domain'] = self.target_domain
        item['PageNumber'] = response.meta['page']
        
        yield item
    
    def extract_title(self, response):
        """Extract product title"""
        title_selectors = [
            '#productTitle::text',
            '.product-title::text',
            'h1 span::text',
            'h1::text'
        ]
        
        for selector in title_selectors:
            title = response.css(selector).get()
            if title:
                return title.strip()
        return None
    
    def extract_brand(self, response):
        """Extract brand name"""
        brand_selectors = [
            '#bylineInfo::text',
            '#bylineInfo a::text',
            '.a-offscreen::text',
            'tr:contains("Brand") td::text',
            'tr:contains("Manufacturer") td::text',
            'span:contains("Brand")::text',
            'span:contains("by") a::text'
        ]
        
        for selector in brand_selectors:
            brand = response.css(selector).get()
            if brand:
                clean_brand = brand.strip().replace('by ', '').replace('Brand:', '').strip()
                if clean_brand and len(clean_brand) > 1:
                    return clean_brand
        return None
    
    def extract_star_rating(self, response):
        """Extract star rating"""
        rating_selectors = [
            '[data-hook="average-star-rating"] .a-icon-alt::text',
            '.a-icon-alt::text',
            '[data-hook="rating-out-of-text"]::text',
            'span:contains("out of 5")::text',
            '.cr-widget-FocusReviews .a-icon-alt::text'
        ]
        
        for selector in rating_selectors:
            rating_text = response.css(selector).get()
            if rating_text:
                rating_match = re.search(r'(\d+\.?\d*)\s*out\s*of\s*5', rating_text)
                if rating_match:
                    return float(rating_match.group(1))
        return None
    
    def extract_number_of_ratings(self, response):
        """Extract number of ratings"""
        rating_selectors = [
            '[data-hook="total-review-count"]::text',
            '#acrCustomerReviewText::text',
            'span[data-hook="total-review-count"]::text',
            'a:contains("ratings")::text',
            'span:contains("ratings")::text'
        ]
        
        for selector in rating_selectors:
            rating_text = response.css(selector).get()
            if rating_text:
                rating_match = re.search(r'([\d,]+)', rating_text.replace(',', ''))
                if rating_match:
                    return int(rating_match.group(1))
        return None
    
    def extract_price(self, response):
        """Extract price"""
        price_selectors = [
            '.a-price-whole::text',
            '.a-price.a-text-price.a-size-medium.apexPriceToPay .a-offscreen::text',
            '.a-price .a-offscreen::text',
            '#priceblock_ourprice::text',
            '#priceblock_dealprice::text',
            '.a-price-range .a-price .a-offscreen::text',
            'span.a-price-symbol + span.a-price-whole::text'
        ]
        
        for selector in price_selectors:
            price_text = response.css(selector).get()
            if price_text:
                # Clean price text and extract number
                clean_price = price_text.replace('£', '').replace(',', '').strip()
                price_match = re.search(r'(\d+\.?\d*)', clean_price)
                if price_match:
                    return float(price_match.group(1))
        return None
    
    def extract_shipping_cost(self, response):
        """Extract shipping cost - UPDATED WITH MULTIPLE PRODUCT LAYOUTS"""
        # Method 1: JBL-style product (mir-layout-DELIVERY_BLOCK)
        delivery_text = response.css('#mir-layout-DELIVERY_BLOCK *::text').getall()
        if delivery_text:
            full_text = ' '.join(delivery_text)
            if 'FREE delivery' in full_text:
                return 0.0
            
            # Look for shipping cost pattern
            cost_match = re.search(r'£(\d+\.?\d*)', full_text)
            if cost_match:
                return float(cost_match.group(1))
        
        # Method 2: Anker-style product (check for FREE Returns/shipping)
        # Based on shell testing: "FREE Returns" found in apex_desktop
        if 'FREE Returns' in response.text or 'FREE delivery' in response.text:
            return 0.0
        
        # Method 3: Check buybox for delivery info
        buybox_text = response.css('#buybox *::text').getall()
        if buybox_text:
            full_text = ' '.join(buybox_text)
            if 'FREE' in full_text and ('delivery' in full_text.lower() or 'shipping' in full_text.lower()):
                return 0.0
        
        # Method 4: Check apex_desktop for shipping info
        apex_text = response.css('#apex_desktop *::text').getall()
        if apex_text:
            full_text = ' '.join(apex_text)
            if 'FREE' in full_text and ('delivery' in full_text.lower() or 'shipping' in full_text.lower()):
                return 0.0
        
        return None
    
    def extract_best_seller_rank(self, response):
        """Extract best seller rank - UPDATED WITH MULTIPLE PRODUCT LAYOUTS"""
        # Method 1: JBL-style product (productDetails_detailBullets_sections1)
        rank_text = response.css('#productDetails_detailBullets_sections1 tr:contains("Best Sellers Rank") td span li span span::text').get()
        if rank_text:
            rank_match = re.search(r'(\d+)', rank_text)
            if rank_match:
                return int(rank_match.group(1))
        
        # Method 2: Anker-style product (search in page text)
        # Look for "Best Sellers Rank: 312 in Climate Pledge Friendly"
        if 'Best Sellers Rank' in response.text:
            rank_match = re.search(r'Best Sellers Rank:?\s*(\d+)\s+in', response.text)
            if rank_match:
                return int(rank_match.group(1))
        
        # Method 3: Additional fallback selectors
        fallback_selectors = [
            '#productDetails_detailBullets_sections1 tr:contains("Best Sellers Rank") td::text',
            '#productDetails_db_sections tr:contains("Best Sellers Rank") td::text',
            'tr:contains("Best Sellers Rank") td::text'
        ]
        
        for selector in fallback_selectors:
            rank_text = response.css(selector).get()
            if rank_text:
                rank_match = re.search(r'(\d+)', rank_text)
                if rank_match:
                    return int(rank_match.group(1))
        
        return None
    
    def extract_sales_sub_rank(self, response):
        """Extract sales sub-rank"""
        # Get the category name from best seller rank
        rank_text = response.css('#productDetails_detailBullets_sections1 tr:contains("Best Sellers Rank") td span li span span::text').get()
        if rank_text:
            # Extract category from "430 in In-Ear Headphones"
            category_match = re.search(r'\d+\s+in\s+(.+)', rank_text)
            if category_match:
                return category_match.group(1).strip()
        
        return None
    
    def extract_sales_sub_sub_rank(self, response):
        """Extract sales sub-sub-rank"""
        # Look for additional category rankings in the same section
        rank_elements = response.css('#productDetails_detailBullets_sections1 tr:contains("Best Sellers Rank") td span li span span::text').getall()
        if len(rank_elements) > 1:
            # If there are multiple rankings, return the second one
            second_rank = rank_elements[1]
            rank_match = re.search(r'(\d+)', second_rank)
            if rank_match:
                return int(rank_match.group(1))
        
        return None
    
    def extract_delivery_info(self, response):
        """Extract delivery information - UPDATED WITH MULTIPLE PRODUCT LAYOUTS"""
        delivery_info = {}
        
        # Method 1: JBL-style product (mir-layout-DELIVERY_BLOCK)
        delivery_text = response.css('#mir-layout-DELIVERY_BLOCK *::text').getall()
        if delivery_text:
            full_text = ' '.join(delivery_text)
            delivery_info['FastestDelivery'] = full_text.strip()
            
            # Extract delivery date - WORKING PATTERN
            date_pattern = re.search(r'(\w+day,\s+\d+\s+\w+)', full_text)
            if date_pattern:
                delivery_date = date_pattern.group(1)
                delivery_info['DeliveryEstimateFastest'] = delivery_date
                delivery_info['FastestDeliveryDate'] = delivery_date
                
                # Calculate delivery days
                delivery_days = self.calculate_delivery_days(delivery_date)
                if delivery_days is not None:
                    delivery_info['DeliveryDaysFastest'] = delivery_days
                    delivery_info['DeliveryDays'] = delivery_days
            
            # Check for today/tomorrow
            if 'tomorrow' in full_text.lower():
                delivery_info['DeliveryDaysFastest'] = 1
                delivery_info['DeliveryDays'] = 1
            elif 'today' in full_text.lower():
                delivery_info['DeliveryDaysFastest'] = 0
                delivery_info['DeliveryDays'] = 0
        
        # Method 2: Anker-style product (check buybox and apex_desktop)
        if not delivery_info.get('FastestDelivery'):
            # Check buybox for delivery info
            buybox_text = response.css('#buybox *::text').getall()
            if buybox_text:
                full_text = ' '.join(buybox_text)
                
                # Look for delivery patterns
                delivery_patterns = [
                    r'delivery\s+(\w+day,?\s+\d+\s+\w+)',
                    r'arrives\s+(\w+day,?\s+\d+\s+\w+)',
                    r'get it\s+(\w+day,?\s+\d+\s+\w+)'
                ]
                
                for pattern in delivery_patterns:
                    date_match = re.search(pattern, full_text, re.IGNORECASE)
                    if date_match:
                        delivery_date = date_match.group(1)
                        delivery_info['DeliveryEstimateFastest'] = delivery_date
                        delivery_info['FastestDeliveryDate'] = delivery_date
                        delivery_info['FastestDelivery'] = f"Delivery {delivery_date}"
                        
                        # Calculate delivery days
                        delivery_days = self.calculate_delivery_days(delivery_date)
                        if delivery_days is not None:
                            delivery_info['DeliveryDaysFastest'] = delivery_days
                            delivery_info['DeliveryDays'] = delivery_days
                        break
        
        # Method 3: Check contextualIngressPt for delivery location
        if not delivery_info.get('FastestDelivery'):
            context_text = response.css('#contextualIngressPt *::text').getall()
            if context_text:
                full_text = ' '.join(context_text)
                if 'Select delivery location' in full_text:
                    delivery_info['FastestDelivery'] = 'Select delivery location for estimate'
        
        return delivery_info
    
    def calculate_delivery_days(self, delivery_date):
        """Calculate delivery days from date string like 'Tuesday, 8 July'"""
        try:
            # Simple day calculation
            today = datetime.now()
            weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            
            # Extract day name
            day_match = re.search(r'(\w+day)', delivery_date)
            if day_match:
                day_name = day_match.group(1)
                if day_name in weekdays:
                    today_weekday = today.weekday()  # 0=Monday, 6=Sunday
                    target_weekday = weekdays.index(day_name)
                    
                    if target_weekday >= today_weekday:
                        return target_weekday - today_weekday
                    else:
                        return 7 - (today_weekday - target_weekday)
        except:
            pass
        
        return None
    
    def extract_seller_info(self, response):
        """Extract seller information - UPDATED WITH MULTIPLE PRODUCT LAYOUTS"""
        seller_info = {}
        
        # Method 1: Get buybox text (works for both product types)
        buybox_text = response.css('#buybox *::text').getall()
        if buybox_text:
            full_text = ' '.join(buybox_text)
            
            # Extract seller name - improved regex for cleaner extraction
            # Based on shell testing: "Sold by: AnkerDirect UK", "Dispatches from: Amazon"
            sold_by_patterns = [
                r'Sold by:\s*([^,\n]+?)(?:\s*Dispatches|\s*Returns|\s*$)',
                r'Sold by\s+([A-Za-z\s&\-\.]+?)(?:\s{2,}|\s*Returns|\s*$)',
                r'Sold by:\s*([^,\n\r]+?)(?:\s*[\n\r]|$)'
            ]
            
            for pattern in sold_by_patterns:
                sold_by_match = re.search(pattern, full_text, re.IGNORECASE)
                if sold_by_match:
                    seller_name = sold_by_match.group(1).strip()
                    if seller_name and len(seller_name) > 1:
                        seller_info['SoldBy'] = seller_name
                        seller_info['SellerName'] = seller_name
                        break
            
            # Extract dispatches from - improved regex
            dispatch_patterns = [
                r'Dispatches from:\s*([^,\n]+?)(?:\s*Sold by|\s*Returns|\s*$)',
                r'Dispatches from\s+([A-Za-z\s&\-\.]+?)(?:\s{2,}|\s*Sold by|\s*$)',
                r'Dispatches from:\s*([^,\n\r]+?)(?:\s*[\n\r]|$)'
            ]
            
            for pattern in dispatch_patterns:
                dispatches_match = re.search(pattern, full_text, re.IGNORECASE)
                if dispatches_match:
                    dispatch_from = dispatches_match.group(1).strip()
                    if dispatch_from and len(dispatch_from) > 1:
                        seller_info['DispatchesFrom'] = dispatch_from
                        break
        
        # Method 2: Try alternative selectors for seller info
        if not seller_info.get('SoldBy'):
            seller_selectors = [
                '#merchant-info a::text',
                '#soldByThirdParty a::text',
                'span:contains("Sold by")::text'
            ]
            
            for selector in seller_selectors:
                seller = response.css(selector).get()
                if seller:
                    clean_seller = seller.strip().replace('Sold by ', '').replace(':', '').strip()
                    if clean_seller and len(clean_seller) > 1:
                        seller_info['SoldBy'] = clean_seller
                        seller_info['SellerName'] = clean_seller
                        break
        
        # Check if fulfilled by Amazon
        if 'amazon' in response.text.lower():
            seller_info['FulfilledBy'] = 'Amazon'
        
        return seller_info
    
    def extract_prime_status(self, response):
        """Extract Prime status"""
        prime_indicators = [
            'prime',
            'Prime',
            'PRIME',
            'prime-logo',
            'prime-badge'
        ]
        
        page_text = response.text
        for indicator in prime_indicators:
            if indicator in page_text:
                return True
        return False
    
    def extract_available_quantity(self, response):
        """Extract available quantity - UPDATED WITH MULTIPLE PRODUCT LAYOUTS"""
        # Method 1: JBL-style product (availability section)
        quantity_selectors = [
            '#availability span::text',
            '#availability::text',
            '#availability-brief::text'
        ]
        
        for selector in quantity_selectors:
            quantity_text = response.css(selector).get()
            if quantity_text:
                clean_text = quantity_text.strip().lower()
                if 'in stock' in clean_text:
                    return 'In Stock'
                elif 'out of stock' in clean_text:
                    return 'Out of Stock'
                elif 'temporarily unavailable' in clean_text:
                    return 'Temporarily Unavailable'
                elif 'limited' in clean_text:
                    return 'Limited Stock'
        
        # Method 2: Anker-style product (check buybox for availability)
        # Since #availability section is missing, check buybox
        buybox_text = response.css('#buybox *::text').getall()
        if buybox_text:
            full_text = ' '.join(buybox_text).lower()
            if 'in stock' in full_text:
                return 'In Stock'
            elif 'out of stock' in full_text:
                return 'Out of Stock'
            elif 'temporarily unavailable' in full_text:
                return 'Temporarily Unavailable'
            elif 'add to basket' in full_text:
                # If "Add to Basket" button is present, assume in stock
                return 'In Stock'
        
        # Method 3: Check apex_desktop for availability
        apex_text = response.css('#apex_desktop *::text').getall()
        if apex_text:
            full_text = ' '.join(apex_text).lower()
            if 'in stock' in full_text:
                return 'In Stock'
            elif 'out of stock' in full_text:
                return 'Out of Stock'
        
        # Method 4: If quantity selector is present, assume in stock
        if response.css('select[name="quantity"]').get() or response.css('#quantity').get():
            return 'In Stock'
        
        return None
    
    def extract_listing_date(self, response):
        """Extract listing date - UPDATED WITH WORKING SELECTOR"""
        # Based on shell testing: ' 5 Oct. 2022 '
        date_text = response.css('#productDetails_detailBullets_sections1 tr:contains("Date First Available") td::text').get()
        if date_text:
            clean_date = date_text.strip()
            if clean_date and clean_date != ' ':
                return clean_date
        
        return None
    
    def extract_customer_service_provider(self, response):
        """Extract customer service provider - NOT AVAILABLE"""
        # Based on shell testing, this field is not available for most products
        return None
    
    def extract_seller_offers_count(self, response):
        """Extract seller offers count - NOT AVAILABLE"""
        # Based on shell testing, no additional offers found for this product
        return None
    
    def extract_buy_box_winner(self, response):
        """Extract buy box winner status - UPDATED WITH WORKING LOGIC"""
        # Based on shell testing, if there's a main seller displayed, they're the buy box winner
        buybox_text = response.css('#buybox *::text').getall()
        if buybox_text:
            full_text = ' '.join(buybox_text)
            if 'Sold by' in full_text:
                return True
        
        return False
    
    def closed(self, reason):
        """Called when spider closes - mark any remaining keywords as attempted"""
        if self.db_manager:
            self.logger.info(f"Spider closed with reason: {reason}")