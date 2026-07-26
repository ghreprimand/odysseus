# Cookbook

Features in this document are generated from [`../feature-catalog.json`](../feature-catalog.json), the canonical inventory.

## COOKBOOK-001 — Local Model Download & Recipe Lifecycle Management

- **Domain**: `cookbook`
- **Status**: `verified`
- **Evidence Maturity**: `E0`
- **Commit Verified**: `d8a2059df8e53bc7275c45339849d14c8651e73c`
- **Runtime Validation**: not-required — No separate environment-dependent runtime validation was identified during this documentation pass.

### Purpose

Downloads HuggingFace models, configures execution parameters, and manages local GGUF/MLX model servers.

### Evidence summary

- `routes/cookbook_routes.py` — `setup_cookbook_routes` — Exposes model downloading and process serving endpoints.
- `static/js/cookbook.js` — `initCookbook` — UI manager for local model library.

### Unknowns

- Disk space exhaustion during multi-gigabyte GGUF weights downloads.

## COOKBOOK-002 — Hardware Model Fitting ('What Fits?') Analysis Engine

- **Domain**: `cookbook`
- **Status**: `verified`
- **Evidence Maturity**: `E0`
- **Commit Verified**: `d8a2059df8e53bc7275c45339849d14c8651e73c`
- **Runtime Validation**: not-required — No separate environment-dependent runtime validation was identified during this documentation pass.

### Purpose

Calculates RAM/VRAM requirements, quantized size, and context overhead to determine model compatibility.

### Evidence summary

- `routes/hwfit_routes.py` — `setup_hwfit_routes` — Calculates hardware model compatibility.
- `services/hwfit/fit.py` — `calculate_fit` — Performs parameter and memory fit calculations.

### Unknowns

- Inaccurate VRAM estimation for non-standard KV-cache quantization.

## COOKBOOK-003 — HuggingFace & MLX Model Discovery Services

- **Domain**: `cookbook`
- **Status**: `verified`
- **Evidence Maturity**: `E0`
- **Commit Verified**: `d8a2059df8e53bc7275c45339849d14c8651e73c`
- **Runtime Validation**: not-required — No separate environment-dependent runtime validation was identified during this documentation pass.

### Purpose

Searches HuggingFace Hub and local MLX model repositories for compatible GGUF and MLX weights.

### Evidence summary

- `services/hwfit/hf_discovery.py` — `search_hf_models` — Queries HuggingFace API for model tags and files.

### Unknowns

- HuggingFace API rate limits when searching without an API token.

## COOKBOOK-004 — Host Docker Access for Inference Container Runtimes

- **Domain**: `cookbook`
- **Status**: `verified`
- **Evidence Maturity**: `E0`
- **Commit Verified**: `d8a2059df8e53bc7275c45339849d14c8651e73c`
- **Runtime Validation**: pending — Requires Docker access and supported physical GPU hardware.

### Purpose

Detects and connects to host Docker engine to launch containerized Ollama, vLLM, or SGLang runtimes.

### Evidence summary

- `src/host_docker_access.py` — `HostDockerAccess` — Interacts with host docker daemon.

### Unknowns

- Permission denied accessing docker socket on non-root setups.
