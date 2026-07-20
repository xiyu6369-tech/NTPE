# NTPE 2.0 Stage 1 — Translation Launcher Product Foundation

## Outcome

Stage 1 adds an offline product-layer launcher foundation without changing the existing translation execution layer. `ntpe_launcher.py` provides catalog, validation, dry-run, and Tkinter GUI entry points; it never starts `launcher_translate.py` or performs translation.

## Product Surface

- `python ntpe_launcher.py` opens the Tkinter launcher skeleton.
- `--dry-run` validates configuration and renders the real existing TXT command syntax without starting a subprocess.
- `--validate-config` performs deterministic offline preflight checks.
- `--list-languages`, `--list-providers`, and `--list-models` expose static JSON catalogs.
- The GUI supports file inspection, validation, and preview. **Start Translation** remains disabled with the Stage 1 explanation.

## Honest Capability Boundary

- Korean (`ko`) to Traditional Chinese (`zh-Hant`) is the only execution-compatible language route represented by the existing CLI integration.
- Japanese and English can be detected but are blocked as `not_yet_integrated`.
- NVIDIA is catalogued as the existing integration and is configured only when `NVIDIA_API_KEY` exists; its value is never read into output.
- Gemini and `gemini-2.5-flash` are catalogued but disabled as `not_yet_integrated`.
- Literary and balanced profiles map to existing CLI values. Faithful is catalogued but unavailable.
- Overwrite is represented in the product model but blocked because the existing TXT CLI has no overwrite flag.

## Safety Properties

Provider requests, network requests, translation executions, output writes, and resume-state writes are all zero in Stage 1 validation. The command builder returns only an argument list, PowerShell-safe preview, and validation result.

`launcher_translate.py`, Provider execution, Translation Runtime, resume behavior, output behavior, TE v7.2 contracts, LCR contracts, and historical evidence remain unchanged.

## Validation

- Launcher product unit tests: 27 passed.
- Launcher product integration tests: 3 passed.
- `python ntpe_validate.py`: PASS; 2641 Python files compiled and 666 tests inventoried.
- Acceptance entry: `verification/release/ntpe_v20_stage1_translation_launcher_product_foundation_test.py`.
- Evidence: `artifacts/ntpe_v20_stage1_translation_launcher_product_foundation/`.

## Git Decision

Commit is HOLD. Push, tag, Provider execution, and production activation are not performed.
