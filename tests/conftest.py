"""Repository-level pytest collection boundary (S13-03).

The repository carries a large historical test surface that predates the canonical
reader-first product:

* top-level historical suites (``beta_stage_*``, ``stage_*``, ``foundation_*``,
  ``rc_stage_*``, ``rm5``);
* legacy ``launcher_*_test.py`` wrappers, several of which run code at **import time**
  (``subprocess.run`` + ``raise SystemExit``) and abort whole-tree collection with a
  pytest INTERNALERROR;
* legacy ``controlled_*`` / ``prompt_runtime`` suites and ``*_test.py`` wrappers under
  ``tests/integration`` and ``tests/unit`` that import modules which no longer exist
  (``runtime_api.runtime_context``, ``core.prompt_builder``, ``core.quality.quality_context``).

This conftest quarantines ONLY that historical surface so the canonical suites collect and
run cleanly. Nothing is deleted or moved; quarantined files stay on disk and can still be
run explicitly by path when required.

Note: ``tests/contract/controlled_*`` are **canonical** contract tests and are intentionally
NOT ignored; only the legacy ``unit/`` / ``integration/`` controlled suites are.

Test-only boundary: no production code, runtime, schema, provider or EPUB behaviour is
affected.
"""

from __future__ import annotations

from pathlib import Path

_TESTS_DIR = Path(__file__).parent

# Top-level historical suites that are not part of the canonical reader-first workflow.
_LEGACY_DIR_GLOBS = (
    "beta_stage_*",
    "stage_*",
    "foundation_*",
    "rc_stage_*",
    "rm5",
)

collect_ignore: list[str] = []
for _pattern in _LEGACY_DIR_GLOBS:
    for _path in _TESTS_DIR.glob(_pattern):
        if _path.is_dir():
            collect_ignore.append(str(_path.relative_to(_TESTS_DIR)))

collect_ignore_glob = [
    # Legacy import-time ``launcher_*`` wrappers (all 7 unguarded SystemExit files and
    # the wider historical launcher surface).
    "**/launcher_*_test.py",
    # Legacy wrappers at the integration top level (historical lcr_*/translation_* names).
    "integration/*_test.py",
    # Nested legacy controlled-runtime suites (canonical contract/ is NOT affected).
    "unit/controlled_*/**",
    "integration/controlled_*/**",
    "unit/prompt_runtime/**",
    # Individual legacy files that import removed modules.
    "unit/test_stage15_4_repetition_detection.py",
    "unit/test_stage15_5_structure_integrity.py",
    "validation/test_ntpe_validate.py",
    "launcher_prompt_narrative_integration_test.py",
]
