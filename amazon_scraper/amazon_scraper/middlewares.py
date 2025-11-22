# amazon_scraper/middlewares.py

from scrapy import signals
from scrapy.downloadermiddlewares.useragent import UserAgentMiddleware
import random
import logging
import config
import time
import requests

class AmazonScraperSpiderMiddleware:
    """Spider middleware for Amazon scraper"""
    
    @classmethod
    def from_crawler(cls, crawler):
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        return None

    def process_spider_output(self, response, result, spider):
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        logging.error(f"Spider exception: {exception}")
        pass

    def process_start_requests(self, start_requests, spider):
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


class AmazonScraperDownloaderMiddleware:
    """Downloader middleware for Amazon scraper"""
    
    @classmethod
    def from_crawler(cls, crawler):
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # additional headers from config
        for header, value in config.DEFAULT_HEADERS.items():
            request.headers[header] = value
        
        return None

    def process_response(self, request, response, spider):
        # Check if we're being blocked
        if response.status == 503:
            spider.logger.warning(f"503 Service Unavailable for {request.url}")
            
        if "robot check" in response.text.lower() or "captcha" in response.text.lower():
            spider.logger.warning(f"CAPTCHA detected for {request.url}")
            if config.LOG_BLOCKED_REQUESTS:
                user_agent = request.headers.get('User-Agent', b'').decode('utf-8')
                spider.logger.warning(f"Blocked User-Agent: {user_agent[:50]}...")
            
        return response

    def process_exception(self, request, exception, spider):
        spider.logger.error(f"Download exception for {request.url}: {exception}")
        pass

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


class DynamicUserAgentMiddleware(UserAgentMiddleware):
    """Dynamic User Agent middleware with multiple sources"""
    
    def __init__(self, user_agent=''):
        self.user_agent = user_agent
        self.logger = logging.getLogger(__name__)
        self.user_agent_list = []
        self.last_refresh = 0
        self.strategy = config.USER_AGENT_STRATEGY
        
        # Initialize user agent list
        self.refresh_user_agents()

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            user_agent=crawler.settings.get('USER_AGENT')
        )

    def refresh_user_agents(self):
        """Refresh user agent list from configured source"""
        current_time = time.time()
        
        # Check if refresh is needed
        if (current_time - self.last_refresh) < config.USER_AGENT_REFRESH_INTERVAL and self.user_agent_list:
            return
        
        new_agents = []
        
        if self.strategy == 'scrapeops':
            new_agents = self._fetch_scrapeops_user_agents()
        elif self.strategy == 'fake_useragent':
            new_agents = self._fetch_fake_useragent()
        elif self.strategy == 'dynamic':
            # Try ScrapeOps first, fallback to fake_useragent
            new_agents = self._fetch_scrapeops_user_agents()
            if not new_agents:
                new_agents = self._fetch_fake_useragent()
        
        # Use fallback user agents if no dynamic source worked
        if not new_agents:
            self.logger.warning("Failed to fetch dynamic user agents, using fallback list")
            new_agents = config.FALLBACK_USER_AGENTS
        
        self.user_agent_list = new_agents[:config.USER_AGENT_CACHE_SIZE]
        self.last_refresh = current_time
        
        self.logger.info(f"Refreshed user agents: {len(self.user_agent_list)} agents loaded using '{self.strategy}' strategy")

    def _fetch_scrapeops_user_agents(self):
        """Fetch user agents from ScrapeOps API"""
        try:
            if config.SCRAPEOPS_API_KEY == 'YOUR_SCRAPEOPS_API_KEY_HERE':
                self.logger.warning("ScrapeOps API key not configured")
                return []
            
            params = config.SCRAPEOPS_USER_AGENT_PARAMS.copy()
            params['api_key'] = config.SCRAPEOPS_API_KEY
            
            response = requests.get(
                config.SCRAPEOPS_USER_AGENT_ENDPOINT,
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                user_agents = data.get('result', [])
                if user_agents:
                    self.logger.info(f"Fetched {len(user_agents)} user agents from ScrapeOps")
                    return user_agents
                else:
                    self.logger.warning("ScrapeOps returned empty user agent list")
            else:
                self.logger.warning(f"ScrapeOps API error: {response.status_code}")
                
        except Exception as e:
            self.logger.error(f"Error fetching user agents from ScrapeOps: {e}")
        
        return []

    def _fetch_fake_useragent(self):
        """Fetch user agents using fake-useragent library"""
        try:
            from fake_useragent import UserAgent
            ua = UserAgent()
            
            # Generate multiple user agents
            agents = []
            browsers = ['chrome', 'firefox', 'safari', 'edge']
            
            for _ in range(config.USER_AGENT_CACHE_SIZE):
                for browser in browsers:
                    try:
                        agent = getattr(ua, browser)
                        if agent not in agents:
                            agents.append(agent)
                        if len(agents) >= config.USER_AGENT_CACHE_SIZE:
                            break
                    except:
                        continue
                if len(agents) >= config.USER_AGENT_CACHE_SIZE:
                    break
            
            if agents:
                self.logger.info(f"Generated {len(agents)} user agents using fake-useragent")
                return agents
                
        except ImportError:
            self.logger.warning("fake-useragent library not installed. Install with: pip install fake-useragent")
        except Exception as e:
            self.logger.error(f"Error generating user agents with fake-useragent: {e}")
        
        return []

    def process_request(self, request, spider):
        # Refresh user agents if needed
        self.refresh_user_agents()
        
        # Select random user agent
        if self.user_agent_list:
            ua = random.choice(self.user_agent_list)
            request.headers['User-Agent'] = ua
            
            if config.LOG_USER_AGENT_ROTATION:
                spider.logger.debug(f"Using User-Agent: {ua[:50]}...")
        else:
            spider.logger.error("No user agents available!")
        
        return None

    def get_stats(self):
        """Get user agent statistics"""
        return {
            'total_agents': len(self.user_agent_list),
            'strategy': self.strategy,
            'last_refresh': self.last_refresh,
            'refresh_interval': config.USER_AGENT_REFRESH_INTERVAL
        }


# Alias for backward compatibility
RotateUserAgentMiddleware = DynamicUserAgentMiddleware