<div align="center">

# Web Scraper

**A modern command-line web scraper & crawler with a beautiful Rich terminal UI.**

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776ab?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Requests](https://img.shields.io/badge/requests-2.31%2B-2496ed?style=for-the-badge)](https://requests.readthedocs.io)
[![BeautifulSoup](https://img.shields.io/badge/BeautifulSoup4-4.12%2B-59a14f?style=for-the-badge)](https://www.crummy.com/software/BeautifulSoup/)
[![Rich](https://img.shields.io/badge/Rich-13%2B-ff6f61?style=for-the-badge)](https://rich.readthedocs.io)
[![License](https://img.shields.io/badge/License-MIT-7c3aed?style=for-the-badge)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-44%20passing-22c55e?style=for-the-badge)]()

*Scrape, crawl and export web pages — fast, polite, pretty. No account. No cloud. Runs locally.*

<sub>Version **2.0.0** · MIT · Built with Python · [Changelog](CHANGELOG.md)</sub>

</div>

---

<div align="center">

```text
__        __   _       ____
\ \      / /__| |__   / ___|  ___ _ __ __ _ _ __   ___ _ __
 \ \ /\ / / _ \ '_ \  \___ \ / __| '__/ _` | '_ \ / _ \ '__|
  \ V  V /  __/ |_) |  ___) | (__| | | (_| | |_) |  __/ |
   \_/\_/ \___|_.__/  |____/ \___|_|  \__,_| .__/ \___|_|
                                           |_|
```

*Scrape · Crawl · Export*

</div>

<!-- For a real screenshot: run the project, take a screenshot, and replace this placeholder. -->
<!-- ![Screenshot](docs/screenshot.png) -->

---

## Contents

- [Features](#features)
- [Quick Start](#quick-start)
- [Commands](#commands)
- [Options in Detail](#options-in-detail)
- [Examples](#examples)
- [Use as a Library](#use-as-a-library)
- [Project Structure](#project-structure)
- [Architecture](#architecture)
- [Dependencies](#dependencies)
- [Tests](#tests)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [Ethics](#ethics)
- [License](#license)

---

## Features

|    | Feature | Description |
|----|---------|-------------|
| 🕷 | **Single-page scrape** | Title, meta, headings, paragraphs, links, images, OpenGraph, JSON-LD |
| 🌐 | **BFS crawler** | Follows internal links with configurable page and depth limits |
| 🤝 | **robots.txt** | Respected by default — can be disabled with `--no-robots` |
| 🗺 | **Sitemap** | Automatic sitemap discovery + `--use-sitemap` as a crawl seed |
| 🎯 | **URL filters** | Include/exclude via arbitrary regex patterns |
| 🔁 | **Retry & backoff** | Exponential backoff on transient failures |
| ⏲ | **Rate limiting** | Delay + optional jitter for natural request pacing |
| 🎭 | **UA rotation** | Rotating browser User-Agent per request |
| 🎨 | **Rich UI** | Colored panels, tables, progress bars in your terminal |
| 💾 | **Multi-format export** | JSON, CSV, **Markdown** report, or everything at once |
| 📊 | **Statistics** | Words, response time, top domains, total size |
| 🧪 | **Tested** | 44 tests with `pytest`, clean type hints |

---

## Quick Start

```bash
# 1) Clone the repo
git clone https://github.com/Pommes2030450/web-scraper.git
cd web-scraper

# 2) Install dependencies
pip install -r requirements.txt

# 3) Go!
python -m src.main scrape https://example.com
```

**Windows users:** just double-click `start.bat` — it installs dependencies and opens a ready-to-use shell.

---

## Commands

| Command   | Purpose |
|-----------|---------|
| `scrape`  | Scrape a single page and show it as a panel |
| `crawl`   | Crawl a website (BFS), export results |
| `links`   | List all links on a page |
| `sitemap` | Discover a sitemap and list URLs |
| `info`    | Compact one-line summary of a URL |

Full help:

```bash
python -m src.main --help
python -m src.main crawl --help
```

---

## Options in Detail

### `crawl`

| Option | Default | Description |
|---|---|---|
| `--max-pages` | `10` | Maximum number of scraped pages |
| `--max-depth` | `3` | Maximum link depth from the start URL |
| `--delay` | `1.0` | Pause between requests (seconds) |
| `--jitter` | `0.0` | Random extra delay (seconds, 0 = off) |
| `--timeout` | `10` | HTTP timeout (seconds) |
| `--retries` | `2` | Number of retries on failure |
| `--stay-on-domain / --cross-domain` | stay | Only same domain, or follow external links |
| `--no-robots` | — | Ignore robots.txt (not recommended) |
| `--rotate-ua` | — | Rotate User-Agent per request |
| `--user-agent` | — | Custom User-Agent |
| `--include REGEX` | — | Only URLs matching the regex (can be repeated) |
| `--exclude REGEX` | — | Skip URLs matching the regex |
| `--use-sitemap` | — | Additionally use the sitemap as a seed |
| `--export` | — | `json` · `csv` · `md` · `both` · `all` |
| `--output-dir` | `data` | Output directory |
| `--output-name` | `result` | File name without extension |
| `--verbose / -v` | — | Verbose output |

### `scrape`

| Option | Purpose |
|---|---|
| `--timeout` | HTTP timeout |
| `--user-agent` | Custom User-Agent |
| `--no-robots` | Ignore robots.txt |
| `--verbose` | Verbose output |

### `links`

| Option | Purpose |
|---|---|
| `--limit` | How many links to display |
| `--same-domain-only` | Only internal links |
| `--external-only` | Only external links |

### `sitemap`

| Option | Purpose |
|---|---|
| `--limit` | How many URLs to display |
| `--export PATH` | Export URLs to a text file |

---

## Examples

```bash
# Quick-check a page
python -m src.main info https://example.com

# Detailed single-page scrape
python -m src.main scrape https://example.com --verbose

# Crawl 50 pages, 2s delay, export Markdown + JSON + CSV
python -m src.main crawl https://example.com \
    --max-pages 50 --delay 2.0 --export all --output-name example

# Only /blog/**, skip /drafts/, up to depth 4
python -m src.main crawl https://example.com \
    --include "/blog/" --exclude "/drafts/" --max-depth 4

# Cross-domain crawl with UA rotation
python -m src.main crawl https://example.com \
    --cross-domain --rotate-ua --max-pages 30

# Seed the crawl from a sitemap, 100 pages
python -m src.main crawl https://example.com \
    --use-sitemap --max-pages 100 --export json

# Show sitemap and export URLs to urls.txt
python -m src.main sitemap https://example.com --export urls.txt

# Only external links on a page
python -m src.main links https://example.com --external-only
```

---

## Use as a Library

```python
from src import WebScraper, ScraperConfig

cfg = ScraperConfig(
    max_pages=25,
    max_depth=3,
    delay=1.0,
    include_patterns=[r"/docs/"],
    respect_robots=True,
)
scraper = WebScraper(cfg)

result = scraper.scrape("https://example.com")

print(result.summary())
for page in result.pages:
    print(f"{page.status_code}  {page.title}  ({page.word_count} words)")

result.export_json("data/example.json")
result.export_markdown("data/example.md")
```

Or the ergonomic short form:

```python
from src import WebScraper

scraper = WebScraper(max_pages=5, delay=0.5)
page = scraper.scrape_single("https://example.com")
print(page.title, page.canonical_url, page.language, page.word_count)
```

---

## Project Structure

```
002_web_scraper/
├── src/
│   ├── __init__.py          # Public API (WebScraper, ScraperConfig, …)
│   ├── main.py              # CLI (scrape, crawl, links, sitemap, info)
│   ├── scraper.py           # BFS crawler + ScraperConfig
│   ├── models.py            # ScrapedPage, ScrapeResult, exporters
│   ├── display.py           # Rich panels, tables, banner
│   └── utils.py             # URLs, HTTP, robots, sitemap, parsing
├── tests/
│   └── test_main.py         # 44 unit tests
├── data/                    # Exported JSON/CSV/Markdown files
├── docs/                    # Screenshots, extra docs
├── requirements.txt
├── pyproject.toml
├── LICENSE
├── CHANGELOG.md
├── .gitignore
├── .env.example
├── start.bat                # Windows one-click
└── README.md
```

---

## Architecture

```
         ┌─────────────────────────┐
         │        CLI (click)      │  src/main.py
         └──────────────┬──────────┘
                        ▼
         ┌─────────────────────────┐
         │  WebScraper + Config    │  BFS, retries, rate limit,
         │                         │  robots, patterns, sitemap
         └──────┬─────────────┬────┘
                ▼             ▼
   ┌───────────────────┐  ┌─────────────────────┐
   │    utils.py       │  │      models.py      │
   │  - fetch_page     │  │  - ScrapedPage      │
   │  - parse_page     │  │  - ScrapeResult     │
   │  - robots/sitemap │  │  - JSON/CSV/MD      │
   └───────────────────┘  └──────────┬──────────┘
                                     ▼
                           ┌───────────────────┐
                           │   display.py      │  Rich UI
                           │  Panels, tables,  │
                           │  progress, tree   │
                           └───────────────────┘
```

- **Separation of concerns:** networking (`utils`), state (`models`), engine (`scraper`), UI (`display`), CLI (`main`).
- **Pure-function friendly:** parsers and normalizers are side-effect-free and easy to test.
- **Configuration object:** `ScraperConfig` bundles every parameter — clean, typed, documented.

---

## Dependencies

| Package | Purpose |
|---|---|
| `requests` | HTTP requests |
| `beautifulsoup4` | HTML parsing |
| `lxml` | Fast HTML/XML parser backend |
| `rich` | Colored terminal output and progress bars |
| `click` | CLI framework |
| `python-dotenv` | `.env` support |

Dev-only: `pytest`, `pytest-cov`, `ruff`.

---

## Tests

```bash
pytest -q
pytest tests/ -v --cov=src           # with coverage
```

**Current status:** 44 tests passing.

---

## Roadmap

- [ ] Async crawler (`httpx` + `asyncio`) for massively parallel requests
- [ ] Persistent crawl resume (resume-from-checkpoint)
- [ ] Pluggable exporters (SQLite, Parquet)
- [ ] Headless-browser mode for JavaScript-heavy sites (Playwright)
- [ ] Optional **Web UI** (FastAPI + HTMX) as an alternative to the CLI
- [ ] Optional **TUI** (Textual) with a live-log panel

---

## Contributing

Contributions are welcome! Workflow:

1. Open an issue or pick an existing one.
2. Fork → feature branch → write tests → PR.
3. Linting: `ruff check src tests`. Formatting usually takes care of itself.

---

## Ethics

Please scrape responsibly:

- **Respect robots.txt** (default).
- Use non-trivial delays (`--delay 1.5` or more).
- Set an honest User-Agent with a contact method.
- Don't scrape content behind login/paywall unless you're allowed to.
- Check the target site's ToS.

---

## License

[MIT](LICENSE) © 2026 Pommes2030450

<div align="center">

**⭐ If you like this tool, give it a star on GitHub!**

</div>
