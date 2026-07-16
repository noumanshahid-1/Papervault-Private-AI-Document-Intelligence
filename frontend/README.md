# Papervault Frontend

The Papervault frontend is a React 19, TypeScript, Vite, Tailwind CSS, and
shadcn/ui workspace for local document review.

The interface uses a responsive desktop rail and mobile navigation drawer,
route-level code splitting, structured loading/error/empty states, and
phone-specific layouts for dense data such as official-notice tables.

## Commands

```powershell
npm install
npm run dev
npm run test
npm run lint
npm run build
npm run check
```

The development server runs on `http://localhost:5173` and proxies `/api`
requests to the local BFF on port `3001`.

## Main routes

- `/` — document intake and processing
- `/workspace` — findings, risks, checklist, Q&A, and evidence
- `/history` — local saved-review metadata and structured results

## Interface behavior

- Desktop navigation stays visible while mobile navigation opens in an
  accessible drawer.
- Workspace tabs scroll horizontally on narrow screens without expanding the
  page viewport.
- Intake processing shows extraction, analysis, and checklist progress.
- History uses skeleton, retry, empty, confirmation, and per-review loading
  states.
- Saved reviews are restored atomically into the workspace to avoid route-guard
  races.
- Route pages are lazy-loaded into separate production bundles.
- Evidence shows backend-owned extraction/OCR and analysis-confidence
  diagnostics.
- Q&A exposes retrieval scores, matched terms, provider/backend metadata,
  generation mode, and fallback reasons.
- When the local runtime enables Ollama, the Q&A controls can select an
  installed model per question.

## Privacy behavior

Active uploads keep extracted text in browser memory for analysis, evidence, and
Q&A. Saved reviews are summary-only by default, so restored sessions show
structured findings and checklists but require re-uploading the source document
for new Q&A or full-text evidence.

## Validation

```powershell
npm run check:api-types
npm run test
npx tsc --noEmit
npm run lint
npm run build
```

Raw API contracts are generated from FastAPI's committed OpenAPI document:

```powershell
cd ..
npm run generate:api
```

Do not edit `src/lib/api.generated.ts` manually. UI-facing models remain in
`src/lib/types.ts`, and focused mappers under `src/lib/mappers/` translate the
generated backend shapes.
