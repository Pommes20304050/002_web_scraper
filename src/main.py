#!/usr/bin/env python3
"""Web Scraper — command-line interface.

Examples
--------
    python -m src.main scrape  https://example.com
    python -m src.main crawl   https://example.com --max-pages 20 --export json
    python -m src.main links   https://example.com
    python -m src.main sitemap https://example.com
"""
from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

import click
from dotenv import load_dotenv
from rich.console import Console

from . import __version__
from .display import (
    print_banner,
    print_links_table,
    print_page_summary,
    print_result_summary,
    print_run_config,
    print_sitemap_summary,
)
from .scraper import ScraperConfig, WebScraper
from .utils import discover_sitemap, parse_sitemap, same_domain

load_dotenv()
console = Console()
log = logging.getLogger("web_scraper")


def _configure_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.WARNING
    logging.basicConfig(
        level=level,
        format="%(asctime)s  %(levelname)-5s  %(message)s",
        datefmt="%H:%M:%S",
    )


def _export_results(result, output_dir: str, export: str | None, name: str) -> None:
    """Export results in one or more formats."""
    if not export:
        return

    formats: list[str]
    if export == "all":
        formats = ["json", "csv", "md"]
    elif export == "both":
        formats = ["json", "csv"]
    else:
        formats = [export]

    Path(output_dir).mkdir(parents=True, exist_ok=True)

    for fmt in formats:
        path = os.path.join(output_dir, f"{name}.{fmt}")
        try:
            if fmt == "json":
                result.export_json(path)
            elif fmt == "csv":
                result.export_csv(path)
            elif fmt == "md":
                result.export_markdown(path)
            console.print(f"[green]✓[/green] {fmt.upper():4} → [cyan]{path}[/cyan]")
        except OSError as exc:
            console.print(f"[bold red]Export ({fmt}) fehlgeschlagen:[/bold red] {exc}")


# ── CLI root ───────────────────────────────────────────────────────────────

@click.group(
    help="Web Scraper — scrape, crawl, export from the command line.",
    context_settings={"help_option_names": ["-h", "--help"]},
)
@click.version_option(__version__, "-V", "--version", prog_name="web-scraper")
@click.option("--no-banner", is_flag=True, help="Unterdrückt das ASCII-Banner.")
@click.pass_context
def cli(ctx: click.Context, no_banner: bool) -> None:
    ctx.ensure_object(dict)
    ctx.obj["no_banner"] = no_banner
    if not no_banner and ctx.invoked_subcommand and sys.stdout.isatty():
        print_banner(__version__)


# ── scrape ─────────────────────────────────────────────────────────────────

@cli.command(help="Eine einzelne Seite scrapen und anzeigen.")
@click.argument("url")
@click.option("--timeout", default=10, show_default=True, help="HTTP-Timeout in Sekunden.")
@click.option("--user-agent", default=None, help="Eigener User-Agent (überschreibt Default).")
@click.option("--no-robots", is_flag=True, help="robots.txt ignorieren.")
@click.option("--verbose", "-v", is_flag=True, help="Ausführliche Ausgabe.")
def scrape(url: str, timeout: int, user_agent: str | None, no_robots: bool, verbose: bool) -> None:
    _configure_logging(verbose)
    cfg = ScraperConfig(
        timeout=timeout,
        user_agent=user_agent or os.getenv("USER_AGENT"),
        respect_robots=not no_robots,
        verbose=verbose,
    )
    scraper = WebScraper(cfg)
    console.print(f"[bold green]▶ Scrape:[/bold green] [link={url}]{url}[/link]\n")
    page = scraper.scrape_single(url)
    if page is None:
        console.print("[bold red]✗ Fehler:[/bold red] Seite konnte nicht geladen werden.")
        sys.exit(1)
    print_page_summary(page)


# ── crawl ──────────────────────────────────────────────────────────────────

@cli.command(help="Ganze Website crawlen (folgt internen Links, BFS).")
@click.argument("url")
@click.option("--max-pages",   default=10,   show_default=True, help="Maximale Seitenanzahl.")
@click.option("--max-depth",   default=3,    show_default=True, help="Maximale Link-Tiefe.")
@click.option("--delay",       default=1.0,  show_default=True, help="Pause zwischen Requests (s).")
@click.option("--jitter",      default=0.0,  show_default=True, help="Zufälliger Extra-Delay-Anteil (s).")
@click.option("--timeout",     default=10,   show_default=True, help="HTTP-Timeout (s).")
@click.option("--retries",     default=2,    show_default=True, help="Anzahl Wiederholungen bei Fehler.")
@click.option("--stay-on-domain/--cross-domain", default=True, show_default=True,
              help="Nur gleiche Domain crawlen oder extern folgen.")
@click.option("--no-robots",   is_flag=True, help="robots.txt ignorieren.")
@click.option("--rotate-ua",   is_flag=True, help="User-Agent pro Request rotieren.")
@click.option("--user-agent",  default=None, help="Eigener User-Agent (überschreibt Default).")
@click.option("--include",     multiple=True, metavar="REGEX", help="Nur URLs, die dem Regex entsprechen.")
@click.option("--exclude",     multiple=True, metavar="REGEX", help="URLs ausschließen, die dem Regex entsprechen.")
@click.option("--use-sitemap", is_flag=True, help="Zusätzlich Sitemap als Seed verwenden.")
@click.option("--export",      type=click.Choice(["json", "csv", "md", "both", "all"]), default=None,
              help="Export-Format(e). `both` = json+csv, `all` = alles.")
