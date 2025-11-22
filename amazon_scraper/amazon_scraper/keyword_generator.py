# amazon_scraper/keyword_generator.py

import logging
import time
import random
from typing import List, Dict, Set
from datetime import datetime
import config
from amazon_scraper.database import get_db_manager

class KeywordGenerator:
    """Generate and manage keywords for Amazon scraping"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.db_manager = get_db_manager()
        
    def generate_keywords_for_categories(self, categories: List[str] = None, domain: str = 'us') -> int:
        """Generate keywords for specified categories"""
        if not config.KEYWORD_GENERATION_ENABLED:
            self.logger.info("Keyword generation is disabled")
            return 0
        
        if categories is None:
            categories = config.PRODUCT_CATEGORIES
        
        total_generated = 0
        
        for category in categories:
            self.logger.info(f"Generating keywords for category: {category}")
            
            # Generate keywords multiple times for variety
            category_keywords = set()
            
            for attempt in range(config.GENERATION_PROMPTS_COUNT):
                try:
                    keywords = self._generate_keywords_for_category(category, domain)
                    category_keywords.update(keywords)
                    self.logger.debug(f"Generated {len(keywords)} keywords for {category} (attempt {attempt + 1})")
                    
                    # Add delay between API calls
                    if attempt < config.GENERATION_PROMPTS_COUNT - 1:
                        time.sleep(1)
                        
                except Exception as e:
                    self.logger.error(f"Error generating keywords for {category} (attempt {attempt + 1}): {e}")
                    continue
            
            # Prepare keyword documents for database
            keyword_docs = []
            for keyword in list(category_keywords)[:config.KEYWORDS_PER_CATEGORY]:
                # Check if keyword already exists
                if not self.db_manager.is_keyword_scraped(keyword, domain, category):
                    keyword_doc = {
                        'keyword': keyword.strip(),
                        'category': category,
                        'domain': domain,
                        'priority': self._calculate_keyword_priority(keyword, category),
                        'generated_by': 'openai'  # Will be 'placeholder' for now
                    }
                    keyword_docs.append(keyword_doc)
            
            # Bulk insert keywords
            if keyword_docs:
                inserted_count = self.db_manager.bulk_insert_keywords(keyword_docs)
                total_generated += inserted_count
                self.logger.info(f"Inserted {inserted_count} new keywords for category: {category}")
            else:
                self.logger.info(f"No new keywords to insert for category: {category}")
        
        self.logger.info(f"Total keywords generated: {total_generated}")
        return total_generated
    
    def _generate_keywords_for_category(self, category: str, domain: str) -> List[str]:
        """Generate keywords for a specific category"""
        # PLACEHOLDER IMPLEMENTATION - Replace with OpenAI API call
        return self._placeholder_keyword_generation(category, domain)
    
    def _placeholder_keyword_generation(self, category: str, domain: str) -> List[str]:
        """Placeholder keyword generation with hardcoded values"""
        # Hardcoded keyword sets for different categories
        keyword_templates = {
            'Electronics': [
                'wireless headphones', 'bluetooth speaker', 'smartphone case', 'laptop stand',
                'usb cable', 'wireless charger', 'gaming mouse', 'mechanical keyboard',
                'webcam', 'tablet', 'smart watch', 'power bank', 'bluetooth earbuds',
                'monitor', 'hdmi cable', 'wireless adapter'
            ],
            'Home & Kitchen': [
                'coffee machine', 'air fryer', 'blender', 'toaster', 'microwave',
                'pressure cooker', 'kitchen knife set', 'cutting board', 'mixing bowl',
                'coffee grinder', 'food processor', 'stand mixer', 'rice cooker',
                'slow cooker', 'electric kettle', 'can opener'
            ],
            'Sports & Outdoors': [
                'running shoes', 'yoga mat', 'dumbbell set', 'resistance bands',
                'treadmill', 'bicycle', 'camping tent', 'hiking backpack',
                'water bottle', 'fitness tracker', 'golf clubs', 'tennis racket',
                'basketball', 'soccer ball', 'swimming goggles', 'gym bag'
            ],
            'Health & Personal Care': [
                'electric toothbrush', 'hair dryer', 'face cream', 'shampoo',
                'body lotion', 'sunscreen', 'vitamins', 'protein powder',
                'massage gun', 'blood pressure monitor', 'thermometer',
                'first aid kit', 'hand sanitizer', 'face mask', 'hair straightener'
            ],
            'Clothing & Accessories': [
                'sneakers', 't-shirt', 'jeans', 'dress', 'jacket',
                'handbag', 'sunglasses', 'watch', 'belt', 'scarf',
                'hoodie', 'socks', 'underwear', 'shoes', 'backpack', 'wallet'
            ],
            'Books': [
                'fiction book', 'cookbook', 'self help book', 'biography',
                'mystery novel', 'romance novel', 'science book', 'history book',
                'children book', 'textbook', 'comic book', 'poetry book',
                'travel guide', 'art book', 'business book', 'psychology book'
            ],
            'Toys & Games': [
                'lego set', 'board game', 'puzzle', 'action figure',
                'doll', 'remote control car', 'video game', 'card game',
                'building blocks', 'stuffed animal', 'educational toy',
                'outdoor toy', 'craft kit', 'musical toy', 'science kit'
            ],
            'Automotive': [
                'car charger', 'phone mount', 'dash cam', 'car vacuum',
                'tire gauge', 'jumper cables', 'car cover', 'floor mats',
                'air freshener', 'car wax', 'motor oil', 'brake pads',
                'headlights', 'car battery', 'windshield wipers'
            ],
            'Beauty': [
                'makeup brush set', 'lipstick', 'foundation', 'mascara',
                'eyeshadow palette', 'nail polish', 'perfume', 'skincare set',
                'face serum', 'moisturizer', 'cleanser', 'hair mask',
                'nail file', 'makeup remover', 'concealer', 'blush'
            ],
            'Office Products': [
                'notebook', 'pen set', 'stapler', 'paper clips',
                'desk organizer', 'office chair', 'desk lamp', 'printer paper',
                'file folders', 'calculator', 'whiteboard', 'desk pad',
                'hole punch', 'tape dispenser', 'paper shredder', 'label maker'
            ]
        }
        
        # Get keywords for the category
        base_keywords = keyword_templates.get(category, [
            'wireless headphones', 'laptop', 'smartphone', 'gaming chair',
            'bluetooth speaker', 'coffee machine', 'running shoes', 'tablet'
        ])
        
        # Add some variation and randomness
        variations = []
        for keyword in base_keywords:
            variations.append(keyword)
            
            # Add brand variations (simulate different searches)
            if random.random() < 0.3:  # 30% chance
                brands = ['apple', 'samsung', 'sony', 'amazon', 'nike', 'adidas']
                brand = random.choice(brands)
                variations.append(f"{brand} {keyword}")
            
            # Add color/size variations
            if random.random() < 0.2:  # 20% chance
                modifiers = ['black', 'white', 'small', 'large', 'wireless', 'portable']
                modifier = random.choice(modifiers)
                variations.append(f"{modifier} {keyword}")
        
        # Randomly select keywords to return
        num_to_return = min(config.KEYWORDS_PER_CATEGORY, len(variations))
        selected_keywords = random.sample(variations, num_to_return)
        
        self.logger.debug(f"Generated {len(selected_keywords)} placeholder keywords for {category}")
        return selected_keywords
    
    def _openai_generate_keywords(self, category: str, domain: str) -> List[str]:
        """Generate keywords using OpenAI API (placeholder for now)"""
        # TODO: Implement OpenAI API integration
        # This will be implemented when you're ready to use the actual API
        
        self.logger.warning("OpenAI keyword generation not implemented yet, using placeholder")
        return self._placeholder_keyword_generation(category, domain)
    
    def _calculate_keyword_priority(self, keyword: str, category: str) -> int:
        """Calculate priority for keyword (1-10, higher is better)"""
        priority = 5  # Default priority
        
        # Higher priority for shorter, more specific keywords
        if len(keyword.split()) == 2:
            priority += 2
        elif len(keyword.split()) == 1:
            priority += 1
        
        # Higher priority for certain categories
        high_priority_categories = ['Electronics', 'Home & Kitchen']
        if category in high_priority_categories:
            priority += 1
        
        # Higher priority for trending keywords
        trending_words = ['wireless', 'smart', 'portable', 'gaming', 'bluetooth']
        if any(word in keyword.lower() for word in trending_words):
            priority += 1
        
        return min(priority, 10)  # Cap at 10
    
    def add_manual_keywords(self, keywords: List[str], category: str = 'Manual', 
                           domain: str = 'us', priority: int = 8) -> int:
        """Add manual keywords to database"""
        keyword_docs = []
        
        for keyword in keywords:
            if not self.db_manager.is_keyword_scraped(keyword, domain, category):
                keyword_doc = {
                    'keyword': keyword.strip(),
                    'category': category,
                    'domain': domain,
                    'priority': priority,
                    'generated_by': 'manual'
                }
                keyword_docs.append(keyword_doc)
        
        if keyword_docs:
            inserted_count = self.db_manager.bulk_insert_keywords(keyword_docs)
            self.logger.info(f"Added {inserted_count} manual keywords")
            return inserted_count
        
        return 0
    
    def get_keywords_for_scraping(self, limit: int = None, domain: str = 'us') -> List[str]:
        """Get keywords that need to be scraped"""
        keyword_docs = self.db_manager.get_unscraped_keywords(limit, domain)
        keywords = [doc['keyword'] for doc in keyword_docs]
        
        self.logger.info(f"Retrieved {len(keywords)} keywords for scraping")
        return keywords
    
    def cleanup_old_keywords(self, days_old: int = 90):
        """Clean up old unsuccessful keywords"""
        # This can be implemented to remove keywords that consistently fail
        pass

# Global keyword generator instance
keyword_generator = None

def get_keyword_generator() -> KeywordGenerator:
    """Get global keyword generator instance"""
    global keyword_generator
    if keyword_generator is None:
        keyword_generator = KeywordGenerator()
    return keyword_generator