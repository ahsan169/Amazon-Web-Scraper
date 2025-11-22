# amazon_scraper/database.py

import logging
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import DuplicateKeyError, ConnectionFailure
import config

class DatabaseManager:
    """MongoDB database manager for Amazon scraper"""
    
    def __init__(self):
        self.client = None
        self.db = None
        self.logger = logging.getLogger(__name__)
        self._asin_cache = set()  # Cache for scraped ASINs
        self._keyword_cache = set()  # Cache for scraped keywords
        self.connect()
        self.setup_indexes()
        if config.PRELOAD_SCRAPED_ASINS:
            self.preload_caches()
    
    def connect(self):
        """Connect to MongoDB"""
        try:
            self.client = MongoClient(
                config.get_mongodb_url(),
                serverSelectionTimeoutMS=config.MONGODB_CONNECTION_TIMEOUT,
                socketTimeoutMS=config.MONGODB_SOCKET_TIMEOUT,
                maxPoolSize=config.MONGODB_MAX_POOL_SIZE
            )
            self.db = self.client[config.MONGODB_DATABASE]
            # Test connection
            self.client.server_info()
            self.logger.info(f"Connected to MongoDB: {config.MONGODB_DATABASE}")
        except ConnectionFailure as e:
            self.logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    def setup_indexes(self):
        """Create database indexes for performance"""
        if not config.USE_MONGODB_INDEXES:
            return
        
        try:
            # Product collection indexes
            products_collection = self.db[config.get_collection_name('products')]
            products_collection.create_index([('ASIN', ASCENDING), ('domain', ASCENDING)], unique=True)
            products_collection.create_index([('scraped_at', DESCENDING)])
            products_collection.create_index([('keyword', ASCENDING)])
            products_collection.create_index([('BestSellerRank', ASCENDING)])
            
            # Keywords collection indexes
            keywords_collection = self.db[config.get_collection_name('keywords')]
            keywords_collection.create_index([
                ('keyword', ASCENDING), 
                ('domain', ASCENDING), 
                ('category', ASCENDING)
            ], unique=True)
            keywords_collection.create_index([('is_scraped', ASCENDING)])
            keywords_collection.create_index([('priority', DESCENDING)])
            keywords_collection.create_index([('created_at', DESCENDING)])
            
            self.logger.info("Database indexes created successfully")
        except Exception as e:
            self.logger.error(f"Error creating indexes: {e}")
    
    def preload_caches(self):
        """Preload frequently accessed data into memory"""
        try:
            # Load scraped ASINs
            if config.PREVENT_DUPLICATE_PRODUCTS:
                cutoff_date = datetime.now() - timedelta(days=config.DUPLICATE_CHECK_TIMEFRAME_DAYS)
                products = self.db[config.get_collection_name('products')].find(
                    {'scraped_at': {'$gte': cutoff_date}},
                    {'ASIN': 1, 'domain': 1}
                )
                self._asin_cache = {f"{p['ASIN']}_{p.get('domain', 'us')}" for p in products}
                self.logger.info(f"Preloaded {len(self._asin_cache)} ASINs into cache")
            
            # Load scraped keywords
            if config.PREVENT_DUPLICATE_KEYWORDS:
                keywords = self.db[config.get_collection_name('keywords')].find(
                    {'is_scraped': True},
                    {'keyword': 1, 'domain': 1, 'category': 1}
                )
                self._keyword_cache = {
                    f"{k['keyword']}_{k.get('domain', 'us')}_{k.get('category', '')}" 
                    for k in keywords
                }
                self.logger.info(f"Preloaded {len(self._keyword_cache)} keywords into cache")
                
        except Exception as e:
            self.logger.error(f"Error preloading caches: {e}")
    
    def is_product_scraped(self, asin: str, domain: str = 'us') -> bool:
        """Check if product is already scraped (fast cache lookup)"""
        if not config.PREVENT_DUPLICATE_PRODUCTS:
            return False
        
        cache_key = f"{asin}_{domain}"
        return cache_key in self._asin_cache
    
    def is_keyword_scraped(self, keyword: str, domain: str = 'us', category: str = '') -> bool:
        """Check if keyword is already scraped (fast cache lookup)"""
        if not config.PREVENT_DUPLICATE_KEYWORDS:
            return False
        
        cache_key = f"{keyword}_{domain}_{category}"
        return cache_key in self._keyword_cache
    
    def insert_product(self, product_data: Dict) -> bool:
        """Insert product into database"""
        try:
            # Add metadata
            product_data['scraped_at'] = datetime.now()
            product_data['updated_at'] = datetime.now()
            product_data['scrape_count'] = 1
            
            collection = self.db[config.get_collection_name('products')]
            
            if config.PRODUCT_UPDATE_EXISTING:
                # Upsert: update if exists, insert if new
                result = collection.replace_one(
                    {
                        'ASIN': product_data['ASIN'],
                        'domain': product_data.get('domain', 'us')
                    },
                    product_data,
                    upsert=True
                )
                
                # Update cache
                cache_key = f"{product_data['ASIN']}_{product_data.get('domain', 'us')}"
                self._asin_cache.add(cache_key)
                
                return True
            else:
                # Insert only if not exists
                collection.insert_one(product_data)
                
                # Update cache
                cache_key = f"{product_data['ASIN']}_{product_data.get('domain', 'us')}"
                self._asin_cache.add(cache_key)
                
                return True
                
        except DuplicateKeyError:
            # Product already exists
            return False
        except Exception as e:
            self.logger.error(f"Error inserting product {product_data.get('ASIN')}: {e}")
            return False
    
    def bulk_insert_products(self, products: List[Dict]) -> int:
        """Bulk insert products for better performance"""
        if not products:
            return 0
        
        try:
            # Add metadata to all products
            now = datetime.now()
            for product in products:
                product['scraped_at'] = now
                product['updated_at'] = now
                product['scrape_count'] = 1
            
            collection = self.db[config.get_collection_name('products')]
            
            if config.PRODUCT_UPDATE_EXISTING:
                # Use replace_one for each product individually (more reliable)
                inserted_count = 0
                for product in products:
                    try:
                        result = collection.replace_one(
                            {
                                'ASIN': product['ASIN'],
                                'domain': product.get('domain', 'us')
                            },
                            product,
                            upsert=True
                        )
                        if result.upserted_id or result.modified_count > 0:
                            inserted_count += 1
                    except Exception as e:
                        self.logger.error(f"Error inserting product {product.get('ASIN')}: {e}")
                        continue
            else:
                # Simple bulk insert
                try:
                    result = collection.insert_many(products, ordered=False)
                    inserted_count = len(result.inserted_ids)
                except Exception as e:
                    self.logger.error(f"Bulk insert failed, trying individual inserts: {e}")
                    # Fallback to individual inserts
                    inserted_count = 0
                    for product in products:
                        try:
                            collection.insert_one(product)
                            inserted_count += 1
                        except Exception:
                            continue
            
            # Update cache
            for product in products:
                cache_key = f"{product['ASIN']}_{product.get('domain', 'us')}"
                self._asin_cache.add(cache_key)
            
            self.logger.info(f"Successfully inserted {inserted_count} products")
            return inserted_count
            
        except Exception as e:
            self.logger.error(f"Error bulk inserting products: {e}")
            return 0
    
    def insert_keyword(self, keyword_data: Dict) -> bool:
        """Insert keyword into database"""
        try:
            # Add metadata
            keyword_data['created_at'] = datetime.now()
            keyword_data['is_scraped'] = False
            keyword_data['scraping_attempts'] = 0
            keyword_data['success_count'] = 0
            keyword_data['error_count'] = 0
            keyword_data['products_found'] = 0
            
            collection = self.db[config.get_collection_name('keywords')]
            collection.insert_one(keyword_data)
            
            self.logger.debug(f"Inserted keyword: {keyword_data['keyword']}")
            return True
            
        except DuplicateKeyError:
            self.logger.debug(f"Keyword already exists: {keyword_data['keyword']}")
            return False
        except Exception as e:
            self.logger.error(f"Error inserting keyword {keyword_data['keyword']}: {e}")
            return False
    
    def bulk_insert_keywords(self, keywords: List[Dict]) -> int:
        """Bulk insert keywords with duplicate handling"""
        if not keywords:
            return 0
        
        try:
            # Add metadata
            now = datetime.now()
            for keyword in keywords:
                keyword['created_at'] = now
                keyword['is_scraped'] = False
                keyword['scraping_attempts'] = 0
                keyword['success_count'] = 0
                keyword['error_count'] = 0
                keyword['products_found'] = 0
            
            collection = self.db[config.get_collection_name('keywords')]
            
            # Method 1: Try bulk insert with ordered=False to continue on duplicates
            try:
                result = collection.insert_many(keywords, ordered=False)
                inserted_count = len(result.inserted_ids)
                self.logger.info(f"Bulk inserted {inserted_count} keywords")
                return inserted_count
            except Exception as bulk_error:
                # If bulk insert fails due to duplicates, insert individually
                self.logger.warning(f"Bulk insert failed, trying individual inserts: {bulk_error}")
                
                inserted_count = 0
                for keyword_data in keywords:
                    try:
                        collection.insert_one(keyword_data)
                        inserted_count += 1
                        self.logger.debug(f"Inserted keyword: {keyword_data['keyword']}")
                    except Exception as e:
                        if 'duplicate key error' in str(e).lower() or '11000' in str(e):
                            self.logger.debug(f"Keyword already exists: {keyword_data['keyword']}")
                        else:
                            self.logger.error(f"Error inserting keyword {keyword_data['keyword']}: {e}")
                        continue
                
                self.logger.info(f"Individually inserted {inserted_count} new keywords")
                return inserted_count
                
        except Exception as e:
            self.logger.error(f"Error bulk inserting keywords: {e}")
            return 0

    def get_unscraped_keywords(self, limit: int = None, domain: str = 'us') -> List[Dict]:
        """Get unscraped keywords from database"""
        try:
            collection = self.db[config.get_collection_name('keywords')]
            
            query = {
                'is_scraped': False,
                'domain': domain
            }
            
            # Limit scraping attempts
            max_attempts = 3
            query['scraping_attempts'] = {'$lt': max_attempts}
            
            cursor = collection.find(query).sort([
                ('priority', DESCENDING),
                ('created_at', ASCENDING)
            ])
            
            if limit:
                cursor = cursor.limit(limit)
            
            keywords = list(cursor)
            self.logger.info(f"Found {len(keywords)} unscraped keywords for domain {domain}")
            return keywords
            
        except Exception as e:
            self.logger.error(f"Error fetching unscraped keywords: {e}")
            return []
    
    def mark_keyword_scraped(self, keyword: str, domain: str, category: str, products_found: int = 0):
        """Mark keyword as scraped"""
        try:
            collection = self.db[config.get_collection_name('keywords')]
            
            # First, check if the keyword document exists
            query = {
                'keyword': keyword,
                'domain': domain,
                'category': category
            }
            
            existing_doc = collection.find_one(query)
            if not existing_doc:
                self.logger.warning(f"No keyword document found for: keyword='{keyword}', domain='{domain}', category='{category}'")
                
                # Try to find with just keyword and domain
                partial_query = {'keyword': keyword, 'domain': domain}
                partial_doc = collection.find_one(partial_query)
                if partial_doc:
                    self.logger.warning(f"Found keyword with different category: {partial_doc}")
                else:
                    self.logger.warning(f"No keyword document found even with partial query: {partial_query}")
                    
                    # Check if keyword exists with any domain/category
                    any_keyword = collection.find_one({'keyword': keyword})
                    if any_keyword:
                        self.logger.warning(f"Keyword exists but with different domain/category: {any_keyword}")
                    else:
                        self.logger.error(f"Keyword '{keyword}' does not exist in database at all!")
                return False
            
            self.logger.info(f"Found keyword document to update: {existing_doc}")
            
            result = collection.update_one(
                query,
                {
                    '$set': {
                        'is_scraped': True,
                        'scraped_at': datetime.now(),
                        'products_found': products_found
                    },
                    '$inc': {
                        'success_count': 1
                    }
                }
            )
            
            if result.modified_count > 0:
                # Update cache
                cache_key = f"{keyword}_{domain}_{category}"
                self._keyword_cache.add(cache_key)
                self.logger.info(f"Successfully marked keyword as scraped: {keyword}")
                return True
            else:
                self.logger.error(f"Update query matched document but modified_count was 0 for keyword: {keyword}")
                return False
            
        except Exception as e:
            self.logger.error(f"Error marking keyword as scraped: {e}")
        
        return False
    
    def increment_keyword_attempts(self, keyword: str, domain: str, category: str):
        """Increment scraping attempts for keyword"""
        try:
            collection = self.db[config.get_collection_name('keywords')]
            collection.update_one(
                {
                    'keyword': keyword,
                    'domain': domain,
                    'category': category
                },
                {
                    '$inc': {'scraping_attempts': 1},
                    '$set': {'last_attempt_at': datetime.now()}
                }
            )
        except Exception as e:
            self.logger.error(f"Error incrementing keyword attempts: {e}")
    
    def get_scraping_stats(self) -> Dict:
        """Get scraping statistics"""
        try:
            products_collection = self.db[config.get_collection_name('products')]
            keywords_collection = self.db[config.get_collection_name('keywords')]
            
            stats = {
                'total_products': products_collection.count_documents({}),
                'total_keywords': keywords_collection.count_documents({}),
                'scraped_keywords': keywords_collection.count_documents({'is_scraped': True}),
                'pending_keywords': keywords_collection.count_documents({'is_scraped': False}),
                'products_today': products_collection.count_documents({
                    'scraped_at': {'$gte': datetime.now().replace(hour=0, minute=0, second=0)}
                }),
                'cache_size': {
                    'asins': len(self._asin_cache),
                    'keywords': len(self._keyword_cache)
                }
            }
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error getting scraping stats: {e}")
            return {}
    
    def close(self):
        """Close database connection"""
        if self.client:
            self.client.close()
            self.logger.info("Database connection closed")

# Global database manager instance
db_manager = None

def get_db_manager() -> DatabaseManager:
    """Get global database manager instance"""
    global db_manager
    if db_manager is None:
        db_manager = DatabaseManager()
    return db_manager

def close_db_connection():
    """Close global database connection"""
    global db_manager
    if db_manager:
        db_manager.close()
        db_manager = None