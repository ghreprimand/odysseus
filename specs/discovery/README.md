# Discovery guide

Discovery keeps a shared maintainer understanding of how the checked-in Odysseus code works without becoming a permanent audit system. It is a compact companion to the code for cross-cutting systems, not a feature certification or a substitute for normal testing.

## Working model

- Code is the ground truth for current behaviour. Trace current paths in source before recording a claim.
- These specs record current code-grounded behaviour and system boundaries only. They do not record accepted intent, design direction, refactor plans, or decision history.
- Keep this package in sync with code changes that alter a documented cross-cutting system, its authority boundary, or its canonical implementation location.
- Do not exhaustively revalidate existing functionality simply because it appears in a map. Investigate when there is a report, normal use visibly fails, a change affects the area, or a high-authority boundary needs review.
- Record a confirmed, actionable problem in the relevant project within the canonical Plane workspace. Keep high-level design, prioritization, ownership, and refactor discussion in Plane. Do not create parallel issue lists here.
- After implementation changes the code, update the relevant map to describe the resulting current state.
- Review safety-sensitive authority first: execution, data access, external tools, credentials, destructive operations, and unattended work.
- Cite stable source locations such as modules, routes, classes, and functions. Avoid fragile line ranges and generated evidence tables.

## Package

- [Current system map](system-map.md) describes the code-grounded subsystem boundaries.
- [Safety boundaries](safety-boundaries.md) records where review effort is most valuable.

The existing [architecture runtime inventory](../architecture-runtime-inventory.md) remains useful structural context. It is explicitly a draft snapshot; re-check its measurements against the code before using them for an implementation decision.

## How to use this package

1. Start at the subsystem in the system map and confirm the relevant source.
2. For a defect, create or update the relevant project within the canonical Plane workspace with a reproducible report and ownership.
3. For a design, prioritization, ownership, or refactor question, use a Plane thread.
4. Make and validate the implementation through the normal engineering workflow, then update this package if the code changed a documented system boundary.

This package intentionally has no generator, validator, maturity scale, feature database, or duplicate work tracker.
