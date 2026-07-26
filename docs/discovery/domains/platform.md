# Platform

Features in this document are generated from [`../feature-catalog.json`](../feature-catalog.json), the canonical inventory.

## PLATFORM-001 — Application Initialization & Lifespan Management

- **Domain**: `platform`
- **Status**: `verified`
- **Evidence Maturity**: `E0`
- **Commit Verified**: `d8a2059df8e53bc7275c45339849d14c8651e73c`
- **Runtime Validation**: not-required — No separate environment-dependent runtime validation was identified during this documentation pass.

### Purpose

Orchestrates server startup, database table migration, background daemon initialization, and clean shutdown.

### Evidence summary

- `app.py` — `_lifespan` — FastAPI lifespan context manager executing startup tasks.
- `src/app_initializer.py` — `initialize_app` — Initializes app directories, DB schemas, and logging.

### Unknowns

- Un-handled exceptions during startup halt application launch.

## PLATFORM-002 — System Health, Readiness & Version Monitoring APIs

- **Domain**: `platform`
- **Status**: `verified`
- **Evidence Maturity**: `E0`
- **Commit Verified**: `d8a2059df8e53bc7275c45339849d14c8651e73c`
- **Runtime Validation**: not-required — No separate environment-dependent runtime validation was identified during this documentation pass.

### Purpose

Exposes Liveness (/api/health), Readiness (/api/ready), App Version (/api/version), and Client Perf APIs.

### Evidence summary

- `app.py` — `readiness_check` — Performs system component integrity check.
- `src/readiness.py` — `check_readiness` — Checks database, storage, and key paths for read/write access.

### Unknowns

- Readiness check delays if verifying connectivity to offline remote endpoints.

## PLATFORM-003 — Database Schema, Migrations & SQLite Persistence

- **Domain**: `platform`
- **Status**: `verified`
- **Evidence Maturity**: `E0`
- **Commit Verified**: `d8a2059df8e53bc7275c45339849d14c8651e73c`
- **Runtime Validation**: not-required — No separate environment-dependent runtime validation was identified during this documentation pass.

### Purpose

Defines core relational tables (users, tokens, tasks, sessions) and executes automated SQLite schema upgrades.

### Evidence summary

- `core/database.py` — `init_db` — Creates ORM tables and establishes connection pool.
- `scripts/update_database.py` — `run_migrations` — Applies missing schema columns and indices.

### Unknowns

- SQLite file lock contention under high concurrent write loads.

## PLATFORM-004 — User Data Export & Import Backup Infrastructure

- **Domain**: `platform`
- **Status**: `verified`
- **Evidence Maturity**: `E0`
- **Commit Verified**: `d8a2059df8e53bc7275c45339849d14c8651e73c`
- **Runtime Validation**: not-required — No separate environment-dependent runtime validation was identified during this documentation pass.

### Purpose

Exports complete user workspace state (sessions, memory, skills, notes, presets) into a zip archive.

### Evidence summary

- `routes/backup_routes.py` — `setup_backup_routes` — Handles workspace data export and import upload unpack.
- `docs/backup-restore.md` — `Documentation` — Backup and restore operational documentation.

### Unknowns

- Corrupt archive files causing partial data restore.

## PLATFORM-005 — File Cleanup & Storage Maintenance Engine

- **Domain**: `platform`
- **Status**: `verified`
- **Evidence Maturity**: `E0`
- **Commit Verified**: `d8a2059df8e53bc7275c45339849d14c8651e73c`
- **Runtime Validation**: not-required — No separate environment-dependent runtime validation was identified during this documentation pass.

### Purpose

Scans data directories for orphaned files, old uploads, temporary vision images, and frees disk space.

### Evidence summary

- `routes/cleanup/cleanup_routes.py` — `@router.get('/preview')` — Previews reclaimable disk space across storage directories.
- `src/cleanup_service.py` — `CleanupService` — Executes filesystem purge of orphaned asset files.

### Unknowns

- Deletes files uploaded in active sessions if retention window is set too short.

