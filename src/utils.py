"""Utility functions for Web Scraper.

Low-level helpers: URL validation, HTTP fetch with retries, HTML parsing,
robots.txt + sitemap.xml support, headers, rate limiting.
"""
from __future__ import annotations

import json
import logging
import random
import re
import time
from dataclasses import dataclass
from typing import Iterable, Optional
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
from xml.etree import ElementTree as ET

import requests
from bs4 import BeautifulSoup

log = logging.getLogger("web_scraper")


# ── URL helpers ────────────────────────────────────────────────────────────

def is_valid_url(url: str) -> bool:
    """Check if a URL has a valid HTTP/HTTPS scheme and netloc."""
    try:
        parsed = urlparse(url)
        return parsed.scheme in ("http", "https") and bool(parsed.netloc)
    except Exception:
        return False


def normalize_url(base_url: str, href: str) -> Optional[str]:
    """Resolve a (possibly relative) href against a base URL.

    Strips fragments and filters out mailto:/tel:/javascript: links.
    """
    if not href:
        return None
    href = href.strip()
    if href.startswith(("#", "mailto:", "javascript:", "tel:", "data:")):
        return None
    full = urljoin(base_url, href)
    if "#" in full:
        full = full.split("#", 1)[0]
    return full if is_valid_url(full) else None


def same_domain(url_a: str, url_b: str) -> bool:
    """Return True if both URLs share the same netloc (case-insensitive)."""
    a = urlparse(url_a).netloc.lower().removeprefix("www.")
    b = urlparse(url_b).netloc.lower().removeprefix("www.")
    return a == b


def host_of(url: str) -> str:
    return urlparse(url).netloc.lower()


# ── Headers / User-Agent ───────────────────────────────────────────────────

_DEFAULT_UA_POOL = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Firefox/123.0",
]


def get_headers(user_agent: Optional[str] = None, *, rotate: bool = False) -> dict:
    """Build request headers, optionally with a rotating browser UA."""
    if user_agent:
        ua = user_agent
    elif rotate:
        ua = random.choice(_DEFAULT_UA_POOL)
    else:
        ua = _DEFAULT_UA_POOL[0]
    return {
        "User-Agent": ua,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }


# ── HTTP fetch with retries ────────────────────────────────────────────────

@dataclass
class FetchConfig:
    timeout: int = 10
    max_retries: int = 2
    backoff: float = 0.8


def fetch_page(
    url: str,
    timeout: int = 10,
    headers: Optional[dict] = None,
    max_retries: int = 2,
    backoff: float = 0.8,
) -> Optional[requests.Response]:
    """Fetch a URL with a small retry policy. Returns Response or None."""
    last_err: Optional[Exception] = None
    for attempt in range(max_retries + 1):
        try:
            resp = requests.get(
                url,
                headers=headers or get_headers(),
                timeout=timeout,
                allow_redirects=True,
            )
            resp.raise_for_status()
            return resp
        except requests.RequestException as exc:
            last_err = exc
            if attempt < max_retries:
                time.sleep(backoff * (2 ** attempt))
    log.debug("fetch_page failed for %s: %s", url, last_err)
    return None


# ── robots.txt ─────────────────────────────────────────────────────────────

class RobotsCache:
    """Per-host cache around urllib.robotparser.RobotFileParser."""

    def __init__(self, user_agent: str = "*"):
        self.user_agent = user_agent
        self._cache: dict[str, RobotFileParser] = {}

    def allowed(self, url: str) -> bool:
        parsed = urlparse(url)
        host = f"{parsed.scheme}://{parsed.netloc}"
        rp = self._cache.get(host)
        if rp is None:
            rp = RobotFileParser()
            rp.set_url(f"{host}/robots.txt")
            try:
                rp.read()
            except Exception:
                # If robots.txt is unreachable, be permissive.
                self._cache[host] = rp
                return True
            self._cache[host] = rp
        try:
            return rp.can_fetch(self.user_agent, url)
        except Exception:
            return True


# ── Sitemap parsing ────────────────────────────────────────────────────────

_SITEMAP_NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"


def discover_sitemap(base_url: str, timeout: int = 10) -> Optional[str]:
    """Try common sitemap locations. Returns the first sitemap URL found."""
    candidates = [
        urljoin(base_url, "/sitemap.xml"),
        urljoin(base_url, "/sitemap_index.xml"),
        urljoin(base_url, "/sitemap/sitemap.xml"),
    ]
    for url in candidates:
        try:
            resp = requests.get(url, timeout=timeout, headers=get_headers())
            if resp.status_code == 200 and ("xml" in resp.headers.get("Content-Type", "") or resp.text.lstrip().startswith("<?xml")):
                return url
        except requests.RequestException:
            continue
    return None


def parse_sitemap(url: str, timeout: int = 10) -> list[str]:
    """Return all <loc> URLs from a sitemap or sitemap index (recursive)."""
    try:
        resp = requests.get(url, timeout=timeout, headers=get_headers())
        resp.raise_for_status()
    except requests.RequestException:
        return []

    urls: list[str] = []
    try:
        root = ET.fromstring(resp.content)
    except ET.ParseError:
        return []

    tag = root.tag.lower()
    if tag.endswith("sitemapindex"):
        for sm in root.findall(f"{_SITEMAP_NS}sitemap"):
            loc = sm.find(f"{_SITEMAP_NS}loc")
            if loc is not None and loc.text:
                urls.extend(parse_sitemap(loc.text.strip(), timeout))
    else:
        for page in root.findall(f"{_SITEMAP_NS}url"):
            loc = page.find(f"{_SITEMAP_NS}loc")
            if loc is not None and loc.text:
                urls.append(loc.text.strip())
    return urls