@click.option("--output-dir",  default="data", show_default=True, help="Ausgabe-Verzeichnis.")
@click.option("--output-name", default="result", show_default=True, help="Dateiname ohne Endung.")
@click.option("--verbose", "-v", is_flag=True, help="Ausführliche Ausgabe.")
def crawl(
    url: str,
    max_pages: int,
    max_depth: int,
    delay: float,
    jitter: float,
    timeout: int,
    retries: int,
    stay_on_domain: bool,
    no_robots: bool,
    rotate_ua: bool,
    user_agent: str | None,
    include: tuple[str, ...],
    exclude: tuple[str, ...],
    use_sitemap: bool,
    export: str | None,
    output_dir: str,
    output_name: str,
    verbose: bool,
) -> None:
    _configure_logging(verbose)

    cfg = ScraperConfig(
        max_pages=max_pages,
        max_depth=max_depth,
        delay=delay,
        jitter=jitter,
        timeout=timeout,
        max_retries=retries,
        stay_on_domain=stay_on_domain,
        respect_robots=not no_robots,
        rotate_user_agent=rotate_ua,
        user_agent=user_agent or os.getenv("USER_AGENT"),
        include_patterns=list(include),
        exclude_patterns=list(exclude),
        verbose=verbose,
    )

    print_run_config(
        "Crawl-Konfiguration",
        [
            ("Start-URL",   url),
            ("Max-Seiten",  str(max_pages)),
            ("Max-Tiefe",   str(max_depth)),
            ("Delay",       f"{delay}s (+{jitter}s jitter)" if jitter else f"{delay}s"),
            ("Timeout",     f"{timeout}s"),
            ("Domain",      "nur gleiche" if stay_on_domain else "cross-domain"),
            ("robots.txt",  "ignoriert" if no_robots else "respektiert"),
            ("UA-Rotation", "an" if rotate_ua else "aus"),
            ("Include",     ", ".join(include) if include else "—"),
            ("Exclude",     ", ".join(exclude) if exclude else "—"),
        ],
    )

    seeds: list[str] = []
    if use_sitemap:
        sm = discover_sitemap(url, timeout=timeout)
        if sm:
            seeds = [u for u in parse_sitemap(sm, timeout=timeout) if same_domain(url, u)]
            console.print(f"[green]✓[/green] Sitemap gefunden: {len(seeds)} URLs als Seed")
        else:
            console.print("[yellow]![/yellow] Keine Sitemap gefunden — fahre ohne Seeds fort")

    scraper = WebScraper(cfg)
    result = scraper.scrape(url, seed_urls=seeds)

    console.print()
    print_result_summary(result)

    _export_results(result, output_dir, export, output_name)


# ── links ──────────────────────────────────────────────────────────────────

@cli.command(help="Alle Links einer Seite auflisten.")
@click.argument("url")
@click.option("--limit", default=20, show_default=True, help="Maximale Anzahl angezeigter Links.")
@click.option("--same-domain-only", is_flag=True, help="Nur Links zur selben Domain.")
@click.option("--external-only",    is_flag=True, help="Nur externe Links.")
def links(url: str, limit: int, same_domain_only: bool, external_only: bool) -> None:
    scraper = WebScraper(ScraperConfig())
    page = scraper.scrape_single(url)
    if page is None:
        console.print("[bold red]✗ Fehler:[/bold red] Seite konnte nicht geladen werden.")
        sys.exit(1)

    if same_domain_only:
        page.links = [l for l in page.links if same_domain(url, l)]
    elif external_only:
        page.links = [l for l in page.links if not same_domain(url, l)]

    print_links_table(page, limit=limit)
    console.print(f"\n[dim]Angezeigt: {min(limit, len(page.links))} / {len(page.links)} Links[/dim]")


# ── sitemap ────────────────────────────────────────────────────────────────

@cli.command(help="Sitemap einer Domain finden und URLs auflisten.")
@click.argument("url")
@click.option("--limit",   default=20, show_default=True, help="Wie viele URLs anzeigen.")
@click.option("--timeout", default=10, show_default=True, help="HTTP-Timeout (s).")
@click.option("--export",  type=click.Path(dir_okay=False), default=None,
              help="URLs als Textdatei speichern.")
def sitemap(url: str, limit: int, timeout: int, export: str | None) -> None:
    sm = discover_sitemap(url, timeout=timeout)
    if not sm:
        console.print("[bold red]✗ Keine Sitemap gefunden.[/bold red]")
        sys.exit(1)
    urls = parse_sitemap(sm, timeout=timeout)
    print_sitemap_summary(urls, sm, limit=limit)
    if export:
        Path(os.path.dirname(export) or ".").mkdir(parents=True, exist_ok=True)
        with open(export, "w", encoding="utf-8") as f:
            f.write("\n".join(urls))
        console.print(f"[green]✓[/green] Export → [cyan]{export}[/cyan]")


# ── info ───────────────────────────────────────────────────────────────────

@cli.command(help="Kompakte Info-Zeile zu einer URL (Status, Titel, Sprache, Größe).")
@click.argument("url")
def info(url: str) -> None:
    scraper = WebScraper(ScraperConfig())
    page = scraper.scrape_single(url)
    if page is None:
        console.print("[bold red]✗ Fehler:[/bold red] Seite konnte nicht geladen werden.")
        sys.exit(1)
    console.print(
        f"[green]{page.status_code}[/green]  "
        f"[bold]{page.title}[/bold]  "
        f"[dim]lang={page.language or '—'}  "
        f"words={page.word_count}  "
        f"links={len(page.links)}  "
        f"images={len(page.images)}  "
        f"{page.elapsed_ms}ms[/dim]"
    )


if __name__ == "__main__":
    cli()
