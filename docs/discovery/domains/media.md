# Media

Features in this document are generated from [`../feature-catalog.json`](../feature-catalog.json), the canonical inventory.

## MEDIA-001 — Gallery Image Library & Album Operations

- **Domain**: `media`
- **Status**: `verified`
- **Evidence Maturity**: `E0`
- **Commit Verified**: `d8a2059df8e53bc7275c45339849d14c8651e73c`
- **Runtime Validation**: not-required — No separate environment-dependent runtime validation was identified during this documentation pass.

### Purpose

Organizes images into custom albums, provides grid browsing, tagging, and album metadata management.

### Evidence summary

- `routes/gallery/gallery_routes.py` — `@router.get('/api/gallery/library')` — Fetches image library list with tag filters.
- `static/js/gallery.js` — `initGallery` — Main gallery grid renderer and uploader.

### Unknowns

- Thumbnail generation overhead for high-resolution RAW camera images.

## MEDIA-002 — Image Processing, AI Upscaling & Style Transfer

- **Domain**: `media`
- **Status**: `verified`
- **Evidence Maturity**: `E0`
- **Commit Verified**: `d8a2059df8e53bc7275c45339849d14c8651e73c`
- **Runtime Validation**: not-required — No separate environment-dependent runtime validation was identified during this documentation pass.

### Purpose

Executes local image enhancement, background removal, face sharpening, and AI upscaling operations.

### Evidence summary

- `routes/gallery/gallery_routes.py` — `@router.post('/api/gallery/ai-upscale')` — Runs RealESRGAN image upscaling.
- `routes/gallery/gallery_routes.py` — `@router.post('/api/image/remove-bg')` — Executes background removal pass.

### Unknowns

- High GPU memory allocation when upscaling 4K images.

## MEDIA-003 — Interactive Image Canvas Editor & Persisted Drafts

- **Domain**: `media`
- **Status**: `verified`
- **Evidence Maturity**: `E0`
- **Commit Verified**: `d8a2059df8e53bc7275c45339849d14c8651e73c`
- **Runtime Validation**: not-required — No separate environment-dependent runtime validation was identified during this documentation pass.

### Purpose

Provides full multi-layer raster canvas editor, brush tools, transforms, masks, and draft project persistence.

### Evidence summary

- `routes/editor_draft_routes.py` — `setup_editor_draft_routes` — API routes for saving and loading canvas project drafts.
- `static/js/editor/history-panel.js` — `HistoryManager` — Canvas undo/redo stack manager.

### Unknowns

- Browser memory leak if multi-gigabyte layer undo buffers are kept indefinitely.

## MEDIA-004 — Text-to-Speech (TTS) Synthesis Service

- **Domain**: `media`
- **Status**: `verified`
- **Evidence Maturity**: `E0`
- **Commit Verified**: `d8a2059df8e53bc7275c45339849d14c8651e73c`
- **Runtime Validation**: not-required — No separate environment-dependent runtime validation was identified during this documentation pass.

### Purpose

Synthesizes spoken audio from text using local Kokoro, EdgeTTS, or OpenAI TTS engines.

### Evidence summary

- `routes/tts_routes.py` — `@router.post('/synthesize')` — Synthesizes TTS audio clip.
- `services/tts/tts_service.py` — `TTSService` — Provider abstraction layer for audio speech generation.

### Unknowns

- Audio synthesis latency on CPU-only hardware setups.

## MEDIA-005 — Speech-to-Text (STT) Audio Transcription Service

- **Domain**: `media`
- **Status**: `verified`
- **Evidence Maturity**: `E0`
- **Commit Verified**: `d8a2059df8e53bc7275c45339849d14c8651e73c`
- **Runtime Validation**: not-required — No separate environment-dependent runtime validation was identified during this documentation pass.

### Purpose

Transcribes user audio recordings into text using faster-whisper or local speech models.

### Evidence summary

- `routes/stt_routes.py` — `@router.post('/transcribe')` — Accepts multipart audio file and returns transcription text.
- `services/stt/stt_service.py` — `STTService` — Whisper audio transcription engine wrapper.

### Unknowns

- Missing ffmpeg system dependency prevents audio format decoding.

## MEDIA-006 — Digital Signature Stamp Storage & Placement

- **Domain**: `media`
- **Status**: `verified`
- **Evidence Maturity**: `E0`
- **Commit Verified**: `d8a2059df8e53bc7275c45339849d14c8651e73c`
- **Runtime Validation**: not-required — No separate environment-dependent runtime validation was identified during this documentation pass.

### Purpose

Stores transparent PNG user signatures and stamps for placement onto PDF forms and documents.

### Evidence summary

- `routes/signature_routes.py` — `setup_signature_routes` — CRUD endpoints for managing user signature PNG stamps.

### Unknowns

- Cross-site scripting if signature image titles contain unescaped user input.

## MEDIA-007 — Generated Image Artifact Route & MCP Integration

- **Domain**: `media`
- **Status**: `verified`
- **Evidence Maturity**: `E0`
- **Commit Verified**: `d8a2059df8e53bc7275c45339849d14c8651e73c`
- **Runtime Validation**: not-required — No separate environment-dependent runtime validation was identified during this documentation pass.

### Purpose

Serves generated AI artwork artifacts and integrates with image generation MCP server.

### Evidence summary

- `app.py` — `serve_generated_image` — Serves generated image artifacts with cache headers.
- `src/generated_images.py` — `resolve_generated_image_path` — Confines requested image path within artifacts directory.

### Unknowns

- Path traversal vulnerability if filename parameter is un-sanitized.

## MEDIA-008 — Native MLX Image Bridge (macOS Apple Silicon)

- **Domain**: `media`
- **Status**: `experimental`
- **Evidence Maturity**: `E0`
- **Commit Verified**: `d8a2059df8e53bc7275c45339849d14c8651e73c`
- **Runtime Validation**: pending — Requires Apple Silicon, macOS tooling, and the compiled MLX bridge.

### Purpose

Native Apple Swift bridge for hardware-accelerated diffusion and MLX image colorization on macOS.

### Evidence summary

- `swift/odysseus-mlx-image-bridge/Package.swift` — `Package` — Swift package manifest for native MLX image bridge.
- `scripts/mlx_image_server.py` — `main` — Python daemon wrapping native Swift MLX binary.

### Unknowns

- Binary build requires Xcode command line tools build step (`build-macos-app.sh`).