# ── HTML parsing ───────────────────────────────────────────────────────────

def _meta(soup: BeautifulSoup, name: str = "", prop: str = "") -> str:
    """Read a <meta> tag content by name= or property=."""
    if name:
        tag = soup.find("meta", attrs={"name": re.compile(rf"^{re.escape(name)}$", re.I)})
        if tag and tag.get("content"):
            return tag["content"].strip()
    if prop:
        tag = soup.find("meta", attrs={"property": re.compile(rf"^{re.escape(prop)}$", re.I)})
        if tag and tag.get("content"):
            return tag["content"].strip()
    return ""


def _language(soup: BeautifulSoup) -> str:
    html = soup.find("html")
    if html and html.get("lang"):
        return html["lang"].strip()[:10]
    return _meta(soup, name="language")


def _canonical(soup: BeautifulSoup, base_url: str) -> str:
    link = soup.find("link", attrs={"rel": re.compile(r"canonical", re.I)})
    if link and link.get("href"):
        return normalize_url(base_url, link["href"]) or ""
    return ""


def _favicon(soup: BeautifulSoup, base_url: str) -> str:
    link = soup.find("link", attrs={"rel": re.compile(r"(shortcut )?icon", re.I)})
    if link and link.get("href"):
        return normalize_url(base_url, link["href"]) or ""
    return normalize_url(base_url, "/favicon.ico") or ""


def _jsonld(soup: BeautifulSoup) -> list[dict]:
    items: list[dict] = []
    for tag in soup.find_all("script", attrs={"type": re.compile(r"application/ld\+json", re.I)}):
        try:
            data = json.loads(tag.string or "")
        except (json.JSONDecodeError, TypeError):
            continue
        if isinstance(data, list):
            items.extend(x for x in data if isinstance(x, dict))
        elif isinstance(data, dict):
            items.append(data)
    return items


def parse_page(url: str, html: str) -> dict:
    """Parse HTML and extract metadata + content."""
    soup = BeautifulSoup(html, "lxml")

    title = ""
    if soup.title and soup.title.string:
        title = soup.title.string.strip()

    meta_description = _meta(soup, name="description")
    og_title = _meta(soup, prop="og:title")
    og_description = _meta(soup, prop="og:description")
    og_image_raw = _meta(soup, prop="og:image")
    og_image = normalize_url(url, og_image_raw) if og_image_raw else ""
    og_type = _meta(soup, prop="og:type")
    twitter_card = _meta(soup, name="twitter:card")
    keywords = _meta(soup, name="keywords")
    author = _meta(soup, name="author")

    links: list[str] = []
    for tag in soup.find_all("a", href=True):
        normalized = normalize_url(url, tag["href"])
        if normalized:
            links.append(normalized)

    images: list[str] = []
    for tag in soup.find_all("img", src=True):
        normalized = normalize_url(url, tag["src"])
        if normalized:
            images.append(normalized)

    headings: list[str] = [
        tag.get_text(strip=True)
        for tag in soup.find_all(["h1", "h2", "h3"])
        if tag.get_text(strip=True)
    ]

    paragraphs: list[str] = [
        clean_text(p.get_text(" ", strip=True))
        for p in soup.find_all("p")
        if len(p.get_text(strip=True)) > 20
    ][:15]

    # Rough word count from visible body text.
    body = soup.body.get_text(" ", strip=True) if soup.body else ""
    words = len(re.findall(r"\w+", body))

    return {
        "title": title,
        "meta_description": meta_description,
        "og_title": og_title,
        "og_description": og_description,
        "og_image": og_image,
        "og_type": og_type,
        "twitter_card": twitter_card,
        "keywords": keywords,
        "author": author,
        "language": _language(soup),
        "canonical_url": _canonical(soup, url),
        "favicon": _favicon(soup, url),
        "links": list(dict.fromkeys(links)),
        "images": list(dict.fromkeys(images)),
        "headings": headings,
        "paragraphs": paragraphs,
        "word_count": words,
        "jsonld": _jsonld(soup),
    }


# ── Misc ───────────────────────────────────────────────────────────────────

def rate_limit(delay: float, jitter: float = 0.0) -> None:
    """Sleep for `delay` seconds (+ optional random jitter)."""
    if delay > 0:
        extra = random.uniform(0, jitter) if jitter > 0 else 0.0
        time.sleep(delay + extra)


def clean_text(text: str) -> str:
    """Collapse whitespace."""
    return re.sub(r"\s+", " ", text or "").strip()


def match_any(patterns: Iterable[str], value: str) -> bool:
    """Return True if any regex pattern matches `value`."""
    for pat in patterns:
        try:
            if re.search(pat, value):
                return True
        except re.error:
            continue
    return False


def human_bytes(n: int) -> str:
    """Format byte count as e.g. '3.4 KB'."""
    units = ["B", "KB", "MB", "GB"]
    size = float(n)
    for u in units:
        if size < 1024 or u == units[-1]:
            return f"{size:.1f} {u}"
        size /= 1024
    return f"{n} B"