## PLATFORM-006 — System Health & RAG Diagnostic Suite

- **Domain**: `platform`
- **Status**: `verified`
- **Evidence Maturity**: `E0`
- **Commit Verified**: `d8a2059df8e53bc7275c45339849d14c8651e73c`
- **Runtime Validation**: not-required — No separate environment-dependent runtime validation was identified during this documentation pass.

### Purpose

Executes real-time integrity diagnostics across ChromaDB, SearXNG, local models, and network interfaces.

### Evidence summary

- `routes/diagnostics_routes.py` — `setup_diagnostics_routes` — Runs subsystem health check suite.
- `src/service_health.py` — `collect_health_status` — Inspects vector database, email, search, and local provider status.

### Unknowns

- Diagnostic timeout if external search provider is unreachable.

## PLATFORM-007 — Desktop CLI Utilities & Shell Integration Tools

- **Domain**: `platform`
- **Status**: `verified`
- **Evidence Maturity**: `E0`
- **Commit Verified**: `d8a2059df8e53bc7275c45339849d14c8651e73c`
- **Runtime Validation**: not-required — No separate environment-dependent runtime validation was identified during this documentation pass.

### Purpose

Provides command-line interface tools (`odysseus`, `odysseus-mcp`, `odysseus-mail`) for terminal usage.

### Evidence summary

- `scripts/_lib/cli.py` — `main` — Shared CLI framework for terminal helper commands.
- `scripts/odysseus` — `odysseus` — Main terminal launcher script.

### Unknowns

- Outdated CLI scripts if backend API schemas change.

## PLATFORM-008 — Desktop Companion App Integration

- **Domain**: `platform`
- **Status**: `verified`
- **Evidence Maturity**: `E0`
- **Commit Verified**: `d8a2059df8e53bc7275c45339849d14c8651e73c`
- **Runtime Validation**: not-required — No separate environment-dependent runtime validation was identified during this documentation pass.

### Purpose

Provides API routes and pairing mechanisms for the native macOS/desktop menu bar companion app.

### Evidence summary

- `companion/routes.py` — `setup_companion_routes` — Endpoints for pairing and status sync with desktop companion.
- `companion/pairing.py` — `PairingManager` — Generates and validates companion pairing codes.

### Unknowns

- Pairing code expiration timing window.

## PLATFORM-009 — Docker Containerization & GPU Hardware Manifests

- **Domain**: `platform`
- **Status**: `verified`
- **Evidence Maturity**: `E0`
- **Commit Verified**: `d8a2059df8e53bc7275c45339849d14c8651e73c`
- **Runtime Validation**: pending — Requires Docker GPU pass-through and compatible host drivers.

### Purpose

Provides multi-stage Dockerfile and Docker Compose manifests for CPU, NVIDIA CUDA, and AMD ROCm GPUs.

### Evidence summary

- `Dockerfile` — `multi-stage-build` — Multi-stage container build environment.
- `docker-compose.gpu-nvidia.yml` — `nvidia-gpu-manifest` — NVIDIA GPU pass-through container specification.
- `scripts/check-docker-gpu.sh` — `check-docker-gpu` — Automated diagnostic test script for host NVIDIA GPU passthrough.

### Unknowns

- Driver version incompatibility with host NVIDIA/AMD kernel drivers.

## PLATFORM-010 — Legacy FAISS Vector Index Migration Script

- **Domain**: `platform`
- **Status**: `legacy`
- **Evidence Maturity**: `E0`
- **Commit Verified**: `d8a2059df8e53bc7275c45339849d14c8651e73c`
- **Runtime Validation**: not-required — No separate environment-dependent runtime validation was identified during this documentation pass.

### Purpose

Legacy utility script to migrate older FAISS vector indices into ChromaDB.

### Evidence summary

- `scripts/migrate_faiss_to_chroma.py` — `migrate_faiss` — Reads FAISS vector index files and writes to ChromaDB collection.

### Unknowns

- Superseded by native ChromaDB vector index pipeline.
