# amazon_scraper/items.py

import scrapy
from scrapy import Item, Field

class AmazonProductItem(scrapy.Item):
    # Product identifiers
    ASIN = Field()
    Title = Field()
    ProductURL = Field()
    
    # Ratings and reviews
    StarRating = Field()
    NumberOfRatings = Field()
    
    # Pricing
    Price = Field()
    ShippingCost = Field()
    
    # Rankings
    BestSellerRank = Field()
    SalesSubRank = Field()
    SalesSubSubRank = Field()
    
    # Delivery information
    FastestDelivery = Field()
    DeliveryEstimateFastest = Field()
    DeliveryEstimateSlowest = Field()
    DeliveryDaysFastest = Field()
    DeliveryDaysSlowest = Field()
    FastestDeliveryDate = Field()
    SlowestDeliveryDate = Field()
    
    # Seller information
    SellerOffersCount = Field()
    DispatchesFrom = Field()
    SoldBy = Field()
    SellerName = Field()
    IsBuyBoxWinner = Field()
    FulfilledBy = Field()
    CustomerServiceProvider = Field()
    
    # Prime and availability
    IsPrime = Field()
    Prime = Field()
    AvailableQuantity = Field()
    
    # Product details
    Brand = Field()
    ListingDate = Field()
    
    # Scraping metadata
    ScrapedAt = Field()
    Keyword = Field()
    Domain = Field()
    PageNumber = Field()
    DeliveryDays = Field()