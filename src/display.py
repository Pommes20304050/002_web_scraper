"""Rich display helpers — banners, tables, panels, trees."""
from __future__ import annotations

from collections import Counter
from urllib.parse import urlparse

from rich import box
from rich.align import Align
from rich.columns import Columns
from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.tree import Tree

from .models import ScrapedPage, ScrapeResult
from .utils import human_bytes

console = Console()

BANNER = r"""
__        __   _       ____
\ \      / /__| |__   / ___|  ___ _ __ __ _ _ __   ___ _ __
 \ \ /\ / / _ \ '_ \  \___ \ / __| '__/ _` | '_ \ / _ \ '__|
  \ V  V /  __/ |_) |  ___) | (__| | | (_| | |_) |  __/ |
   \_/\_/ \___|_.__/  |____/ \___|_|  \__,_| .__/ \___|_|
                                           |_|
"""


def print_banner(version: str = "") -> None:
    """Print the ASCII banner in a gradient-like color."""
    text = Text(BANNER, style="bold cyan")
    subtitle = Text.assemble(
        ("Scrape · Crawl · Export", "italic magenta"),
        ("   ", ""),
        (f"v{version}" if version else "", "dim"),
    )
    console.print(Align.center(text))
    console.print(Align.center(subtitle))
    console.print()


def print_run_config(title: str, rows: list[tuple[str, str]]) -> None:
    """Print a small compact config panel at the start of a run."""
    t = Table(box=box.MINIMAL, show_header=False, padding=(0, 2), expand=False)
    t.add_column(style="bold cyan", no_wrap=True)
    t.add_column(style="white")
    for label, value in rows:
        t.add_row(label, value)
    console.print(Panel(t, title=f"[bold]{title}[/bold]", border_style="blue", expand=False))


def print_page_summary(page: ScrapedPage) -> None:
    """Pretty panel for a single scraped page."""
    meta = Table(box=box.MINIMAL, show_header=False, padding=(0, 1), expand=True)
    meta.add_column(style="bold cyan", width=18, no_wrap=True)
    meta.add_column(style="white", overflow="fold")

    meta.add_row("URL", f"[link={page.url}]{page.url}[/link]")
    meta.add_row("Title", page.title or "[dim]—[/dim]")
    meta.add_row("Status", _status_color(page.status_code))
    meta.add_row("Language", page.language or "[dim]—[/dim]")
    meta.add_row("Canonical", page.canonical_url or "[dim]—[/dim]")
    meta.add_row("Author", page.author or "[dim]—[/dim]")
    meta.add_row("Description", page.meta_description or "[dim]—[/dim]")
    if page.og_title:
        meta.add_row("OG Title", page.og_title)
    if page.og_image:
        meta.add_row("OG Image", page.og_image)

    stats = Table(box=box.MINIMAL, show_header=False, padding=(0, 1), expand=True)
    stats.add_column(style="bold magenta", no_wrap=True)
    stats.add_column(style="bold green", justify="right")
    stats.add_row("Links", str(len(page.links)))
    stats.add_row("Images", str(len(page.images)))
    stats.add_row("Headings", str(len(page.headings)))
    stats.add_row("Words", str(page.word_count))
    stats.add_row("Size", human_bytes(page.content_length))
    stats.add_row("Elapsed", f"{page.elapsed_ms} ms")

    body = Columns([meta, stats], expand=True, padding=(0, 2))
    console.print(Panel(body, title="[bold]📄 Page[/bold]", border_style="blue"))

    if page.headings:
        tree = Tree("[bold]Headings[/bold]", guide_style="cyan")
        for h in page.headings[:12]:
            tree.add(Text(h, style="white"))
        console.print(Panel(tree, border_style="magenta", expand=False))


