#!/usr/bin/env python3
"""Fetch arXiv PDFs for papers listed in vitae.html.

Usage:
    res/fetch_arxiv.py [--dry-run]
"""

import re
import sys
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
VITAE_PATH = REPO_ROOT / "vitae.html"
SCI_DIR = REPO_ROOT / "res" / "sci"

ARXIV_ENTRY_RE = re.compile(
    r'(?P<link>arxiv:<a href="https://arxiv\.org/abs/(?P<id>[^"]+)">[^<]*</a>)'
    r'(?P<after>\s*(?:,\s*pdf:<a[^>]*>[^<]*</a>)?)'
)

USER_AGENT = "Mozilla/5.0 (compatible; fetch_arxiv.py; +https://h-nicholls.space)"


# Download the PDF using requests library and save it to the path
def download_pdf(arxiv_id: str, dest_path: Path) -> None:
    url = f"https://arxiv.org/pdf/{arxiv_id}"
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=30) as response:
        data = response.read()
    if not data.startswith(b"%PDF-"):
        raise ValueError(f"response for {arxiv_id} does not look like a PDF")
    dest_path.write_bytes(data)


# Main function to fetch arXiv PDFs and update vitae.html with path to PDFs
def main(argv: list[str]) -> None:
    dry_run = "--dry-run" in argv[1:]

    text = VITAE_PATH.read_text()
    matches = list(ARXIV_ENTRY_RE.finditer(text))
    if not matches:
        print("No arxiv links found in vitae.html")
        return

    SCI_DIR.mkdir(parents=True, exist_ok=True)

    stats = {"downloaded": 0, "already_had_pdf": 0, "skipped_existing_link": 0, "failed": 0}

    def replace(match: re.Match) -> str:
        arxiv_id = match["id"]
        if match["after"].strip():
            stats["skipped_existing_link"] += 1
            return match.group(0)

        dest_name = f"{arxiv_id}.pdf"
        dest_path = SCI_DIR / dest_name

        if dest_path.exists():
            stats["already_had_pdf"] += 1
        elif dry_run:
            print(f"Would download {arxiv_id} -> res/sci/{dest_name}")
            return match.group(0)
        else:
            try:
                download_pdf(arxiv_id, dest_path)
                stats["downloaded"] += 1
                print(f"Downloaded {arxiv_id} -> res/sci/{dest_name}")
            except Exception as exc:
                print(f"Failed to download {arxiv_id}: {exc}", file=sys.stderr)
                stats["failed"] += 1
                return match.group(0)

        rel_dest = dest_path.relative_to(REPO_ROOT).as_posix()
        return f'{match["link"]}, pdf:<a href="{rel_dest}">{dest_name}</a>{match["after"]}'

    new_text = ARXIV_ENTRY_RE.sub(replace, text)

    if dry_run:
        return

    if new_text != text:
        VITAE_PATH.write_text(new_text)

    print(
        f"Done. downloaded={stats['downloaded']} "
        f"already_had_pdf={stats['already_had_pdf']} "
        f"skipped_existing_link={stats['skipped_existing_link']} "
        f"failed={stats['failed']}"
    )


if __name__ == "__main__":
    main(sys.argv)
