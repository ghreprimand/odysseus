# Discovery Baseline Status

## Purpose and scope

This package is a commit-pinned discovery baseline and feature index for the `discovery` branch at frozen commit `d8a2059df8e53bc7275c45339849d14c8651e73c`. It inventories **79 feature records** across **16 domains** to help maintainers locate likely implementation areas and identify validation gaps. It is not an authoritative architecture reference or a runtime-certification record.

The canonical inventory is [`feature-catalog.json`](feature-catalog.json); [`feature-catalog.md`](feature-catalog.md) and the files in [`domains/`](domains/) are derived reading views. See [`audit-method.md`](audit-method.md) for the status and maturity definitions.

## What maintainers may use now

- Use the catalog and domain views as a frozen discovery index, including their feature IDs, stated scope, likely source locations, and declared runtime prerequisites.
- Treat a catalog status such as `verified` as meaning implementation was identified during discovery. It does **not** mean every evidence locator, line range, test claim, or runtime behaviour has passed semantic validation.
- Use the structural checks to confirm package shape and cross-view consistency; use the evidence validator to assess whether individual evidence assertions are semantically supported.

## Validation snapshot

Structural validation passes: the catalog has 79 records, the 16 domain views match it, and the package structural validators pass. All 11 focused evidence-validator tests pass.

The evidence validator found **170 evidence entries**: **82 valid**, **66 invalid**, **6 ambiguous**, and **16 unsupported**. Its non-zero exit is expected while those semantic evidence defects remain.

Structural validity checks the documentation schema, record counts, derived-view consistency, file existence, line-range bounds, links, and public-safety rules. Semantic evidence validity additionally checks whether the cited locator exists, falls within its cited range, uses a supported parser, and actually supports the feature claim. Passing the former does not establish the latter.

## E2 review decisions

E2 means directly relevant automated test evidence supports the feature claim; a test file’s existence alone is insufficient. The generated evidence report was used to reassess all ten E2 records.

| Feature | Decision | Reason |
|---|---|---|
| `CHAT-001` | Retain E2 | Two cited tests directly exercise documented streaming-related behaviour. |
| `MODEL-006` | Retain E2 | The cited device-flow test exercises the Copilot start/poll contract and verification URI. |
| `MODEL-007` | Retain E2 | The cited device-flow test exercises the ChatGPT subscription contract and verification URI. |
| `RESEARCH-003` | Demote to E1 | The cited test covers ranking, not provider connectivity or dispatch; the route-to-provider implementation path was identified. |
| `DOCUMENT-002` | Demote to E1 | The cited marker test does not support form processing or rendering; the document route does call the PDF form handlers. |
| `EMAIL-001` | Demote to E1 | The cited health test is narrower than setup, SMTP, and polling; application setup invokes the email router and its poller. |
| `SECURITY-002` | Demote to E1 | Relevant vault-password tests exist, but the cited test locator is fabricated; the application mounts the vault route implementation. |
| `SECURITY-004` | Demote to E1 | Relevant injection tests exist, but the cited locator names are fabricated; callers use the documented context guard. |
| `SECURITY-005` | Demote to E1 | Relevant guard tests exist, but the cited locator names are fabricated; route code calls the documented URL guard. |
| `PLATFORM-009` | Demote to E0 | The manifests and diagnostic script establish discovered operational artifacts, not a traced application path or directly relevant automated test. |

The current maturity distribution is **E0: 68**, **E1: 8**, **E2: 3**, **E3: 0**, **E4: 0**. Runtime validation is still pending where the catalog says it requires external services, interactive authentication, specialised hardware, or host Docker GPU support.

## Known discovery caveats

- `AGENT-004` includes a legacy no-op activity-log shim rather than active assistant-log behaviour.
- `FRONTEND-007` points to a missing `static/backgrounds.html` target; its existing variant pages do not make that route functional.
- `RESEARCH-003` retains a compatibility module that aliases the canonical search implementation, and `DOCUMENT-002` separates optional PDF viewing from form handling.
- Secret-storage and vault-command handling are distinct implementation areas; this index does not make an end-to-end security guarantee.

## Recommended next documentation work

Repair semantic evidence selectively while architecture and operations documentation is written, beginning with the seven E2 demotions and maintainer-owned feature descriptions. Do not wait for the complete evidence queue before documenting the system. Record controlled runtime observations when external services, credentials, hardware, or Docker GPU access are available, and label unsupported claims explicitly.

## Validation commands

```bash
PYTHONDONTWRITEBYTECODE=1 python3 docs/discovery/tools/validate_discovery_docs.py --repo-root .
PYTHONDONTWRITEBYTECODE=1 python3 docs/discovery/tools/validate_discovery_consistency.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest docs/discovery/tools/test_validate_discovery_evidence.py -v
PYTHONDONTWRITEBYTECODE=1 python3 docs/discovery/tools/validate_discovery_evidence.py --repo-root . --catalog docs/discovery/feature-catalog.json --output-dir <local-report-directory>
```

Supply a local report directory outside `docs/discovery/` for the final command so generated reports are not added to the package.
