# Odysseus discovery maps

Compact, code-grounded maps of the cross-cutting systems in the checked-in Odysseus codebase. They are not a feature certification or substitute for normal testing, and do not become a permanent audit system.

> [!IMPORTANT]
> Code is the source of truth for current behaviour. These specifications describe only the checked-in system and its current boundaries; keep them synchronized with relevant code changes.

## Explore the maps

| Document | Purpose |
|---|---|
| [Current system map](system-map.md) | Explains the current subsystem boundaries, implementation locations, confirmed problems, and factual open questions. |
| [Safety boundaries](safety-boundaries.md) | Maps broad authority, safeguards, confirmed risks or gaps, and unverified behaviour. |

## Working rules

- **Trace the code first.** Confirm the current path in source before recording a claim.
- **Keep specs current-state only.** Do not record intentions, design direction, refactor plans, or decision history here.
- **Synchronize with code.** Update this package when a code change alters a documented cross-cutting system, authority boundary, or canonical implementation location.
- **Investigate with cause.** Do not exhaustively revalidate existing functionality without a report, visible failure, relevant change, or high-authority review need.
- **Keep planning in Plane.** Record confirmed problems in the relevant project within the canonical Plane workspace; keep high-level design, prioritization, ownership, and refactor discussion there.
- **Review authority carefully.** Give execution, data access, external tools, credentials, destructive operations, and unattended work focused review.
- **Use stable locations.** Cite modules, routes, classes, and functions instead of fragile line ranges or generated evidence tables.

## Working flow

1. Start with the relevant map and trace the cited code.
2. For a defect, create or update the relevant project within the canonical Plane workspace with a reproducible report and ownership.
3. Use a Plane thread for design, prioritization, ownership, or refactor discussion.
4. After implementation changes the code, update the affected map to describe the resulting current state.

> [!NOTE]
> This package intentionally contains no generator, validator, maturity scale, feature database, or parallel work tracker. The [architecture runtime inventory](../architecture-runtime-inventory.md) remains useful structural context, but is an explicitly draft snapshot.
