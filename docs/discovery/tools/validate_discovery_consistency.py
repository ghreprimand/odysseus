#!/usr/bin/env python3

from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "feature-catalog.json"
CATALOG_MD_PATH = ROOT / "feature-catalog.md"
DOMAINS_DIR = ROOT / "domains"
REVIEWS_DIR = ROOT / "reviews"

EXPECTED_COMMIT = "d8a2059df8e53bc7275c45339849d14c8651e73c"
EXPECTED_FEATURES = 79
EXPECTED_DOMAINS = 16

VALID_STATUSES = {
    "verified",
    "partial",
    "disabled",
    "experimental",
    "legacy",
    "dead-code-candidate",
    "unverified",
}

VALID_MATURITY = {"E0", "E1", "E2", "E3", "E4"}

VALID_RUNTIME = {
    "not-required",
    "pending",
    "blocked",
    "completed",
}

REQUIRED_FIELDS = {
    "id",
    "domain",
    "name",
    "purpose",
    "status",
    "evidence_maturity",
    "verified_at_commit",
    "evidence",
    "runtime_validation",
}

FEATURE_ID_RE = re.compile(r"^[A-Z][A-Z0-9]*-\d{3}$")

DOMAIN_HEADING_RE = re.compile(
    r"^##\s+`?([A-Z][A-Z0-9]*-\d{3})`?"
    r"\s+(?:—|-)\s+(.+?)\s*$"
)

DOMAIN_FIELD_RE = re.compile(
    r"^-\s+\*\*"
    r"(Domain|Status|Evidence Maturity|Commit Verified)"
    r"\*\*:\s*(.*?)\s*$"
)

DOMAIN_RUNTIME_RE = re.compile(
    r"^-\s+\*\*Runtime Validation\*\*:\s*(.*?)\s*$"
)

REVIEW_HEADING_RE = re.compile(
    r"^###\s+(?:\d+\.\s+)?"
    r"([A-Z][A-Z0-9]*-\d{3})"
    r"\s+(?:—|-)\s+.+$"
)

REVIEW_RESULT_RE = re.compile(
    r"^-\s+\*\*Resulting Status(?:\s+and|/)\s+Maturity\*\*:"
    r"\s*`([^`]+)`\s*/\s*`([^`]+)`\s*$"
)


def clean(value: str) -> str:
    value = value.strip()

    if (
        len(value) >= 2
        and value.startswith("`")
        and value.endswith("`")
    ):
        return value[1:-1].strip()

    return value


def load_catalog(errors: list[str]) -> list[dict[str, Any]]:
    try:
        data = json.loads(
            CATALOG_PATH.read_text(encoding="utf-8")
        )
    except Exception as exc:
        errors.append(f"Unable to read catalog: {exc}")
        return []

    if isinstance(data, list):
        features = data
    elif isinstance(data, dict) and isinstance(data.get("features"), list):
        features = data["features"]
    else:
        errors.append(
            "Catalog must be an array or contain a features array"
        )
        return []

    if not all(isinstance(feature, dict) for feature in features):
        errors.append("Every catalog feature must be an object")
        return []

    return features


def validate_catalog(
    features: list[dict[str, Any]],
    errors: list[str],
) -> None:
    if len(features) != EXPECTED_FEATURES:
        errors.append(
            f"Expected {EXPECTED_FEATURES} features, "
            f"found {len(features)}"
        )

    ids = [feature.get("id") for feature in features]

    duplicates = sorted(
        feature_id
        for feature_id, count in Counter(ids).items()
        if feature_id and count > 1
    )

    if duplicates:
        errors.append(
            "Duplicate feature IDs: " + ", ".join(duplicates)
        )

    for index, feature in enumerate(features):
        feature_id = feature.get("id")
        label = (
            feature_id
            if isinstance(feature_id, str)
            else f"<index:{index}>"
        )

        missing = sorted(
            field
            for field in REQUIRED_FIELDS
            if feature.get(field) in (None, "", [])
        )

        if missing:
            errors.append(
                f"{label}: missing fields: {', '.join(missing)}"
            )

        if (
            not isinstance(feature_id, str)
            or not FEATURE_ID_RE.fullmatch(feature_id)
        ):
            errors.append(f"{label}: invalid feature ID")

        if feature.get("status") not in VALID_STATUSES:
            errors.append(
                f"{label}: invalid status "
                f"{feature.get('status')!r}"
            )

        if feature.get("evidence_maturity") not in VALID_MATURITY:
            errors.append(
                f"{label}: invalid maturity "
                f"{feature.get('evidence_maturity')!r}"
            )

        if feature.get("verified_at_commit") != EXPECTED_COMMIT:
            errors.append(
                f"{label}: incorrect verified_at_commit"
            )

        runtime = feature.get("runtime_validation")

        if not isinstance(runtime, dict):
            errors.append(
                f"{label}: runtime_validation must be an object"
            )
            continue

        required = runtime.get("required")
        runtime_status = runtime.get("status")
        reason = runtime.get("reason")

        if not isinstance(required, bool):
            errors.append(
                f"{label}: runtime required must be boolean"
            )

        if runtime_status not in VALID_RUNTIME:
            errors.append(
                f"{label}: invalid runtime status "
                f"{runtime_status!r}"
            )

        if not isinstance(reason, str) or not reason.strip():
            errors.append(
                f"{label}: runtime reason is blank"
            )

        if required is False and runtime_status != "not-required":
            errors.append(
                f"{label}: required=false requires not-required"
            )

        if required is True and runtime_status == "not-required":
            errors.append(
                f"{label}: required=true cannot be not-required"
            )


