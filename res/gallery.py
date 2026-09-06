#!/usr/bin/env python3
"""Manage photographs in an art gallery.

Ingests, removes, and lists photos in res/art/<gallery>/, keeping the
gallery's HTML page (art_<gallery>.html) in sync.

Usage:
    res/gallery.py <gallery> add <photo> [<photo> ...]
    res/gallery.py <gallery> remove <photo> [<photo> ...]
    res/gallery.py <gallery> rename <old> <new>
    res/gallery.py <gallery> renamegallery <new>
    res/gallery.py <gallery> list

Examples:
    res/gallery.py people add ~/Pictures/IMG_1234.JPG ~/Pictures/IMG_1235.JPG
    res/gallery.py people remove IMG_1234.JPG
    res/gallery.py people rename IMG_1234.JPG "Family portrait"
    res/gallery.py people renamegallery portraits
    res/gallery.py people list

The gallery name must match an existing res/art/<gallery>/ directory and
art_<gallery>.html page (e.g. "people", "places"). For "remove" and
"rename", <photo>/<old> may be given as the original filename (e.g.
IMG_1234.JPG), the stored filename (e.g. img_1234.jpeg), or a path to
either — only the stem is used to locate the stored files. "rename" only
changes the caption text shown in the HTML page; it does not touch the
underlying image files. "renamegallery" moves res/art/<gallery>/ to
res/art/<new>/, renames art_<gallery>.html to art_<new>.html, and updates
any HTML files (e.g. art.html) that link to the old page.
"""

import argparse
import re
import sys
from pathlib import Path

from PIL import Image, ImageOps

MAX_SIZE = 1024
THUMB_SIZE = 240
JPEG_QUALITY = 80

REPO_ROOT = Path(__file__).resolve().parent.parent
ART_DIR = REPO_ROOT / "res" / "art"

ENTRY_RE = re.compile(
    r'<li><a href="(?P<href>[^"]+)">.*?<img src="(?P<src>[^"]+)"[^>]*>'
    r'<br>(?P<caption>[^<]*)</a></li>',
    re.DOTALL,
)


def gallery_paths(gallery: str) -> tuple[Path, Path]:
    html_path = REPO_ROOT / f"art_{gallery}.html"
    if not html_path.exists():
        raise SystemExit(f"Gallery page not found: {html_path.name}")
    return ART_DIR / gallery, html_path


def make_full(src: Image.Image) -> Image.Image:
    img = ImageOps.exif_transpose(src).convert("RGB")
    img.thumbnail((MAX_SIZE, MAX_SIZE), Image.LANCZOS)
    return img


def make_thumb(src: Image.Image) -> Image.Image:
    img = ImageOps.exif_transpose(src).convert("RGB")
    side = min(img.width, img.height)
    left = (img.width - side) // 2
    top = (img.height - side) // 2
    img = img.crop((left, top, left + side, top + side))
    img = img.resize((THUMB_SIZE, THUMB_SIZE), Image.LANCZOS)
    return img


def insert_entry(html_path: Path, entry: str) -> None:
    text = html_path.read_text()
    marker = "<div id=\"content\"><ul>\n"
    idx = text.index(marker) + len(marker)
    text = text[:idx] + entry + "\n" + text[idx:]
    html_path.write_text(text)


def remove_entry(html_path: Path, rel_dest: str) -> bool:
    text = html_path.read_text()
    pattern = re.compile(
        r'<li><a href="' + re.escape(rel_dest) + r'".*?</li>\n?'
    )
    new_text, count = pattern.subn("", text)
    if count:
        html_path.write_text(new_text)
    return bool(count)


def rename_entry(html_path: Path, rel_dest: str, new_caption: str) -> bool:
    text = html_path.read_text()
    pattern = re.compile(
        r'(<li><a href="' + re.escape(rel_dest) + r'">.*?<br>)'
        r'[^<]*(</a></li>)',
        re.DOTALL,
    )
    new_text, count = pattern.subn(
        lambda m: m.group(1) + new_caption + m.group(2), text
    )
    if count:
        html_path.write_text(new_text)
    return bool(count)


def cmd_add(gallery: str, photo_args: list[str]) -> None:
    gallery_dir, html_path = gallery_paths(gallery)
    full_dir = gallery_dir / "full"
    thumb_dir = gallery_dir / "thumb"
    full_dir.mkdir(parents=True, exist_ok=True)
    thumb_dir.mkdir(parents=True, exist_ok=True)

    for photo_arg in photo_args:
        photo_path = Path(photo_arg).expanduser().resolve()
        if not photo_path.exists():
            raise SystemExit(f"Photo not found: {photo_path}")

        caption = photo_path.name.upper()
        caption = re.sub(r"\.JPEG$", ".JPG", caption)
        stem = photo_path.stem.lower()
        dest_name = f"{stem}.jpeg"
        dest_path = full_dir / dest_name
        thumb_path = thumb_dir / dest_name

        if dest_path.exists() or thumb_path.exists():
            raise SystemExit(f"Refusing to overwrite existing file: {dest_path}")

        with Image.open(photo_path) as src:
            make_full(src).save(dest_path, "JPEG", quality=JPEG_QUALITY)
        with Image.open(photo_path) as src:
            make_thumb(src).save(thumb_path, "JPEG", quality=JPEG_QUALITY)

        rel_dest = dest_path.relative_to(REPO_ROOT).as_posix()
        rel_thumb = thumb_path.relative_to(REPO_ROOT).as_posix()
        entry = (
            f'<li><a href="{rel_dest}"><img src="{rel_thumb}" '
            f'width="{THUMB_SIZE}" height="{THUMB_SIZE}"><br>{caption}</a></li>'
        )
        insert_entry(html_path, entry)
        print(f"Added {photo_path.name} -> {rel_dest} ({html_path.name})")


