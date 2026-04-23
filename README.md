<div align="center">

# Web Scraper

**Modern command-line web scraper & crawler with a beautiful Rich terminal UI.**

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776ab?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Requests](https://img.shields.io/badge/requests-2.31%2B-2496ed?style=for-the-badge)](https://requests.readthedocs.io)
[![BeautifulSoup](https://img.shields.io/badge/BeautifulSoup4-4.12%2B-59a14f?style=for-the-badge)](https://www.crummy.com/software/BeautifulSoup/)
[![Rich](https://img.shields.io/badge/Rich-13%2B-ff6f61?style=for-the-badge)](https://rich.readthedocs.io)
[![License](https://img.shields.io/badge/License-MIT-7c3aed?style=for-the-badge)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-44%20passing-22c55e?style=for-the-badge)]()

*Seiten scrapen, crawlen und exportieren — schnell, höflich, hübsch. Kein Account. Keine Cloud. Läuft lokal.*

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

<!-- Für einen echten Screenshot: starte das Projekt, mach einen Screenshot und ersetze den Platzhalter. -->
<!-- ![Screenshot](docs/screenshot.png) -->

---

## Inhalt

- [Features](#features)
- [Schnellstart](#schnellstart)
- [Befehle](#befehle)
- [Optionen im Detail](#optionen-im-detail)
- [Beispiele](#beispiele)
- [Als Bibliothek nutzen](#als-bibliothek-nutzen)
- [Projektstruktur](#projektstruktur)
- [Architektur](#architektur)
- [Abhängigkeiten](#abhängigkeiten)
- [Tests](#tests)
- [Roadmap](#roadmap)
- [Mitmachen](#mitmachen)
- [Ethik](#ethik)
- [Lizenz](#lizenz)

---

## Features

|    | Feature | Beschreibung |
|----|---------|--------------|
| 🕷 | **Einzelseiten-Scrape** | Titel, Meta, Headings, Paragraphen, Links, Bilder, OpenGraph, JSON-LD |
| 🌐 | **BFS-Crawler** | Folgt internen Links mit einstellbarer Seiten- und Tiefenbegrenzung |
| 🤝 | **robots.txt** | Respektiert standardmäßig — optional via `--no-robots` abschaltbar |
| 🗺 | **Sitemap** | Automatische Sitemap-Erkennung + `--use-sitemap` als Crawl-Seed |
| 🎯 | **URL-Filter** | Include/Exclude über beliebige Regex-Patterns |
| 🔁 | **Retry & Backoff** | Exponentielles Backoff bei transienten Fehlern |
| ⏲ | **Rate Limiting** | Delay + optionaler Jitter für natürliches Request-Timing |
| 🎭 | **UA-Rotation** | Rotierender Browser-User-Agent pro Request |
| 🎨 | **Rich-UI** | Farbige Panels, Tabellen, Progress Bars im Terminal |
| 💾 | **Multi-Export** | JSON, CSV, **Markdown**-Report, oder alles auf einmal |
| 📊 | **Statistiken** | Wörter, Response-Zeit, Top-Domains, Gesamtgröße |
| 🧪 | **Getestet** | 44 Tests mit `pytest`, saubere Type-Hints |

---

## Schnellstart

```bash
# 1) Repo klonen
git clone https://github.com/Pommes2030450/web-scraper.git
cd web-scraper

# 2) Abhängigkeiten installieren
pip install -r requirements.txt

# 3) Los geht's
python -m src.main scrape https://example.com
```

**Windows-Nutzer:** einfach `start.bat` doppelklicken — installiert und öffnet eine fertige Shell.

---

## Befehle

| Befehl    | Zweck |
|-----------|-------|
| `scrape`  | Eine einzelne Seite scrapen und als Panel anzeigen |
| `crawl`   | Website crawlen (BFS), Ergebnisse exportieren |
| `links`   | Alle Links einer Seite auflisten |
| `sitemap` | Sitemap entdecken und URLs anzeigen |
| `info`    | Kompakte 1-Zeilen-Zusammenfassung einer URL |

Komplette Hilfe:

```bash
python -m src.main --help
python -m src.main crawl --help
```

---

## Optionen im Detail

### `crawl`

| Option | Standard | Beschreibung |
|---|---|---|
| `--max-pages` | `10` | Maximale Anzahl gescrapter Seiten |
| `--max-depth` | `3` | Maximale Link-Tiefe ausgehend von der Start-URL |
| `--delay` | `1.0` | Pause zwischen Requests (Sekunden) |
| `--jitter` | `0.0` | Zufälliger Extra-Delay (Sekunden, 0 = aus) |
| `--timeout` | `10` | HTTP-Timeout (Sekunden) |
| `--retries` | `2` | Anzahl Wiederholungen bei Fehler |
| `--stay-on-domain / --cross-domain` | stay | Nur gleiche Domain, oder extern folgen |
| `--no-robots` | — | robots.txt ignorieren (nicht empfohlen) |
| `--rotate-ua` | — | User-Agent pro Request rotieren |
| `--user-agent` | — | Eigener User-Agent |
| `--include REGEX` | — | Nur URLs, die dem Regex entsprechen (mehrfach möglich) |
| `--exclude REGEX` | — | URLs ausschließen, die dem Regex entsprechen |
| `--use-sitemap` | — | Sitemap zusätzlich als Seed verwenden |
| `--export` | — | `json` · `csv` · `md` · `both` · `all` |
| `--output-dir` | `data` | Ausgabe-Verzeichnis |
| `--output-name` | `result` | Dateiname ohne Endung |
| `--verbose / -v` | — | Ausführliche Ausgabe |

### `scrape`

| Option | Zweck |
|---|---|
| `--timeout` | HTTP-Timeout |
| `--user-agent` | Eigener User-Agent |
| `--no-robots` | robots.txt ignorieren |
| `--verbose` | Ausführliche Ausgabe |

### `links`

| Option | Zweck |
|---|---|
| `--limit` | Wie viele Links anzeigen |
| `--same-domain-only` | Nur interne Links |
| `--external-only` | Nur externe Links |

### `sitemap`

| Option | Zweck |
|---|---|
| `--limit` | Wie viele URLs anzeigen |
| `--export PATH` | URLs als Textdatei exportieren |

---

## Beispiele

```bash
# Schnellcheck einer Seite
python -m src.main info https://example.com

# Detaillierte Einzelseite
python -m src.main scrape https://example.com --verbose

# 50 Seiten crawlen, 2 s Delay, Markdown + JSON + CSV exportieren
python -m src.main crawl https://example.com \
    --max-pages 50 --delay 2.0 --export all --output-name example

# Nur /blog/**, keine /drafts/, bis Tiefe 4
python -m src.main crawl https://example.com \
    --include "/blog/" --exclude "/drafts/" --max-depth 4

# Cross-Domain-Crawl mit UA-Rotation
python -m src.main crawl https://example.com \
    --cross-domain --rotate-ua --max-pages 30

# Sitemap als Seed, 100 Seiten
python -m src.main crawl https://example.com \
    --use-sitemap --max-pages 100 --export json

# Sitemap anzeigen und nach urls.txt exportieren
python -m src.main sitemap https://example.com --export urls.txt

# Nur externe Links einer Seite
python -m src.main links https://example.com --external-only
```

---

## Als Bibliothek nutzen

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
    print(f"{page.status_code}  {page.title}  ({page.word_count} Wörter)")

result.export_json("data/example.json")
result.export_markdown("data/example.md")
```

Oder die ergonomische Kurzform:

```python
from src import WebScraper

scraper = WebScraper(max_pages=5, delay=0.5)
page = scraper.scrape_single("https://example.com")
print(page.title, page.canonical_url, page.language, page.word_count)
```

---

## Projektstruktur

```
002_web_scraper/
├── src/
│   ├── __init__.py          # Public API (WebScraper, ScraperConfig, …)
│   ├── main.py              # CLI (scrape, crawl, links, sitemap, info)
│   ├── scraper.py           # BFS-Crawler + ScraperConfig
│   ├── models.py            # ScrapedPage, ScrapeResult, Exporter
│   ├── display.py           # Rich-Panels, Tabellen, Banner
│   └── utils.py             # URLs, HTTP, robots, sitemap, parsing
├── tests/
│   └── test_main.py         # 44 Unit-Tests
├── data/                    # Exportierte JSON/CSV/Markdown-Dateien
├── docs/                    # Screenshots, zusätzliche Docs
├── requirements.txt
├── pyproject.toml
├── LICENSE
├── CHANGELOG.md
├── .gitignore
├── .env.example
├── start.bat                # Windows One-Click
└── README.md
```

---

## Architektur

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
                           │   display.py      │  Rich-UI
                           │  Panels, Tables,  │
                           │  Progress, Tree   │
                           └───────────────────┘
```

- **Trennung der Verantwortlichkeiten:** Netzwerk (`utils`), Zustand (`models`), Engine (`scraper`), UI (`display`), CLI (`main`).
- **Pure-Functions-freundlich:** Parser und Normalisierer sind ohne Seiteneffekte und leicht testbar.
- **Konfigurationsobjekt:** `ScraperConfig` kapselt alle Parameter — sauber, typsicher, dokumentiert.

---

## Abhängigkeiten

| Paket | Zweck |
|---|---|
| `requests` | HTTP-Requests |
| `beautifulsoup4` | HTML-Parsing |
| `lxml` | Schneller HTML/XML-Parser-Backend |
| `rich` | Farbige Terminal-Ausgabe und Progress Bars |
| `click` | CLI-Framework |
| `python-dotenv` | `.env`-Unterstützung |

Dev-only: `pytest`, `pytest-cov`, `ruff`.

---

## Tests

```bash
pytest -q
pytest tests/ -v --cov=src           # mit Coverage
```

**Aktueller Stand:** 44 Tests grün.

---

## Roadmap

- [ ] Async-Crawler (`httpx` + `asyncio`) für massiv parallele Requests
- [ ] Persistente Crawl-Wiederaufnahme (Resume-from-checkpoint)
- [ ] Pluggable Exporter (SQLite, Parquet)
- [ ] Headless-Browser-Mode für JavaScript-lastige Seiten (Playwright)
- [ ] Optionale **Web-UI** (FastAPI + HTMX) als Alternative zur CLI
- [ ] Optionale **TUI** (Textual) mit Live-Log-Panel

---

## Mitmachen

Contributions sind willkommen! Ablauf:

1. Issue öffnen oder bestehenden auswählen.
2. Fork → Feature-Branch → Tests schreiben → PR.
3. Linting: `ruff check src tests`. Formatting passt meistens automatisch.

---

## Ethik

Bitte scrape verantwortungsvoll:

- **robots.txt respektieren** (Default).
- Nicht-triviale Delays verwenden (`--delay 1.5` oder mehr).
- Eigenen, ehrlichen User-Agent mit Kontaktweg setzen.
- Keine Seiten hinter Login/Paywall scrapen, sofern du kein Recht dazu hast.
- ToS der Zielsite prüfen.

---

## Lizenz

[MIT](LICENSE) © 2026 Pommes2030450

<div align="center">

**⭐ Wenn dir das Tool gefällt, gib ihm einen Star auf GitHub!**

</div>
