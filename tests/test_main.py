"""Tests for Web Scraper."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.models import ScrapedPage, ScrapeResult
from src.scraper import ScraperConfig, WebScraper
from src.utils import (
    clean_text,
    human_bytes,
    is_valid_url,
    match_any,
    normalize_url,
    parse_page,
    same_domain,
)


# ── utils: URL validation ──────────────────────────────────────────────────

def test_is_valid_url_http():
    assert is_valid_url("http://example.com") is True


def test_is_valid_url_https():
    assert is_valid_url("https://example.com/path?q=1") is True


@pytest.mark.parametrize("bad", ["", "not-a-url", "ftp://example.com", "javascript:void(0)"])
def test_is_valid_url_invalid(bad):
    assert is_valid_url(bad) is False


def test_normalize_url_relative():
    assert normalize_url("https://example.com/page", "/about") == "https://example.com/about"


def test_normalize_url_absolute():
    assert normalize_url("https://example.com", "https://other.com") == "https://other.com"


def test_normalize_url_strips_fragment():
    assert normalize_url("https://example.com", "/a#section") == "https://example.com/a"


@pytest.mark.parametrize("bad", ["#section", "mailto:a@b.com", "tel:+49", "javascript:1", "data:,"])
def test_normalize_url_rejects(bad):
    assert normalize_url("https://example.com", bad) is None


def test_same_domain_true():
    assert same_domain("https://example.com/a", "https://example.com/b") is True


def test_same_domain_strips_www():
    assert same_domain("https://www.example.com", "https://example.com/x") is True


def test_same_domain_false():
    assert same_domain("https://example.com", "https://other.com") is False


# ── utils: misc ────────────────────────────────────────────────────────────

def test_clean_text():
    assert clean_text("  hello   world  ") == "hello world"
    assert clean_text("a\n\nb") == "a b"
    assert clean_text("") == ""


def test_match_any_matches():
    assert match_any([r"^/blog"], "/blog/post") is True


def test_match_any_no_match():
    assert match_any([r"^/docs"], "/blog/post") is False


def test_match_any_invalid_pattern_is_skipped():
    assert match_any(["[unclosed"], "/a") is False


def test_human_bytes():
    assert human_bytes(0).startswith("0")
    assert "KB" in human_bytes(2048)
    assert "MB" in human_bytes(5 * 1024 * 1024)


# ── parse_page ─────────────────────────────────────────────────────────────

SAMPLE_HTML = """
<!doctype html>
<html lang="de">
<head>
  <title>Test Page</title>
  <meta name="description" content="Eine Testseite">
  <meta name="author" content="Jane Doe">
  <meta property="og:title" content="OG Title">
  <meta property="og:image" content="/og.png">
  <link rel="canonical" href="https://example.com/canonical">
  <link rel="icon" href="/favicon.ico">
  <script type="application/ld+json">{"@type":"Article","name":"x"}</script>
</head>
<body>
  <h1>Willkommen</h1>
  <h2>Abschnitt</h2>
  <p>Dies ist ein langer Paragraph mit mehr als 20 Zeichen.</p>
  <a href="/intern">Intern</a>
  <a href="https://extern.com">Extern</a>
  <a href="mailto:a@b.com">Mail</a>
  <img src="/bild.jpg">
