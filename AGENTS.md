# document-templates — Euro-Office Initialization Templates

@../AGENTS.md

Guidance for Claude Code (and other AI agents) working in **document-templates** — default blank assets and system samples.

## What this repo is
A static asset storage module housing the baseline OOXML binary templates (`.docx`, `.xlsx`, `.pptx`) cloned whenever a user creates a new file within the editor interface.

## Technical Execution & Locale Fallback
- **No-Code Constraint:** This repository contains **no compiled code and no build steps**. It is an asset store consumed by `server` when creating a blank file (`FileConverter/sources/converter.js` → `replaceEmptyFile`).
- **Layout:** `new/<locale>/new.{docx,xlsx,pptx,pdf}` across 45 locale folders, plus `sample/` universal examples.
- **`en-US` is the fallback locale and must stay complete.** `TEMPLATES_DEFAULT_LOCALE` is `en-US` (`server` `Common/sources/constants.js`). Template lookup degrades gracefully in two steps: (1) if the requested locale folder is missing, the server logs a debug line and falls back to `en-US`; (2) if a specific `new.<ext>` is missing, it falls back to the base editor format (`docx`/`xlsx`/`pptx`). An incomplete *non-default* locale does **not** error — it silently serves the `en-US` / base-format template. The real risk is an incomplete **`en-US`** folder, since that is the last-resort fallback.
- **Binary Integrity:** Never edit OOXML files by hand. Use a compliant office suite and save back as zipped Open XML.
- **Integration Test Anchors:** The universal assets inside `sample/` are bound to integration test workflows. Do not alter their content without checking the test suite.

## Rules
- **Never** introduce package.json files, scripts, or build automation frameworks to this repository.
- **Never** ship an incomplete `en-US` folder — it is the final fallback; a missing template there has no further fallback. (Other locales degrade to `en-US` and are non-fatal.)
- **Never** modify `sample/` files without executing the automated integration test verification loop.

## Findings & Long-tail
No centralized findings store exists in this repository yet. Document edge cases in code comments or GitHub issues until one is established.