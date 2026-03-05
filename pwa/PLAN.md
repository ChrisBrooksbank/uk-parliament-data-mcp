# Plan: Hansard Semantic Search PWA

## Context

The UK Parliament MCP server exposes 163 tools over the Hansard API and others. The goal is to build a standalone Progressive Web App that lets users search Hansard debates and contributions by *meaning*, not just keywords — using transformers.js to run an embedding model entirely in-browser. The PWA calls the Hansard API directly (no MCP server, no backend). It ships as a static site inside a new `pwa/` directory in this repo.

The key insight: Parliament's keyword search finds speeches containing exact words; semantic search finds speeches about the same *idea*, even when different vocabulary is used. E.g. "cost of living pressures" finds speeches about inflation, food banks, rent rises.

---

## Architecture

```
User query
    │
    ▼
[Query Embedding]         ← transformers.js Web Worker (Xenova/all-MiniLM-L6-v2, 384-dim)
    │
    ├── Phase 1 (MVP): Hansard API search → fetch top-N results → embed snippets → re-rank by cosine similarity → display
    │
    └── Phase 2: Local IndexedDB corpus of pre-embedded debates → pure local search, offline
```

Phase 1 ships first. Phase 2 is designed in from the start (schema, worker API) but activates via a background "index" button.

---

## Tech Stack