def cmd_remove(gallery: str, photo_args: list[str]) -> None:
    gallery_dir, html_path = gallery_paths(gallery)

    for photo_ref in photo_args:
        stem = Path(photo_ref).stem.lower()
        dest_name = f"{stem}.jpeg"
        dest_path = gallery_dir / "full" / dest_name
        thumb_path = gallery_dir / "thumb" / dest_name
        rel_dest = dest_path.relative_to(REPO_ROOT).as_posix()

        removed_any = False
        for path in (dest_path, thumb_path):
            if path.exists():
                path.unlink()
                removed_any = True

        entry_removed = remove_entry(html_path, rel_dest)

        if not removed_any and not entry_removed:
            raise SystemExit(f"No files or gallery entry found for '{photo_ref}' in '{gallery}'")

        print(f"Removed {photo_ref} from {gallery} (files={removed_any}, html_entry={entry_removed})")


def cmd_rename(gallery: str, old: str, new: str) -> None:
    gallery_dir, html_path = gallery_paths(gallery)

    stem = Path(old).stem.lower()
    dest_name = f"{stem}.jpeg"
    dest_path = gallery_dir / "full" / dest_name
    rel_dest = dest_path.relative_to(REPO_ROOT).as_posix()

    if not rename_entry(html_path, rel_dest, new):
        raise SystemExit(f"No gallery entry found for '{old}' in '{gallery}'")

    print(f"Renamed '{old}' -> '{new}' in {gallery} ({html_path.name})")


def cmd_renamegallery(old_gallery: str, new_gallery: str) -> None:
    old_dir = ART_DIR / old_gallery
    new_dir = ART_DIR / new_gallery
    old_html = REPO_ROOT / f"art_{old_gallery}.html"
    new_html = REPO_ROOT / f"art_{new_gallery}.html"

    if not old_dir.exists():
        raise SystemExit(f"Gallery directory not found: {old_dir.relative_to(REPO_ROOT)}")
    if not old_html.exists():
        raise SystemExit(f"Gallery page not found: {old_html.name}")
    if new_dir.exists():
        raise SystemExit(f"Target gallery directory already exists: {new_dir.relative_to(REPO_ROOT)}")
    if new_html.exists():
        raise SystemExit(f"Target gallery page already exists: {new_html.name}")

    old_dir.rename(new_dir)
    old_html.rename(new_html)

    text = new_html.read_text()
    text = text.replace(f"res/art/{old_gallery}/", f"res/art/{new_gallery}/")
    new_html.write_text(text)

    updated_refs = []
    for html_file in sorted(REPO_ROOT.glob("*.html")):
        if html_file == new_html:
            continue
        text = html_file.read_text()
        new_text = text.replace(f'"art_{old_gallery}.html"', f'"art_{new_gallery}.html"')
        if new_text != text:
            html_file.write_text(new_text)
            updated_refs.append(html_file.name)

    print(f"Renamed gallery '{old_gallery}' -> '{new_gallery}'")
    print(f"  {old_dir.relative_to(REPO_ROOT)} -> {new_dir.relative_to(REPO_ROOT)}")
    print(f"  {old_html.name} -> {new_html.name}")
    if updated_refs:
        print(f"  updated references in: {', '.join(updated_refs)}")


def cmd_list(gallery: str) -> None:
    _, html_path = gallery_paths(gallery)
    text = html_path.read_text()
    matches = list(ENTRY_RE.finditer(text))
    if not matches:
        print(f"No photos in gallery '{gallery}'")
        return

    headers = ("NAME", "CAPTION", "HREF")
    rows = [(Path(m["href"]).stem, m["caption"], m["href"]) for m in matches]
    widths = [max(len(header), *(len(row[i]) for row in rows)) for i, header in enumerate(headers)]

    def format_row(row: tuple[str, str, str]) -> str:
        return "  ".join(value.ljust(width) for value, width in zip(row, widths))

    print(format_row(headers))
    for row in rows:
        print(format_row(row))
    print(f"{len(matches)} photo(s) in gallery '{gallery}'")


def main(argv: list[str]) -> None:
    parser = argparse.ArgumentParser(prog="gallery.py", description=__doc__.splitlines()[0])
    parser.add_argument("gallery", help="gallery name, e.g. 'people' or 'places'")
    subparsers = parser.add_subparsers(dest="command", required=True)

    add_parser = subparsers.add_parser("add", help="add one or more photos")
    add_parser.add_argument("photos", nargs="+", help="path(s) to source photo(s)")

    remove_parser = subparsers.add_parser("remove", help="remove one or more photos")
    remove_parser.add_argument("photos", nargs="+", help="filename(s) or path(s) of photo(s) to remove")

    rename_parser = subparsers.add_parser(
        "rename", help="change the displayed caption of a photo (does not touch image files)"
    )
    rename_parser.add_argument("old", help="filename or path identifying the existing photo")
    rename_parser.add_argument("new", help="new caption text to display")

    renamegallery_parser = subparsers.add_parser(
        "renamegallery", help="rename the whole gallery, moving its files and updating the HTML"
    )
    renamegallery_parser.add_argument("new", help="new gallery name")

    subparsers.add_parser("list", help="list photos currently in the gallery")

    args = parser.parse_args(argv[1:])

    if args.command == "add":
        cmd_add(args.gallery, args.photos)
    elif args.command == "remove":
        cmd_remove(args.gallery, args.photos)
    elif args.command == "rename":
        cmd_rename(args.gallery, args.old, args.new)
    elif args.command == "renamegallery":
        cmd_renamegallery(args.gallery, args.new)
    elif args.command == "list":
        cmd_list(args.gallery)


if __name__ == "__main__":
    main(sys.argv)
