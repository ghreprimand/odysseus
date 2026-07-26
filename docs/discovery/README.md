# Odysseus Discovery Package

## Provisional discovery baseline

This is a commit-pinned discovery baseline and feature index for the `discovery` branch at `d8a2059df8e53bc7275c45339849d14c8651e73c`. It contains 79 feature records across 16 domains. It is **not** an authoritative architecture reference, a runtime certification, or a claim that every evidence citation is semantically valid.

Read [`BASELINE-STATUS.md`](BASELINE-STATUS.md) first for the publication status, evidence-validation totals, E2 decisions, known caveats, and the recommended next documentation work.

## Package contents

- [`feature-catalog.json`](feature-catalog.json) is the canonical machine-readable catalog.
- [`feature-catalog.md`](feature-catalog.md) and [`domains/`](domains/) are derived reading views.
- [`audit-method.md`](audit-method.md) defines feature status and evidence maturity.
- [`references/source-provenance.md`](references/source-provenance.md) records the frozen snapshot.
- [`tools/`](tools/) contains the structural, consistency, and evidence validators.

A feature status such as `verified` means implementation was identified during discovery. It does not mean every evidence locator, line range, test claim, or runtime behaviour has passed semantic validation.

## Validation

Run the commands in [`BASELINE-STATUS.md`](BASELINE-STATUS.md#validation-commands). Structural checks and semantic evidence checks have different purposes; see that status document for the current results and interpretation.
