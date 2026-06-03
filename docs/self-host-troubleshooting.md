# Self-Host Troubleshooting

Odysseus is a local-first app with several moving parts: the web app, SQLite,
ChromaDB, SearXNG, ntfy, model servers, browser MCP, and optional Cookbook
serve engines. Most setup problems are one of three things:

- a service is not running,
- Odysseus is pointed at the wrong host/port, or
- Docker/native networking is being mixed up.

Use this page as a quick runbook before digging through logs.

## First Checks

### Docker installs

```bash
docker compose ps
docker compose logs --tail=160 odysseus
docker compose logs --tail=120 chromadb
docker compose logs --tail=120 searxng
```

Useful direct probes from the host:

```bash
curl -fsS http://127.0.0.1:7000/api/health
curl -fsS http://127.0.0.1:8100/api/v2/heartbeat || curl -fsS http://127.0.0.1:8100/api/v1/heartbeat
curl -I http://127.0.0.1:8080
```

If the web UI port is busy, set a different host port in `.env`:

```dotenv
APP_PORT=7001
```

Then recreate the service:

```bash
docker compose up -d --build
```

### Native installs

```bash
python --version
python -m py_compile app.py routes/*.py src/*.py
python -m uvicorn app:app --host 127.0.0.1 --port 7000
```

If you use the Cookbook for background downloads or serves, make sure `tmux` is
installed:

```bash
tmux -V
```

### Browser checks

Open the app at the exact host and port where it is listening:

```text
http://127.0.0.1:7000
```

If you already had Odysseus open while updating, hard refresh the browser so it
reloads `static/js/*.js` and `static/style.css`.

## Login And First Setup

### Generated admin password does not work

On first setup, Odysseus creates an admin user named `admin` unless
`ODYSSEUS_ADMIN_USER` is set. The generated password is printed once.

For Docker:

```bash
docker compose logs odysseus | grep -i admin
```

For native installs, check the terminal that ran:

```bash
python setup.py
```

Usernames are normalized to lowercase. If you pre-seeded
`ODYSSEUS_ADMIN_USER=AdminUser`, log in as:

```text
adminuser
```

If you intentionally need a fresh local setup, stop Odysseus first, then move
the auth file aside:

```bash
mv data/auth.json data/auth.json.bak
python setup.py
```

Do not delete `data/auth.json` on a shared install unless you understand who
will regain admin access after setup runs again.

### Browser warns about an insecure password field

Odysseus serves plain HTTP by default. This is expected on localhost. If the app
is reachable from another device, put it behind HTTPS with a reverse proxy
before trusting login sessions or API tokens over the network.

## Docker Networking

### Localhost means different things in Docker

Inside the Odysseus container, `localhost` means the container itself, not your
host machine.

Use these defaults:

| Service | Docker-to-Docker URL | Host browser URL |
|---|---|---|
| Odysseus | `http://odysseus:7000` | `http://127.0.0.1:7000` |
| ChromaDB | `http://chromadb:8000` | `http://127.0.0.1:8100` |
| SearXNG | `http://searxng:8080` | `http://127.0.0.1:8080` |
| Host Ollama | `http://host.docker.internal:11434/v1` | `http://127.0.0.1:11434/v1` |

If a model server runs on the host and Odysseus runs in Docker, point Odysseus
at `host.docker.internal`, not `localhost`.

### Service is reachable on the host but not from Odysseus

Check the URL Odysseus is using. For Docker, `.env` values such as
`SEARXNG_INSTANCE` and `CHROMADB_HOST` may be overridden by Compose service
names.

```bash
docker compose exec odysseus env | grep -E 'SEARXNG|CHROMA|OLLAMA|APP_'
```

## ChromaDB And Memory

### ChromaDB heartbeat fails

For Docker:

```bash
docker compose ps chromadb
docker compose logs --tail=120 chromadb
curl -fsS http://127.0.0.1:8100/api/v2/heartbeat || curl -fsS http://127.0.0.1:8100/api/v1/heartbeat
```

For native installs, either run a Chroma server yourself or disable RAG/memory
features you do not need. A typical local Chroma command is:

```bash
chroma run --host 127.0.0.1 --port 8100 --path data/chroma
```

Then set:

```dotenv
CHROMADB_HOST=localhost
CHROMADB_PORT=8100
```

### Embedding endpoint returns 404

Ollama's OpenAI-compatible API may not expose `/v1/embeddings` for every model.
Odysseus can fall back to local FastEmbed. A startup warning about the HTTP
embedding API being unavailable is not always fatal if FastEmbed loads after it.

Look for:

