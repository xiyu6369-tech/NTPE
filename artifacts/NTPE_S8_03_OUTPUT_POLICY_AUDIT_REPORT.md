# NTPE S8-03 — Unified TXT/EPUB Output Path & Result Policy Audit

**Task**: `NTPE-S8-03`
**Date**: 2026-10-01
**Executor**: Kilo (Automated)
**Status**: `S8_03_OUTPUT_POLICY_AUDITED_ACCEPTED`

---

## 1. Repository State

| Metric | Value |
|--------|-------|
| Baseline HEAD | `53138c6caff628d0e9994a458e87e3aef8bec3b0` |
| Actual HEAD | `53138c6caff628d0e9994a458e87e3aef8bec3b0` |
| Branch | `main` |
| Git Commit / Push / Tag / History Rewrite | NO |

---

## 2. Working Tree

### Before S8-03
Four pre-existing literary residuals (untouched) + uncommitted S8-01 and S8-02 deliverables.

### After S8-03
Same, plus the S8-03 UI clarification in `ui/translation_studio/pages/project_page.py` and the new test file `tests/ui/test_s8_03_output_policy.py`.

---

## 3. TXT Output Path Flow (Studio)

```text
ProjectPage._on_translate()                 (TXT branch)
  output_dir = Path("output") / <stem>       # UI-derived, project-scoped
  output_dir.mkdir(...)
  → TxtTranslationOptions(output_dir=output_dir)
  → TranslationRunner(options, root_path)
  → TranslationWorker.run()  → runtime.translate_txt(options)
  → lts.txt_translation_runtime.translate_txt()
       root_path  = <root passed by worker>
       output_dir = <root>/output/<stem>
       final_output = output_dir / f"{stem}_zh.txt"
  → result["output"] = str(final_output), result["output_dir"] = str(output_dir)
  → UI completion dialog shows result["output"]
```

- The runtime **honors** `options.output_dir` (`txt_translation_runtime.py:1934-1935,1065,1129`).
- `result["output"]` and `result["output_dir"]` are self-consistent (`output.parent == output_dir`).
- Studio `root_path` is resolved at `project_page.py:526` as `Path(__file__).resolve().parents[2]`.

Exact values (Studio file `D:\Python\NTPE\ui\translation_studio\pages\project_page.py`):

```text
root_path = D:\Python\NTPE\ui
TXT output_dir = D:\Python\NTPE\ui\output\<stem>
TXT final artifact = D:\Python\NTPE\ui\output\<stem>\<stem>_zh.txt
```

---

## 4. EPUB Output Path Flow (Studio)

```text
ProjectPage._on_translate()                 (EPUB branch)
  → _build_epub_options(project, source_path)   # NO output path supplied (S8-03 clarification)
  → EpubTranslationOptions (no output-dir field)
  → TranslationWorker.run() → _runtime_epub_translate(options)
       output_dir   = source_epub_path.parent / "output" / "epub_translation" / <identifier>
       output_path  = output_dir / f"{stem}_zh.epub"
  → translate_epub_translation_input(options, root=<root>)
       adapter internal output_dir = <root>/output/epub_translation/<book_id>   (resume/memory/progress only)
  → build_epub_reader_chapter_map_with_metadata(...)
  → pack_epub_resource_aware(packaging_input, output_path)
  → result["output"] = str(packaging_result.output_path)     # == output_path
    result["output_dir"] = str(output_dir)
    result["pipeline_mode"] = "epub"
  → UI completion dialog shows result["output"]
```

Exact values (source at `D:\Python\NTPE\books\book.epub`, identifier `id-9`):

```text
EPUB final artifact = D:\Python\NTPE\books\output\epub_translation\id-9\book_zh.epub
EPUB result output_dir = D:\Python\NTPE\books\output\epub_translation\id-9
adapter internal dir  = D:\Python\NTPE\ui\output\epub_translation\id-9   (internal only)
```

The final artifact is **source-adjacent** and owned by the worker/packager; the UI does not (and after S8-03, cannot) select it. `output.parent == output_dir`.

---

## 5. Output Path Mapping

