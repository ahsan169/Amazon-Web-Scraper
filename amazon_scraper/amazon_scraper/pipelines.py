# amazon_scraper/pipelines.py

import json
import logging
from datetime import datetime
from itemadapter import ItemAdapter
from amazon_scraper.database import get_db_manager
import config
from scrapy.exceptions import DropItem

class AmazonScraperPipeline:
    """Pipeline for processing Amazon product items"""
    
    def __init__(self):
        self.items_processed = 0
        self.items_dropped = 0
        
    def open_spider(self, spider):
        """Initialize pipeline when spider opens"""
        spider.logger.info("Amazon scraper pipeline opened")
        
    def close_spider(self, spider):
        """Clean up when spider closes"""
        spider.logger.info(f"Pipeline processed {self.items_processed} items, dropped {self.items_dropped} items")
        
    def process_item(self, item, spider):
        """Process each item"""
        adapter = ItemAdapter(item)
        
        # Validate required fields
        if not adapter.get('ASIN'):
            spider.logger.warning(f"Item dropped - missing ASIN: {adapter.get('Title', 'Unknown')}")
            self.items_dropped += 1
            return item
            
        # Clean and validate data
        self.clean_item_data(adapter, spider)
        
        # Log successful processing
        self.items_processed += 1
        spider.logger.info(f"Processed item: {adapter.get('Title', 'Unknown')} (ASIN: {adapter.get('ASIN')})")
        
        return item
    
    def clean_item_data(self, adapter, spider):
        """Clean and validate item data"""
        
        # Clean title
        title = adapter.get('Title')
        if title:
            adapter['Title'] = title.strip()
        
        # Clean price
        price = adapter.get('Price')
        if price:
            try:
                adapter['Price'] = float(price)
            except (ValueError, TypeError):
                adapter['Price'] = None
        
        # Clean star rating
        star_rating = adapter.get('StarRating')
        if star_rating:
            try:
                rating = float(star_rating)
                if 0 <= rating <= 5:
                    adapter['StarRating'] = rating
                else:
                    adapter['StarRating'] = None
            except (ValueError, TypeError):
                adapter['StarRating'] = None
        
        # Clean number of ratings
        num_ratings = adapter.get('NumberOfRatings')
        if num_ratings:
            try:
                adapter['NumberOfRatings'] = int(num_ratings)
            except (ValueError, TypeError):
                adapter['NumberOfRatings'] = None
        
        # Clean brand
        brand = adapter.get('Brand')
        if brand:
            adapter['Brand'] = brand.strip()
        
        # Set default values for missing fields
        self.set_default_values(adapter)
    
    def set_default_values(self, adapter):
        """Set default values for missing fields"""
        
        # Set default values
        defaults = {
            'SalesSubRank': None,
            'SalesSubSubRank': None,
            'ShippingCost': None,
            'SellerOffersCount': None,
            'DispatchesFrom': None,
            'IsBuyBoxWinner': None,
            'CustomerServiceProvider': None,
            'ListingDate': None,
            'DeliveryEstimateFastest': None,
            'DeliveryEstimateSlowest': None,
            'DeliveryDaysSlowest': None,
            'FastestDeliveryDate': None,
            'SlowestDeliveryDate': None,
            'DeliveryDays': None,
        }
        
        for field, default_value in defaults.items():
            if not adapter.get(field):
                adapter[field] = default_value


class DuplicatesPipeline:
    """Pipeline to filter out duplicate items"""
    
    def __init__(self):
        self.asins_seen = set()
        
    def process_item(self, item, spider):
        # Safety check for None items
        if item is None:
            spider.logger.warning("DuplicatesPipeline received None item")
            raise DropItem("Item is None")
            
        adapter = ItemAdapter(item)
        asin = adapter.get('ASIN')
        
        if not asin:
            spider.logger.warning("Item missing ASIN, skipping duplicate check")
            return item
        
        if asin in self.asins_seen:
            spider.logger.info(f"Duplicate item found: {asin}")
            raise DropItem(f"Duplicate item: {asin}")
        else:
            self.asins_seen.add(asin)
            return item
        
class JsonWriterPipeline:
    """Pipeline to write items to JSON file"""
    
    def __init__(self):
        self.file = None
        self.items = []
        
    def open_spider(self, spider):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"amazon_products_{timestamp}.json"
        self.file = open(filename, 'w', encoding='utf-8')
        spider.logger.info(f"Opened JSON file: {filename}")
        
    def close_spider(self, spider):
        # Write all items to file
        json.dump(self.items, self.file, indent=2, ensure_ascii=False)
        self.file.close()
        spider.logger.info(f"Closed JSON file with {len(self.items)} items")
        
    def process_item(self, item, spider):
        self.items.append(ItemAdapter(item).asdict())
        return item