```text
Using local FastEmbed
MemoryVectorStore ready
```

## SearXNG And Search

### Web search fails or SearXNG is not reachable

For Docker:

```bash
docker compose ps searxng
docker compose logs --tail=120 searxng
curl -I http://127.0.0.1:8080
```

For native installs, either run SearXNG yourself or choose another search
provider in **Settings -> Search**.

Docker Compose normally lets Odysseus reach SearXNG at:

```text
http://searxng:8080
```

The host browser normally reaches it at:

```text
http://127.0.0.1:8080
```

### "Permission denied" around SearXNG

Recreate the service and its generated config first:

```bash
docker compose up -d --build --force-recreate searxng
docker compose logs --tail=120 searxng
```

If you mounted custom SearXNG files, make sure the container user can read them.
For a stock Odysseus install, prefer the generated Docker volume over manually
editing files inside the container.

## Ollama And Model Endpoints

### Odysseus cannot see Ollama from Docker

Start Ollama so it listens beyond its own loopback interface:

```bash
OLLAMA_HOST=0.0.0.0:11434 ollama serve
```

Then add this endpoint in **Settings -> Add Models**:

```text
http://host.docker.internal:11434/v1
```

Check from the host:

```bash
curl -fsS http://127.0.0.1:11434/api/tags
```

Check from the container:

```bash
docker compose exec odysseus python - <<'PY'
import httpx
print(httpx.get("http://host.docker.internal:11434/api/tags", timeout=5).status_code)
PY
```

### Native Odysseus cannot see Ollama

Use:

```text
http://localhost:11434/v1
```

or:

```text
http://127.0.0.1:11434/v1
```

Then test in **Settings -> Add Models**.

### Models appear but chat fails

Check whether the endpoint is OpenAI-compatible and whether chat completions are
enabled:

```bash
curl -fsS http://127.0.0.1:11434/v1/models
```

For vLLM, SGLang, llama.cpp, or LM Studio, confirm the server is using the
OpenAI-compatible route expected by Odysseus.

## Browser MCP

### Browser automation tools are missing

Odysseus skips the npx-based browser MCP on fresh installs unless the package is
already cached locally. This prevents startup from hanging on a large Playwright
download.

Install/cache it once:

```bash
npx -y @playwright/mcp@latest --version
```

Restart Odysseus. You should see a startup log similar to:

```text
Built-in NPX server registered: Built-in: Browser
```

If the command downloads browsers or system dependencies, let it finish before
restarting Odysseus.

## ntfy Reminders

### ntfy is configured but the phone does not receive reminders

First verify Odysseus can reach the ntfy server URL configured in
**Settings -> Integrations**.

For a local bundled ntfy server, the host URL is usually:

```text
http://127.0.0.1:8091
```

If your phone is not on the same localhost, it cannot subscribe to that URL. For
phone delivery, expose ntfy on a LAN or Tailscale address and update both:

```dotenv
NTFY_BIND=100.x.y.z
NTFY_BASE_URL=http://100.x.y.z:8091
```

Then recreate ntfy:

```bash
docker compose up -d --build ntfy
```

On Android, non-ntfy.sh servers may need the ntfy app's instant delivery
settings adjusted. If delayed delivery is the only symptom, check the phone app
settings before changing Odysseus.

## Email

### Email list is empty or logs say IMAP/SMTP is not configured

Email accounts are configured in **Settings -> Integrations**. Odysseus needs
IMAP for reading and SMTP for sending.

Common local-stack gotcha: some Dovecot test stacks require explicit cleartext
auth settings when TLS is not configured. Prefer TLS for anything beyond a local
throwaway mailbox.

If you configured multiple accounts, confirm the account you expect is enabled
and selected as default.

## Cookbook

Cookbook failures often come from environment differences: GPU runtime, shell,
tmux, Python package state, Hugging Face metadata, or serve-engine support.

### First Cookbook checks

```bash
docker compose logs --tail=160 odysseus
docker compose exec odysseus tmux -V
docker compose exec odysseus python --version
```

For native installs:

```bash
tmux -V
python --version
```

Inside Odysseus, check the Cookbook task output. It usually contains the exact
download, dependency, or serve command that failed.

### Downloads fail or never show progress

Check available disk space and the cache path:

```bash
df -h
du -sh data/huggingface data/local 2>/dev/null || true
```

Docker stores Cookbook downloads in:

```text
./data/huggingface
```

Cookbook-installed CLIs and serve engines live in:

```text
./data/local
```

If a partial download is corrupt, remove only the affected model directory, not
the whole `data/` directory.

### vLLM/SGLang does not work on macOS