| Input | UI output_dir | worker output | canonical runtime output | final artifact |
|-------|---------------|---------------|--------------------------|----------------|
| TXT | `output/<stem>` (UI-derived; forwarded in `TxtTranslationOptions`) | `options.output_dir` | `<root>/output/<stem>` (honored) | `<root>/output/<stem>/<stem>_zh.txt` |
| EPUB | none (removed by S8-03 clarification) | `<source.parent>/output/epub_translation/<id>` | adapter internal `<root>/output/epub_translation/<id>` (resume/memory only); packager writes worker path | `<source.parent>/output/epub_translation/<id>/<stem>_zh.epub` |

`<root>` for the Studio is `D:\Python\NTPE\ui` (see §8).

---

## 6. CLI / Tkinter / PySide6 Output Semantics Comparison

| Entry | Output selection | TXT artifact | EPUB behavior |
|-------|------------------|--------------|---------------|
| CLI (`launcher_translate.py` → `ntpe_production_translate.py`) | user `output` positional | `<output>/<stem>_zh.txt` | `epub` subcommand extracts → temp TXT → **TXT pipeline** → `<output>/<stem>_zh.txt` (no packaged `.epub`) |
| Tkinter (`ui/translation_launcher`, `core/launcher_product`) | user `Output folder`; `command_builder` forwards it to the CLI `txt`/`epub` subcommands | user output dir | same as CLI `epub` (EPUB→TXT) |
| PySide6 Studio (S8-01/S8-03) | **no user output selection**; outputs derived | UI-derived `output/<stem>` | canonical EPUB runtime/packager → source-adjacent `.epub` |

Per S8-03 §5(D), this is recorded as a **comparison only**; the task does not require unifying product entry points. Note the CLI/Tkinter `epub` path is a legacy EPUB→TXT flow and is **not** the S8-01 canonical resource-aware EPUB packaging path.

---

## 7. Audit Conclusion

**No user-visible output contract mismatch exists (Case 1).**

- The Studio UI never asks the user for an output destination and never displays a predicted output path. It displays `result["output"]` on completion, which is exactly the produced artifact (`…_zh.txt` for TXT, `…_zh.epub` for EPUB).
- The TXT UI-derived `output/<stem>` is honored by the runtime.
- The EPUB output is **intentionally** owned by the canonical EPUB runtime/packager (source-adjacent). The UI does not promise a custom destination.
- Before S8-03, `ProjectPage._on_translate()` computed a TXT-style `output_dir` and passed it into `_build_epub_options(...)`, where it was silently ignored. This was a latent, non-user-visible confusion (the parameter implied the UI selected the EPUB output), not a contract mismatch.

### 7.1 Disposition
`intentional backend contract` — the differing TXT/EPUB conventions are an accepted output contract, not an accidental mismatch.

### 7.2 Minimal clarification applied (Case 1)
Removed the misleading unused `output_dir` from the EPUB UI call path:
- `_on_translate()` now computes `output_dir` only inside the TXT branch and calls `_build_epub_options(project, source_path)`.
- `_build_epub_options(self, project, source_path)` documents that the EPUB destination is canonical/runtime-owned.

No output behavior changed (EPUB already ignored the parameter). No propagation repair was required.

---

## 8. Related Defects Discovered (NOT fixed — out of scope)

These are recorded for follow-up; §7 forbids expanding S8-03 into them.

1. **Studio root off-by-one: `root_path = parents[2]` resolves to `D:\Python\NTPE\ui`, not the repo root.** By contrast `ui/translation_launcher/app.py` uses the same expression from a shallower module and correctly resolves to the repo root. Consequence: Studio TXT output lands in `ui/output/...` and the EPUB adapter's internal dir is `ui/output/epub_translation/...`; `TranslationRuntime(root=ui)` would look for `ui/config/provider_config.json` (does not exist; repo `config/provider_config.json` does). Fixing this changes output locations/runtime-root resolution, so it is not part of S8-03 (output *policy*) and was not applied.
2. **EPUB live-progress filename mismatch (Studio).** Worker polls `<stem>_live_progress.json` under the source-adjacent dir; the adapter writes `<stem>_epub_live_progress.json`. EPUB progress therefore does not stream mid-run (only the final emit lands). Out of scope.
3. **TXT success result lacks `chunk_successful`.** `lts` TXT success dict (`:1126`) exposes counts only in `summary`, while the UI reads `result.get("chunk_successful", 0)`; TXT completion therefore shows `成功區塊：0 / N`. This is a result-state count issue, not an output-path issue; out of scope.