def print_result_summary(result: ScrapeResult) -> None:
    """Pretty panel summarising a crawl run."""
    s = result.summary()
    stats = Table(
        title="[bold]📊 Ergebnis[/bold]",
        box=box.ROUNDED,
        header_style="bold magenta",
        border_style="magenta",
    )
    stats.add_column("Metrik", style="bold cyan")
    stats.add_column("Wert", style="bold green", justify="right")
    stats.add_row("Seiten gescrapt", str(s["pages_scraped"]))
    stats.add_row("Fehler",          str(s["errors"]))
    stats.add_row("Dauer",           f"{s['duration_seconds']} s")
    stats.add_row("Ø Antwortzeit",   f"{s['avg_response_ms']} ms")
    stats.add_row("Links gesamt",    str(s["total_links"]))
    stats.add_row("Bilder gesamt",   str(s["total_images"]))
    stats.add_row("Wörter gesamt",   f"{s['total_words']:,}")
    stats.add_row("Daten gesamt",    human_bytes(s["total_bytes"]))
    console.print(stats)

    # Top domains (if crawl crossed domains).
    hosts = Counter(urlparse(p.url).netloc for p in result.pages)
    if len(hosts) > 1:
        t = Table(
            title="[bold]🌐 Top Domains[/bold]",
            box=box.SIMPLE_HEAVY,
            header_style="bold magenta",
        )
        t.add_column("Domain", style="cyan")
        t.add_column("Seiten", style="green", justify="right")
        for host, count in hosts.most_common(8):
            t.add_row(host, str(count))
        console.print(t)

    if result.errors:
        console.print()
        err_panel = Table(box=box.MINIMAL, show_header=False, padding=(0, 1))
        err_panel.add_column(style="red")
        err_panel.add_column(style="dim")
        for err in result.errors[:8]:
            err_panel.add_row(f"✗ {err['url']}", err["reason"])
        if len(result.errors) > 8:
            err_panel.add_row("…", f"(+{len(result.errors) - 8} weitere)")
        console.print(
            Panel(err_panel, title="[bold red]Fehler[/bold red]", border_style="red")
        )


def print_links_table(page: ScrapedPage, limit: int = 20) -> None:
    """Render a numbered table of links on a page."""
    host_self = urlparse(page.url).netloc
    t = Table(
        title=f"[bold]🔗 Links auf {page.url[:60]}[/bold]",
        box=box.SIMPLE_HEAVY,
        header_style="bold magenta",
    )
    t.add_column("#", style="dim", width=4, justify="right")
    t.add_column("Typ", style="yellow", width=8)
    t.add_column("URL", style="cyan", overflow="fold")

    for i, link in enumerate(page.links[:limit], 1):
        link_host = urlparse(link).netloc
        kind = "intern" if link_host == host_self else "extern"
        style = "green" if kind == "intern" else "yellow"
        t.add_row(str(i), f"[{style}]{kind}[/{style}]", f"[link={link}]{link}[/link]")
    console.print(t)


def print_sitemap_summary(urls: list[str], sitemap_url: str, limit: int = 20) -> None:
    """Pretty summary of a sitemap fetch."""
    top_hosts = Counter(urlparse(u).netloc for u in urls)
    header = Table(box=box.MINIMAL, show_header=False, padding=(0, 1))
    header.add_column(style="bold cyan")
    header.add_column(style="white")
    header.add_row("Sitemap", f"[link={sitemap_url}]{sitemap_url}[/link]")
    header.add_row("URLs",    str(len(urls)))
    header.add_row("Hosts",   ", ".join(f"{h} ({c})" for h, c in top_hosts.most_common(3)))
    console.print(Panel(header, title="[bold]🗺️  Sitemap[/bold]", border_style="blue"))

    if urls:
        t = Table(box=box.SIMPLE, header_style="bold magenta")
        t.add_column("#", style="dim", width=4, justify="right")
        t.add_column("URL", style="cyan", overflow="fold")
        for i, u in enumerate(urls[:limit], 1):
            t.add_row(str(i), f"[link={u}]{u}[/link]")
        console.print(t)
        if len(urls) > limit:
            console.print(f"[dim](+{len(urls) - limit} weitere)[/dim]")


def _status_color(status: int) -> str:
    if status == 0:
        return "[dim]—[/dim]"
    if 200 <= status < 300:
        return f"[green]{status}[/green]"
    if 300 <= status < 400:
        return f"[yellow]{status}[/yellow]"
    return f"[red]{status}[/red]"