</body>
</html>
"""


@pytest.fixture
def parsed():
    return parse_page("https://example.com", SAMPLE_HTML)


def test_parse_title(parsed):
    assert parsed["title"] == "Test Page"


def test_parse_meta_description(parsed):
    assert parsed["meta_description"] == "Eine Testseite"


def test_parse_author(parsed):
    assert parsed["author"] == "Jane Doe"


def test_parse_og(parsed):
    assert parsed["og_title"] == "OG Title"
    assert parsed["og_image"] == "https://example.com/og.png"


def test_parse_canonical(parsed):
    assert parsed["canonical_url"] == "https://example.com/canonical"


def test_parse_favicon(parsed):
    assert parsed["favicon"] == "https://example.com/favicon.ico"


def test_parse_language(parsed):
    assert parsed["language"].startswith("de")


def test_parse_links(parsed):
    assert "https://example.com/intern" in parsed["links"]
    assert "https://extern.com" in parsed["links"]
    assert not any("mailto" in l for l in parsed["links"])


def test_parse_images(parsed):
    assert "https://example.com/bild.jpg" in parsed["images"]


def test_parse_headings(parsed):
    assert "Willkommen" in parsed["headings"]
    assert "Abschnitt" in parsed["headings"]


def test_parse_jsonld(parsed):
    assert parsed["jsonld"] and parsed["jsonld"][0].get("name") == "x"


def test_parse_word_count(parsed):
    assert parsed["word_count"] > 0


# ── models ─────────────────────────────────────────────────────────────────

def test_scraped_page_to_dict_flat():
    page = ScrapedPage(
        url="https://example.com",
        title="Test",
        status_code=200,
        links=["https://a.com", "https://b.com"],
    )
    d = page.to_dict()
    assert d["url"] == "https://example.com"
    assert d["links_count"] == 2
    assert d["status_code"] == 200


def test_scraped_page_to_dict_full():
    page = ScrapedPage(url="https://example.com", title="X", status_code=200)
    d = page.to_dict(full=True)
    assert "scraped_at" in d and isinstance(d["scraped_at"], str)
    assert "jsonld" in d


def test_scrape_result_totals():
    result = ScrapeResult(start_url="https://x.com")
    result.add_page(ScrapedPage(url="https://x.com/a", status_code=200,
                                links=["l1"], images=["i1"], word_count=100, content_length=500))
    result.add_page(ScrapedPage(url="https://x.com/b", status_code=200,
                                links=["l2", "l3"], word_count=200, content_length=1500))
    result.add_error("https://x.com/c", "Timeout")
    result.finish()

    assert len(result.pages) == 2
    assert len(result.errors) == 1
    assert result.total_links == 3
    assert result.total_images == 1
    assert result.total_words == 300
    assert result.total_bytes == 2000
    assert result.duration_seconds >= 0


def test_scrape_result_export_json(tmp_path: Path):
    result = ScrapeResult(start_url="https://x.com")
    result.add_page(ScrapedPage(url="https://x.com/a", status_code=200))
    result.finish()
    path = tmp_path / "out" / "result.json"
    result.export_json(str(path))
    assert path.exists()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["summary"]["pages_scraped"] == 1
    assert data["pages"][0]["url"] == "https://x.com/a"


def test_scrape_result_export_csv_empty(tmp_path: Path):
    result = ScrapeResult()
    result.finish()
    path = tmp_path / "r.csv"
    result.export_csv(str(path))
    assert path.exists()


def test_scrape_result_export_markdown(tmp_path: Path):
    result = ScrapeResult(start_url="https://x.com")
    result.add_page(ScrapedPage(url="https://x.com", title="Home", status_code=200))
    result.finish()
    path = tmp_path / "report.md"
    result.export_markdown(str(path))
    content = path.read_text(encoding="utf-8")
    assert "# Web Scraper Report" in content
    assert "Home" in content


# ── scraper config ─────────────────────────────────────────────────────────

def test_scraper_config_defaults():
    cfg = ScraperConfig()
    assert cfg.max_pages == 10
    assert cfg.respect_robots is True


def test_scraper_constructor_kwargs_override():
    scraper = WebScraper(max_pages=42, delay=0.5)
    assert scraper.config.max_pages == 42
    assert scraper.config.delay == 0.5


def test_should_visit_domain_guard():
    scraper = WebScraper(ScraperConfig(stay_on_domain=True))
    assert scraper._should_visit("https://example.com/a", "https://example.com") is True
    assert scraper._should_visit("https://other.com/a", "https://example.com") is False


def test_should_visit_patterns():
    scraper = WebScraper(ScraperConfig(
        stay_on_domain=False,
        include_patterns=[r"/blog/"],
        exclude_patterns=[r"/drafts/"],
    ))
    start = "https://example.com"
    assert scraper._should_visit("https://example.com/blog/post", start) is True
    assert scraper._should_visit("https://example.com/about", start) is False
    assert scraper._should_visit("https://example.com/blog/drafts/x", start) is False
