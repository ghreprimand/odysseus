#!/usr/bin/env python3
"""Validate the Odysseus public discovery documentation package."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[1]
CATALOG_PATH = ROOT / "feature-catalog.json"
DOMAINS_DIR = ROOT / "domains"

EXPECTED_COMMIT = "d8a2059df8e53bc7275c45339849d14c8651e73c"
ALLOWED_STATUSES = {
    "verified", "partial", "disabled", "experimental", "legacy",
    "dead-code-candidate", "unverified"
}

LINE_RANGE_RE = re.compile(r"^L([1-9]\d*)-L([1-9]\d*)$")
FEATURE_HEADING_RE = re.compile(
    r"^##\s+`?([A-Z][A-Z0-9]*-\d{3})`?\s+(?:—|-)\s+.+$",
    re.MULTILINE,
)
LINK_RE = re.compile(r"(?<!!)\[[^\]]*\]\(([^)]+)\)")
FORBIDDEN_TERMS_RE = re.compile(
    r"(roadforge|kanban|matrix|owner link|editor link|github support|"
    r"private maintainer|OD-AUD-|[A-Z]{2,10}-AUD-\d+|TASK-\d+)",
    re.IGNORECASE,
)

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate Odysseus discovery docs.")
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=REPO_ROOT,
        help="Path to Odysseus repository root.",
    )
    return parser.parse_args()

def validate() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    errors: list[str] = []

    # 1. Validate Catalog JSON existence and content
    if not CATALOG_PATH.is_file():
        errors.append(f"Missing catalog file: {CATALOG_PATH}")
        print(f"Errors: {len(errors)}")
        for e in errors:
            print(f"ERROR: {e}")
        return 1

    try:
        catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    except Exception as e:
        errors.append(f"Failed to parse catalog JSON: {e}")
        print(f"Errors: {len(errors)}")
        for err in errors:
            print(f"ERROR: {err}")
        return 1

    if not isinstance(catalog, list):
        errors.append("feature-catalog.json must be a JSON array")
        return 1

    feature_ids = [item.get("id") for item in catalog if isinstance(item, dict)]
    if len(feature_ids) != 79:
        errors.append(f"Expected 79 unique feature IDs, found {len(feature_ids)}")
    if len(feature_ids) != len(set(feature_ids)):
        errors.append("Duplicate feature IDs found in catalog JSON")

    # Domain catalog counts
    catalog_domain_counts: dict[str, int] = {}
    for item in catalog:
        if not isinstance(item, dict):
            errors.append("Catalog item is not an object")
            continue
        fid = item.get("id", "<missing>")
        status = item.get("status")
        domain = item.get("domain", "").lower()
        catalog_domain_counts[domain] = catalog_domain_counts.get(domain, 0) + 1

        if status not in ALLOWED_STATUSES:
            errors.append(f"{fid}: Invalid status '{status}'")

        evidence_list = item.get("evidence")
        if not isinstance(evidence_list, list) or not evidence_list:
            errors.append(f"{fid}: Missing or empty evidence list")
            continue

        for ev in evidence_list:
            if not isinstance(ev, dict):
                errors.append(f"{fid}: Evidence item is not an object")
                continue
            path_str = ev.get("path")
            lr_str = str(ev.get("line_range", ""))
            if not path_str or Path(path_str).is_absolute() or ".." in Path(path_str).parts:
                errors.append(f"{fid}: Unsafe or invalid path '{path_str}'")
                continue

            # Check path exists in repo
            target_path = repo_root / path_str
            if not target_path.is_file():
                errors.append(f"{fid}: Referenced path '{path_str}' does not exist on disk")
                continue

            # Check line range format & bounds
            m = LINE_RANGE_RE.fullmatch(lr_str)
            if not m:
                errors.append(f"{fid}: Invalid line range format '{lr_str}' for path '{path_str}'")
                continue

            start, end = int(m.group(1)), int(m.group(2))
            lines_cnt = len(target_path.read_text(encoding="utf-8", errors="ignore").splitlines())
            if start > end or end > lines_cnt or start < 1:
                errors.append(
                    f"{fid}: Line range '{lr_str}' exceeds file length ({lines_cnt} lines) in '{path_str}'"
                )

    # 2. Check Domain Markdown files
    md_feature_ids: list[str] = []
    domain_files = sorted(DOMAINS_DIR.glob("*.md"))
    for df in domain_files:
        domain_name = df.stem.lower()
        content = df.read_text(encoding="utf-8")
        found_ids = FEATURE_HEADING_RE.findall(content)
        md_feature_ids.extend(found_ids)
        if len(found_ids) != catalog_domain_counts.get(domain_name, 0):
            errors.append(
                f"Domain '{domain_name}' count mismatch: catalog has {catalog_domain_counts.get(domain_name, 0)}, Markdown has {len(found_ids)}"
            )

    if sorted(md_feature_ids) != sorted(feature_ids):
        errors.append("Markdown domain feature IDs do not match catalog JSON feature IDs")

    # 3. Check for forbidden/private terms, sensitive credentials, and broken links across all docs
    for md_file in ROOT.rglob("*.md"):
        rel_md = md_file.relative_to(ROOT)
        content = md_file.read_text(encoding="utf-8")

        # Forbidden terms scan
        forbidden_matches = FORBIDDEN_TERMS_RE.findall(content)
        if forbidden_matches:
            errors.append(
                f"{rel_md}: Found forbidden/internal terms: {set(forbidden_matches)}"
            )

        # Broken local link check
        for target in LINK_RE.findall(content):
            target = target.strip().strip("<>")
            if not target or target.startswith(("#", "http://", "https://", "mailto:")):
                continue
            target_path = target.split("#", 1)[0]
            resolved = (md_file.parent / target_path).resolve()
            if not resolved.exists():
                errors.append(f"{rel_md}: Broken local link '{target}'")

    print(f"Catalog Features: {len(catalog)}")
    print(f"Domain Files: {len(domain_files)}")
    print(f"Validation Errors: {len(errors)}")
    for err in errors:
        print(f"ERROR: {err}")

    return 1 if errors else 0

if __name__ == "__main__":
    sys.exit(validate())
