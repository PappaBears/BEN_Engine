#!/usr/bin/env python3
"""Check that every relative link and image in the repository's Markdown files points at a file that exists.

Usage: python scripts/check_links.py [repo_root]
Exit status 1 when a broken target is found. External (http/https/mailto), anchor-only and
template placeholders (e.g. `<tier>`) are skipped.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import unquote

EXCLUDE_DIRS = {".git", "dist", "node_modules", ".schreiber-ai", "__pycache__"}
# [text](target) and ![alt](target); the target may carry a title after a space
INLINE = re.compile(r"!?\[[^\]]*\]\(\s*<?([^)\s>]+)>?(?:\s+\"[^\"]*\")?\s*\)")
# [label]: target  (reference definitions)
REFDEF = re.compile(r"^\s*\[[^\]]+\]:\s*<?(\S+)>?", re.M)
HTML_SRC = re.compile(r"<(?:img|a|source)\b[^>]*?\b(?:src|href)=[\"']([^\"']+)[\"']", re.I)
FENCE = re.compile(r"```.*?```", re.S)
INLINE_CODE = re.compile(r"`[^`\n]*`")


def iter_markdown(root: Path):
    for path in sorted(root.rglob("*.md")):
        if any(part in EXCLUDE_DIRS for part in path.relative_to(root).parts):
            continue
        yield path


def targets(text: str):
    text = FENCE.sub("", text)
    text = INLINE_CODE.sub("", text)
    for m in INLINE.finditer(text):
        yield m.group(1)
    for m in REFDEF.finditer(text):
        yield m.group(1)
    for m in HTML_SRC.finditer(text):
        yield m.group(1)


def is_external(t: str) -> bool:
    return bool(re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", t)) or t.startswith("//")


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]).resolve()
    checked = broken = files = 0
    failures: list[tuple[Path, str]] = []
    for md in iter_markdown(root):
        files += 1
        text = md.read_text(encoding="utf-8", errors="replace")
        for t in targets(text):
            if is_external(t) or t.startswith("#") or "<" in t or "{" in t:
                continue
            path_part = unquote(t.split("#", 1)[0].split("?", 1)[0])
            if not path_part:
                continue
            checked += 1
            target = (root / path_part.lstrip("/")) if path_part.startswith("/") else (md.parent / path_part)
            if not target.exists():
                broken += 1
                failures.append((md.relative_to(root), t))
    for md, t in failures:
        print(f"BROKEN  {md}: {t}")
    print(f"{files} markdown files, {checked} relative targets checked, {broken} broken")
    return 1 if broken else 0


if __name__ == "__main__":
    sys.exit(main())
