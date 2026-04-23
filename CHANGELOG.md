# Changelog

All notable changes to this project will be documented in this file.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and this project adheres to [Semantic Versioning](https://semver.org/).

## [2.0.0] — 2026-04-23

### Added
- `ScraperConfig` dataclass for clean, type-safe configuration.
- **robots.txt** support with per-host caching (`--no-robots` to ignore).
- **Retry policy** with exponential backoff (`--retries`).
- **Sitemap discovery & parsing** — new `sitemap` command and `--use-sitemap` crawl flag.
- **Depth-limited** crawl (`--max-depth`).
- **URL include/exclude** regex patterns (`--include`, `--exclude`).
- **User-Agent rotation** (`--rotate-ua`) with multi-browser UA pool.
- **Jitter** delay option for natural request pacing.
- **Richer metadata**: OpenGraph, Twitter Card, canonical URL, favicon, language,
  author, keywords, JSON-LD structured data, word count, response size/time.
- **Markdown export** (`--export md`) plus `all` option for JSON + CSV + Markdown.
- **Info** command — one-liner page summary.
- ASCII banner, colored status codes, per-run config panel, top-domains table.
- `pyproject.toml`, `LICENSE`, `.gitignore`, `CHANGELOG.md`.

### Changed
- Scraper constructor now accepts a `ScraperConfig` (kwargs still work for ergonomics).
- Display functions rewritten for richer, prettier output.
- Tests expanded to 44 cases across utils, parser, models, and scraper config.

### Removed
- Unused `httpx` and `fake-useragent` dependencies.

## [1.0.0] — 2026-04-21

- Initial release: `scrape`, `crawl`, `links` commands; JSON/CSV export.
