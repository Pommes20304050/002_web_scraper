"""Web Scraper — scrape, crawl and export web pages from the command line."""
from .models import ScrapedPage, ScrapeResult
from .scraper import ScraperConfig, WebScraper

__all__ = ["WebScraper", "ScraperConfig", "ScrapedPage", "ScrapeResult"]
__version__ = "2.0.0"