This is expected. vLLM and SGLang are CUDA/ROCm-oriented. On Apple Silicon, use
native Odysseus with Ollama or llama.cpp/Metal-backed serving.

### Docker on macOS cannot see the Metal GPU

This is expected. Docker Desktop on macOS does not pass the Metal GPU into Linux
containers. For GPU-accelerated local serving on Apple Silicon, run Odysseus
natively with:

```bash
./start-macos.sh
```

### NVIDIA GPU is not detected in Docker

Install and configure the NVIDIA container runtime on the host, then set:

```dotenv
COMPOSE_FILE=docker-compose.yml:docker/gpu.nvidia.yml
```

Verify:

```bash
docker compose exec odysseus nvidia-smi -L
```

If that command fails, fix the host Docker GPU runtime before debugging
Odysseus.

### llama.cpp builds CPU-only despite a working GPU

`nvidia-smi` passing inside the container only proves driver passthrough. It
does not mean a CUDA toolkit was present when Cookbook compiled `llama-server`.
The first time you serve, Cookbook builds llama.cpp from source and picks its
backend automatically:

- ROCm/HIP toolchain present: HIP (AMD) build
- `nvcc` present: CUDA build
- neither: CPU-only build

If no `nvcc` was on `PATH` at build time, you get a CPU-only `llama-server`, and
at serve time it prints:

```text
warning: no usable GPU found, --gpu-layers option will be ignored
warning: one possible reason is that llama.cpp was compiled without GPU support
```

The build runs once. Cookbook only compiles when `llama-server` is not already
on `PATH`, so re-launching the serve task reuses the cached CPU-only binary and
will not rebuild on its own. To get a CUDA build you must make a toolkit
available and then clear the cached build.

1. Open a shell in the container:

   ```bash
   docker compose exec odysseus bash
   ```

2. Confirm the cause (most often there is no compiler):

   ```bash
   command -v nvcc || echo "no nvcc: this is why the build was CPU-only"
   ```

3. Make a CUDA toolkit available. The bootstrap auto-detects CUDA pip wheels
   under `~/.local`, so the lightest option is:

   ```bash
   pip install --user nvidia-cuda-nvcc-cu12 nvidia-cuda-runtime-cu12
   ```

   Installing the full CUDA Toolkit works too and is more robust. Match the CUDA
   version to your GPU: older cards (Pascal sm_61, the GTX 10-series) need
   CUDA 12.8+ and cannot build with CUDA 13.

4. Clear the cached CPU-only build so the next serve recompiles, then launch the
   serve task again from Cookbook:

   ```bash
   rm -f ~/bin/llama-server
   rm -rf ~/llama.cpp/build
   ```

   A successful CUDA build logs `CUDA nvcc found ... building llama-server with
   CUDA (GPU) support`, and the serve no longer prints the CPU-only warning.

Hand changes inside the container can be lost on a full `docker compose down`
and rebuild, so once it works, bake the toolkit into your image to make it
stick. If the rebuild fails with `Could NOT find CUDAToolkit (missing:
CUDA_CUDART)`, the compiler is present but the runtime is not; install the
matching `cudart`/runtime package as well.

### AMD GPU is not detected in Docker

Set the AMD overlay and render group ID:

```dotenv
COMPOSE_FILE=docker-compose.yml:docker/gpu.amd.yml
RENDER_GID=992
```

The render group ID varies by host:

```bash
getent group render
```

Verify:

```bash
docker compose exec odysseus rocm-smi
```

If `rocm-smi` fails inside the container, fix host ROCm/device permissions
before debugging Cookbook.

### WSL and Windows model serving

The core app can run on Windows, but local GPU serving with vLLM/SGLang usually
needs Linux or WSL2. For Windows users, the simplest local model path is often:

1. Run Ollama on Windows.
2. Add `http://localhost:11434/v1` in **Settings -> Add Models** for native
   Odysseus, or `http://host.docker.internal:11434/v1` for Docker Odysseus.

## Logs To Include In Issues

If you open an issue, include the smallest relevant logs and remove secrets:

```bash
docker compose ps
docker compose logs --tail=160 odysseus
docker compose logs --tail=120 chromadb
docker compose logs --tail=120 searxng
```

Also include:

- install method: Docker, native Linux/macOS, Windows, WSL, or remote server,
- OS and browser,
- model backend: Ollama, vLLM, SGLang, llama.cpp, LM Studio, etc.,
- GPU model and driver/runtime when Cookbook is involved,
- exact endpoint URL shape, with tokens removed,
- what you expected and what happened.

Do not post `.env`, API keys, auth tokens, private documents, or public IPs.