---

## 9. Tests (Tests A–D)

New: `tests/ui/test_s8_03_output_policy.py` (8 tests) — fake/mock runtimes only.
- **A1** — TXT UI derives `output/<stem>` and forwards it in `TxtTranslationOptions`.
- **A2** — TXT worker final artifact is `<options.output_dir>/<stem>_zh.txt` and exists; `output.parent == output_dir`.
- **B1** — EPUB worker final artifact is canonical source-adjacent `<source.parent>/output/epub_translation/<id>/<stem>_zh.epub`; `pipeline_mode == "epub"`; TXT runtime is never invoked.
- **B2** — EPUB UI call path supplies no output path (2 positional args, no `output_dir`).
- **C1** (parametrized TXT/EPUB) — success `output` lives inside the reported `output_dir`; dialog shows the artifact name.
- **C2** — `dry_run` is not mapped to success/incomplete.
- **D** — EPUB launch routes to `EpubTranslationOptions`; `TxtTranslationOptions` is never constructed.

Provider = 0 · Network = 0 · Real Translation = 0.

---

## 10. Regression & Compile Boundary

| Check | Result |
|-------|--------|
| `pytest tests/ui/test_s8_03_output_policy.py` | 8 passed |
| `pytest tests/ui` (excl. pre-existing hanging shell file) | 113 passed, 1 skipped |
| `pytest tests/contract` | 338 passed |
| `python -m compileall -q ui` | PASS (0) |
| `python -m compileall -q core` | PASS (0) |
| `python -m compileall -q lts` | PASS (0) |
| `python -m compileall -q cli` | PASS (0) |
| `python -m compileall -q tests/ui` | PASS (0) |
| `python -m compileall -q tests/contract` | PASS (0) |
| `git diff --check` | clean (exit 0) |

Repo-wide `python -m compileall -q .` remains **FAIL** (exit 1) confined to pre-existing unrelated/non-canonical files (`tools/one_shots/*`, `archive/legacy_tests/*`, ignored `.kilo/` worktree), per the S8-02 closure classification. Not modified.

---

## 11. Pre-existing Failures (unchanged)

- `TranslationLauncherApp` Tk pack/grid defect.
- `tests/ui/test_translation_studio_shell.py` blocking-modal hang + `歡迎使用` localization assertion.
- `tests/unit/launcher_product/test_gui_state.py::test_controller_never_starts_translation` (stale signature).
- Repo-wide compileall malformed files (§10).

None are S8-03 regressions.

---

## 12. Scope Contamination Check

- S8-03 production change: **only** `ui/translation_studio/pages/project_page.py` (UI clarification, no behavior change).
- No `core/epub_translation/*`, `lts/txt_translation_runtime.py`, `TranslationEngine`, `RuntimeOrchestrator`, `ProviderManager`, provider, or client change.
- No project persistence, no output UI redesign, no config system, no Tk/shell/localization/literary changes.
- Four literary residuals untouched.
- No commit / push / tag.

---

## 13. Final Verdict

```text
S8_03_OUTPUT_POLICY_AUDITED_ACCEPTED
```

- [x] Output difference proven intentional and documented
- [x] UI does not mislead about output location
- [x] TXT output destination honored and consistent with artifact
- [x] EPUB output contract (source-adjacent, runtime-owned) accepted
- [x] UI semantics clarified (no behavior change)
- [x] Tests prove TXT/EPUB output semantics and result-state consistency
- [x] S6 TXT flow preserved; S8-01 EPUB direct launch preserved; no TXT fallback
- [x] Compile boundary PASS; `git diff --check` PASS
- [x] Provider / Network / Real Translation = 0 / 0 / 0
- [x] No unrelated production changes; no canonical architecture duplication
- [x] No commit / push / tag
