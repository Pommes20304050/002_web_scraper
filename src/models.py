"""Data models for Web Scraper."""
from __future__ import annotations

import csv
import json
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional


@dataclass
class ScrapedPage:
    """A single page's scraped data."""

    url: str
    title: str = ""
    status_code: int = 0
    links: list[str] = field(default_factory=list)
    images: list[str] = field(default_factory=list)
    headings: list[str] = field(default_factory=list)
    paragraphs: list[str] = field(default_factory=list)
    meta_description: str = ""
    og_title: str = ""
    og_description: str = ""
    og_image: str = ""
    og_type: str = ""
    twitter_card: str = ""
    keywords: str = ""
    author: str = ""
    language: str = ""
    canonical_url: str = ""
    favicon: str = ""
    word_count: int = 0
    content_length: int = 0
    elapsed_ms: int = 0
    depth: int = 0
    jsonld: list[dict] = field(default_factory=list)
    scraped_at: datetime = field(default_factory=datetime.now)

    def to_dict(self, *, full: bool = False) -> dict:
        """Dictionary representation.

        full=False produces a flat summary (good for CSV).
        full=True keeps every field including nested structures (good for JSON).
        """
        if full:
            d = asdict(self)
            d["scraped_at"] = self.scraped_at.isoformat()
            return d
        return {
            "url": self.url,
            "title": self.title,
            "status_code": self.status_code,
            "depth": self.depth,
            "language": self.language,
            "word_count": self.word_count,
            "links_count": len(self.links),
            "images_count": len(self.images),
            "headings_count": len(self.headings),
            "meta_description": self.meta_description,
            "canonical_url": self.canonical_url,
            "elapsed_ms": self.elapsed_ms,
            "content_length": self.content_length,
            "scraped_at": self.scraped_at.isoformat(),
        }


@dataclass
class ScrapeResult:
    """Aggregate result of a scrape/crawl run."""

    start_url: str = ""
    pages: list[ScrapedPage] = field(default_factory=list)
    errors: list[dict] = field(default_factory=list)
    started_at: datetime = field(default_factory=datetime.now)
    finished_at: Optional[datetime] = None

    def add_page(self, page: ScrapedPage) -> None:
        self.pages.append(page)

    def add_error(self, url: str, reason: str) -> None:
        self.errors.append(
            {"url": url, "reason": reason, "time": datetime.now().isoformat()}
        )

    def finish(self) -> None:
        if self.finished_at is None:
            self.finished_at = datetime.now()

    @property
    def duration_seconds(self) -> float:
        end = self.finished_at or datetime.now()
        return (end - self.started_at).total_seconds()

    @property
    def total_links(self) -> int:
        return sum(len(p.links) for p in self.pages)

    @property
    def total_images(self) -> int:
        return sum(len(p.images) for p in self.pages)

    @property
    def total_words(self) -> int:
        return sum(p.word_count for p in self.pages)

    @property
    def total_bytes(self) -> int:
        return sum(p.content_length for p in self.pages)

    @property
    def avg_response_ms(self) -> float:
        if not self.pages:
            return 0.0
        return sum(p.elapsed_ms for p in self.pages) / len(self.pages)

    def summary(self) -> dict:
        return {
            "start_url": self.start_url,
            "pages_scraped": len(self.pages),
            "errors": len(self.errors),
            "duration_seconds": round(self.duration_seconds, 2),
            "total_links": self.total_links,
            "total_images": self.total_images,
            "total_words": self.total_words,
            "total_bytes": self.total_bytes,
            "avg_response_ms": round(self.avg_response_ms, 1),
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
        }

    # ── Exporters ──────────────────────────────────────────────────────────

    def export_json(self, path: str) -> str:
        data = {
            "summary": self.summary(),
            "pages": [p.to_dict(full=True) for p in self.pages],
            "errors": self.errors,
        }
        _ensure_dir(path)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        return path

    def export_csv(self, path: str) -> str:
        _ensure_dir(path)
        rows = [p.to_dict() for p in self.pages]
        fieldnames = rows[0].keys() if rows else ["url", "title", "status_code"]
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for row in rows:
                writer.writerow(row)
        return path

    def export_markdown(self, path: str) -> str:
        """Export a human-readable Markdown report."""
        _ensure_dir(path)
        lines: list[str] = []
        s = self.summary()
        lines.append(f"# Web Scraper Report")
        lines.append("")
        lines.append(f"- **Start-URL:** {s['start_url']}")
        lines.append(f"- **Gestartet:** {s['started_at']}")
        lines.append(f"- **Beendet:** {s['finished_at']}")
        lines.append(f"- **Dauer:** {s['duration_seconds']}s")
        lines.append(f"- **Seiten:** {s['pages_scraped']}")
        lines.append(f"- **Fehler:** {s['errors']}")
        lines.append(f"- **Links gesamt:** {s['total_links']}")
        lines.append(f"- **Bilder gesamt:** {s['total_images']}")
        lines.append(f"- **Wörter gesamt:** {s['total_words']}")
        lines.append("")
        lines.append("## Seiten")
        lines.append("")
        for p in self.pages:
            lines.append(f"### [{p.title or p.url}]({p.url})")
            if p.meta_description:
                lines.append(f"> {p.meta_description}")
            lines.append("")
            lines.append(
                f"- Status: `{p.status_code}` · "
                f"Tiefe: {p.depth} · "
                f"Wörter: {p.word_count} · "
                f"Links: {len(p.links)} · Bilder: {len(p.images)}"
            )
            if p.headings:
                lines.append("")
                lines.append("**Headings:**")
                for h in p.headings[:8]:
                    lines.append(f"- {h}")
            lines.append("")
        if self.errors:
            lines.append("## Fehler")
            lines.append("")
            for e in self.errors:
                lines.append(f"- `{e['url']}` — {e['reason']}")
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        return path


def _ensure_dir(path: str) -> None:
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)