def parse_domain(
    path: Path,
    errors: list[str],
) -> dict[str, dict[str, str]]:
    records: dict[str, dict[str, str]] = {}
    current_id: str | None = None

    for line_number, line in enumerate(
        path.read_text(encoding="utf-8").splitlines(),
        start=1,
    ):
        heading = DOMAIN_HEADING_RE.match(line)

        if heading:
            current_id = heading.group(1)

            if current_id in records:
                errors.append(
                    f"{path.relative_to(ROOT)}:{line_number}: "
                    f"duplicate heading {current_id}"
                )

            records[current_id] = {
                "Name": heading.group(2).strip(),
            }
            continue

        field = DOMAIN_FIELD_RE.match(line)

        if field and current_id:
            value = clean(field.group(2))

            if not value:
                errors.append(
                    f"{path.relative_to(ROOT)}:{line_number}: "
                    f"blank {field.group(1)}"
                )

            records[current_id][field.group(1)] = value
            continue

        runtime = DOMAIN_RUNTIME_RE.match(line)

        if runtime and current_id:
            value = clean(runtime.group(1))
            runtime_status = re.split(
                r"\s+(?:—|-)\s+",
                value,
                maxsplit=1,
            )[0]
            records[current_id]["Runtime Validation"] = (
                runtime_status.strip("` ")
            )

    return records


def validate_domains(
    features: list[dict[str, Any]],
    errors: list[str],
) -> None:
    catalog = {
        feature["id"]: feature
        for feature in features
        if feature.get("id")
    }

    expected_by_domain: defaultdict[str, set[str]] = defaultdict(set)

    for feature in features:
        expected_by_domain[feature["domain"]].add(feature["id"])

    paths = sorted(DOMAINS_DIR.glob("*.md"))

    if len(paths) != EXPECTED_DOMAINS:
        errors.append(
            f"Expected {EXPECTED_DOMAINS} domain files, "
            f"found {len(paths)}"
        )

    all_found: set[str] = set()

    for path in paths:
        domain = path.stem
        records = parse_domain(path, errors)
        found = set(records)
        expected = expected_by_domain.get(domain, set())
        all_found.update(found)

        if found != expected:
            missing = sorted(expected - found)
            extra = sorted(found - expected)

            errors.append(
                f"{domain}: missing={missing}, unexpected={extra}"
            )

        for feature_id, record in records.items():
            feature = catalog.get(feature_id)

            if feature is None:
                continue

            expected_values = {
                "Name": feature["name"],
                "Domain": feature["domain"],
                "Status": feature["status"],
                "Evidence Maturity": feature["evidence_maturity"],
                "Commit Verified": feature["verified_at_commit"],
                "Runtime Validation": (
                    feature["runtime_validation"]["status"]
                ),
            }

            for field, expected_value in expected_values.items():
                actual = record.get(field)

                if actual != expected_value:
                    errors.append(
                        f"{path.relative_to(ROOT)}: "
                        f"{feature_id} {field}: "
                        f"{actual!r} != {expected_value!r}"
                    )

    if all_found != set(catalog):
        errors.append(
            "Domain Markdown IDs do not match catalog JSON"
        )


