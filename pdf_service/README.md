# pdf_service — customer estimate PDF renderer

Renders the written estimate PDF the chatbot emails to customers. Node script,
invoked as a subprocess by `quote_emailer/pdf_estimate.py`:
JSON payload on stdin → PDF bytes on stdout.

- **`render_estimate.cjs` is a checked-in esbuild bundle** — the Docker image
  only needs the `node` runtime (installed in the dockerfile), never npm.
  After editing anything in `src/`, rebuild and commit the bundle:
  `npm install && npm run build`.
- `src/windowDiagram.ts` is copied verbatim (import path aside) from
  `estimatorsoftware/window-quote-app/src/services/windowDiagram.ts` — the
  rep app's window-diagram renderer. Re-sync from there rather than diverging.
- `src/estimatePdf.js` is the estimate-mode layout: price **ranges**, an
  "About this estimate" disclaimer (not a contract; final price after free
  exact measure), Direct Windows branding. It consumes the chatbot's
  `display_dict` (see `chatbot_project_quoter.py::_build_quote_display`) plus
  the raw window config (for per-unit diagram layout).
- Test: `node render_estimate.cjs < test/sample_payload.json > out.pdf`

PDF generation is deliberately best-effort: any failure logs and returns None
upstream, and the quote email goes out without the attachment.