class ValidationPipeline:
    """Enhanced pipeline to validate item data"""
    
    def __init__(self):
        self.validation_errors = 0
        
    def open_spider(self, spider):
        self.validation_errors = 0
        
    def close_spider(self, spider):
        if self.validation_errors > 0:
            spider.logger.warning(f"Total validation errors: {self.validation_errors}")
    
    def process_item(self, item, spider):
        # Safety check - ValidationPipeline
        if item is None:
            spider.logger.error("ValidationPipeline received None item - this shouldn't happen")
            raise DropItem("ValidationPipeline received None item")
        
        adapter = ItemAdapter(item)
        asin = adapter.get('ASIN')
        
        # Validate ASIN format
        if asin and len(asin) != 10:
            spider.logger.warning(f"Invalid ASIN format: {asin}")
            self.validation_errors += 1
        
        # Validate price using config
        price = adapter.get('Price')
        if price:
            if price < config.MIN_PRICE or price > config.MAX_PRICE:
                spider.logger.warning(f"Suspicious price: {price} for ASIN: {asin}")
                self.validation_errors += 1
        
        # Validate star rating using config
        star_rating = adapter.get('StarRating')
        if star_rating:
            if star_rating < config.MIN_STAR_RATING or star_rating > config.MAX_STAR_RATING:
                spider.logger.warning(f"Invalid star rating: {star_rating} for ASIN: {asin}")
                self.validation_errors += 1
        
        # Validate number of ratings using config
        num_ratings = adapter.get('NumberOfRatings')
        if num_ratings and num_ratings < config.MIN_NUM_RATINGS:
            spider.logger.warning(f"Invalid number of ratings: {num_ratings} for ASIN: {asin}")
            self.validation_errors += 1
        
        # Validate title length
        title = adapter.get('Title')
        if title and len(title) > config.MAX_TITLE_LENGTH:
            spider.logger.warning(f"Title too long ({len(title)} chars) for ASIN: {asin}")
            self.validation_errors += 1
        
        # Filter invalid products if configured
        if config.FILTER_INVALID_PRICES and price and (price < config.MIN_PRICE or price > config.MAX_PRICE):
            raise DropItem(f"Invalid price {price} for ASIN: {asin}")
        
        return item
    

class MongoDBPipeline:
    """Pipeline to store scraped data in MongoDB"""
    
    def __init__(self):
        self.db_manager = None
        self.logger = logging.getLogger(__name__)
        self.products_buffer = []
        self.buffer_size = config.MONGODB_BATCH_SIZE
        
    def open_spider(self, spider):
        """Initialize database connection when spider opens"""
        if config.MONGODB_ENABLED:
            self.db_manager = get_db_manager()
            self.logger.info("MongoDB pipeline initialized")
        else:
            self.logger.info("MongoDB pipeline disabled")
    
    def close_spider(self, spider):
        """Flush remaining items and close connection when spider closes"""
        if self.db_manager and self.products_buffer:
            # Insert remaining items in buffer
            self._flush_buffer()
        
        # Print statistics
        if self.db_manager:
            stats = self.db_manager.get_scraping_stats()
            spider.logger.info(f"Scraping completed. Database stats: {stats}")
    
    def process_item(self, item, spider):
        """Process each scraped item"""
        if not self.db_manager:
            return item
        
        try:
            # Convert item to dict
            product_data = dict(item)
            
            # Check for duplicates before processing
            asin = product_data.get('ASIN')
            domain = product_data.get('Domain', 'us')
            
            if asin and self.db_manager.is_product_scraped(asin, domain):
                spider.logger.debug(f"Skipping duplicate product: {asin}")
                return item
            
            # Add to buffer for batch processing
            self.products_buffer.append(product_data)
            
            # Flush buffer when it reaches batch size
            if len(self.products_buffer) >= self.buffer_size:
                self._flush_buffer()
            
            return item
            
        except Exception as e:
            self.logger.error(f"Error processing item in MongoDB pipeline: {e}")
            return item
    
    def _flush_buffer(self):
        """Flush products buffer to database"""
        if not self.products_buffer:
            return
        
        try:
            inserted_count = self.db_manager.bulk_insert_products(self.products_buffer)
            self.logger.info(f"Inserted {inserted_count} products to MongoDB")
            self.products_buffer = []  # Clear buffer
            
        except Exception as e:
            self.logger.error(f"Error flushing products buffer: {e}")


class DatabaseDuplicatesPipeline:
    """Enhanced duplicate filter pipeline using database"""
    
    def __init__(self):
        self.db_manager = None
        self.logger = logging.getLogger(__name__)
        self.filtered_count = 0
        self.memory_asins = set()  # Fallback to memory if DB disabled
    
    def open_spider(self, spider):
        if config.MONGODB_ENABLED and config.PREVENT_DUPLICATE_PRODUCTS:
            self.db_manager = get_db_manager()
            self.logger.info("Database duplicate filter pipeline initialized")
        else:
            self.logger.info("Using memory-based duplicate filtering")
    
    def close_spider(self, spider):
        if self.filtered_count > 0:
            spider.logger.info(f"Filtered {self.filtered_count} duplicate products")
    
    def process_item(self, item, spider):
        # Safety check - DatabaseDuplicatesPipeline
        if item is None:
            spider.logger.error("DatabaseDuplicatesPipeline received None item")
            raise DropItem("DatabaseDuplicatesPipeline received None item")
        
        try:
            adapter = ItemAdapter(item)
            asin = adapter.get('ASIN')
            domain = adapter.get('Domain', 'us')
            
            if not asin:
                spider.logger.warning("Item missing ASIN in DatabaseDuplicatesPipeline")
                return item
            
            # Check duplicates using database if enabled
            if self.db_manager:
                if self.db_manager.is_product_scraped(asin, domain):
                    self.filtered_count += 1
                    spider.logger.debug(f"Dropping duplicate product from DB: {asin}")
                    raise DropItem(f"Duplicate product in database: {asin}")
            else:
                # Fallback to memory-based duplicate checking
                asin_key = f"{asin}_{domain}"
                if asin_key in self.memory_asins:
                    self.filtered_count += 1
                    spider.logger.debug(f"Dropping duplicate product from memory: {asin}")
                    raise DropItem(f"Duplicate product in memory: {asin}")
                else:
                    self.memory_asins.add(asin_key)
            
            # ✅ CRITICAL: Always return the item if not dropped
            return item
            
        except DropItem:
            # Re-raise DropItem exceptions
            raise
        except Exception as e:
            # Log any unexpected errors but don't return None
            spider.logger.error(f"Error in DatabaseDuplicatesPipeline: {e}")
            return item  # ✅ Return item even if there's an error