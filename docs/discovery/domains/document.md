# Document

Features in this document are generated from [`../feature-catalog.json`](../feature-catalog.json), the canonical inventory.

## DOCUMENT-001 — Document & Canvas Artifact Management

- **Domain**: `document`
- **Status**: `verified`
- **Evidence Maturity**: `E0`
- **Commit Verified**: `d8a2059df8e53bc7275c45339849d14c8651e73c`
- **Runtime Validation**: not-required — No separate environment-dependent runtime validation was identified during this documentation pass.

### Purpose

Renders dynamic canvas documents, handles live editing, markdown preview, and side-by-side artifact display.

### Evidence summary

- `routes/document_routes.py` — `setup_document_routes` — Registers document artifact CRUD routes.
- `static/js/document.js` — `initDocumentView` — Renders interactive canvas document panel.

### Unknowns

- Concurrent edits on the same document artifact.

## DOCUMENT-002 — PDF Form Processing & High-Fidelity Rendering

- **Domain**: `document`
- **Status**: `verified`
- **Evidence Maturity**: `E1`
- **Commit Verified**: `d8a2059df8e53bc7275c45339849d14c8651e73c`
- **Runtime Validation**: pending — Requires optional PyMuPDF (`fitz`) or pypdf runtime dependency.

### Purpose

Extracts form fields from PDF files, fills dynamic values, and generates PDF previews.

### Evidence summary

- `src/pdf_runtime.py` — `load_pymupdf_for_pdf_viewer` — Loads optional PyMuPDF runtime for PDF viewing.
- `src/pdf_forms.py` — `extract_form_fields` — Handles PDF form field extraction and filling.
- `tests/test_document_pdf_marker.py` — `test_marker_removed_without_eating_following_text` — Tests PDF text extraction wrapper stripping without content corruption.

### Unknowns

- Complex XFA PDF forms may not extract cleanly with standard pdf parsers.

## DOCUMENT-003 — Personal Document Indexing & RAG Retrieval

- **Domain**: `document`
- **Status**: `verified`
- **Evidence Maturity**: `E0`
- **Commit Verified**: `d8a2059df8e53bc7275c45339849d14c8651e73c`
- **Runtime Validation**: not-required — No separate environment-dependent runtime validation was identified during this documentation pass.

### Purpose

Indexes local user documents (PDF, DOCX, TXT) into ChromaDB for semantic vector retrieval.

### Evidence summary

- `routes/personal_routes.py` — `setup_personal_routes` — Personal document RAG indexing and search API endpoints.
- `src/personal_docs.py` — `PersonalDocsManager` — Handles file text chunking and vector storage.

### Unknowns

- Slow vector embedding indexing step for massive multi-thousand page documents.

## DOCUMENT-004 — Document Conversion & Text Extraction Engine

- **Domain**: `document`
- **Status**: `verified`
- **Evidence Maturity**: `E0`
- **Commit Verified**: `d8a2059df8e53bc7275c45339849d14c8651e73c`
- **Runtime Validation**: not-required — No separate environment-dependent runtime validation was identified during this documentation pass.

### Purpose

Converts office formats (.docx, .xlsx, .pptx) and HTML into clean Markdown text representations.

### Evidence summary

- `src/markitdown_runtime.py` — `convert_to_markdown` — Converts binary office documents into structured Markdown text.

### Unknowns

- Formatting loss when parsing legacy binary doc/xls files.

## DOCUMENT-005 — Document Library UI Navigation

- **Domain**: `document`
- **Status**: `verified`
- **Evidence Maturity**: `E0`
- **Commit Verified**: `d8a2059df8e53bc7275c45339849d14c8651e73c`
- **Runtime Validation**: not-required — No separate environment-dependent runtime validation was identified during this documentation pass.

### Purpose

Provides dedicated UI view for browsing, filtering, and organizing saved user documents.

### Evidence summary

- `static/js/documentLibrary.js` — `initDocumentLibrary` — Renders document library navigation grid.
- `app.py` — `serve_library` — Serves SPA shell for /library route.

### Unknowns

- Large folder trees may cause initial DOM render slowdown.