def validate_catalog_markdown(
    features: list[dict[str, Any]],
    errors: list[str],
) -> None:
    expected = {
        feature["id"]: feature
        for feature in features
    }
    found: dict[str, list[str]] = {}

    for line in CATALOG_MD_PATH.read_text(
        encoding="utf-8"
    ).splitlines():
        if not line.startswith("|"):
            continue

        cells = [
            cell.strip()
            for cell in line.strip().strip("|").split("|")
        ]

        if len(cells) < 6:
            continue

        feature_id = clean(cells[0])

        if FEATURE_ID_RE.fullmatch(feature_id):
            found[feature_id] = cells

    if set(found) != set(expected):
        errors.append(
            "feature-catalog.md IDs do not match JSON"
        )

    for feature_id, cells in found.items():
        feature = expected[feature_id]
        runtime = feature["runtime_validation"]
        runtime_display = (
            runtime["status"]
            if runtime["required"]
            else "not required"
        )

        actual = {
            "name": cells[1].replace("\\|", "|"),
            "domain": clean(cells[2]),
            "status": clean(cells[3]),
            "maturity": clean(cells[4]),
            "runtime": clean(cells[5]),
        }

        wanted = {
            "name": feature["name"],
            "domain": feature["domain"],
            "status": feature["status"],
            "maturity": feature["evidence_maturity"],
            "runtime": runtime_display,
        }

        for field, expected_value in wanted.items():
            if actual[field] != expected_value:
                errors.append(
                    f"feature-catalog.md: {feature_id} "
                    f"{field}: {actual[field]!r} "
                    f"!= {expected_value!r}"
                )


def validate_reviews(
    features: list[dict[str, Any]],
    errors: list[str],
) -> int:
    catalog = {
        feature["id"]: feature
        for feature in features
    }
    checked = 0

    for path in sorted(
        REVIEWS_DIR.glob("evidence-sample-*.md")
    ):
        current_id: str | None = None
        results: set[str] = set()

        for line_number, line in enumerate(
            path.read_text(encoding="utf-8").splitlines(),
            start=1,
        ):
            heading = REVIEW_HEADING_RE.match(line)

            if heading:
                current_id = heading.group(1)
                continue

            result = REVIEW_RESULT_RE.match(line)

            if not result or current_id is None:
                continue

            status, maturity = result.groups()
            results.add(current_id)
            checked += 1

            feature = catalog.get(current_id)

            if feature is None:
                errors.append(
                    f"{path.relative_to(ROOT)}:{line_number}: "
                    f"unknown feature {current_id}"
                )
                continue

            if feature["status"] != status:
                errors.append(
                    f"{current_id}: review status {status!r} "
                    f"!= catalog {feature['status']!r}"
                )

            if feature["evidence_maturity"] != maturity:
                errors.append(
                    f"{current_id}: review maturity {maturity!r} "
                    f"!= catalog "
                    f"{feature['evidence_maturity']!r}"
                )

        if path.name == "evidence-sample-01.md" and len(results) != 12:
            errors.append(
                f"{path.relative_to(ROOT)}: expected 12 "
                f"review results, found {len(results)}"
            )

    return checked


def validate_whitespace(errors: list[str]) -> None:
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file():
            continue

        if path.suffix not in {".md", ".json", ".py", ".txt"}:
            continue

        for line_number, line in enumerate(
            path.read_text(
                encoding="utf-8",
                errors="replace",
            ).splitlines(),
            start=1,
        ):
            if line != line.rstrip(" \t"):
                errors.append(
                    f"{path.relative_to(ROOT)}:{line_number}: "
                    "trailing whitespace"
                )

    if any(ROOT.rglob("*.pyc")):
        errors.append("Generated .pyc files exist")

    if any(
        path.is_dir()
        for path in ROOT.rglob("__pycache__")
    ):
        errors.append("__pycache__ exists")


def main() -> int:
    errors: list[str] = []
    features = load_catalog(errors)
    reviewed = 0

    if features:
        validate_catalog(features, errors)
        validate_domains(features, errors)
        validate_catalog_markdown(features, errors)
        reviewed = validate_reviews(features, errors)

    validate_whitespace(errors)

    print(f"Catalog Features: {len(features)}")
    print(
        "Unique Feature IDs:",
        len({feature.get("id") for feature in features}),
    )
    print(
        "Domain Files:",
        len(list(DOMAINS_DIR.glob("*.md"))),
    )

    if features:
        print(
            "Statuses:",
            dict(
                Counter(
                    feature.get("status")
                    for feature in features
                )
            ),
        )
        print(
            "Evidence Maturity:",
            dict(
                Counter(
                    feature.get("evidence_maturity")
                    for feature in features
                )
            ),
        )
        print(
            "Runtime Validation:",
            dict(
                Counter(
                    (
                        feature.get(
                            "runtime_validation",
                            {},
                        ).get("required"),
                        feature.get(
                            "runtime_validation",
                            {},
                        ).get("status"),
                    )
                    for feature in features
                )
            ),
        )

    print(f"Review Results Checked: {reviewed}")
    print(f"Consistency Errors: {len(errors)}")

    for error in errors:
        print(f"ERROR: {error}")

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