- **Build**: Vite (vanilla JS, no framework — keeps bundle lean, transformers.js works well with Vite's ESM handling)
- **Embedding model**: `Xenova/all-MiniLM-L6-v2` — 23 MB, 384-dim, fast, normalized outputs
- **Model caching**: transformers.js auto-caches in browser cache / OPFS after first download
- **Storage**: IndexedDB (via `idb` npm package) for debate corpus + embeddings
- **Similarity**: brute-force dot product (vectors pre-normalized → equals cosine similarity); adequate for <10k items
- **Styling**: Plain CSS, no UI framework
- **PWA**: `vite-plugin-pwa` (generates service worker + manifest)
- **Hansard API**: Direct fetch to `https://hansard-api.parliament.uk` (public, no auth, CORS-open)

---

## Project Structure

```
pwa/
├── PLAN.md                  ← this file
├── package.json
├── vite.config.js
├── index.html
├── manifest.json
├── public/
│   └── icons/               ← PWA icons (parliament portcullis SVG)
└── src/
    ├── main.js              ← app entry, UI orchestration
    ├── api.js               ← Hansard API client (fetch wrappers)
    ├── db.js                ← IndexedDB schema + CRUD via idb
    ├── worker.js            ← embedding Web Worker (transformers.js)
    ├── search.js            ← search logic: API fetch + embed + re-rank
    ├── index-corpus.js      ← Phase 2: bulk indexing logic
    └── ui/
        ├── results.js       ← render search results
        ├── progress.js      ← model load / index progress bar
        └── filters.js       ← filter controls
```

---

## Key Implementation Details

### 1. Hansard API Endpoints Used

| Purpose | Endpoint |
|---|---|
| Search contributions (MVP) | `GET /search/contributions/Spoken.json?queryParameters.searchTerm={q}&queryParameters.skip=0&queryParameters.take=50` |
| Search debates | `GET /search/debates.json?queryParameters.searchTerm={q}` |
| Full debate text (Phase 2 indexing) | `GET /debates/debate/{debateSectionExtId}.json` |
| Sections for a sitting day (Phase 2) | `GET /overview/sectionsforday.json?house={house}&date={date}` |
| Last sitting date | `GET /overview/lastsittingdate.json?house=Commons` |

Response fields used for embedding:
- `ContributionTextFull` (primary content to embed)
- `ContributionText` (snippet for display)
- `MemberName`, `SittingDate`, `House`, `DebateSection`, `DebateSectionExtId`

### 2. Embedding Web Worker (`src/worker.js`)

```js
import { pipeline, env } from '@xenova/transformers';

env.allowRemoteModels = true;
// transformers.js auto-caches in Cache API after first download

let extractor = null;

self.onmessage = async ({ data }) => {
  const { type, texts, id } = data;

  if (type === 'load') {
    extractor = await pipeline('feature-extraction', 'Xenova/all-MiniLM-L6-v2', {
      progress_callback: (p) => self.postMessage({ type: 'progress', progress: p })
    });
    self.postMessage({ type: 'ready' });
  }

  if (type === 'embed') {
    const out = await extractor(texts, { pooling: 'mean', normalize: true });
    self.postMessage({ type: 'embeddings', embeddings: out.tolist(), id });
  }
};
```

Worker is created once on app init. Model downloads in background; UI shows progress bar.

### 3. Search Flow — Phase 1 (Re-rank)

```
search(query):
  1. queryEmbedding = embed([query])          // worker
  2. results = fetch Hansard contributions API (take=50)
  3. snippets = results.map(r => r.ContributionTextFull || r.ContributionText)
  4. snippetEmbeddings = embed(snippets)      // worker (batch)
  5. scores = snippetEmbeddings.map(e => dot(queryEmbedding, e))
  6. ranked = zip(results, scores).sort by score desc
  7. display top 20
```

This gives semantic re-ranking of API results. Fast because only ~50 items to embed.

### 4. IndexedDB Schema (`src/db.js`)

```js
// DB: 'hansard-semantic', version 1
// Object store: 'debates'
{
  id: debateSectionExtId,     // keyPath
  title: string,
  house: 'Commons' | 'Lords',
  date: string,               // YYYY-MM-DD
  snippet: string,
  embedding: Array<number>,   // Float32, 384-dim, pre-normalized
  indexedAt: number,          // timestamp
}

// Object store: 'meta'
{ key: 'indexedDays', value: string[] }  // dates fully indexed
{ key: 'modelReady', value: boolean }
```

### 5. Phase 2 — Local Corpus Indexing

- "Index recent debates" button visible after model loads
- Fetches last 30 days of sitting days via `/overview/sectionsforday.json`
- For each section, fetches full debate from `/debates/debate/{id}.json`
- Embeds the title + first 512 chars of debate content
- Stores in IndexedDB
- Progress bar shows items indexed / total
- Once indexed, search falls back to local corpus (offline-capable)

### 6. PWA Config (`vite.config.js`)

```js
import { defineConfig } from 'vite'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  plugins: [
    VitePWA({
      registerType: 'autoUpdate',
      manifest: {
        name: 'Hansard Semantic Search',
        short_name: 'Hansard Search',
        description: 'Search UK Parliament debates by meaning',
        theme_color: '#1a3a5c',
        icons: [{ src: 'icons/icon-192.png', sizes: '192x192', type: 'image/png' }]
      },
      workbox: {
        // Don't cache transformers.js models via workbox — they self-cache
        globIgnores: ['**/*.onnx', '**/ort-wasm*']
      }
    })
  ],
  optimizeDeps: {
    exclude: ['@xenova/transformers']   // must be excluded for ESM worker compatibility
  },
  worker: { format: 'es' }
})
```

### 7. CORS

The Hansard API (`hansard-api.parliament.uk`) is publicly accessible and returns CORS headers allowing browser requests. No proxy needed.

---

## UI Layout

```
┌─────────────────────────────────────────────────────┐
│  Hansard Semantic Search        [Commons] [Lords]    │
│  ─────────────────────────────────────────────────  │
│  [Search debates and speeches by meaning...    ] [⏎] │
│                                                      │
│  Model: ████████░░ 80% loading...                   │
│  (or: Model ready  •  Local index: 847 debates)     │
│                                                      │
│  Filter: [Date from] [Date to]  [Member name]       │
│                                                      │
│  Results (ranked by relevance):                     │
│  ┌──────────────────────────────────────────────┐   │
│  │  0.91  "Autumn Statement" — Commons          │   │
│  │  15 Nov 2023 · Jeremy Hunt                   │   │
│  │  "...the cost of living support we have..."  │   │
│  │  [View full debate →]                        │   │
│  └──────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────┐   │
│  │  0.87  "Cost of Living Crisis" — Lords       │   │
│  │  ...                                         │   │
│  └──────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

Similarity score shown (0.0–1.0). "View full debate" links to `hansard.parliament.uk/...` using the `DebateSectionExtId`.

---

## Files to Create

All new — no existing files modified.

| File | Purpose |
|---|---|
| `pwa/PLAN.md` | This file |
| `pwa/package.json` | Vite + transformers + idb + vite-plugin-pwa |
| `pwa/vite.config.js` | Vite config with PWA plugin |
| `pwa/index.html` | App shell |
| `pwa/src/main.js` | App init, worker setup, UI orchestration |
| `pwa/src/api.js` | Hansard fetch helpers |
| `pwa/src/db.js` | IndexedDB via idb |
| `pwa/src/worker.js` | Embedding Web Worker |
| `pwa/src/search.js` | Phase 1 + Phase 2 search logic |
| `pwa/src/ui/results.js` | Result card rendering |
| `pwa/src/ui/progress.js` | Model load progress |
| `pwa/src/ui/filters.js` | Filter controls |
| `pwa/public/icons/` | PWA icons |

---

## Verification

```bash
cd pwa
npm install
npm run dev        # Vite dev server on localhost:5173

# Manual tests:
# 1. Open app — model download progress bar appears
# 2. Search "NHS funding" — results appear, ranked by semantic similarity score
# 3. Compare with keyword search on hansard.parliament.uk — semantic results include
#    speeches about health budgets that don't use "NHS funding" exactly
# 4. Filter by house: Commons only
# 5. Click "View full debate" → opens correct hansard.parliament.uk URL
# 6. Reload page — model loads instantly from cache (no re-download)
# 7. Click "Index recent debates" → progress bar, IndexedDB populated
# 8. Disconnect from internet, search again → results still appear from local index
# 9. npm run build && npm run preview → production build works
# 10. Lighthouse PWA audit → installable, offline-ready
```
