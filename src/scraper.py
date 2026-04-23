"""Core scraper engine — BFS crawler with depth, patterns, robots.txt."""
from __future__ import annotations

import logging
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Optional

from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
)

from .models import ScrapedPage, ScrapeResult
from .utils import (
    RobotsCache,
    fetch_page,
    get_headers,
    match_any,
    parse_page,
    rate_limit,
    same_domain,
)

log = logging.getLogger("web_scraper")
console = Console()


@dataclass
class ScraperConfig:
    """Tunable parameters for the crawler."""

    max_pages: int = 10
    max_depth: int = 3
    delay: float = 1.0
    jitter: float = 0.0
    timeout: int = 10
    max_retries: int = 2
    stay_on_domain: bool = True
    respect_robots: bool = True
    rotate_user_agent: bool = False
    user_agent: Optional[str] = None
    include_patterns: list[str] = field(default_factory=list)
    exclude_patterns: list[str] = field(default_factory=list)
    verbose: bool = False


class WebScraper:
    """BFS web crawler with rate limiting, retries and robots.txt support."""

    def __init__(self, config: Optional[ScraperConfig] = None, **overrides):
        if config is None:
            config = ScraperConfig()
        # Allow lightweight kwargs-style construction (back-compat + ergonomics).
        for key, value in overrides.items():
            if hasattr(config, key):
                setattr(config, key, value)
        self.config = config
        self.headers = get_headers(
            config.user_agent, rotate=config.rotate_user_agent
        )
        self._robots: Optional[RobotsCache] = (
            RobotsCache(user_agent=self.headers["User-Agent"])
            if config.respect_robots
            else None
        )

    # ── Public API ─────────────────────────────────────────────────────────

    def scrape_single(self, url: str) -> Optional[ScrapedPage]:
        """Fetch + parse one URL. Returns None on failure."""
        if self._robots and not self._robots.allowed(url):
            log.info("Blocked by robots.txt: %s", url)
            return None

        start = time.perf_counter()
        resp = fetch_page(
            url,
            timeout=self.config.timeout,
            headers=self._request_headers(),
            max_retries=self.config.max_retries,
        )
        if resp is None:
            return None

        parsed = parse_page(url, resp.text)
        return ScrapedPage(
            url=url,
            title=parsed["title"],
            status_code=resp.status_code,
            links=parsed["links"],
            images=parsed["images"],
            headings=parsed["headings"],
            paragraphs=parsed["paragraphs"],
            meta_description=parsed["meta_description"],
            og_title=parsed["og_title"],
            og_description=parsed["og_description"],
            og_image=parsed["og_image"],
            og_type=parsed["og_type"],
            twitter_card=parsed["twitter_card"],
            keywords=parsed["keywords"],
            author=parsed["author"],
            language=parsed["language"],
            canonical_url=parsed["canonical_url"],
            favicon=parsed["favicon"],
            word_count=parsed["word_count"],
            content_length=len(resp.content),
            elapsed_ms=int((time.perf_counter() - start) * 1000),
            jsonld=parsed["jsonld"],
        )

    def scrape(self, start_url: str, seed_urls: Optional[list[str]] = None) -> ScrapeResult:
        """Crawl starting from `start_url` (BFS). Optional additional seeds."""
        cfg = self.config
        result = ScrapeResult(start_url=start_url)

        visited: set[str] = set()
        queue: deque[tuple[str, int]] = deque()
        queue.append((start_url, 0))
        for extra in seed_urls or []:
            queue.append((extra, 0))

        with self._progress() as progress:
            task = progress.add_task("Scraping...", total=cfg.max_pages)

            while queue and len(result.pages) < cfg.max_pages:
                url, depth = queue.popleft()
                if url in visited:
                    continue
                visited.add(url)

                if not self._should_visit(url, start_url):
                    continue

                if self._robots and not self._robots.allowed(url):
                    result.add_error(url, "Blocked by robots.txt")
                    if cfg.verbose:
                        console.print(f"  [yellow]robots.txt:[/yellow] {url}")
                    continue

                progress.update(
                    task,
                    description=f"[cyan]{url[:70]}[/cyan]",
                )

                if cfg.verbose:
                    console.print(f"  [dim]→ d{depth} {url}[/dim]")

                rate_limit(cfg.delay, cfg.jitter)

                start = time.perf_counter()
                resp = fetch_page(
                    url,
                    timeout=cfg.timeout,
                    headers=self._request_headers(),
                    max_retries=cfg.max_retries,
                )
                if resp is None:
                    result.add_error(url, "Fetch failed")
                    continue

                content_type = resp.headers.get("Content-Type", "")
                if "text/html" not in content_type:
                    result.add_error(url, f"Skipped non-HTML ({content_type.split(';')[0] or 'unknown'})")
                    continue

                parsed = parse_page(url, resp.text)
                page = ScrapedPage(
                    url=url,
                    title=parsed["title"],
                    status_code=resp.status_code,
                    links=parsed["links"],
                    images=parsed["images"],
                    headings=parsed["headings"],
                    paragraphs=parsed["paragraphs"],
                    meta_description=parsed["meta_description"],
                    og_title=parsed["og_title"],
                    og_description=parsed["og_description"],
                    og_image=parsed["og_image"],
                    og_type=parsed["og_type"],
                    twitter_card=parsed["twitter_card"],
                    keywords=parsed["keywords"],
                    author=parsed["author"],
                    language=parsed["language"],
                    canonical_url=parsed["canonical_url"],
                    favicon=parsed["favicon"],
                    word_count=parsed["word_count"],
                    content_length=len(resp.content),
                    elapsed_ms=int((time.perf_counter() - start) * 1000),
                    depth=depth,
                    jsonld=parsed["jsonld"],
                )
                result.add_page(page)
                progress.update(task, advance=1)

                if depth + 1 <= cfg.max_depth:
                    for link in parsed["links"]:
                        if link not in visited:
                            queue.append((link, depth + 1))

        result.finish()
        return result

    # ── Internals ──────────────────────────────────────────────────────────

    def _request_headers(self) -> dict:
        if self.config.rotate_user_agent:
            return get_headers(rotate=True)
        return self.headers

    def _should_visit(self, url: str, start_url: str) -> bool:
        cfg = self.config
        if cfg.stay_on_domain and not same_domain(start_url, url):
            return False
        if cfg.include_patterns and not match_any(cfg.include_patterns, url):
            return False
        if cfg.exclude_patterns and match_any(cfg.exclude_patterns, url):
            return False
        return True

    def _progress(self) -> Progress:
        return Progress(
            SpinnerColumn(style="cyan"),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(bar_width=None, complete_style="green", finished_style="green"),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            console=console,
            transient=True,
        )
