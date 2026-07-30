# RM-2.3B Full Root Dependency Evidence Sweep Report

**Generated:** 2026-07-27T08:10:07+00:00
**Repository:** `D:\Python\NTPE`
**Total Scope Files:** 337

## Executive Summary

This report provides a comprehensive, read-only dependency evidence analysis for all root-level Python files matching `launcher_*.py` and `ntpe_*.py`. Every file has been evaluated for direct Python imports, incoming import references, runtime subprocess invocations, documentation/README references, automation manifest ties, artifact/audit references, and test harness usage.

### Classification Breakdown

| Classification | Count | Description |
| --- | ---: | --- |
| **KEEP_ROOT** | 15 | Primary entry points, launchers, or validators required at repository root. |
| **MOVE_WITH_WRAPPER** | 31 | Secondary launchers or modules referenced by docs/manifests requiring a root shim if moved. |
| **SAFE_MOVE** | 0 | Standalone utilities or helper scripts eligible for clean relocation to `tools/` or `verification/`. |
| **ARCHIVE_ONLY** | 291 | Historical stage test suites, benchmarks, or frozen stage verification scripts. |
| **DELETE_CANDIDATE** | 0 | Obsolete/superseded temporary scripts with zero references. |

---

## In-Depth File Dependency Evidence

### `launcher_adaptive_recovery.py`

- **Classification:** `MOVE_WITH_WRAPPER`
- **Reason:** Referenced by project configuration, automation manifests, or documentation; relocating requires maintaining a root compatibility wrapper shim.
- **Direct Imports:** 0 module import(s), 2 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (5):** `docs/archive/release_history/README_NTPE_v0_9_2_Adaptive_Chunk_Recovery.txt`, `docs/governance/migration/NTPE_ROOT_MIGRATION_MAP.json`, `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`, `docs/governance/repository/ROOT_INVENTORY_FREEZE.json`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (5):** 5 item(s)

### `launcher_analyzer.py`

- **Classification:** `MOVE_WITH_WRAPPER`
- **Reason:** Referenced by project configuration, automation manifests, or documentation; relocating requires maintaining a root compatibility wrapper shim.
- **Direct Imports:** 0 module import(s), 1 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (5):** `docs/archive/release_history/README_Analyzer_v1_0.txt`, `docs/governance/migration/NTPE_ROOT_MIGRATION_MAP.json`, `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`, `docs/governance/repository/ROOT_INVENTORY_FREEZE.json`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (6):** 6 item(s)

### `launcher_character_db.py`

- **Classification:** `MOVE_WITH_WRAPPER`
- **Reason:** Referenced by project configuration, automation manifests, or documentation; relocating requires maintaining a root compatibility wrapper shim.
- **Direct Imports:** 0 module import(s), 1 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (5):** `docs/archive/release_history/README_Character_Database_v2_0.txt`, `docs/governance/migration/NTPE_ROOT_MIGRATION_MAP.json`, `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`, `docs/governance/repository/ROOT_INVENTORY_FREEZE.json`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (6):** 6 item(s)

### `launcher_coverage_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 1 module import(s), 2 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (7):** `docs/archive/release_history/README_TQF_03_1_Title_Lock_Coverage_Strict_Patch.txt`, `docs/archive/release_history/README_TQF_03_2_Best_Effort_Save_UltraSplit.txt`, `docs/archive/release_history/README_TQF_03_Coverage_QA_No_Summary_Retranslate.txt`, `docs/governance/migration/NTPE_ROOT_MIGRATION_MAP.json`, `docs/governance/migration/rm_2_3b_scope.txt`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (7):** 7 item(s)

### `launcher_expansion_plan.py`

- **Classification:** `MOVE_WITH_WRAPPER`
- **Reason:** Referenced by project configuration, automation manifests, or documentation; relocating requires maintaining a root compatibility wrapper shim.
- **Direct Imports:** 1 module import(s), 2 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (5):** `docs/archive/release_history/README_TQF_05_2_Coverage_Aware_Style_Expansion.txt`, `docs/governance/migration/NTPE_ROOT_MIGRATION_MAP.json`, `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`, `docs/governance/repository/ROOT_INVENTORY_FREEZE.json`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (6):** 6 item(s)

### `launcher_glossary.py`

- **Classification:** `MOVE_WITH_WRAPPER`
- **Reason:** Referenced by project configuration, automation manifests, or documentation; relocating requires maintaining a root compatibility wrapper shim.
- **Direct Imports:** 0 module import(s), 1 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (7):** `docs/archive/release_history/LTS_Stage_03_Glossary_Character_Memory_Hash.json`, `docs/archive/release_history/LTS_Stage_03_Glossary_Character_Memory_Manifest.json`, `docs/archive/release_history/README_Glossary_Builder_v1_0.txt`, `docs/governance/migration/NTPE_ROOT_MIGRATION_MAP.json`, `docs/governance/migration/rm_2_3b_scope.txt`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (8):** 8 item(s)

### `launcher_kb.py`

- **Classification:** `MOVE_WITH_WRAPPER`
- **Reason:** Referenced by project configuration, automation manifests, or documentation; relocating requires maintaining a root compatibility wrapper shim.
- **Direct Imports:** 0 module import(s), 1 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (5):** `docs/archive/release_history/README_Knowledge_Base_Builder_v1_0.txt`, `docs/governance/migration/NTPE_ROOT_MIGRATION_MAP.json`, `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`, `docs/governance/repository/ROOT_INVENTORY_FREEZE.json`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (7):** 7 item(s)

### `launcher_memory.py`

- **Classification:** `MOVE_WITH_WRAPPER`
- **Reason:** Referenced by project configuration, automation manifests, or documentation; relocating requires maintaining a root compatibility wrapper shim.
- **Direct Imports:** 0 module import(s), 1 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (5):** `docs/archive/release_history/README_Character_Memory_v1_0.txt`, `docs/governance/migration/NTPE_ROOT_MIGRATION_MAP.json`, `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`, `docs/governance/repository/ROOT_INVENTORY_FREEZE.json`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (6):** 6 item(s)

### `launcher_novel_prompt_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 2 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (5):** `docs/archive/release_history/README_NTPE_v1_1_TQF_06_1_Novel_Prompt_Engine.txt`, `docs/governance/migration/NTPE_ROOT_MIGRATION_MAP.json`, `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`, `docs/governance/repository/ROOT_INVENTORY_FREEZE.json`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (7):** 7 item(s)

### `launcher_pipeline.py`

- **Classification:** `KEEP_ROOT`
- **Reason:** Core production entrypoint, primary CLI launcher, or primary project validator referenced in repository root documentation and operational scripts.
- **Direct Imports:** 0 module import(s), 2 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (14):** `docs/archive/release_history/README_NTPE_1_0_Beta_Stage_09_2.txt`, `docs/archive/release_history/README_NTPE_1_0_Beta_Stage_09_4.txt`, `docs/archive/release_history/README_NTPE_1_0_Beta_Stage_09_6.txt`, `docs/archive/release_history/README_NTPE_v0_9_0_Production_Pipeline.txt`, `docs/archive/release_history/README_NTPE_v0_9_1_1_Transactional_Recovery.txt`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (9):** 9 item(s)

### `launcher_pipeline_production.py`

- **Classification:** `KEEP_ROOT`
- **Reason:** Core production entrypoint, primary CLI launcher, or primary project validator referenced in repository root documentation and operational scripts.
- **Direct Imports:** 0 module import(s), 2 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (6):** `docs/archive/release_history/README_NTPE_v0_9_0_Production_Pipeline.txt`, `docs/governance/migration/NTPE_ROOT_MIGRATION_MAP.json`, `docs/governance/migration/NTPE_ROOT_MIGRATION_MAP.md`, `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (4):** 4 item(s)

### `launcher_pipeline_recovery.py`

- **Classification:** `MOVE_WITH_WRAPPER`
- **Reason:** Referenced by project configuration, automation manifests, or documentation; relocating requires maintaining a root compatibility wrapper shim.
- **Direct Imports:** 0 module import(s), 2 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (6):** `docs/archive/release_history/README_NTPE_v0_9_1_1_Transactional_Recovery.txt`, `docs/archive/release_history/README_NTPE_v0_9_1_Production_Recovery.txt`, `docs/governance/migration/NTPE_ROOT_MIGRATION_MAP.json`, `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (5):** 5 item(s)

### `launcher_pipeline_v1.py`

- **Classification:** `MOVE_WITH_WRAPPER`
- **Reason:** Referenced by project configuration, automation manifests, or documentation; relocating requires maintaining a root compatibility wrapper shim.
- **Direct Imports:** 0 module import(s), 2 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (6):** `docs/archive/release_history/README_NTPE_v1_0_1_Pipeline_Safety_Patch.txt`, `docs/archive/release_history/README_NTPE_v1_0_Production_Pipeline.txt`, `docs/governance/migration/NTPE_ROOT_MIGRATION_MAP.json`, `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (4):** 4 item(s)

### `launcher_profile.py`

- **Classification:** `MOVE_WITH_WRAPPER`
- **Reason:** Referenced by project configuration, automation manifests, or documentation; relocating requires maintaining a root compatibility wrapper shim.
- **Direct Imports:** 0 module import(s), 1 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (5):** `docs/archive/release_history/README_Project_Profile_v1_0.txt`, `docs/governance/migration/NTPE_ROOT_MIGRATION_MAP.json`, `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`, `docs/governance/repository/ROOT_INVENTORY_FREEZE.json`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (6):** 6 item(s)

### `launcher_prompt_builder.py`

- **Classification:** `MOVE_WITH_WRAPPER`
- **Reason:** Referenced by project configuration, automation manifests, or documentation; relocating requires maintaining a root compatibility wrapper shim.
- **Direct Imports:** 0 module import(s), 2 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (8):** `docs/archive/release_history/README_Pipeline_Engine_v1_0_Core.txt`, `docs/archive/release_history/README_Prompt_Builder_v1_0_1_Hotfix.txt`, `docs/archive/release_history/README_Prompt_Builder_v1_0_Core.txt`, `docs/archive/release_history/README_Translation_Engine_v2_0_Core.txt`, `docs/governance/migration/NTPE_ROOT_MIGRATION_MAP.json`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (6):** 6 item(s)

### `launcher_quality_benchmark.py`

- **Classification:** `MOVE_WITH_WRAPPER`
- **Reason:** Referenced by project configuration, automation manifests, or documentation; relocating requires maintaining a root compatibility wrapper shim.
- **Direct Imports:** 1 module import(s), 2 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (12):** `docs/archive/release_history/README_NTPE_v1_1_TQF_06_1_Novel_Prompt_Engine.txt`, `docs/archive/release_history/README_TQF_02_Semantic_Translation_Engine.txt`, `docs/archive/release_history/README_TQF_03_1_Title_Lock_Coverage_Strict_Patch.txt`, `docs/archive/release_history/README_TQF_03_2_Best_Effort_Save_UltraSplit.txt`, `docs/archive/release_history/README_TQF_03_Coverage_QA_No_Summary_Retranslate.txt`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (6):** 6 item(s)

### `launcher_retranslate_chunk.py`

- **Classification:** `MOVE_WITH_WRAPPER`
- **Reason:** Referenced by project configuration, automation manifests, or documentation; relocating requires maintaining a root compatibility wrapper shim.
- **Direct Imports:** 1 module import(s), 2 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (10):** `docs/archive/release_history/README_NTPE_v0_9_1_2_Retranslate_Chunk_Tool.txt`, `docs/archive/release_history/README_NTPE_v1_1_TQF_06_1_Novel_Prompt_Engine.txt`, `docs/archive/release_history/README_TQF_02_Semantic_Translation_Engine.txt`, `docs/archive/release_history/README_TQF_03_1_Title_Lock_Coverage_Strict_Patch.txt`, `docs/archive/release_history/README_TQF_03_2_Best_Effort_Save_UltraSplit.txt`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (4):** 4 item(s)

### `launcher_semantic_repair.py`

- **Classification:** `MOVE_WITH_WRAPPER`
- **Reason:** Referenced by project configuration, automation manifests, or documentation; relocating requires maintaining a root compatibility wrapper shim.
- **Direct Imports:** 1 module import(s), 2 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (7):** `docs/archive/release_history/README_NTPE_v1_1_TQF_06_1_Novel_Prompt_Engine.txt`, `docs/archive/release_history/README_TQF_04_Semantic_QA_Auto_Repair.txt`, `docs/archive/release_history/README_TQF_05_1_Novel_Style_Planner.txt`, `docs/archive/release_history/README_TQF_05_2_Coverage_Aware_Style_Expansion.txt`, `docs/governance/migration/NTPE_ROOT_MIGRATION_MAP.json`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (6):** 6 item(s)

### `launcher_semantic_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 1 module import(s), 2 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (4):** `docs/archive/release_history/README_TQF_02_Semantic_Translation_Engine.txt`, `docs/governance/migration/NTPE_ROOT_MIGRATION_MAP.json`, `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (7):** 7 item(s)

### `launcher_structure_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 2 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (4):** `docs/archive/release_history/README_TQF_01_Document_Structure_Engine.txt`, `docs/governance/migration/NTPE_ROOT_MIGRATION_MAP.json`, `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (7):** 7 item(s)

### `launcher_style_expansion.py`

- **Classification:** `MOVE_WITH_WRAPPER`
- **Reason:** Referenced by project configuration, automation manifests, or documentation; relocating requires maintaining a root compatibility wrapper shim.
- **Direct Imports:** 1 module import(s), 2 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (4):** `docs/archive/release_history/README_TQF_05_2_Coverage_Aware_Style_Expansion.txt`, `docs/governance/migration/NTPE_ROOT_MIGRATION_MAP.json`, `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (6):** 6 item(s)

### `launcher_style_planner_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 2 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (4):** `docs/archive/release_history/README_TQF_05_1_Novel_Style_Planner.txt`, `docs/governance/migration/NTPE_ROOT_MIGRATION_MAP.json`, `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (7):** 7 item(s)

### `launcher_translate.py`

- **Classification:** `KEEP_ROOT`
- **Reason:** Core production entrypoint, primary CLI launcher, or primary project validator referenced in repository root documentation and operational scripts.
- **Direct Imports:** 0 module import(s), 1 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (34):** `README.md`, `docs/PROJECT_LAYOUT.md`, `docs/archive/release_history/CHANGELOG_Stage_01_Translation_Runtime_Integration.md`, `docs/archive/release_history/CHANGELOG_Stage_02_Runtime_Contract_Stabilization.md`, `docs/archive/release_history/CHANGELOG_Stage_04_Runtime_Resume_Recovery_Layer.md`
- **Manifest/Config References (18):** `config/project_layout_policy.json`, `manifests/te_v32_runtime_scheduler_manifest.json`, `manifests/te_v33_runtime_integration_boundary_manifest.json`, `manifests/te_v33_runtime_integration_contract_manifest.json`, `manifests/te_v33_runtime_integration_manifest.json`
- **Artifact/Audit References (14):** 14 item(s)
- **Test Suite References (96):** `tests/integration/architecture_consolidation_batch2_test_consolidation_test.py`, `tests/integration/architecture_consolidation_batch5a_dynamic_usage_audit_test.py`, `tests/integration/launcher_product/test_launcher_product_integration.py`, `tests/integration/launcher_ps02_literary_regression_runner_test.py`, `tests/integration/launcher_ps03_translation_corpus_evaluation_test.py`

### `ntpe_architecture_consolidation_batch1_repository_hygiene_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 5 module import(s), 5 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (14):** 14 item(s)
- **Subprocess Invocations:** 7 call(s) inside file

### `ntpe_architecture_consolidation_batch2_test_consolidation_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 6 module import(s), 2 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (16):** 16 item(s)
- **Subprocess Invocations:** 3 call(s) inside file

### `ntpe_architecture_consolidation_batch3_shared_utilities_pilot_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 6 module import(s), 3 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (9):** 9 item(s)
- **Subprocess Invocations:** 1 call(s) inside file

### `ntpe_architecture_consolidation_batch4_quality_api_consolidation_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 4 module import(s), 7 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (10):** 10 item(s)
- **Subprocess Invocations:** 1 call(s) inside file

### `ntpe_architecture_consolidation_batch5a1_replacement_parity_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 2 module import(s), 2 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (7):** 7 item(s)

### `ntpe_architecture_consolidation_batch5a_dynamic_usage_audit_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 2 module import(s), 2 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (7):** 7 item(s)

### `ntpe_authorized_provider_invocation.py`

- **Classification:** `KEEP_ROOT`
- **Reason:** Core production entrypoint, primary CLI launcher, or primary project validator referenced in repository root documentation and operational scripts.
- **Direct Imports:** 1 module import(s), 3 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (2):** `config/project_layout_policy.json`, `manifests/te_v700_stage106_authorized_provider_execution_cli_manifest.json`
- **Artifact/Audit References (2):** 2 item(s)
- **Test Suite References (1):** `tests/integration/translation_engine_v700_stage106_authorized_provider_execution_cli_test.py`

### `ntpe_batch_monitor.py`

- **Classification:** `KEEP_ROOT`
- **Reason:** Core production entrypoint, primary CLI launcher, or primary project validator referenced in repository root documentation and operational scripts.
- **Direct Imports:** 0 module import(s), 1 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (7):** `docs/archive/release_history/CHANGELOG_LTS_STAGE_09.md`, `docs/archive/release_history/LTS_Stage_09_Batch_Runtime_Monitor_Report.md`, `docs/archive/release_history/LTS_Stage_11_Runtime_Freeze_Hash.json`, `docs/archive/release_history/LTS_Stage_11_Runtime_Freeze_Manifest.json`, `docs/archive/release_history/LTS_Stage_11_Runtime_Freeze_Report.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (4):** 4 item(s)
- **Test Suite References (1):** `tests/lts_stage_09/launcher_batch_runtime_monitor_test.py`

### `ntpe_controlled_real_provider_retry.py`

- **Classification:** `KEEP_ROOT`
- **Reason:** Core production entrypoint, primary CLI launcher, or primary project validator referenced in repository root documentation and operational scripts.
- **Direct Imports:** 4 module import(s), 3 `from` statement(s)
- **Imported By:** 1 other Python module(s)
  - *Importers:* `tests/integration/translation_engine_v700_stage10101_provider_timeout_controlled_retry_test.py`
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (2):** `config/project_layout_policy.json`, `manifests/te_v700_stage10101_provider_timeout_controlled_retry_manifest.json`
- **Artifact/Audit References (4):** 4 item(s)
- **Test Suite References (1):** `tests/integration/translation_engine_v700_stage10101_provider_timeout_controlled_retry_test.py`

### `ntpe_launcher.py`

- **Classification:** `KEEP_ROOT`
- **Reason:** Core production entrypoint, primary CLI launcher, or primary project validator referenced in repository root documentation and operational scripts.
- **Direct Imports:** 3 module import(s), 10 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (3):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`, `docs/releases/ntpe_v2_0/NTPE_V20_STAGE1_TRANSLATION_LAUNCHER_PRODUCT_FOUNDATION.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Test Suite References (2):** `tests/integration/launcher_product/test_launcher_product_integration.py`, `verification/release/ntpe_v20_stage1_translation_launcher_product_foundation_test.py`

### `ntpe_lcr_batch101_production_shadow_hook_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 2 module import(s), 1 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (9):** 9 item(s)
- **Test Suite References (1):** `tests/integration/lcr_batch101_production_shadow_hook_integration_test.py`
- **Subprocess Invocations:** 1 call(s) inside file

### `ntpe_lcr_batch102_character_memory_shadow_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 2 module import(s), 2 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (9):** 9 item(s)
- **Subprocess Invocations:** 1 call(s) inside file

### `ntpe_lcr_batch103_context_scene_shadow_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 2 module import(s), 2 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (9):** 9 item(s)
- **Subprocess Invocations:** 1 call(s) inside file

### `ntpe_lcr_batch104_dual_pass_semantic_shadow_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 2 module import(s), 2 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (5):** 5 item(s)
- **Subprocess Invocations:** 1 call(s) inside file

### `ntpe_lcr_batch105_bounded_dual_pass_pilot_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 2 module import(s), 1 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (4):** 4 item(s)
- **Subprocess Invocations:** 1 call(s) inside file

### `ntpe_lcr_batch106_single_chunk_dual_pass_execution_review_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 2 module import(s), 1 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (5):** 5 item(s)
- **Subprocess Invocations:** 1 call(s) inside file

### `ntpe_lcr_batch107_pre_execution_package_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 2 module import(s), 1 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (5):** 5 item(s)
- **Subprocess Invocations:** 1 call(s) inside file

### `ntpe_lcr_batch107_real_provider_validation.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 3 module import(s), 4 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (7):** 7 item(s)

### `ntpe_lcr_batch108_failure_characterization_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 2 module import(s), 1 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (2):** `config/project_layout_policy.json`, `manifests/lcr_batch109_provider_failure_policy_freeze_manifest.json`
- **Artifact/Audit References (6):** 6 item(s)
- **Subprocess Invocations:** 1 call(s) inside file

### `ntpe_lcr_batch109_provider_failure_policy_freeze_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 2 module import(s), 1 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (2):** `config/project_layout_policy.json`, `manifests/lcr_batch109_provider_failure_policy_freeze_manifest.json`
- **Artifact/Audit References (6):** 6 item(s)
- **Subprocess Invocations:** 1 call(s) inside file

### `ntpe_lcr_batch10_production_shadow_planning_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 2 module import(s), 1 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (9):** 9 item(s)
- **Test Suite References (1):** `tests/integration/lcr_batch10_production_shadow_planning_integration_test.py`
- **Subprocess Invocations:** 1 call(s) inside file

### `ntpe_lcr_batch110_governance_freeze_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 2 module import(s), 1 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (1):** `docs/governance/migration/rm_2_3b_scope.txt`
- **Manifest/Config References (2):** `config/project_layout_policy.json`, `manifests/lcr_batch110_governance_freeze_manifest.json`
- **Artifact/Audit References (7):** 7 item(s)
- **Subprocess Invocations:** 1 call(s) inside file

### `ntpe_lcr_batch111_governance_baseline_consumption_audit_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 2 module import(s), 1 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/releases/lcr/LCR_BATCH111_GOVERNANCE_BASELINE_CONSUMPTION_AUDIT.md`
- **Manifest/Config References (2):** `config/project_layout_policy.json`, `manifests/lcr_batch111_governance_baseline_consumption_audit_manifest.json`
- **Artifact/Audit References (6):** 6 item(s)
- **Subprocess Invocations:** 1 call(s) inside file

### `ntpe_lcr_batch1_legacy_capability_recovery_audit_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 4 module import(s), 2 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (1):** `docs/governance/migration/rm_2_3b_scope.txt`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (7):** 7 item(s)
- **Test Suite References (1):** `tests/integration/lcr_batch1_legacy_capability_recovery_audit_test.py`
- **Subprocess Invocations:** 2 call(s) inside file

### `ntpe_lcr_batch2_character_memory_v2_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 5 module import(s), 3 `from` statement(s)
- **Imported By:** 1 other Python module(s)
  - *Importers:* `audits/legacy_capability_recovery/batch2/generate_lcr_batch2_audit.py`
- **Docs/README References (1):** `docs/governance/migration/rm_2_3b_scope.txt`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (8):** 8 item(s)
- **Subprocess Invocations:** 3 call(s) inside file

### `ntpe_lcr_batch3_context_scene_memory_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 4 module import(s), 1 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (1):** `docs/governance/migration/rm_2_3b_scope.txt`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (9):** 9 item(s)
- **Test Suite References (1):** `tests/integration/lcr_batch3_context_scene_memory_integration_test.py`

### `ntpe_lcr_batch4_chunk_cache_v2_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 2 module import(s), 1 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (1):** `docs/governance/migration/rm_2_3b_scope.txt`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (9):** 9 item(s)
- **Test Suite References (1):** `tests/integration/lcr_batch4_chunk_cache_v2_integration_test.py`

### `ntpe_lcr_batch5_dual_pass_prototype_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 2 module import(s), 1 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (1):** `docs/governance/migration/rm_2_3b_scope.txt`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (9):** 9 item(s)
- **Test Suite References (1):** `tests/integration/lcr_batch5_dual_pass_translation_integration_test.py`

### `ntpe_lcr_batch6_post_polish_semantic_verification_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 2 module import(s), 1 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (1):** `docs/governance/migration/rm_2_3b_scope.txt`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (10):** 10 item(s)
- **Subprocess Invocations:** 1 call(s) inside file

### `ntpe_lcr_batch7_multilingual_profiles_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 2 module import(s), 1 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (1):** `docs/governance/migration/rm_2_3b_scope.txt`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (10):** 10 item(s)
- **Test Suite References (1):** `tests/integration/lcr_batch7_multilingual_profiles_integration_test.py`
- **Subprocess Invocations:** 1 call(s) inside file

### `ntpe_lcr_batch8_controlled_provider_routing_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 2 module import(s), 1 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (1):** `docs/governance/migration/rm_2_3b_scope.txt`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (10):** 10 item(s)
- **Test Suite References (1):** `tests/integration/lcr_batch8_controlled_provider_routing_integration_test.py`
- **Subprocess Invocations:** 1 call(s) inside file

### `ntpe_lcr_batch9_offline_golden_tic_validation_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 2 module import(s), 1 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (1):** `docs/governance/migration/rm_2_3b_scope.txt`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (9):** 9 item(s)
- **Test Suite References (1):** `tests/integration/lcr_batch9_offline_golden_tic_validation_integration_test.py`
- **Subprocess Invocations:** 1 call(s) inside file

### `ntpe_literary_evaluation.py`

- **Classification:** `MOVE_WITH_WRAPPER`
- **Reason:** Referenced by project configuration, automation manifests, or documentation; relocating requires maintaining a root compatibility wrapper shim.
- **Direct Imports:** 3 module import(s), 6 `from` statement(s)
- **Imported By:** 3 other Python module(s)
  - *Importers:* `ntpe_literary_regression.py`, `ntpe_production_translate.py`, `ntpe_ps03_translation_corpus_evaluation_test.py`
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (8):** 8 item(s)

### `ntpe_literary_regression.py`

- **Classification:** `MOVE_WITH_WRAPPER`
- **Reason:** Referenced by project configuration, automation manifests, or documentation; relocating requires maintaining a root compatibility wrapper shim.
- **Direct Imports:** 3 module import(s), 8 `from` statement(s)
- **Imported By:** 5 other Python module(s)
  - *Importers:* `ntpe_production_translate.py`, `ntpe_ps02_literary_regression_runner_test.py`, `ntpe_te_v523_provider_backpressure_resume_test.py`, `ntpe_translation_engine_refactor_v1_test.py`, `tests/smoke/launcher_ps02_literary_regression_runner_smoke_test.py`
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (9):** 9 item(s)
- **Test Suite References (1):** `tests/smoke/launcher_ps02_literary_regression_runner_smoke_test.py`

### `ntpe_long_run_recovery.py`

- **Classification:** `MOVE_WITH_WRAPPER`
- **Reason:** Referenced by project configuration, automation manifests, or documentation; relocating requires maintaining a root compatibility wrapper shim.
- **Direct Imports:** 0 module import(s), 1 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (8):** `docs/archive/release_history/CHANGELOG_LTS_STAGE_10.md`, `docs/archive/release_history/LTS_Stage_10_Long_Run_Stability_Report.md`, `docs/archive/release_history/LTS_Stage_11_Runtime_Freeze_Hash.json`, `docs/archive/release_history/LTS_Stage_11_Runtime_Freeze_Manifest.json`, `docs/archive/release_history/LTS_Stage_11_Runtime_Freeze_Report.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (5):** 5 item(s)
- **Test Suite References (1):** `tests/lts_stage_10/launcher_long_run_recovery_test.py`

### `ntpe_lts_rc_compatibility.py`

- **Classification:** `MOVE_WITH_WRAPPER`
- **Reason:** Referenced by project configuration, automation manifests, or documentation; relocating requires maintaining a root compatibility wrapper shim.
- **Direct Imports:** 0 module import(s), 1 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (4):** 4 item(s)

### `ntpe_lts_rc_final_validation.py`

- **Classification:** `MOVE_WITH_WRAPPER`
- **Reason:** Referenced by project configuration, automation manifests, or documentation; relocating requires maintaining a root compatibility wrapper shim.
- **Direct Imports:** 0 module import(s), 1 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (4):** `docs/archive/release_history/CHANGELOG_LTS_RC_05.md`, `docs/archive/release_history/README_NTPE_1_1_LTS_RC_05.txt`, `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (4):** 4 item(s)
- **Test Suite References (1):** `tests/lts_rc_05/launcher_lts_rc_final_validation_test.py`

### `ntpe_lts_rc_freeze.py`

- **Classification:** `MOVE_WITH_WRAPPER`
- **Reason:** Referenced by project configuration, automation manifests, or documentation; relocating requires maintaining a root compatibility wrapper shim.
- **Direct Imports:** 0 module import(s), 1 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (3):** `docs/archive/release_history/CHANGELOG_LTS_RC_06.md`, `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (4):** 4 item(s)
- **Test Suite References (1):** `tests/lts_rc_06/test_lts_rc_freeze_launcher.py`

### `ntpe_lts_rc_performance.py`

- **Classification:** `MOVE_WITH_WRAPPER`
- **Reason:** Referenced by project configuration, automation manifests, or documentation; relocating requires maintaining a root compatibility wrapper shim.
- **Direct Imports:** 0 module import(s), 1 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (3):** `docs/archive/release_history/LTS_RC_03_Performance_Long_Run_Validation_Report.md`, `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (4):** 4 item(s)

### `ntpe_lts_rc_quality.py`

- **Classification:** `MOVE_WITH_WRAPPER`
- **Reason:** Referenced by project configuration, automation manifests, or documentation; relocating requires maintaining a root compatibility wrapper shim.
- **Direct Imports:** 0 module import(s), 1 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (3):** `docs/archive/release_history/CHANGELOG_LTS_RC_04.md`, `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (4):** 4 item(s)
- **Test Suite References (1):** `tests/lts_rc_04/launcher_lts_rc_quality_test.py`

### `ntpe_lts_rc_regression.py`

- **Classification:** `MOVE_WITH_WRAPPER`
- **Reason:** Referenced by project configuration, automation manifests, or documentation; relocating requires maintaining a root compatibility wrapper shim.
- **Direct Imports:** 0 module import(s), 1 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (4):** 4 item(s)

### `ntpe_lts_release_candidate.py`

- **Classification:** `MOVE_WITH_WRAPPER`
- **Reason:** Referenced by project configuration, automation manifests, or documentation; relocating requires maintaining a root compatibility wrapper shim.
- **Direct Imports:** 0 module import(s), 1 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (4):** `docs/archive/release_history/CHANGELOG_LTS_STAGE_12.md`, `docs/archive/release_history/LTS_Stage_12_Release_Candidate_Preparation_Report.md`, `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (4):** 4 item(s)
- **Test Suite References (1):** `tests/lts_stage_12/launcher_lts_release_candidate_test.py`

### `ntpe_lts_runtime_freeze.py`

- **Classification:** `MOVE_WITH_WRAPPER`
- **Reason:** Referenced by project configuration, automation manifests, or documentation; relocating requires maintaining a root compatibility wrapper shim.
- **Direct Imports:** 0 module import(s), 1 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (4):** `docs/archive/release_history/CHANGELOG_LTS_STAGE_11.md`, `docs/archive/release_history/README_NTPE_1_1_LTS_Stage_11.txt`, `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (4):** 4 item(s)
- **Test Suite References (1):** `tests/lts_stage_11/launcher_lts_runtime_freeze_test.py`

### `ntpe_lts_stable_complete.py`

- **Classification:** `MOVE_WITH_WRAPPER`
- **Reason:** Referenced by project configuration, automation manifests, or documentation; relocating requires maintaining a root compatibility wrapper shim.
- **Direct Imports:** 0 module import(s), 1 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (4):** `docs/archive/release_history/CHANGELOG_LTS_STABLE_COMPLETE.md`, `docs/archive/release_history/README_NTPE_1_1_LTS_Stable_Release_Complete.txt`, `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (4):** 4 item(s)
- **Test Suite References (1):** `tests/lts_stable_complete/launcher_lts_stable_complete_test.py`

### `ntpe_lts_stable_finalization.py`

- **Classification:** `MOVE_WITH_WRAPPER`
- **Reason:** Referenced by project configuration, automation manifests, or documentation; relocating requires maintaining a root compatibility wrapper shim.
- **Direct Imports:** 0 module import(s), 1 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (3):** `docs/archive/release_history/CHANGELOG_LTS_STABLE_FINALIZATION.md`, `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (4):** 4 item(s)
- **Test Suite References (1):** `tests/lts_stable_finalization/launcher_lts_stable_finalization_test.py`

### `ntpe_lts_stable_preparation.py`

- **Classification:** `MOVE_WITH_WRAPPER`
- **Reason:** Referenced by project configuration, automation manifests, or documentation; relocating requires maintaining a root compatibility wrapper shim.
- **Direct Imports:** 0 module import(s), 1 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (4):** `docs/archive/release_history/CHANGELOG_LTS_STABLE_PREPARATION.md`, `docs/archive/release_history/README_NTPE_1_1_LTS_Stable_Preparation.txt`, `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (4):** 4 item(s)
- **Test Suite References (1):** `tests/lts_stable_preparation/test_lts_stable_preparation_launcher.py`

### `ntpe_plugin_marketplace.py`

- **Classification:** `MOVE_WITH_WRAPPER`
- **Reason:** Referenced by project configuration, automation manifests, or documentation; relocating requires maintaining a root compatibility wrapper shim.
- **Direct Imports:** 0 module import(s), 3 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (3):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`, `docs/release_notes/STAGE_12_PLUGIN_MARKETPLACE_CLI.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (7):** 7 item(s)

### `ntpe_production_translate.py`

- **Classification:** `KEEP_ROOT`
- **Reason:** Core production entrypoint, primary CLI launcher, or primary project validator referenced in repository root documentation and operational scripts.
- **Direct Imports:** 4 module import(s), 21 `from` statement(s)
- **Imported By:** 12 other Python module(s)
  - *Importers:* `launcher_translate.py`, `ntpe_ps04_1_regression_timeout_encoding_hotfix_test.py`, `ntpe_ter_v24_runtime_provider_stability_test.py`, `ntpe_translate_batch.py`, `ntpe_translate_txt.py`
- **Docs/README References (10):** `docs/PROJECT_LAYOUT.md`, `docs/governance/audits/NTPE_GOVERNANCE_GAP_ANALYSIS.md`, `docs/governance/migration/NTPE_ROOT_MIGRATION_MAP.json`, `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_REPOSITORY_STATUS_REPORT.md`
- **Manifest/Config References (11):** `config/project_layout_policy.json`, `manifests/te_v700_stage03_runtime_shadow_activation_manifest.json`, `manifests/te_v700_stage04_production_shadow_validation_manifest.json`, `manifests/te_v700_stage06_ace_canary_production_validation_manifest.json`, `manifests/te_v700_stage072_canary_diagnostics_target_stop_manifest.json`
- **Artifact/Audit References (31):** 31 item(s)
- **Test Suite References (17):** `tests/integration/architecture_consolidation_batch2_test_consolidation_test.py`, `tests/integration/architecture_consolidation_batch5a_dynamic_usage_audit_test.py`, `tests/integration/launcher_ps04_1_regression_timeout_encoding_hotfix_test.py`, `tests/integration/launcher_stage18_11_translation_timeout_debug_hotfix_test.py`, `tests/integration/launcher_ter_v21_provider_degraded_fallback_test.py`

### `ntpe_provider_audit.py`

- **Classification:** `KEEP_ROOT`
- **Reason:** Core production entrypoint, primary CLI launcher, or primary project validator referenced in repository root documentation and operational scripts.
- **Direct Imports:** 4 module import(s), 4 `from` statement(s)
- **Imported By:** 2 other Python module(s)
  - *Importers:* `ntpe_ter_v23_provider_configuration_audit_test.py`, `tests/integration/provider_configuration_test.py`
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (10):** 10 item(s)
- **Test Suite References (1):** `tests/integration/provider_configuration_test.py`

### `ntpe_provider_benchmark_session.py`

- **Classification:** `MOVE_WITH_WRAPPER`
- **Reason:** Referenced by project configuration, automation manifests, or documentation; relocating requires maintaining a root compatibility wrapper shim.
- **Direct Imports:** 0 module import(s), 2 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (3):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`, `docs/releases/te_v7_0/TE_V7_0_STAGE10_3_CONTROLLED_PROVIDER_SESSION_CLI_HARNESS.md`
- **Manifest/Config References (2):** `config/project_layout_policy.json`, `manifests/te_v700_stage103_controlled_provider_session_cli_harness_manifest.json`
- **Artifact/Audit References (4):** 4 item(s)
- **Test Suite References (3):** `tests/integration/translation_engine_v700_stage103_controlled_provider_session_cli_harness_test.py`, `tests/integration/translation_engine_v700_stage104_real_provider_invocation_boundary_contract_test.py`, `tests/integration/translation_engine_v700_stage105_authorized_single_invocation_provider_harness_test.py`

### `ntpe_provider_setup.py`

- **Classification:** `KEEP_ROOT`
- **Reason:** Core production entrypoint, primary CLI launcher, or primary project validator referenced in repository root documentation and operational scripts.
- **Direct Imports:** 5 module import(s), 3 `from` statement(s)
- **Imported By:** 1 other Python module(s)
  - *Importers:* `tests/regression/provider_environment_regression_test.py`
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (8):** 8 item(s)
- **Test Suite References (1):** `tests/regression/provider_environment_regression_test.py`
- **Subprocess Invocations:** 1 call(s) inside file

### `ntpe_provider_verify.py`

- **Classification:** `KEEP_ROOT`
- **Reason:** Core production entrypoint, primary CLI launcher, or primary project validator referenced in repository root documentation and operational scripts.
- **Direct Imports:** 3 module import(s), 3 `from` statement(s)
- **Imported By:** 1 other Python module(s)
  - *Importers:* `tests/regression/provider_environment_regression_test.py`
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (8):** 8 item(s)
- **Test Suite References (1):** `tests/regression/provider_environment_regression_test.py`

### `ntpe_ps01_literary_prompt_engine_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 1 module import(s), 2 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (3):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`, `docs/stages/production-stabilization/PS-01-Literary-Prompt-Engine.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (5):** 5 item(s)
- **Test Suite References (1):** `tests/integration/launcher_ps01_literary_prompt_engine_test.py`

### `ntpe_ps02_literary_regression_runner_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 2 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (5):** 5 item(s)

### `ntpe_ps03_translation_corpus_evaluation_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 2 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (5):** 5 item(s)

### `ntpe_ps04_1_regression_timeout_encoding_hotfix_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 2 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (8):** 8 item(s)

### `ntpe_ps04_2_progress_visibility_hotfix_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 2 module import(s), 3 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (5):** 5 item(s)

### `ntpe_ps04_narrative_character_understanding_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 1 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (5):** 5 item(s)

### `ntpe_single_real_provider_invocation.py`

- **Classification:** `KEEP_ROOT`
- **Reason:** Core production entrypoint, primary CLI launcher, or primary project validator referenced in repository root documentation and operational scripts.
- **Direct Imports:** 4 module import(s), 4 `from` statement(s)
- **Imported By:** 1 other Python module(s)
  - *Importers:* `tests/integration/translation_engine_v700_stage1010_single_real_provider_invocation_test.py`
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (2):** `config/project_layout_policy.json`, `manifests/te_v700_stage1010_single_real_provider_invocation_manifest.json`
- **Artifact/Audit References (4):** 4 item(s)
- **Test Suite References (1):** `tests/integration/translation_engine_v700_stage1010_single_real_provider_invocation_test.py`

### `ntpe_stage14_4_provider_orchestration_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 1 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (9):** 9 item(s)

### `ntpe_stage14_5_provider_observability_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 1 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (9):** 9 item(s)

### `ntpe_stage14_6_provider_security_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 1 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (12):** 12 item(s)
- **Test Suite References (1):** `tests/integration/architecture_consolidation_batch2_test_consolidation_test.py`

### `ntpe_stage15_2_translation_completeness_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 1 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (4):** `docs/archive/release_history/README_STAGE15_2_TRANSLATION_COMPLETENESS.md`, `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`, `docs/stages/stage15/README_STAGE15_2_TRANSLATION_COMPLETENESS.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (8):** 8 item(s)

### `ntpe_stage15_3_terminology_consistency_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 1 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (4):** `docs/archive/release_history/README_STAGE15_3_TERMINOLOGY_CONSISTENCY.md`, `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`, `docs/stages/stage15/README_STAGE15_3_TERMINOLOGY_CONSISTENCY.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (8):** 8 item(s)

### `ntpe_stage15_4_repetition_detection_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 4 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (7):** 7 item(s)

### `ntpe_stage15_5_structure_integrity_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 1 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (3):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`, `docs/stages/stage15/README_STAGE15_5_FORMATTING_STRUCTURE_INTEGRITY.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (9):** 9 item(s)

### `ntpe_stage15_6_quality_export_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 1 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (6):** 6 item(s)

### `ntpe_stage15_7_quality_auto_repair_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 1 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (6):** 6 item(s)

### `ntpe_stage15_8_translation_quality_engine_freeze_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 1 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (3):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`, `docs/stages/stage15/README_STAGE15_8_TRANSLATION_QUALITY_ENGINE_FREEZE.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (9):** 9 item(s)

### `ntpe_stage16_1_context_intelligence_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 1 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (3):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`, `docs/stages/stage16/README_STAGE16_1_CONTEXT_INTELLIGENCE_ENGINE.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (6):** 6 item(s)

### `ntpe_stage16_2_narrative_intelligence_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 1 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (6):** 6 item(s)

### `ntpe_stage16_3_character_relationship_intelligence_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 1 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (7):** 7 item(s)

### `ntpe_stage16_4_semantic_consistency_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 1 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (7):** 7 item(s)

### `ntpe_stage16_5_translation_memory_intelligence_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 1 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (7):** 7 item(s)

### `ntpe_stage16_6_adaptive_translation_strategy_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 2 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (7):** 7 item(s)

### `ntpe_stage16_7_intelligence_runtime_integration_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 3 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (9):** 9 item(s)

### `ntpe_stage16_8_advanced_translation_intelligence_freeze_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 3 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (9):** 9 item(s)

### `ntpe_stage17_1_translation_workflow_engine_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 1 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (7):** 7 item(s)

### `ntpe_stage17_2_job_scheduler_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 1 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (7):** 7 item(s)

### `ntpe_stage17_3_resource_optimizer_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 3 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (7):** 7 item(s)

### `ntpe_stage17_4_review_approval_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 4 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (7):** 7 item(s)

### `ntpe_stage17_5_export_framework_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 5 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (7):** 7 item(s)

### `ntpe_stage17_6_monitoring_dashboard_api_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 2 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (7):** 7 item(s)

### `ntpe_stage17_7_production_runtime_integration_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 2 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (3):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`, `docs/stages/stage17/README_STAGE17_7_PRODUCTION_RUNTIME_INTEGRATION.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (8):** 8 item(s)

### `ntpe_stage17_8_production_platform_freeze_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 1 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (3):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`, `docs/stages/stage17/README_STAGE17_8_PRODUCTION_PLATFORM_FREEZE.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (9):** 9 item(s)

### `ntpe_stage18_10_translation_qa_retry_hotfix_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 2 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (6):** 6 item(s)

### `ntpe_stage18_11_translation_timeout_debug_hotfix_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 1 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (6):** 6 item(s)

### `ntpe_stage18_12_name_lock_hotfix_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 2 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (4):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`, `docs/stages/stage18/18.12-name-lock-hotfix.md`, `docs/stages/stage18/README_STAGE_18_12.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (5):** 5 item(s)

### `ntpe_stage18_13_translation_quality_stabilization_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 2 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (5):** 5 item(s)
- **Test Suite References (1):** `tests/integration/launcher_stage18_13_translation_quality_stabilization_test.py`

### `ntpe_stage18_14_simplified_chinese_qa_hotfix_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 1 module import(s), 2 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (5):** 5 item(s)

### `ntpe_stage18_1_enterprise_deployment_foundation_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 1 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (3):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`, `docs/stages/stage18/README_STAGE18_1_ENTERPRISE_DEPLOYMENT_FOUNDATION.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (8):** 8 item(s)

### `ntpe_stage18_2_enterprise_configuration_center_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 1 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (7):** 7 item(s)

### `ntpe_stage18_3_enterprise_deployment_profiles_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 2 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (3):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`, `docs/stages/stage18/README_STAGE18_3_ENTERPRISE_DEPLOYMENT_PROFILES.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (7):** 7 item(s)

### `ntpe_stage18_4_enterprise_deployment_runtime_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 1 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (3):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`, `docs/stages/stage18/README_STAGE18_4_ENTERPRISE_DEPLOYMENT_RUNTIME.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (8):** 8 item(s)

### `ntpe_stage18_5_enterprise_deployment_orchestrator_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 1 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (3):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`, `docs/stages/stage18/README_STAGE18_5_ENTERPRISE_DEPLOYMENT_ORCHESTRATOR.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (7):** 7 item(s)

### `ntpe_stage18_6_documentation_center_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 1 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (3):** `README.md`, `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (5):** 5 item(s)
- **Test Suite References (1):** `verification/legacy/instructions/APPLY_STAGE_18_6_DOCUMENTATION_CENTER.bat`

### `ntpe_stage18_7_enterprise_deployment_validation_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 1 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (7):** 7 item(s)

### `ntpe_stage18_8_enterprise_deployment_freeze_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 1 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (3):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`, `docs/stages/stage18/18.8.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (9):** 9 item(s)
- **Test Suite References (1):** `verification/legacy/instructions/APPLY_STAGE_18_8_ENTERPRISE_DEPLOYMENT_FREEZE.bat`

### `ntpe_stage18_9_production_translation_integration_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 2 module import(s), 1 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (5):** 5 item(s)
- **Subprocess Invocations:** 1 call(s) inside file

### `ntpe_stage69_controlled_runtime_scheduling_envelope_consumption_acceptance_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 4 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`

### `ntpe_te_v30_stage01_prompt_intelligence_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 4 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (3):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`, `docs/releases/TE_v3_1_SCHEDULER_LAYER_FREEZE.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (7):** 7 item(s)

### `ntpe_te_v30_stage021_naturalness_guard_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 4 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (3):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`, `docs/releases/TE_v3_1_SCHEDULER_LAYER_FREEZE.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (7):** 7 item(s)

### `ntpe_te_v30_stage022_runtime_speed_policy_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 5 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (5):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`, `docs/releases/TE_v3_1_SCHEDULER_LAYER_FREEZE.md`, `docs/releases/TE_v5_2_1_REGRESSION_TIMEOUT_PROPAGATION_FIX.md`, `docs/releases/te_v5_3/TE_V5_3_1_UNIFIED_QUALITY_GATE.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (8):** 8 item(s)
- **Test Suite References (2):** `verification/legacy/instructions/APPLY_TE_V5_2_1.txt`, `verification/legacy/instructions/APPLY_TE_V5_2_3.txt`

### `ntpe_te_v30_stage02_context_intelligence_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 4 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (3):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`, `docs/releases/TE_v3_1_SCHEDULER_LAYER_FREEZE.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (7):** 7 item(s)

### `ntpe_te_v31_scheduler_layer_freeze_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 4 module import(s), 5 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (3):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`, `docs/releases/TE_v3_1_SCHEDULER_LAYER_FREEZE.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (11):** 11 item(s)

### `ntpe_te_v31_stage311_scheduler_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 2 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (3):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`, `docs/releases/TE_v3_1_SCHEDULER_LAYER_FREEZE.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (8):** 8 item(s)

### `ntpe_te_v31_stage312_retry_queue_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 2 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (3):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`, `docs/releases/TE_v3_1_SCHEDULER_LAYER_FREEZE.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (9):** 9 item(s)

### `ntpe_te_v31_stage313_result_collector_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 2 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (3):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`, `docs/releases/TE_v3_1_SCHEDULER_LAYER_FREEZE.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (9):** 9 item(s)

### `ntpe_te_v31_stage314_resume_journal_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 4 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (3):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`, `docs/releases/TE_v3_1_SCHEDULER_LAYER_FREEZE.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (11):** 11 item(s)

### `ntpe_te_v31_stage315_performance_dashboard_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 1 module import(s), 4 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (3):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`, `docs/releases/TE_v3_1_SCHEDULER_LAYER_FREEZE.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (8):** 8 item(s)

### `ntpe_te_v31_stage316_performance_regression_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 1 module import(s), 4 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (3):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`, `docs/releases/TE_v3_1_SCHEDULER_LAYER_FREEZE.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (8):** 8 item(s)

### `ntpe_te_v32_runtime_scheduler_freeze_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 4 module import(s), 4 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (10):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`, `docs/releases/te_v3_5/TE_v3_5_RUNTIME_DISABLED_TRIAL_FREEZE.md`, `docs/releases/te_v3_6/TE_v3_6_RUNTIME_SAFE_HOOK_PREFLIGHT_FREEZE.md`, `docs/releases/te_v3_6/TE_v3_6_STAGE_3_6_4_RUNTIME_SAFE_HOOK_PREFLIGHT_BOUNDARY_REGRESSION.md`
- **Manifest/Config References (16):** `config/project_layout_policy.json`, `manifests/te_v32_runtime_scheduler_manifest.json`, `manifests/te_v33_runtime_integration_boundary_manifest.json`, `manifests/te_v33_runtime_integration_contract_manifest.json`, `manifests/te_v33_runtime_integration_manifest.json`
- **Artifact/Audit References (12):** 12 item(s)

### `ntpe_te_v32_stage321_runtime_scheduler_adapter_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 2 module import(s), 2 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (2):** `config/project_layout_policy.json`, `manifests/te_v32_runtime_scheduler_manifest.json`
- **Artifact/Audit References (9):** 9 item(s)

### `ntpe_te_v32_stage322_runtime_adapter_dry_run_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 2 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (3):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`, `docs/releases/te_v3_2/TE_v3_2_STAGE_3_2_2_RUNTIME_ADAPTER_DRY_RUN.md`
- **Manifest/Config References (2):** `config/project_layout_policy.json`, `manifests/te_v32_runtime_scheduler_manifest.json`
- **Artifact/Audit References (14):** 14 item(s)
- **Test Suite References (1):** `tests/consolidated/test_exact_duplicate_contracts.py`

### `ntpe_te_v32_stage323_existing_scheduler_injection_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 2 module import(s), 3 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (2):** `config/project_layout_policy.json`, `manifests/te_v32_runtime_scheduler_manifest.json`
- **Artifact/Audit References (10):** 10 item(s)

### `ntpe_te_v32_stage324_runtime_scheduler_state_bridge_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 2 module import(s), 3 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (2):** `config/project_layout_policy.json`, `manifests/te_v32_runtime_scheduler_manifest.json`
- **Artifact/Audit References (10):** 10 item(s)

### `ntpe_te_v32_stage325_runtime_scheduler_resume_contract_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 2 module import(s), 3 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (2):** `config/project_layout_policy.json`, `manifests/te_v32_runtime_scheduler_manifest.json`
- **Artifact/Audit References (11):** 11 item(s)

### `ntpe_te_v33_runtime_integration_freeze_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 4 module import(s), 3 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (10):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`, `docs/releases/te_v3_5/TE_v3_5_RUNTIME_DISABLED_TRIAL_FREEZE.md`, `docs/releases/te_v3_6/TE_v3_6_RUNTIME_SAFE_HOOK_PREFLIGHT_FREEZE.md`, `docs/releases/te_v3_6/TE_v3_6_STAGE_3_6_4_RUNTIME_SAFE_HOOK_PREFLIGHT_BOUNDARY_REGRESSION.md`
- **Manifest/Config References (13):** `config/project_layout_policy.json`, `manifests/te_v33_runtime_integration_manifest.json`, `manifests/te_v34_runtime_optin_hook_boundary_manifest.json`, `manifests/te_v34_runtime_optin_hook_contract_manifest.json`, `manifests/te_v34_runtime_optin_hook_manifest.json`
- **Artifact/Audit References (12):** 12 item(s)

### `ntpe_te_v33_stage331_runtime_integration_contract_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 3 module import(s), 3 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (4):** `config/project_layout_policy.json`, `manifests/te_v33_runtime_integration_boundary_manifest.json`, `manifests/te_v33_runtime_integration_contract_manifest.json`, `manifests/te_v33_runtime_integration_manifest.json`
- **Artifact/Audit References (10):** 10 item(s)

### `ntpe_te_v33_stage332_runtime_integration_feature_flag_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 2 module import(s), 3 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (3):** `config/project_layout_policy.json`, `manifests/te_v33_runtime_integration_boundary_manifest.json`, `manifests/te_v33_runtime_integration_manifest.json`
- **Artifact/Audit References (10):** 10 item(s)

### `ntpe_te_v33_stage333_runtime_integration_disabled_guard_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 2 module import(s), 3 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (3):** `config/project_layout_policy.json`, `manifests/te_v33_runtime_integration_boundary_manifest.json`, `manifests/te_v33_runtime_integration_manifest.json`
- **Artifact/Audit References (10):** 10 item(s)

### `ntpe_te_v33_stage334_runtime_integration_mock_orchestrator_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 2 module import(s), 3 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (3):** `config/project_layout_policy.json`, `manifests/te_v33_runtime_integration_boundary_manifest.json`, `manifests/te_v33_runtime_integration_manifest.json`
- **Artifact/Audit References (10):** 10 item(s)

### `ntpe_te_v33_stage335_runtime_integration_boundary_regression_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 3 module import(s), 3 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (3):** `config/project_layout_policy.json`, `manifests/te_v33_runtime_integration_boundary_manifest.json`, `manifests/te_v33_runtime_integration_manifest.json`
- **Artifact/Audit References (10):** 10 item(s)

### `ntpe_te_v34_runtime_optin_hook_freeze_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 4 module import(s), 3 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (10):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`, `docs/releases/te_v3_5/TE_v3_5_RUNTIME_DISABLED_TRIAL_FREEZE.md`, `docs/releases/te_v3_6/TE_v3_6_RUNTIME_SAFE_HOOK_PREFLIGHT_FREEZE.md`, `docs/releases/te_v3_6/TE_v3_6_STAGE_3_6_4_RUNTIME_SAFE_HOOK_PREFLIGHT_BOUNDARY_REGRESSION.md`
- **Manifest/Config References (10):** `config/project_layout_policy.json`, `manifests/te_v34_runtime_optin_hook_manifest.json`, `manifests/te_v35_runtime_disabled_trial_boundary_manifest.json`, `manifests/te_v35_runtime_disabled_trial_contract_manifest.json`, `manifests/te_v35_runtime_disabled_trial_manifest.json`
- **Artifact/Audit References (12):** 12 item(s)

### `ntpe_te_v34_stage341_runtime_optin_hook_contract_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 3 module import(s), 3 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (4):** `config/project_layout_policy.json`, `manifests/te_v34_runtime_optin_hook_boundary_manifest.json`, `manifests/te_v34_runtime_optin_hook_contract_manifest.json`, `manifests/te_v34_runtime_optin_hook_manifest.json`
- **Artifact/Audit References (10):** 10 item(s)

### `ntpe_te_v34_stage342_runtime_optin_hook_guard_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 2 module import(s), 3 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (3):** `config/project_layout_policy.json`, `manifests/te_v34_runtime_optin_hook_boundary_manifest.json`, `manifests/te_v34_runtime_optin_hook_manifest.json`
- **Artifact/Audit References (9):** 9 item(s)

### `ntpe_te_v34_stage343_runtime_optin_hook_mock_bridge_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 2 module import(s), 3 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (3):** `config/project_layout_policy.json`, `manifests/te_v34_runtime_optin_hook_boundary_manifest.json`, `manifests/te_v34_runtime_optin_hook_manifest.json`
- **Artifact/Audit References (9):** 9 item(s)

### `ntpe_te_v34_stage344_runtime_optin_hook_boundary_regression_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 3 module import(s), 3 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (3):** `config/project_layout_policy.json`, `manifests/te_v34_runtime_optin_hook_boundary_manifest.json`, `manifests/te_v34_runtime_optin_hook_manifest.json`
- **Artifact/Audit References (10):** 10 item(s)

### `ntpe_te_v35_runtime_disabled_trial_freeze_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 4 module import(s), 3 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (10):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`, `docs/releases/te_v3_5/TE_v3_5_RUNTIME_DISABLED_TRIAL_FREEZE.md`, `docs/releases/te_v3_6/TE_v3_6_RUNTIME_SAFE_HOOK_PREFLIGHT_FREEZE.md`, `docs/releases/te_v3_6/TE_v3_6_STAGE_3_6_4_RUNTIME_SAFE_HOOK_PREFLIGHT_BOUNDARY_REGRESSION.md`
- **Manifest/Config References (7):** `config/project_layout_policy.json`, `manifests/te_v35_runtime_disabled_trial_manifest.json`, `manifests/te_v36_runtime_safe_hook_preflight_boundary_manifest.json`, `manifests/te_v36_runtime_safe_hook_preflight_contract_manifest.json`, `manifests/te_v36_runtime_safe_hook_preflight_manifest.json`
- **Artifact/Audit References (12):** 12 item(s)

### `ntpe_te_v35_stage351_runtime_disabled_trial_contract_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 3 module import(s), 3 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (3):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`, `docs/releases/te_v3_5/TE_v3_5_RUNTIME_DISABLED_TRIAL_FREEZE.md`
- **Manifest/Config References (4):** `config/project_layout_policy.json`, `manifests/te_v35_runtime_disabled_trial_boundary_manifest.json`, `manifests/te_v35_runtime_disabled_trial_contract_manifest.json`, `manifests/te_v35_runtime_disabled_trial_manifest.json`
- **Artifact/Audit References (10):** 10 item(s)

### `ntpe_te_v35_stage352_runtime_disabled_trial_guard_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 2 module import(s), 3 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (3):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`, `docs/releases/te_v3_5/TE_v3_5_RUNTIME_DISABLED_TRIAL_FREEZE.md`
- **Manifest/Config References (3):** `config/project_layout_policy.json`, `manifests/te_v35_runtime_disabled_trial_boundary_manifest.json`, `manifests/te_v35_runtime_disabled_trial_manifest.json`
- **Artifact/Audit References (10):** 10 item(s)

### `ntpe_te_v35_stage353_runtime_disabled_trial_mock_bridge_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 2 module import(s), 3 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (3):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`, `docs/releases/te_v3_5/TE_v3_5_RUNTIME_DISABLED_TRIAL_FREEZE.md`
- **Manifest/Config References (3):** `config/project_layout_policy.json`, `manifests/te_v35_runtime_disabled_trial_boundary_manifest.json`, `manifests/te_v35_runtime_disabled_trial_manifest.json`
- **Artifact/Audit References (9):** 9 item(s)

### `ntpe_te_v35_stage354_runtime_disabled_trial_boundary_regression_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 3 module import(s), 3 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (3):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`, `docs/releases/te_v3_5/TE_v3_5_RUNTIME_DISABLED_TRIAL_FREEZE.md`
- **Manifest/Config References (3):** `config/project_layout_policy.json`, `manifests/te_v35_runtime_disabled_trial_boundary_manifest.json`, `manifests/te_v35_runtime_disabled_trial_manifest.json`
- **Artifact/Audit References (10):** 10 item(s)

### `ntpe_te_v36_runtime_safe_hook_preflight_freeze_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 4 module import(s), 3 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (8):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`, `docs/releases/te_v3_6/TE_v3_6_RUNTIME_SAFE_HOOK_PREFLIGHT_FREEZE.md`, `docs/releases/te_v3_7/TE_v3_7_RUNTIME_READINESS_FREEZE.md`, `docs/releases/te_v3_7/TE_v3_7_STAGE_3_7_1_RUNTIME_READINESS_GATE_CONTRACT.md`
- **Manifest/Config References (4):** `config/project_layout_policy.json`, `manifests/te_v36_runtime_safe_hook_preflight_manifest.json`, `manifests/te_v37_runtime_readiness_gate_contract_manifest.json`, `manifests/te_v37_runtime_readiness_manifest.json`
- **Artifact/Audit References (12):** 12 item(s)

### `ntpe_te_v36_stage361_runtime_safe_hook_preflight_contract_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 3 module import(s), 3 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (4):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`, `docs/releases/te_v3_6/TE_v3_6_RUNTIME_SAFE_HOOK_PREFLIGHT_FREEZE.md`, `docs/releases/te_v3_6/TE_v3_6_STAGE_3_6_4_RUNTIME_SAFE_HOOK_PREFLIGHT_BOUNDARY_REGRESSION.md`
- **Manifest/Config References (4):** `config/project_layout_policy.json`, `manifests/te_v36_runtime_safe_hook_preflight_boundary_manifest.json`, `manifests/te_v36_runtime_safe_hook_preflight_contract_manifest.json`, `manifests/te_v36_runtime_safe_hook_preflight_manifest.json`
- **Artifact/Audit References (10):** 10 item(s)

### `ntpe_te_v36_stage362_runtime_safe_hook_preflight_guard_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 2 module import(s), 3 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (4):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`, `docs/releases/te_v3_6/TE_v3_6_RUNTIME_SAFE_HOOK_PREFLIGHT_FREEZE.md`, `docs/releases/te_v3_6/TE_v3_6_STAGE_3_6_4_RUNTIME_SAFE_HOOK_PREFLIGHT_BOUNDARY_REGRESSION.md`
- **Manifest/Config References (3):** `config/project_layout_policy.json`, `manifests/te_v36_runtime_safe_hook_preflight_boundary_manifest.json`, `manifests/te_v36_runtime_safe_hook_preflight_manifest.json`
- **Artifact/Audit References (10):** 10 item(s)

### `ntpe_te_v36_stage363_runtime_safe_hook_preflight_mock_bridge_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 2 module import(s), 3 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (4):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`, `docs/releases/te_v3_6/TE_v3_6_RUNTIME_SAFE_HOOK_PREFLIGHT_FREEZE.md`, `docs/releases/te_v3_6/TE_v3_6_STAGE_3_6_4_RUNTIME_SAFE_HOOK_PREFLIGHT_BOUNDARY_REGRESSION.md`
- **Manifest/Config References (3):** `config/project_layout_policy.json`, `manifests/te_v36_runtime_safe_hook_preflight_boundary_manifest.json`, `manifests/te_v36_runtime_safe_hook_preflight_manifest.json`
- **Artifact/Audit References (9):** 9 item(s)

### `ntpe_te_v36_stage364_runtime_safe_hook_preflight_boundary_regression_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 3 module import(s), 3 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (4):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`, `docs/releases/te_v3_6/TE_v3_6_RUNTIME_SAFE_HOOK_PREFLIGHT_FREEZE.md`, `docs/releases/te_v3_6/TE_v3_6_STAGE_3_6_4_RUNTIME_SAFE_HOOK_PREFLIGHT_BOUNDARY_REGRESSION.md`
- **Manifest/Config References (3):** `config/project_layout_policy.json`, `manifests/te_v36_runtime_safe_hook_preflight_boundary_manifest.json`, `manifests/te_v36_runtime_safe_hook_preflight_manifest.json`
- **Artifact/Audit References (10):** 10 item(s)

### `ntpe_te_v37_runtime_readiness_freeze_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 4 module import(s), 3 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (3):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`, `docs/releases/te_v3_7/TE_v3_7_RUNTIME_READINESS_FREEZE.md`
- **Manifest/Config References (2):** `config/project_layout_policy.json`, `manifests/te_v37_runtime_readiness_manifest.json`
- **Artifact/Audit References (13):** 13 item(s)

### `ntpe_te_v37_stage371_runtime_readiness_gate_contract_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 3 module import(s), 3 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (7):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`, `docs/releases/te_v3_7/TE_v3_7_RUNTIME_READINESS_FREEZE.md`, `docs/releases/te_v3_7/TE_v3_7_STAGE_3_7_1_RUNTIME_READINESS_GATE_CONTRACT.md`, `docs/releases/te_v3_7/TE_v3_7_STAGE_3_7_2_RUNTIME_READINESS_GATE_EVALUATOR.md`
- **Manifest/Config References (3):** `config/project_layout_policy.json`, `manifests/te_v37_runtime_readiness_gate_contract_manifest.json`, `manifests/te_v37_runtime_readiness_manifest.json`
- **Artifact/Audit References (10):** 10 item(s)

### `ntpe_te_v37_stage372_runtime_readiness_gate_evaluator_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 2 module import(s), 3 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (6):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`, `docs/releases/te_v3_7/TE_v3_7_RUNTIME_READINESS_FREEZE.md`, `docs/releases/te_v3_7/TE_v3_7_STAGE_3_7_2_RUNTIME_READINESS_GATE_EVALUATOR.md`, `docs/releases/te_v3_7/TE_v3_7_STAGE_3_7_3_RUNTIME_READINESS_EVIDENCE_COLLECTOR.md`
- **Manifest/Config References (2):** `config/project_layout_policy.json`, `manifests/te_v37_runtime_readiness_manifest.json`
- **Artifact/Audit References (9):** 9 item(s)

### `ntpe_te_v37_stage373_runtime_readiness_evidence_collector_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 2 module import(s), 3 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (5):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`, `docs/releases/te_v3_7/TE_v3_7_RUNTIME_READINESS_FREEZE.md`, `docs/releases/te_v3_7/TE_v3_7_STAGE_3_7_3_RUNTIME_READINESS_EVIDENCE_COLLECTOR.md`, `docs/releases/te_v3_7/TE_v3_7_STAGE_3_7_4_RUNTIME_READINESS_DECISION.md`
- **Manifest/Config References (2):** `config/project_layout_policy.json`, `manifests/te_v37_runtime_readiness_manifest.json`
- **Artifact/Audit References (9):** 9 item(s)

### `ntpe_te_v37_stage374_runtime_readiness_decision_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 2 module import(s), 3 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (4):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`, `docs/releases/te_v3_7/TE_v3_7_RUNTIME_READINESS_FREEZE.md`, `docs/releases/te_v3_7/TE_v3_7_STAGE_3_7_4_RUNTIME_READINESS_DECISION.md`
- **Manifest/Config References (2):** `config/project_layout_policy.json`, `manifests/te_v37_runtime_readiness_manifest.json`
- **Artifact/Audit References (9):** 9 item(s)

### `ntpe_te_v38_stage381_controlled_runtime_trial_contract_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 3 module import(s), 3 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (4):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`, `docs/releases/te_v3_8/TE_v3_8_STAGE_3_8_1_CONTROLLED_RUNTIME_TRIAL_CONTRACT.md`, `docs/releases/te_v3_8/TE_v3_8_STAGE_3_8_2_CONTROLLED_RUNTIME_TRIAL_ADMISSION_GATE.md`
- **Manifest/Config References (3):** `config/project_layout_policy.json`, `manifests/te_v38_controlled_runtime_trial_admission_manifest.json`, `manifests/te_v38_controlled_runtime_trial_contract_manifest.json`
- **Artifact/Audit References (10):** 10 item(s)

### `ntpe_te_v38_stage382_controlled_runtime_trial_admission_gate_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 3 module import(s), 3 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (3):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`, `docs/releases/te_v3_8/TE_v3_8_STAGE_3_8_2_CONTROLLED_RUNTIME_TRIAL_ADMISSION_GATE.md`
- **Manifest/Config References (2):** `config/project_layout_policy.json`, `manifests/te_v38_controlled_runtime_trial_admission_manifest.json`
- **Artifact/Audit References (10):** 10 item(s)

### `ntpe_te_v40_stage401_translation_reliability_baseline_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 1 `from` statement(s)
- **Imported By:** 1 other Python module(s)
  - *Importers:* `tests/integration/translation_reliability_stage401_baseline_test.py`
- **Docs/README References (8):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`, `docs/releases/te_v4_0/TE_V4_0_STAGE_4_0_1_TRANSLATION_RELIABILITY_BASELINE.md`, `docs/releases/te_v4_0/TE_V4_0_STAGE_4_0_3_ADAPTIVE_CHUNK_SPLIT_PLANNER.md`, `docs/releases/te_v4_0/TE_V4_0_STAGE_4_0_4_TRANSLATION_FAILURE_ANALYZER.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (8):** 8 item(s)
- **Test Suite References (9):** `tests/integration/translation_reliability_stage401_baseline_test.py`, `verification/legacy/instructions/APPLY_STAGE_401.txt`, `verification/legacy/instructions/APPLY_STAGE_401_FIX1.txt`, `verification/legacy/instructions/APPLY_STAGE_402.txt`, `verification/legacy/instructions/APPLY_STAGE_403.txt`

### `ntpe_te_v40_stage402_adaptive_retry_policy_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 1 `from` statement(s)
- **Imported By:** 1 other Python module(s)
  - *Importers:* `tests/integration/translation_reliability_stage402_adaptive_retry_policy_test.py`
- **Docs/README References (8):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`, `docs/releases/te_v4_0/TE_V4_0_STAGE_4_0_2_ADAPTIVE_RETRY_POLICY.md`, `docs/releases/te_v4_0/TE_V4_0_STAGE_4_0_3_ADAPTIVE_CHUNK_SPLIT_PLANNER.md`, `docs/releases/te_v4_0/TE_V4_0_STAGE_4_0_4_TRANSLATION_FAILURE_ANALYZER.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (9):** 9 item(s)
- **Test Suite References (7):** `tests/integration/translation_reliability_stage402_adaptive_retry_policy_test.py`, `verification/legacy/instructions/APPLY_STAGE_402.txt`, `verification/legacy/instructions/APPLY_STAGE_403.txt`, `verification/legacy/instructions/APPLY_STAGE_404.txt`, `verification/legacy/instructions/APPLY_STAGE_405.txt`

### `ntpe_te_v40_stage403_adaptive_chunk_split_planner_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 1 `from` statement(s)
- **Imported By:** 1 other Python module(s)
  - *Importers:* `tests/integration/translation_reliability_stage403_adaptive_chunk_split_planner_test.py`
- **Docs/README References (7):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`, `docs/releases/te_v4_0/TE_V4_0_STAGE_4_0_3_ADAPTIVE_CHUNK_SPLIT_PLANNER.md`, `docs/releases/te_v4_0/TE_V4_0_STAGE_4_0_4_TRANSLATION_FAILURE_ANALYZER.md`, `docs/releases/te_v4_0/TE_V4_0_STAGE_4_0_5_RETRY_STRATEGY_BENCHMARK.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (8):** 8 item(s)
- **Test Suite References (6):** `tests/integration/translation_reliability_stage403_adaptive_chunk_split_planner_test.py`, `verification/legacy/instructions/APPLY_STAGE_403.txt`, `verification/legacy/instructions/APPLY_STAGE_404.txt`, `verification/legacy/instructions/APPLY_STAGE_405.txt`, `verification/legacy/instructions/APPLY_STAGE_406.txt`

### `ntpe_te_v40_stage404_translation_failure_analyzer_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 1 `from` statement(s)
- **Imported By:** 1 other Python module(s)
  - *Importers:* `tests/integration/translation_reliability_stage404_failure_analyzer_test.py`
- **Docs/README References (6):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`, `docs/releases/te_v4_0/TE_V4_0_STAGE_4_0_4_TRANSLATION_FAILURE_ANALYZER.md`, `docs/releases/te_v4_0/TE_V4_0_STAGE_4_0_5_RETRY_STRATEGY_BENCHMARK.md`, `docs/releases/te_v4_0/TE_V4_0_STAGE_4_0_6_RELIABILITY_RUNTIME_INTEGRATION_ADAPTER.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (8):** 8 item(s)
- **Test Suite References (5):** `tests/integration/translation_reliability_stage404_failure_analyzer_test.py`, `verification/legacy/instructions/APPLY_STAGE_404.txt`, `verification/legacy/instructions/APPLY_STAGE_405.txt`, `verification/legacy/instructions/APPLY_STAGE_406.txt`, `verification/legacy/instructions/APPLY_STAGE_407.txt`

### `ntpe_te_v40_stage405_retry_strategy_benchmark_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 1 `from` statement(s)
- **Imported By:** 1 other Python module(s)
  - *Importers:* `tests/integration/translation_reliability_stage405_retry_strategy_benchmark_test.py`
- **Docs/README References (5):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`, `docs/releases/te_v4_0/TE_V4_0_STAGE_4_0_5_RETRY_STRATEGY_BENCHMARK.md`, `docs/releases/te_v4_0/TE_V4_0_STAGE_4_0_6_RELIABILITY_RUNTIME_INTEGRATION_ADAPTER.md`, `docs/releases/te_v4_0/TE_V4_0_STAGE_4_0_7_RUNTIME_SHADOW_OBSERVATION.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (9):** 9 item(s)
- **Test Suite References (4):** `tests/integration/translation_reliability_stage405_retry_strategy_benchmark_test.py`, `verification/legacy/instructions/APPLY_STAGE_405.txt`, `verification/legacy/instructions/APPLY_STAGE_406.txt`, `verification/legacy/instructions/APPLY_STAGE_407.txt`

### `ntpe_te_v40_stage406_reliability_runtime_integration_adapter_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 1 `from` statement(s)
- **Imported By:** 1 other Python module(s)
  - *Importers:* `tests/integration/translation_reliability_stage406_runtime_integration_adapter_test.py`
- **Docs/README References (4):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`, `docs/releases/te_v4_0/TE_V4_0_STAGE_4_0_6_RELIABILITY_RUNTIME_INTEGRATION_ADAPTER.md`, `docs/releases/te_v4_0/TE_V4_0_STAGE_4_0_7_RUNTIME_SHADOW_OBSERVATION.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (9):** 9 item(s)
- **Test Suite References (3):** `tests/integration/translation_reliability_stage406_runtime_integration_adapter_test.py`, `verification/legacy/instructions/APPLY_STAGE_406.txt`, `verification/legacy/instructions/APPLY_STAGE_407.txt`

### `ntpe_te_v40_stage407_runtime_shadow_observation_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 1 `from` statement(s)
- **Imported By:** 1 other Python module(s)
  - *Importers:* `tests/integration/translation_reliability_stage407_runtime_shadow_observation_test.py`
- **Docs/README References (3):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`, `docs/releases/te_v4_0/TE_V4_0_STAGE_4_0_7_RUNTIME_SHADOW_OBSERVATION.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (9):** 9 item(s)
- **Test Suite References (2):** `tests/integration/translation_reliability_stage407_runtime_shadow_observation_test.py`, `verification/legacy/instructions/APPLY_STAGE_407.txt`

### `ntpe_te_v40_stage408_translation_reliability_freeze_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 0 `from` statement(s)
- **Imported By:** 1 other Python module(s)
  - *Importers:* `tests/integration/translation_reliability_stage408_freeze_test.py`
- **Docs/README References (5):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`, `docs/releases/te_v4_2/TE_V4_2_STAGE_4_2_1_REAL_RUNTIME_RECOVERY_PILOT_CONTRACT.md`, `docs/releases/te_v4_2/TE_V4_2_STAGE_4_2_2_REAL_RUNTIME_RECOVERY_PILOT_ADMISSION_GATE.md`, `docs/releases/te_v4_2/TE_V4_2_STAGE_4_2_3_REAL_RUNTIME_RECOVERY_PILOT_ROLLBACK_CONTROLLER.md`
- **Manifest/Config References (5):** `config/project_layout_policy.json`, `manifests/te_v42_real_runtime_recovery_pilot_admission_manifest.json`, `manifests/te_v42_real_runtime_recovery_pilot_contract_manifest.json`, `manifests/te_v42_real_runtime_recovery_pilot_freeze_manifest.json`, `manifests/te_v42_real_runtime_recovery_pilot_rollback_manifest.json`
- **Artifact/Audit References (9):** 9 item(s)
- **Test Suite References (1):** `tests/integration/translation_reliability_stage408_freeze_test.py`

### `ntpe_te_v41_stage411_adaptive_retry_execution_harness_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 1 `from` statement(s)
- **Imported By:** 1 other Python module(s)
  - *Importers:* `tests/integration/translation_reliability_stage411_adaptive_retry_execution_harness_test.py`
- **Docs/README References (9):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`, `docs/releases/te_v4_1/TE_V4_1_STAGE_4_1_1_ADAPTIVE_RETRY_EXECUTION_HARNESS.md`, `docs/releases/te_v4_1/TE_V4_1_STAGE_4_1_2_RUNTIME_RECOVERY_HOOK_ADAPTER.md`, `docs/releases/te_v4_1/TE_V4_1_STAGE_4_1_3_RECOVERY_OUTCOME_GUARD.md`
- **Manifest/Config References (2):** `config/project_layout_policy.json`, `manifests/te_v41_translation_reliability_execution_freeze_manifest.json`
- **Artifact/Audit References (9):** 9 item(s)
- **Test Suite References (6):** `tests/integration/translation_reliability_stage411_adaptive_retry_execution_harness_test.py`, `verification/legacy/instructions/APPLY_STAGE_411.txt`, `verification/legacy/instructions/APPLY_STAGE_412.txt`, `verification/legacy/instructions/APPLY_STAGE_413.txt`, `verification/legacy/instructions/APPLY_STAGE_414.txt`

### `ntpe_te_v41_stage412_runtime_recovery_hook_adapter_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 1 `from` statement(s)
- **Imported By:** 1 other Python module(s)
  - *Importers:* `tests/integration/translation_reliability_stage412_runtime_recovery_hook_adapter_test.py`
- **Docs/README References (8):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`, `docs/releases/te_v4_1/TE_V4_1_STAGE_4_1_2_RUNTIME_RECOVERY_HOOK_ADAPTER.md`, `docs/releases/te_v4_1/TE_V4_1_STAGE_4_1_3_RECOVERY_OUTCOME_GUARD.md`, `docs/releases/te_v4_1/TE_V4_1_STAGE_4_1_4_RECOVERY_RESULT_BUNDLE.md`
- **Manifest/Config References (2):** `config/project_layout_policy.json`, `manifests/te_v41_translation_reliability_execution_freeze_manifest.json`
- **Artifact/Audit References (10):** 10 item(s)
- **Test Suite References (5):** `tests/integration/translation_reliability_stage412_runtime_recovery_hook_adapter_test.py`, `verification/legacy/instructions/APPLY_STAGE_412.txt`, `verification/legacy/instructions/APPLY_STAGE_413.txt`, `verification/legacy/instructions/APPLY_STAGE_414.txt`, `verification/legacy/instructions/APPLY_STAGE_415.txt`

### `ntpe_te_v41_stage413_recovery_outcome_guard_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 1 `from` statement(s)
- **Imported By:** 1 other Python module(s)
  - *Importers:* `tests/integration/translation_reliability_stage413_recovery_outcome_guard_test.py`
- **Docs/README References (7):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`, `docs/releases/te_v4_1/TE_V4_1_STAGE_4_1_3_RECOVERY_OUTCOME_GUARD.md`, `docs/releases/te_v4_1/TE_V4_1_STAGE_4_1_4_RECOVERY_RESULT_BUNDLE.md`, `docs/releases/te_v4_1/TE_V4_1_STAGE_4_1_5_RECOVERY_FLOW_INTEGRATION.md`
- **Manifest/Config References (2):** `config/project_layout_policy.json`, `manifests/te_v41_translation_reliability_execution_freeze_manifest.json`
- **Artifact/Audit References (10):** 10 item(s)
- **Test Suite References (4):** `tests/integration/translation_reliability_stage413_recovery_outcome_guard_test.py`, `verification/legacy/instructions/APPLY_STAGE_413.txt`, `verification/legacy/instructions/APPLY_STAGE_414.txt`, `verification/legacy/instructions/APPLY_STAGE_415.txt`

### `ntpe_te_v41_stage414_recovery_result_bundle_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 1 `from` statement(s)
- **Imported By:** 1 other Python module(s)
  - *Importers:* `tests/integration/translation_reliability_stage414_recovery_result_bundle_test.py`
- **Docs/README References (6):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`, `docs/releases/te_v4_1/TE_V4_1_STAGE_4_1_4_RECOVERY_RESULT_BUNDLE.md`, `docs/releases/te_v4_1/TE_V4_1_STAGE_4_1_5_RECOVERY_FLOW_INTEGRATION.md`, `docs/releases/te_v4_1/TE_V4_1_STAGE_4_1_6_RECOVERY_FLOW_BOUNDARY_REGRESSION.md`
- **Manifest/Config References (2):** `config/project_layout_policy.json`, `manifests/te_v41_translation_reliability_execution_freeze_manifest.json`
- **Artifact/Audit References (10):** 10 item(s)
- **Test Suite References (3):** `tests/integration/translation_reliability_stage414_recovery_result_bundle_test.py`, `verification/legacy/instructions/APPLY_STAGE_414.txt`, `verification/legacy/instructions/APPLY_STAGE_415.txt`

### `ntpe_te_v41_stage415_recovery_flow_integration_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 1 `from` statement(s)
- **Imported By:** 1 other Python module(s)
  - *Importers:* `tests/integration/translation_reliability_stage415_recovery_flow_integration_test.py`
- **Docs/README References (5):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`, `docs/releases/te_v4_1/TE_V4_1_STAGE_4_1_5_RECOVERY_FLOW_INTEGRATION.md`, `docs/releases/te_v4_1/TE_V4_1_STAGE_4_1_6_RECOVERY_FLOW_BOUNDARY_REGRESSION.md`, `docs/releases/te_v4_1/TE_V4_1_TRANSLATION_RELIABILITY_EXECUTION_FREEZE.md`
- **Manifest/Config References (2):** `config/project_layout_policy.json`, `manifests/te_v41_translation_reliability_execution_freeze_manifest.json`
- **Artifact/Audit References (10):** 10 item(s)
- **Test Suite References (2):** `tests/integration/translation_reliability_stage415_recovery_flow_integration_test.py`, `verification/legacy/instructions/APPLY_STAGE_415.txt`

### `ntpe_te_v41_stage416_recovery_flow_boundary_regression_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 1 `from` statement(s)
- **Imported By:** 1 other Python module(s)
  - *Importers:* `tests/integration/translation_reliability_stage416_recovery_flow_boundary_regression_test.py`
- **Docs/README References (4):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`, `docs/releases/te_v4_1/TE_V4_1_STAGE_4_1_6_RECOVERY_FLOW_BOUNDARY_REGRESSION.md`, `docs/releases/te_v4_1/TE_V4_1_TRANSLATION_RELIABILITY_EXECUTION_FREEZE.md`
- **Manifest/Config References (2):** `config/project_layout_policy.json`, `manifests/te_v41_translation_reliability_execution_freeze_manifest.json`
- **Artifact/Audit References (10):** 10 item(s)
- **Test Suite References (2):** `tests/integration/translation_reliability_stage416_recovery_flow_boundary_regression_test.py`, `verification/legacy/instructions/APPLY_STAGE_416.txt`

### `ntpe_te_v41_stage417_translation_reliability_execution_freeze_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 1 module import(s), 2 `from` statement(s)
- **Imported By:** 1 other Python module(s)
  - *Importers:* `tests/integration/translation_reliability_stage417_execution_freeze_test.py`
- **Docs/README References (6):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`, `docs/releases/te_v4_1/TE_V4_1_TRANSLATION_RELIABILITY_EXECUTION_FREEZE.md`, `docs/releases/te_v4_2/TE_V4_2_STAGE_4_2_1_REAL_RUNTIME_RECOVERY_PILOT_CONTRACT.md`, `docs/releases/te_v4_2/TE_V4_2_STAGE_4_2_2_REAL_RUNTIME_RECOVERY_PILOT_ADMISSION_GATE.md`
- **Manifest/Config References (6):** `config/project_layout_policy.json`, `manifests/te_v41_translation_reliability_execution_freeze_manifest.json`, `manifests/te_v42_real_runtime_recovery_pilot_admission_manifest.json`, `manifests/te_v42_real_runtime_recovery_pilot_contract_manifest.json`, `manifests/te_v42_real_runtime_recovery_pilot_freeze_manifest.json`
- **Artifact/Audit References (10):** 10 item(s)
- **Test Suite References (2):** `tests/integration/translation_reliability_stage417_execution_freeze_test.py`, `verification/legacy/instructions/APPLY_STAGE_417.txt`

### `ntpe_te_v42_stage421_real_runtime_recovery_pilot_contract_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 1 module import(s), 2 `from` statement(s)
- **Imported By:** 1 other Python module(s)
  - *Importers:* `tests/integration/translation_reliability_stage421_real_runtime_recovery_pilot_contract_test.py`
- **Docs/README References (5):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`, `docs/releases/te_v4_2/TE_V4_2_STAGE_4_2_1_REAL_RUNTIME_RECOVERY_PILOT_CONTRACT.md`, `docs/releases/te_v4_2/TE_V4_2_STAGE_4_2_2_REAL_RUNTIME_RECOVERY_PILOT_ADMISSION_GATE.md`, `docs/releases/te_v4_2/TE_V4_2_STAGE_4_2_3_REAL_RUNTIME_RECOVERY_PILOT_ROLLBACK_CONTROLLER.md`
- **Manifest/Config References (5):** `config/project_layout_policy.json`, `manifests/te_v42_real_runtime_recovery_pilot_admission_manifest.json`, `manifests/te_v42_real_runtime_recovery_pilot_contract_manifest.json`, `manifests/te_v42_real_runtime_recovery_pilot_freeze_manifest.json`, `manifests/te_v42_real_runtime_recovery_pilot_rollback_manifest.json`
- **Artifact/Audit References (10):** 10 item(s)
- **Test Suite References (1):** `tests/integration/translation_reliability_stage421_real_runtime_recovery_pilot_contract_test.py`

### `ntpe_te_v42_stage422_real_runtime_recovery_pilot_admission_gate_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 1 module import(s), 2 `from` statement(s)
- **Imported By:** 1 other Python module(s)
  - *Importers:* `tests/integration/translation_reliability_stage422_real_runtime_recovery_pilot_admission_gate_test.py`
- **Docs/README References (4):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`, `docs/releases/te_v4_2/TE_V4_2_STAGE_4_2_2_REAL_RUNTIME_RECOVERY_PILOT_ADMISSION_GATE.md`, `docs/releases/te_v4_2/TE_V4_2_STAGE_4_2_3_REAL_RUNTIME_RECOVERY_PILOT_ROLLBACK_CONTROLLER.md`
- **Manifest/Config References (4):** `config/project_layout_policy.json`, `manifests/te_v42_real_runtime_recovery_pilot_admission_manifest.json`, `manifests/te_v42_real_runtime_recovery_pilot_freeze_manifest.json`, `manifests/te_v42_real_runtime_recovery_pilot_rollback_manifest.json`
- **Artifact/Audit References (10):** 10 item(s)
- **Test Suite References (1):** `tests/integration/translation_reliability_stage422_real_runtime_recovery_pilot_admission_gate_test.py`

### `ntpe_te_v42_stage423_real_runtime_recovery_pilot_rollback_controller_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 1 module import(s), 2 `from` statement(s)
- **Imported By:** 1 other Python module(s)
  - *Importers:* `tests/integration/translation_reliability_stage423_real_runtime_recovery_pilot_rollback_controller_test.py`
- **Docs/README References (3):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`, `docs/releases/te_v4_2/TE_V4_2_STAGE_4_2_3_REAL_RUNTIME_RECOVERY_PILOT_ROLLBACK_CONTROLLER.md`
- **Manifest/Config References (3):** `config/project_layout_policy.json`, `manifests/te_v42_real_runtime_recovery_pilot_freeze_manifest.json`, `manifests/te_v42_real_runtime_recovery_pilot_rollback_manifest.json`
- **Artifact/Audit References (10):** 10 item(s)
- **Test Suite References (1):** `tests/integration/translation_reliability_stage423_real_runtime_recovery_pilot_rollback_controller_test.py`

### `ntpe_te_v42_stage424_real_runtime_recovery_pilot_dry_run_runner_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 1 module import(s), 2 `from` statement(s)
- **Imported By:** 1 other Python module(s)
  - *Importers:* `tests/integration/translation_reliability_stage424_real_runtime_recovery_pilot_dry_run_runner_test.py`
- **Docs/README References (3):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`, `docs/releases/te_v4_2/TE_V4_2_STAGE_4_2_4_REAL_RUNTIME_RECOVERY_PILOT_DRY_RUN_RUNNER.md`
- **Manifest/Config References (2):** `config/project_layout_policy.json`, `manifests/te_v42_real_runtime_recovery_pilot_freeze_manifest.json`
- **Artifact/Audit References (10):** 10 item(s)
- **Test Suite References (1):** `tests/integration/translation_reliability_stage424_real_runtime_recovery_pilot_dry_run_runner_test.py`

### `ntpe_te_v42_stage425_real_runtime_recovery_pilot_dry_run_bundle_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 1 module import(s), 2 `from` statement(s)
- **Imported By:** 1 other Python module(s)
  - *Importers:* `tests/integration/translation_reliability_stage425_real_runtime_recovery_pilot_dry_run_bundle_test.py`
- **Docs/README References (3):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`, `docs/releases/te_v4_2/TE_V4_2_STAGE_4_2_5_REAL_RUNTIME_RECOVERY_PILOT_DRY_RUN_BUNDLE.md`
- **Manifest/Config References (2):** `config/project_layout_policy.json`, `manifests/te_v42_real_runtime_recovery_pilot_freeze_manifest.json`
- **Artifact/Audit References (10):** 10 item(s)
- **Test Suite References (1):** `tests/integration/translation_reliability_stage425_real_runtime_recovery_pilot_dry_run_bundle_test.py`

### `ntpe_te_v42_stage426_real_runtime_recovery_pilot_boundary_regression_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 1 `from` statement(s)
- **Imported By:** 1 other Python module(s)
  - *Importers:* `tests/integration/translation_reliability_stage426_real_runtime_recovery_pilot_boundary_regression_test.py`
- **Docs/README References (3):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`, `docs/releases/te_v4_2/TE_V4_2_STAGE_4_2_6_REAL_RUNTIME_RECOVERY_PILOT_BOUNDARY_REGRESSION.md`
- **Manifest/Config References (2):** `config/project_layout_policy.json`, `manifests/te_v42_real_runtime_recovery_pilot_freeze_manifest.json`
- **Artifact/Audit References (10):** 10 item(s)
- **Test Suite References (1):** `tests/integration/translation_reliability_stage426_real_runtime_recovery_pilot_boundary_regression_test.py`

### `ntpe_te_v42_stage427_real_runtime_recovery_pilot_freeze_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 1 module import(s), 2 `from` statement(s)
- **Imported By:** 1 other Python module(s)
  - *Importers:* `tests/integration/translation_reliability_stage427_real_runtime_recovery_pilot_freeze_test.py`
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (2):** `config/project_layout_policy.json`, `manifests/te_v42_real_runtime_recovery_pilot_freeze_manifest.json`
- **Artifact/Audit References (11):** 11 item(s)
- **Test Suite References (1):** `tests/integration/translation_reliability_stage427_real_runtime_recovery_pilot_freeze_test.py`

### `ntpe_te_v43_stage431_runtime_recovery_hook_contract_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 1 `from` statement(s)
- **Imported By:** 1 other Python module(s)
  - *Importers:* `tests/integration/translation_reliability_stage431_runtime_recovery_hook_contract_test.py`
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (10):** 10 item(s)
- **Test Suite References (1):** `tests/integration/translation_reliability_stage431_runtime_recovery_hook_contract_test.py`

### `ntpe_te_v43_stage432_runtime_hook_admission_adapter_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 1 `from` statement(s)
- **Imported By:** 1 other Python module(s)
  - *Importers:* `tests/integration/translation_reliability_stage432_runtime_hook_admission_adapter_test.py`
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (9):** 9 item(s)
- **Test Suite References (1):** `tests/integration/translation_reliability_stage432_runtime_hook_admission_adapter_test.py`

### `ntpe_te_v43_stage433_runtime_single_chunk_shadow_hook_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 1 `from` statement(s)
- **Imported By:** 1 other Python module(s)
  - *Importers:* `tests/integration/translation_reliability_stage433_runtime_single_chunk_shadow_hook_test.py`
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (9):** 9 item(s)
- **Test Suite References (1):** `tests/integration/translation_reliability_stage433_runtime_single_chunk_shadow_hook_test.py`

### `ntpe_te_v43_stage434_runtime_hook_result_mapper_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 1 `from` statement(s)
- **Imported By:** 1 other Python module(s)
  - *Importers:* `tests/integration/translation_reliability_stage434_runtime_hook_result_mapper_test.py`
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (9):** 9 item(s)
- **Test Suite References (1):** `tests/integration/translation_reliability_stage434_runtime_hook_result_mapper_test.py`

### `ntpe_te_v43_stage435_runtime_recovery_hook_boundary_regression_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 1 `from` statement(s)
- **Imported By:** 1 other Python module(s)
  - *Importers:* `tests/integration/translation_reliability_stage435_runtime_recovery_hook_boundary_regression_test.py`
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (10):** 10 item(s)
- **Test Suite References (1):** `tests/integration/translation_reliability_stage435_runtime_recovery_hook_boundary_regression_test.py`

### `ntpe_te_v43_stage436_translation_runtime_recovery_hook_freeze_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 1 module import(s), 2 `from` statement(s)
- **Imported By:** 1 other Python module(s)
  - *Importers:* `tests/integration/translation_reliability_stage436_runtime_recovery_hook_freeze_test.py`
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (11):** 11 item(s)
- **Test Suite References (1):** `tests/integration/translation_reliability_stage436_runtime_recovery_hook_freeze_test.py`

### `ntpe_te_v44_stage441_controlled_execution_contract_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 1 `from` statement(s)
- **Imported By:** 1 other Python module(s)
  - *Importers:* `tests/integration/translation_reliability_stage441_controlled_execution_contract_test.py`
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (8):** 8 item(s)
- **Test Suite References (1):** `tests/integration/translation_reliability_stage441_controlled_execution_contract_test.py`

### `ntpe_te_v44_stage442_controlled_execution_admission_gate_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 1 `from` statement(s)
- **Imported By:** 5 other Python module(s)
  - *Importers:* `ntpe_te_v44_stage443_single_chunk_controlled_recovery_executor_test.py`, `ntpe_te_v44_stage444_controlled_result_replacement_guard_test.py`, `ntpe_te_v44_stage445_controlled_execution_boundary_regression_test.py`, `ntpe_te_v44_stage446_controlled_execution_pilot_freeze_test.py`, `tests/integration/translation_reliability_stage442_controlled_execution_admission_gate_test.py`
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (9):** 9 item(s)
- **Test Suite References (1):** `tests/integration/translation_reliability_stage442_controlled_execution_admission_gate_test.py`

### `ntpe_te_v44_stage443_single_chunk_controlled_recovery_executor_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 2 `from` statement(s)
- **Imported By:** 4 other Python module(s)
  - *Importers:* `ntpe_te_v44_stage444_controlled_result_replacement_guard_test.py`, `ntpe_te_v44_stage445_controlled_execution_boundary_regression_test.py`, `ntpe_te_v44_stage446_controlled_execution_pilot_freeze_test.py`, `tests/integration/translation_reliability_stage443_single_chunk_controlled_recovery_executor_test.py`
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (10):** 10 item(s)
- **Test Suite References (1):** `tests/integration/translation_reliability_stage443_single_chunk_controlled_recovery_executor_test.py`

### `ntpe_te_v44_stage444_controlled_result_replacement_guard_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 3 `from` statement(s)
- **Imported By:** 1 other Python module(s)
  - *Importers:* `tests/integration/translation_reliability_stage444_controlled_result_replacement_guard_test.py`
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (8):** 8 item(s)
- **Test Suite References (1):** `tests/integration/translation_reliability_stage444_controlled_result_replacement_guard_test.py`

### `ntpe_te_v44_stage445_controlled_execution_boundary_regression_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 3 `from` statement(s)
- **Imported By:** 1 other Python module(s)
  - *Importers:* `tests/integration/translation_reliability_stage445_controlled_execution_boundary_regression_test.py`
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (8):** 8 item(s)
- **Test Suite References (1):** `tests/integration/translation_reliability_stage445_controlled_execution_boundary_regression_test.py`

### `ntpe_te_v44_stage446_controlled_execution_pilot_freeze_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 1 module import(s), 4 `from` statement(s)
- **Imported By:** 1 other Python module(s)
  - *Importers:* `tests/integration/translation_reliability_stage446_controlled_execution_pilot_freeze_test.py`
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (10):** 10 item(s)
- **Test Suite References (1):** `tests/integration/translation_reliability_stage446_controlled_execution_pilot_freeze_test.py`

### `ntpe_te_v50_quality_core_milestone_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 1 `from` statement(s)
- **Imported By:** 1 other Python module(s)
  - *Importers:* `tests/integration/translation_quality_v50_quality_core_milestone_test.py`
- **Docs/README References (4):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`, `docs/releases/te_v5_0/TE_V5_0_QUALITY_CORE_MILESTONE.md`, `docs/releases/te_v5_1/TE_V5_1_QUALITY_REPAIR_PIPELINE_MILESTONE.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (8):** 8 item(s)
- **Test Suite References (3):** `tests/integration/translation_quality_v50_quality_core_milestone_test.py`, `verification/legacy/instructions/APPLY_TE_V50_QUALITY_CORE.txt`, `verification/legacy/instructions/APPLY_TE_V51_QUALITY_REPAIR_PIPELINE.txt`

### `ntpe_te_v50_stage506_quality_core_freeze_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 1 module import(s), 2 `from` statement(s)
- **Imported By:** 1 other Python module(s)
  - *Importers:* `tests/integration/translation_quality_v50_stage506_freeze_test.py`
- **Docs/README References (4):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`, `docs/releases/te_v5_0/TE_V5_0_QUALITY_CORE_MILESTONE.md`, `docs/releases/te_v5_1/TE_V5_1_QUALITY_REPAIR_PIPELINE_MILESTONE.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (10):** 10 item(s)
- **Test Suite References (3):** `tests/integration/translation_quality_v50_stage506_freeze_test.py`, `verification/legacy/instructions/APPLY_TE_V50_QUALITY_CORE.txt`, `verification/legacy/instructions/APPLY_TE_V51_QUALITY_REPAIR_PIPELINE.txt`

### `ntpe_te_v51_quality_repair_pipeline_milestone_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 1 `from` statement(s)
- **Imported By:** 1 other Python module(s)
  - *Importers:* `tests/integration/translation_quality_v51_quality_repair_pipeline_test.py`
- **Docs/README References (3):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`, `docs/releases/te_v5_1/TE_V5_1_QUALITY_REPAIR_PIPELINE_MILESTONE.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (8):** 8 item(s)
- **Test Suite References (2):** `tests/integration/translation_quality_v51_quality_repair_pipeline_test.py`, `verification/legacy/instructions/APPLY_TE_V51_QUALITY_REPAIR_PIPELINE.txt`

### `ntpe_te_v51_stage515_quality_repair_boundary_regression_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 1 `from` statement(s)
- **Imported By:** 1 other Python module(s)
  - *Importers:* `tests/integration/translation_quality_v51_stage515_boundary_regression_test.py`
- **Docs/README References (3):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`, `docs/releases/te_v5_1/TE_V5_1_QUALITY_REPAIR_PIPELINE_MILESTONE.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (8):** 8 item(s)
- **Test Suite References (2):** `tests/integration/translation_quality_v51_stage515_boundary_regression_test.py`, `verification/legacy/instructions/APPLY_TE_V51_QUALITY_REPAIR_PIPELINE.txt`

### `ntpe_te_v51_stage516_quality_repair_pipeline_freeze_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 1 module import(s), 2 `from` statement(s)
- **Imported By:** 1 other Python module(s)
  - *Importers:* `tests/integration/translation_quality_v51_stage516_freeze_test.py`
- **Docs/README References (3):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`, `docs/releases/te_v5_1/TE_V5_1_QUALITY_REPAIR_PIPELINE_MILESTONE.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (10):** 10 item(s)
- **Test Suite References (2):** `tests/integration/translation_quality_v51_stage516_freeze_test.py`, `verification/legacy/instructions/APPLY_TE_V51_QUALITY_REPAIR_PIPELINE.txt`

### `ntpe_te_v521_timeout_propagation_fix_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 1 module import(s), 5 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (3):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`, `docs/releases/TE_v5_2_1_REGRESSION_TIMEOUT_PROPAGATION_FIX.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (13):** 13 item(s)
- **Test Suite References (2):** `tests/consolidated/test_exact_duplicate_contracts.py`, `verification/legacy/instructions/APPLY_TE_V5_2_1.txt`

### `ntpe_te_v522_provider_timeout_resilience_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 1 module import(s), 6 `from` statement(s)
- **Imported By:** 1 other Python module(s)
  - *Importers:* `tests/integration/translation_provider_timeout_resilience_test.py`
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (8):** 8 item(s)
- **Test Suite References (4):** `tests/integration/translation_provider_timeout_resilience_test.py`, `verification/legacy/instructions/APPLY_TE_V5_2_2.txt`, `verification/legacy/instructions/APPLY_TE_V5_2_3.txt`, `verification/legacy/instructions/APPLY_TE_V5_3_0.txt`

### `ntpe_te_v523_provider_backpressure_resume_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 1 module import(s), 5 `from` statement(s)
- **Imported By:** 1 other Python module(s)
  - *Importers:* `tests/integration/translation_provider_backpressure_resume_test.py`
- **Docs/README References (3):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`, `docs/releases/te_v5_3/TE_V5_3_1_UNIFIED_QUALITY_GATE.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (9):** 9 item(s)
- **Test Suite References (3):** `tests/integration/translation_provider_backpressure_resume_test.py`, `verification/legacy/instructions/APPLY_TE_V5_2_3.txt`, `verification/legacy/instructions/APPLY_TE_V5_3_0.txt`

### `ntpe_te_v52_quality_runtime_gate_pilot_milestone_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 1 `from` statement(s)
- **Imported By:** 1 other Python module(s)
  - *Importers:* `tests/integration/translation_quality_v52_quality_runtime_gate_pilot_test.py`
- **Docs/README References (3):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`, `docs/releases/te_v5_2/TE_V5_2_QUALITY_RUNTIME_GATE_PILOT_MILESTONE.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (9):** 9 item(s)
- **Test Suite References (2):** `tests/integration/translation_quality_v52_quality_runtime_gate_pilot_test.py`, `verification/legacy/instructions/APPLY_TE_V52_QUALITY_RUNTIME_GATE_PILOT.txt`

### `ntpe_te_v52_stage525_quality_runtime_gate_boundary_regression_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 1 `from` statement(s)
- **Imported By:** 1 other Python module(s)
  - *Importers:* `tests/integration/translation_quality_v52_stage525_boundary_regression_test.py`
- **Docs/README References (3):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`, `docs/releases/te_v5_2/TE_V5_2_QUALITY_RUNTIME_GATE_PILOT_MILESTONE.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (9):** 9 item(s)
- **Test Suite References (2):** `tests/integration/translation_quality_v52_stage525_boundary_regression_test.py`, `verification/legacy/instructions/APPLY_TE_V52_QUALITY_RUNTIME_GATE_PILOT.txt`

### `ntpe_te_v52_stage526_quality_runtime_gate_pilot_freeze_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 1 module import(s), 2 `from` statement(s)
- **Imported By:** 1 other Python module(s)
  - *Importers:* `tests/integration/translation_quality_v52_stage526_freeze_test.py`
- **Docs/README References (3):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`, `docs/releases/te_v5_2/TE_V5_2_QUALITY_RUNTIME_GATE_PILOT_MILESTONE.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (10):** 10 item(s)
- **Test Suite References (2):** `tests/integration/translation_quality_v52_stage526_freeze_test.py`, `verification/legacy/instructions/APPLY_TE_V52_QUALITY_RUNTIME_GATE_PILOT.txt`

### `ntpe_te_v530_quality_runtime_integration_phase1_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 2 module import(s), 4 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (3):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`, `docs/releases/te_v5_3/TE_V5_3_1_UNIFIED_QUALITY_GATE.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (13):** 13 item(s)
- **Test Suite References (4):** `tests/consolidated/test_exact_duplicate_contracts.py`, `verification/legacy/instructions/APPLY_TE_V5_3_0.txt`, `verification/legacy/instructions/APPLY_TE_V5_3_1_1.txt`, `verification/legacy/instructions/APPLY_TE_V5_3_2.txt`

### `ntpe_te_v5311_paragraph_coverage_corroboration_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 2 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (12):** 12 item(s)
- **Test Suite References (3):** `tests/consolidated/test_exact_duplicate_contracts.py`, `verification/legacy/instructions/APPLY_TE_V5_3_1_1.txt`, `verification/legacy/instructions/APPLY_TE_V5_3_1_2.txt`

### `ntpe_te_v5312_unified_nonblocking_issue_mapping_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 1 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (16):** 16 item(s)
- **Test Suite References (3):** `tests/consolidated/test_exact_duplicate_contracts.py`, `tests/integration/architecture_consolidation_batch2_test_consolidation_test.py`, `verification/legacy/instructions/APPLY_TE_V5_3_1_2.txt`

### `ntpe_te_v531_unified_quality_gate_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 1 module import(s), 2 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (3):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`, `docs/releases/te_v5_3/TE_V5_3_1_UNIFIED_QUALITY_GATE.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (6):** 6 item(s)
- **Test Suite References (8):** `verification/legacy/instructions/APPLY_TE_V5_3_1_1.txt`, `verification/legacy/instructions/APPLY_TE_V5_3_1_2.txt`, `verification/legacy/instructions/APPLY_TE_V5_3_2.txt`, `verification/legacy/instructions/APPLY_TE_V5_4_0.txt`, `verification/legacy/instructions/APPLY_TE_V5_5_1.txt`

### `ntpe_te_v532_semantic_repetition_guard_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 2 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (12):** 12 item(s)
- **Test Suite References (3):** `tests/consolidated/test_exact_duplicate_contracts.py`, `verification/legacy/instructions/APPLY_TE_V5_3_2.txt`, `verification/legacy/instructions/APPLY_TE_V5_4_0.txt`

### `ntpe_te_v540_smart_local_repair_pipeline_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 1 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (1):** `docs/governance/migration/rm_2_3b_scope.txt`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (13):** 13 item(s)
- **Test Suite References (6):** `tests/consolidated/test_exact_duplicate_contracts.py`, `verification/legacy/instructions/APPLY_TE_V5_4_0.txt`, `verification/legacy/instructions/APPLY_TE_V5_5_1.txt`, `verification/legacy/instructions/APPLY_TE_V6_0_STAGE03.txt`, `verification/legacy/instructions/APPLY_TE_V6_0_STAGE04.txt`

### `ntpe_te_v551_prompt_compiler_foundation_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 2 module import(s), 4 `from` statement(s)
- **Imported By:** 1 other Python module(s)
  - *Importers:* `tests/integration/translation_prompt_compiler_foundation_v551_test.py`
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (5):** 5 item(s)
- **Test Suite References (3):** `tests/integration/translation_prompt_compiler_foundation_v551_test.py`, `verification/legacy/instructions/APPLY_TE_V5_5_1.txt`, `verification/legacy/instructions/APPLY_TE_V5_5_2.txt`

### `ntpe_te_v5521_runtime_prompt_compiler_wiring_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 1 module import(s), 3 `from` statement(s)
- **Imported By:** 1 other Python module(s)
  - *Importers:* `tests/integration/translation_runtime_prompt_compiler_wiring_v5521_test.py`
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (6):** 6 item(s)
- **Test Suite References (4):** `tests/integration/translation_runtime_prompt_compiler_wiring_v5521_test.py`, `verification/legacy/instructions/APPLY_TE_V5_5_2_1.txt`, `verification/legacy/instructions/APPLY_TE_V5_5_3.txt`, `verification/legacy/instructions/APPLY_TE_V6_0_STAGE02.txt`

### `ntpe_te_v552_prompt_discipline_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 1 module import(s), 3 `from` statement(s)
- **Imported By:** 1 other Python module(s)
  - *Importers:* `tests/integration/translation_prompt_discipline_v552_test.py`
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (5):** 5 item(s)
- **Test Suite References (3):** `tests/integration/translation_prompt_discipline_v552_test.py`, `verification/legacy/instructions/APPLY_TE_V5_5_2.txt`, `verification/legacy/instructions/APPLY_TE_V5_5_2_1.txt`

### `ntpe_te_v5531_completeness_recovery_best_attempt_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 3 `from` statement(s)
- **Imported By:** 1 other Python module(s)
  - *Importers:* `tests/integration/translation_completeness_recovery_best_attempt_v5531_test.py`
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (9):** 9 item(s)
- **Test Suite References (4):** `tests/integration/translation_completeness_recovery_best_attempt_v5531_test.py`, `verification/legacy/instructions/APPLY_TE_V5_5_3_1.txt`, `verification/legacy/instructions/APPLY_TE_V5_5_3_2.txt`, `verification/legacy/instructions/APPLY_TE_V5_5_3_3.txt`

### `ntpe_te_v5532_adaptive_retry_failure_fallback_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 3 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (13):** 13 item(s)
- **Test Suite References (3):** `tests/consolidated/test_exact_duplicate_contracts.py`, `verification/legacy/instructions/APPLY_TE_V5_5_3_2.txt`, `verification/legacy/instructions/APPLY_TE_V5_5_3_3.txt`

### `ntpe_te_v5533_segment_level_completeness_recovery_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 1 module import(s), 4 `from` statement(s)
- **Imported By:** 1 other Python module(s)
  - *Importers:* `tests/integration/translation_segment_level_completeness_recovery_v5533_test.py`
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (9):** 9 item(s)
- **Test Suite References (3):** `tests/integration/translation_segment_level_completeness_recovery_v5533_test.py`, `verification/legacy/instructions/APPLY_TE_V5_5_3_3.txt`, `verification/legacy/instructions/APPLY_TE_V6_0_STAGE02.txt`

### `ntpe_te_v553_adaptive_prompt_feedback_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 1 module import(s), 3 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (5):** 5 item(s)
- **Test Suite References (3):** `verification/legacy/instructions/APPLY_TE_V5_5_3.txt`, `verification/legacy/instructions/APPLY_TE_V5_5_3_1.txt`, `verification/legacy/instructions/APPLY_TE_V5_5_3_2.txt`

### `ntpe_te_v600_final_release_freeze_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 4 `from` statement(s)
- **Imported By:** 1 other Python module(s)
  - *Importers:* `tests/integration/translation_engine_v600_final_release_freeze_test.py`
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (4):** `config/project_layout_policy.json`, `manifests/te_v600_final_release_manifest.json`, `manifests/te_v700_stage011_adaptive_context_safety_stabilization_manifest.json`, `manifests/te_v700_stage01_adaptive_context_engine_manifest.json`
- **Artifact/Audit References (34):** 34 item(s)
- **Test Suite References (2):** `tests/integration/architecture_consolidation_batch2_test_consolidation_test.py`, `tests/integration/translation_engine_v600_final_release_freeze_test.py`

### `ntpe_te_v600_stage01_discipline_architecture_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 1 module import(s), 5 `from` statement(s)
- **Imported By:** 1 other Python module(s)
  - *Importers:* `tests/integration/translation_discipline_architecture_v600_stage01_test.py`
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (2):** `config/project_layout_policy.json`, `manifests/te_v600_stage01_discipline_architecture_manifest.json`
- **Artifact/Audit References (8):** 8 item(s)
- **Test Suite References (2):** `tests/integration/translation_discipline_architecture_v600_stage01_test.py`, `verification/legacy/instructions/APPLY_TE_V6_0_STAGE02.txt`

### `ntpe_te_v600_stage02_discipline_policy_activation_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 1 module import(s), 6 `from` statement(s)
- **Imported By:** 1 other Python module(s)
  - *Importers:* `tests/integration/translation_discipline_policy_activation_v600_stage02_test.py`
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (7):** 7 item(s)
- **Test Suite References (3):** `tests/integration/translation_discipline_policy_activation_v600_stage02_test.py`, `verification/legacy/instructions/APPLY_TE_V6_0_STAGE02.txt`, `verification/legacy/instructions/APPLY_TE_V6_0_STAGE03.txt`

### `ntpe_te_v600_stage03_discipline_quality_enforcement_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 3 `from` statement(s)
- **Imported By:** 1 other Python module(s)
  - *Importers:* `tests/integration/translation_discipline_quality_enforcement_v600_stage03_test.py`
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (2):** `config/project_layout_policy.json`, `manifests/te_v600_stage03_discipline_quality_enforcement_manifest.json`
- **Artifact/Audit References (8):** 8 item(s)
- **Test Suite References (4):** `tests/integration/translation_discipline_quality_enforcement_v600_stage03_test.py`, `verification/legacy/instructions/APPLY_TE_V6_0_STAGE03.txt`, `verification/legacy/instructions/APPLY_TE_V6_0_STAGE04.txt`, `verification/legacy/instructions/APPLY_TE_V6_0_STAGE05.txt`

### `ntpe_te_v600_stage04_adaptive_local_repair_framework_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 3 `from` statement(s)
- **Imported By:** 1 other Python module(s)
  - *Importers:* `tests/integration/translation_discipline_adaptive_local_repair_v600_stage04_test.py`
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (2):** `config/project_layout_policy.json`, `manifests/te_v600_stage04_adaptive_local_repair_framework_manifest.json`
- **Artifact/Audit References (8):** 8 item(s)
- **Test Suite References (4):** `tests/integration/translation_discipline_adaptive_local_repair_v600_stage04_test.py`, `verification/legacy/instructions/APPLY_TE_V6_0_STAGE04.txt`, `verification/legacy/instructions/APPLY_TE_V6_0_STAGE05.txt`, `verification/legacy/instructions/APPLY_TE_V6_0_STAGE06.txt`

### `ntpe_te_v600_stage05_adaptive_retry_decision_engine_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 2 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (8):** 8 item(s)
- **Test Suite References (2):** `verification/legacy/instructions/APPLY_TE_V6_0_STAGE05.txt`, `verification/legacy/instructions/APPLY_TE_V6_0_STAGE06.txt`

### `ntpe_te_v600_stage06_discipline_runtime_orchestrator_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 2 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (2):** `config/project_layout_policy.json`, `manifests/te_v600_stage06_discipline_runtime_orchestrator_manifest.json`
- **Artifact/Audit References (8):** 8 item(s)
- **Test Suite References (1):** `verification/legacy/instructions/APPLY_TE_V6_0_STAGE06.txt`

### `ntpe_te_v600_stage07_discipline_observability_audit_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 2 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (7):** 7 item(s)

### `ntpe_te_v600_stage081_import_api_compatibility_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 3 `from` statement(s)
- **Imported By:** 1 other Python module(s)
  - *Importers:* `tests/integration/translation_discipline_import_api_compatibility_v600_stage081_test.py`
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (3):** `config/project_layout_policy.json`, `manifests/te_v600_stage081_import_api_compatibility_fix_manifest.json`, `manifests/te_v600_stage125_translation_naturalness_freeze_manifest.json`
- **Artifact/Audit References (9):** 9 item(s)
- **Test Suite References (2):** `tests/integration/translation_discipline_import_api_compatibility_v600_stage081_test.py`, `verification/legacy/instructions/APPLY_TE_V6_0_STAGE08_1.txt`

### `ntpe_te_v600_stage08_translation_discipline_freeze_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 1 module import(s), 3 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (3):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`, `docs/releases/te_v6_0/TE_V6_0_STAGE08_TRANSLATION_DISCIPLINE_FREEZE.md`
- **Manifest/Config References (2):** `config/project_layout_policy.json`, `manifests/te_v600_stage08_translation_discipline_freeze_manifest.json`
- **Artifact/Audit References (9):** 9 item(s)
- **Test Suite References (2):** `verification/legacy/instructions/APPLY_TE_V6_0_STAGE08.txt`, `verification/legacy/instructions/APPLY_TE_V6_0_STAGE08_1.txt`

### `ntpe_te_v600_stage09_discipline_runtime_integration_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 4 `from` statement(s)
- **Imported By:** 1 other Python module(s)
  - *Importers:* `tests/integration/translation_discipline_runtime_integration_v600_stage09_test.py`
- **Docs/README References (3):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`, `docs/releases/te_v6_0/TE_V6_0_STAGE09_DISCIPLINE_RUNTIME_INTEGRATION.md`
- **Manifest/Config References (2):** `config/project_layout_policy.json`, `manifests/te_v600_stage09_discipline_runtime_integration_manifest.json`
- **Artifact/Audit References (9):** 9 item(s)
- **Test Suite References (1):** `tests/integration/translation_discipline_runtime_integration_v600_stage09_test.py`

### `ntpe_te_v600_stage1011_adaptive_retry_plan_runtime_wiring_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 3 `from` statement(s)
- **Imported By:** 1 other Python module(s)
  - *Importers:* `tests/integration/translation_discipline_adaptive_retry_plan_runtime_wiring_v600_stage1011_test.py`
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (2):** `config/project_layout_policy.json`, `manifests/te_v600_stage1011_adaptive_retry_plan_runtime_wiring_fix_manifest.json`
- **Artifact/Audit References (6):** 6 item(s)
- **Test Suite References (1):** `tests/integration/translation_discipline_adaptive_retry_plan_runtime_wiring_v600_stage1011_test.py`

### `ntpe_te_v600_stage101_production_validation_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 2 module import(s), 5 `from` statement(s)
- **Imported By:** 1 other Python module(s)
  - *Importers:* `tests/integration/translation_discipline_production_validation_v600_stage101_test.py`
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (7):** 7 item(s)
- **Test Suite References (1):** `tests/integration/translation_discipline_production_validation_v600_stage101_test.py`

### `ntpe_te_v600_stage102_production_retry_metrics_comparison_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 2 module import(s), 3 `from` statement(s)
- **Imported By:** 1 other Python module(s)
  - *Importers:* `tests/integration/translation_discipline_production_retry_metrics_v600_stage102_test.py`
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (2):** `config/project_layout_policy.json`, `manifests/te_v600_stage102_production_retry_metrics_comparison_manifest.json`
- **Artifact/Audit References (8):** 8 item(s)
- **Test Suite References (1):** `tests/integration/translation_discipline_production_retry_metrics_v600_stage102_test.py`

### `ntpe_te_v600_stage103_freeze_readiness_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 1 module import(s), 4 `from` statement(s)
- **Imported By:** 1 other Python module(s)
  - *Importers:* `tests/integration/translation_discipline_freeze_readiness_v600_stage103_test.py`
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (2):** `config/project_layout_policy.json`, `manifests/te_v600_stage103_freeze_readiness_manifest.json`
- **Artifact/Audit References (10):** 10 item(s)
- **Test Suite References (1):** `tests/integration/translation_discipline_freeze_readiness_v600_stage103_test.py`

### `ntpe_te_v600_stage10_adaptive_retry_policy_v2_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 4 `from` statement(s)
- **Imported By:** 1 other Python module(s)
  - *Importers:* `tests/integration/translation_discipline_adaptive_retry_policy_v2_v600_stage10_test.py`
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (3):** `config/project_layout_policy.json`, `manifests/te_v600_stage10_adaptive_retry_policy_v2_manifest.json`, `manifests/te_v600_stage125_translation_naturalness_freeze_manifest.json`
- **Artifact/Audit References (9):** 9 item(s)
- **Test Suite References (2):** `tests/integration/translation_discipline_adaptive_retry_policy_v2_v600_stage10_test.py`, `verification/legacy/instructions/APPLY_TE_V6_0_STAGE11_3.txt`

### `ntpe_te_v600_stage121_translation_naturalness_engine_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 1 module import(s), 4 `from` statement(s)
- **Imported By:** 1 other Python module(s)
  - *Importers:* `tests/integration/translation_naturalness_engine_v600_stage121_test.py`
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (2):** `config/project_layout_policy.json`, `manifests/te_v600_stage125_translation_naturalness_freeze_manifest.json`
- **Artifact/Audit References (12):** 12 item(s)
- **Test Suite References (3):** `tests/integration/translation_naturalness_engine_v600_stage121_test.py`, `verification/legacy/instructions/APPLY_TE_V6_0_STAGE12_1.txt`, `verification/legacy/instructions/APPLY_TE_V6_0_STAGE12_3.txt`

### `ntpe_te_v600_stage122_hallucination_unsupported_detail_guard_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 3 `from` statement(s)
- **Imported By:** 1 other Python module(s)
  - *Importers:* `tests/integration/translation_hallucination_unsupported_detail_guard_v600_stage122_test.py`
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (3):** `config/project_layout_policy.json`, `manifests/te_v600_stage122_hallucination_unsupported_detail_guard_manifest.json`, `manifests/te_v600_stage125_translation_naturalness_freeze_manifest.json`
- **Artifact/Audit References (9):** 9 item(s)
- **Test Suite References (3):** `tests/integration/translation_hallucination_unsupported_detail_guard_v600_stage122_test.py`, `verification/legacy/instructions/APPLY_TE_V6_0_STAGE12_2.txt`, `verification/legacy/instructions/APPLY_TE_V6_0_STAGE12_3.txt`

### `ntpe_te_v600_stage123_literary_collocation_guard_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 3 `from` statement(s)
- **Imported By:** 1 other Python module(s)
  - *Importers:* `tests/integration/translation_literary_collocation_guard_v600_stage123_test.py`
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (3):** `config/project_layout_policy.json`, `manifests/te_v600_stage123_literary_collocation_guard_manifest.json`, `manifests/te_v600_stage125_translation_naturalness_freeze_manifest.json`
- **Artifact/Audit References (8):** 8 item(s)
- **Test Suite References (2):** `tests/integration/translation_literary_collocation_guard_v600_stage123_test.py`, `verification/legacy/instructions/APPLY_TE_V6_0_STAGE12_3.txt`

### `ntpe_te_v600_stage1241_voice_register_mapping_refinement_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 5 `from` statement(s)
- **Imported By:** 1 other Python module(s)
  - *Importers:* `tests/integration/translation_voice_register_mapping_refinement_v600_stage1241_test.py`
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (3):** `config/project_layout_policy.json`, `manifests/te_v600_stage1241_voice_register_mapping_refinement_manifest.json`, `manifests/te_v600_stage125_translation_naturalness_freeze_manifest.json`
- **Artifact/Audit References (8):** 8 item(s)
- **Test Suite References (1):** `tests/integration/translation_voice_register_mapping_refinement_v600_stage1241_test.py`

### `ntpe_te_v600_stage124_character_voice_register_guard_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 1 module import(s), 6 `from` statement(s)
- **Imported By:** 1 other Python module(s)
  - *Importers:* `tests/integration/translation_character_voice_register_guard_v600_stage124_test.py`
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (4):** `config/project_layout_policy.json`, `manifests/te_v600_stage1241_voice_register_mapping_refinement_manifest.json`, `manifests/te_v600_stage124_character_voice_register_guard_manifest.json`, `manifests/te_v600_stage125_translation_naturalness_freeze_manifest.json`
- **Artifact/Audit References (8):** 8 item(s)
- **Test Suite References (1):** `tests/integration/translation_character_voice_register_guard_v600_stage124_test.py`

### `ntpe_te_v600_stage125_translation_naturalness_freeze_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 3 module import(s), 10 `from` statement(s)
- **Imported By:** 1 other Python module(s)
  - *Importers:* `tests/integration/translation_naturalness_freeze_v600_stage125_test.py`
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (2):** `config/project_layout_policy.json`, `manifests/te_v600_stage125_translation_naturalness_freeze_manifest.json`
- **Artifact/Audit References (9):** 9 item(s)
- **Test Suite References (2):** `tests/integration/translation_naturalness_freeze_v600_stage125_test.py`, `verification/legacy/instructions/APPLY_TE_V6_0_STAGE12_5.txt`

### `ntpe_te_v611_stage111_translation_evidence_foundation_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 4 `from` statement(s)
- **Imported By:** 1 other Python module(s)
  - *Importers:* `tests/integration/translation_evidence_foundation_v611_stage111_test.py`
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (8):** 8 item(s)
- **Test Suite References (3):** `tests/integration/translation_evidence_foundation_v611_stage111_test.py`, `verification/legacy/instructions/APPLY_TE_V6_0_STAGE11_1.txt`, `verification/legacy/instructions/APPLY_TE_V6_0_STAGE11_2.txt`

### `ntpe_te_v611_stage112_source_translation_semantic_alignment_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 4 `from` statement(s)
- **Imported By:** 1 other Python module(s)
  - *Importers:* `tests/integration/translation_evidence_semantic_alignment_v611_stage112_test.py`
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (8):** 8 item(s)
- **Test Suite References (3):** `tests/integration/translation_evidence_semantic_alignment_v611_stage112_test.py`, `verification/legacy/instructions/APPLY_TE_V6_0_STAGE11_2.txt`, `verification/legacy/instructions/APPLY_TE_V6_0_STAGE11_3.txt`

### `ntpe_te_v611_stage113_evidence_to_retry_integration_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 3 `from` statement(s)
- **Imported By:** 1 other Python module(s)
  - *Importers:* `tests/integration/translation_evidence_to_retry_integration_v611_stage113_test.py`
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (2):** `config/project_layout_policy.json`, `manifests/te_v611_stage113_evidence_to_retry_integration_manifest.json`
- **Artifact/Audit References (8):** 8 item(s)
- **Test Suite References (2):** `tests/integration/translation_evidence_to_retry_integration_v611_stage113_test.py`, `verification/legacy/instructions/APPLY_TE_V6_0_STAGE11_3.txt`

### `ntpe_te_v611_stage114_safe_targeted_merge_validation_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 1 `from` statement(s)
- **Imported By:** 1 other Python module(s)
  - *Importers:* `tests/integration/translation_safe_targeted_merge_validation_v611_stage114_test.py`
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (2):** `config/project_layout_policy.json`, `manifests/te_v611_stage114_safe_targeted_merge_validation_manifest.json`
- **Artifact/Audit References (9):** 9 item(s)
- **Test Suite References (1):** `tests/integration/translation_safe_targeted_merge_validation_v611_stage114_test.py`

### `ntpe_te_v611_stage115_evidence_runtime_integration_audit_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 1 `from` statement(s)
- **Imported By:** 1 other Python module(s)
  - *Importers:* `tests/integration/translation_evidence_runtime_integration_audit_v611_stage115_test.py`
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (8):** 8 item(s)
- **Test Suite References (1):** `tests/integration/translation_evidence_runtime_integration_audit_v611_stage115_test.py`

### `ntpe_te_v611_stage116_translation_evidence_freeze_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 1 module import(s), 4 `from` statement(s)
- **Imported By:** 1 other Python module(s)
  - *Importers:* `tests/integration/translation_evidence_freeze_v611_stage116_test.py`
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (2):** `config/project_layout_policy.json`, `manifests/te_v600_stage125_translation_naturalness_freeze_manifest.json`
- **Artifact/Audit References (9):** 9 item(s)
- **Test Suite References (2):** `tests/integration/translation_evidence_freeze_v611_stage116_test.py`, `verification/legacy/instructions/APPLY_TE_V6_0_STAGE11_6.txt`

### `ntpe_te_v700_stage011_adaptive_context_safety_stabilization_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 3 module import(s), 3 `from` statement(s)
- **Imported By:** 1 other Python module(s)
  - *Importers:* `tests/integration/translation_engine_v700_stage011_adaptive_context_safety_boundary_test.py`
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (2):** `config/project_layout_policy.json`, `manifests/te_v700_stage011_adaptive_context_safety_stabilization_manifest.json`
- **Artifact/Audit References (6):** 6 item(s)
- **Test Suite References (1):** `tests/integration/translation_engine_v700_stage011_adaptive_context_safety_boundary_test.py`

### `ntpe_te_v700_stage01_adaptive_context_engine_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 2 module import(s), 4 `from` statement(s)
- **Imported By:** 1 other Python module(s)
  - *Importers:* `tests/integration/translation_engine_v700_stage01_adaptive_context_engine_test.py`
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (3):** `config/project_layout_policy.json`, `manifests/te_v700_stage011_adaptive_context_safety_stabilization_manifest.json`, `manifests/te_v700_stage01_adaptive_context_engine_manifest.json`
- **Artifact/Audit References (6):** 6 item(s)
- **Test Suite References (1):** `tests/integration/translation_engine_v700_stage01_adaptive_context_engine_test.py`

### `ntpe_te_v700_stage02_ace_runtime_integration_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 3 module import(s), 3 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (2):** `config/project_layout_policy.json`, `manifests/te_v700_stage02_ace_runtime_integration_manifest.json`
- **Artifact/Audit References (6):** 6 item(s)

### `ntpe_te_v700_stage03_runtime_shadow_activation_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 4 module import(s), 4 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (2):** `config/project_layout_policy.json`, `manifests/te_v700_stage03_runtime_shadow_activation_manifest.json`
- **Artifact/Audit References (6):** 6 item(s)

### `ntpe_te_v700_stage04_production_shadow_validation_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 4 module import(s), 4 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (3):** `config/project_layout_policy.json`, `manifests/te_v700_stage04_production_shadow_validation_manifest.json`, `manifests/te_v700_stage051_mutable_validation_artifact_integrity_fix_manifest.json`
- **Artifact/Audit References (8):** 8 item(s)

### `ntpe_te_v700_stage051_mutable_validation_artifact_integrity_fix_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 2 module import(s), 2 `from` statement(s)
- **Imported By:** 1 other Python module(s)
  - *Importers:* `ntpe_te_v700_stage071_manifest_chain_decoupling_test.py`
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (3):** `config/project_layout_policy.json`, `manifests/te_v700_stage051_mutable_validation_artifact_integrity_fix_manifest.json`, `manifests/te_v700_stage071_manifest_chain_decoupling_manifest.json`
- **Artifact/Audit References (6):** 6 item(s)

### `ntpe_te_v700_stage05_ace_active_canary_activation_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 2 module import(s), 3 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (2):** `config/project_layout_policy.json`, `manifests/te_v700_stage05_ace_active_canary_activation_manifest.json`
- **Artifact/Audit References (8):** 8 item(s)

### `ntpe_te_v700_stage061_canary_validation_test_hardening_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 3 module import(s), 2 `from` statement(s)
- **Imported By:** 1 other Python module(s)
  - *Importers:* `ntpe_te_v700_stage071_manifest_chain_decoupling_test.py`
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (3):** `config/project_layout_policy.json`, `manifests/te_v700_stage061_canary_validation_test_hardening_manifest.json`, `manifests/te_v700_stage071_manifest_chain_decoupling_manifest.json`
- **Artifact/Audit References (6):** 6 item(s)

### `ntpe_te_v700_stage06_ace_canary_production_validation_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 4 module import(s), 5 `from` statement(s)
- **Imported By:** 2 other Python module(s)
  - *Importers:* `ntpe_te_v700_stage061_canary_validation_test_hardening_test.py`, `ntpe_te_v700_stage071_manifest_chain_decoupling_test.py`
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (4):** `config/project_layout_policy.json`, `manifests/te_v700_stage061_canary_validation_test_hardening_manifest.json`, `manifests/te_v700_stage06_ace_canary_production_validation_manifest.json`, `manifests/te_v700_stage071_manifest_chain_decoupling_manifest.json`
- **Artifact/Audit References (8):** 8 item(s)

### `ntpe_te_v700_stage071_manifest_chain_decoupling_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 6 module import(s), 2 `from` statement(s)
- **Imported By:** 1 other Python module(s)
  - *Importers:* `ntpe_te_v700_stage072_canary_diagnostics_target_stop_test.py`
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (2):** `config/project_layout_policy.json`, `manifests/te_v700_stage071_manifest_chain_decoupling_manifest.json`
- **Artifact/Audit References (6):** 6 item(s)

### `ntpe_te_v700_stage072_canary_diagnostics_target_stop_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 4 module import(s), 3 `from` statement(s)
- **Imported By:** 1 other Python module(s)
  - *Importers:* `ntpe_te_v700_stage073_prompt_context_anchor_contract_test.py`
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (2):** `config/project_layout_policy.json`, `manifests/te_v700_stage072_canary_diagnostics_target_stop_manifest.json`
- **Artifact/Audit References (8):** 8 item(s)

### `ntpe_te_v700_stage073_prompt_context_anchor_contract_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 3 module import(s), 3 `from` statement(s)
- **Imported By:** 1 other Python module(s)
  - *Importers:* `ntpe_te_v700_stage074_package_bound_context_anchor_test.py`
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (2):** `config/project_layout_policy.json`, `manifests/te_v700_stage073_prompt_context_anchor_contract_manifest.json`
- **Artifact/Audit References (8):** 8 item(s)

### `ntpe_te_v700_stage074_package_bound_context_anchor_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 3 module import(s), 3 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (2):** `config/project_layout_policy.json`, `manifests/te_v700_stage074_package_bound_context_anchor_manifest.json`
- **Artifact/Audit References (8):** 8 item(s)

### `ntpe_te_v700_stage0751_integration_test_sandbox_stabilization_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 5 module import(s), 2 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (2):** `config/project_layout_policy.json`, `manifests/te_v700_stage0751_integration_test_sandbox_stabilization_manifest.json`
- **Artifact/Audit References (6):** 6 item(s)
- **Subprocess Invocations:** 1 call(s) inside file

### `ntpe_te_v700_stage075_canary_ab_quality_validation_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 3 module import(s), 3 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (2):** `config/project_layout_policy.json`, `manifests/te_v700_stage075_canary_ab_quality_validation_manifest.json`
- **Artifact/Audit References (8):** 8 item(s)

### `ntpe_te_v700_stage07_ace_canary_resume_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 3 module import(s), 2 `from` statement(s)
- **Imported By:** 3 other Python module(s)
  - *Importers:* `ntpe_te_v700_stage071_manifest_chain_decoupling_test.py`, `ntpe_te_v700_stage072_canary_diagnostics_target_stop_test.py`, `tests/integration/translation_engine_v700_stage07_ace_canary_resume_test.py`
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (3):** `config/project_layout_policy.json`, `manifests/te_v700_stage071_manifest_chain_decoupling_manifest.json`, `manifests/te_v700_stage07_ace_canary_resume_manifest.json`
- **Artifact/Audit References (9):** 9 item(s)
- **Test Suite References (1):** `tests/integration/translation_engine_v700_stage07_ace_canary_resume_test.py`

### `ntpe_te_v700_stage081_production_activation_policy_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 5 module import(s), 3 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (2):** `config/project_layout_policy.json`, `manifests/te_v700_stage081_production_activation_policy_manifest.json`
- **Artifact/Audit References (8):** 8 item(s)
- **Subprocess Invocations:** 1 call(s) inside file

### `ntpe_te_v700_stage082_profile_aware_context_budget_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 5 module import(s), 3 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (2):** `config/project_layout_policy.json`, `manifests/te_v700_stage082_profile_aware_context_budget_manifest.json`
- **Artifact/Audit References (8):** 8 item(s)
- **Subprocess Invocations:** 1 call(s) inside file

### `ntpe_te_v700_stage083_adaptive_context_strategy_selection_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 5 module import(s), 3 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (2):** `config/project_layout_policy.json`, `manifests/te_v700_stage083_adaptive_context_strategy_selection_manifest.json`
- **Artifact/Audit References (8):** 8 item(s)
- **Subprocess Invocations:** 1 call(s) inside file

### `ntpe_te_v700_stage0841_production_quality_rollback_wiring_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 6 module import(s), 3 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (2):** `config/project_layout_policy.json`, `manifests/te_v700_stage0841_production_quality_rollback_wiring_manifest.json`
- **Artifact/Audit References (6):** 6 item(s)
- **Subprocess Invocations:** 1 call(s) inside file

### `ntpe_te_v700_stage084_production_rollout_freeze_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 6 module import(s), 3 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (3):** `config/project_layout_policy.json`, `manifests/te_v700_stage0841_production_quality_rollback_wiring_manifest.json`, `manifests/te_v700_stage084_production_rollout_freeze_manifest.json`
- **Artifact/Audit References (6):** 6 item(s)
- **Subprocess Invocations:** 1 call(s) inside file

### `ntpe_te_v700_stage09_production_performance_quality_benchmark_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 5 module import(s), 3 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (2):** `config/project_layout_policy.json`, `manifests/te_v700_stage09_production_performance_quality_benchmark_manifest.json`
- **Artifact/Audit References (8):** 8 item(s)
- **Subprocess Invocations:** 1 call(s) inside file

### `ntpe_te_v700_stage10101_provider_timeout_controlled_retry_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 6 module import(s), 4 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (2):** `config/project_layout_policy.json`, `manifests/te_v700_stage10101_provider_timeout_controlled_retry_manifest.json`
- **Artifact/Audit References (9):** 9 item(s)
- **Subprocess Invocations:** 1 call(s) inside file

### `ntpe_te_v700_stage1010_single_real_provider_invocation_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 6 module import(s), 3 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (3):** `config/project_layout_policy.json`, `manifests/te_v700_stage10101_provider_timeout_controlled_retry_manifest.json`, `manifests/te_v700_stage1010_single_real_provider_invocation_manifest.json`
- **Artifact/Audit References (8):** 8 item(s)
- **Subprocess Invocations:** 1 call(s) inside file

### `ntpe_te_v700_stage101_provider_timing_evidence_adapter_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 6 module import(s), 3 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (2):** `config/project_layout_policy.json`, `manifests/te_v700_stage101_provider_timing_evidence_adapter_manifest.json`
- **Artifact/Audit References (8):** 8 item(s)
- **Subprocess Invocations:** 1 call(s) inside file

### `ntpe_te_v700_stage102_controlled_provider_benchmark_session_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 6 module import(s), 3 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (2):** `config/project_layout_policy.json`, `manifests/te_v700_stage102_controlled_provider_benchmark_session_manifest.json`
- **Artifact/Audit References (8):** 8 item(s)
- **Subprocess Invocations:** 1 call(s) inside file

### `ntpe_te_v700_stage103_controlled_provider_session_cli_harness_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 6 module import(s), 3 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (2):** `config/project_layout_policy.json`, `manifests/te_v700_stage103_controlled_provider_session_cli_harness_manifest.json`
- **Artifact/Audit References (8):** 8 item(s)
- **Subprocess Invocations:** 1 call(s) inside file

### `ntpe_te_v700_stage104_real_provider_invocation_boundary_contract_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 6 module import(s), 3 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (2):** `config/project_layout_policy.json`, `manifests/te_v700_stage104_real_provider_invocation_boundary_contract_manifest.json`
- **Artifact/Audit References (8):** 8 item(s)
- **Subprocess Invocations:** 1 call(s) inside file

### `ntpe_te_v700_stage105_authorized_single_invocation_provider_harness_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 6 module import(s), 3 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (2):** `config/project_layout_policy.json`, `manifests/te_v700_stage105_authorized_single_invocation_provider_harness_manifest.json`
- **Artifact/Audit References (8):** 8 item(s)
- **Subprocess Invocations:** 1 call(s) inside file

### `ntpe_te_v700_stage106_authorized_provider_execution_cli_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 6 module import(s), 3 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (2):** `config/project_layout_policy.json`, `manifests/te_v700_stage106_authorized_provider_execution_cli_manifest.json`
- **Artifact/Audit References (8):** 8 item(s)
- **Subprocess Invocations:** 1 call(s) inside file

### `ntpe_te_v700_stage107_provider_evidence_artifact_pipeline_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 6 module import(s), 3 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (2):** `config/project_layout_policy.json`, `manifests/te_v700_stage107_provider_evidence_artifact_pipeline_manifest.json`
- **Artifact/Audit References (8):** 8 item(s)
- **Subprocess Invocations:** 1 call(s) inside file

### `ntpe_te_v700_stage108_fake_transport_end_to_end_freeze_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 6 module import(s), 3 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (2):** `config/project_layout_policy.json`, `manifests/te_v700_stage108_fake_transport_end_to_end_freeze_manifest.json`
- **Artifact/Audit References (10):** 10 item(s)
- **Subprocess Invocations:** 1 call(s) inside file

### `ntpe_te_v700_stage109_real_provider_execution_preflight_contract_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 6 module import(s), 3 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (2):** `config/project_layout_policy.json`, `manifests/te_v700_stage109_real_provider_execution_preflight_contract_manifest.json`
- **Artifact/Audit References (8):** 8 item(s)
- **Subprocess Invocations:** 1 call(s) inside file

### `ntpe_te_v710_stage111_translation_defect_classification_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 6 module import(s), 4 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (2):** `config/project_layout_policy.json`, `manifests/te_v710_stage111_translation_defect_classification_manifest.json`
- **Artifact/Audit References (9):** 9 item(s)
- **Subprocess Invocations:** 1 call(s) inside file

### `ntpe_te_v710_stage112_translation_quality_metrics_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 6 module import(s), 3 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (2):** `config/project_layout_policy.json`, `manifests/te_v710_stage112_translation_quality_metrics_manifest.json`
- **Artifact/Audit References (9):** 9 item(s)
- **Subprocess Invocations:** 1 call(s) inside file

### `ntpe_te_v710_stage113_review_artifact_system_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 6 module import(s), 3 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (2):** `config/project_layout_policy.json`, `manifests/te_v710_stage113_review_artifact_system_manifest.json`
- **Artifact/Audit References (9):** 9 item(s)
- **Subprocess Invocations:** 1 call(s) inside file

### `ntpe_te_v710_stage114_prompt_improvement_planner_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 6 module import(s), 3 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (2):** `config/project_layout_policy.json`, `manifests/te_v710_stage114_prompt_improvement_planner_manifest.json`
- **Artifact/Audit References (9):** 9 item(s)
- **Subprocess Invocations:** 1 call(s) inside file

### `ntpe_te_v710_stage115_review_decision_contract_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 6 module import(s), 2 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (2):** `config/project_layout_policy.json`, `manifests/te_v710_stage115_review_decision_contract_manifest.json`
- **Artifact/Audit References (7):** 7 item(s)
- **Subprocess Invocations:** 1 call(s) inside file

### `ntpe_te_v710_stage116_golden_corpus_governance_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 6 module import(s), 2 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (2):** `config/project_layout_policy.json`, `manifests/te_v710_stage116_golden_corpus_governance_manifest.json`
- **Artifact/Audit References (7):** 7 item(s)
- **Subprocess Invocations:** 1 call(s) inside file

### `ntpe_te_v710_stage117_quality_framework_integration_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 6 module import(s), 2 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (1):** `docs/governance/migration/rm_2_3b_scope.txt`
- **Manifest/Config References (2):** `config/project_layout_policy.json`, `manifests/te_v710_stage117_quality_framework_integration_manifest.json`
- **Artifact/Audit References (7):** 7 item(s)
- **Subprocess Invocations:** 1 call(s) inside file

### `ntpe_te_v710_stage118_translation_quality_framework_freeze_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 6 module import(s), 2 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (1):** `docs/governance/migration/rm_2_3b_scope.txt`
- **Manifest/Config References (2):** `config/project_layout_policy.json`, `manifests/te_v710_stage118_translation_quality_framework_freeze_manifest.json`
- **Artifact/Audit References (28):** 28 item(s)
- **Test Suite References (1):** `tests/integration/architecture_consolidation_batch2_test_consolidation_test.py`
- **Subprocess Invocations:** 1 call(s) inside file

### `ntpe_te_v720_milestone_a_translation_quality_integration_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 2 module import(s), 2 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (2):** `config/project_layout_policy.json`, `manifests/te_v720_milestone_a_translation_quality_integration_manifest.json`
- **Artifact/Audit References (4):** 4 item(s)

### `ntpe_te_v720_stage121_evidence_based_prompt_quality_candidate_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 6 module import(s), 2 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (2):** `config/project_layout_policy.json`, `manifests/te_v720_stage121_evidence_based_prompt_quality_candidate_manifest.json`
- **Artifact/Audit References (28):** 28 item(s)
- **Subprocess Invocations:** 1 call(s) inside file

### `ntpe_te_v720_stage1221_controlled_provider_ab_execution_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 6 module import(s), 2 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (2):** `config/project_layout_policy.json`, `manifests/te_v720_stage1221_controlled_provider_ab_execution_manifest.json`
- **Artifact/Audit References (6):** 6 item(s)
- **Subprocess Invocations:** 1 call(s) inside file

### `ntpe_te_v720_stage1222_independent_pair_recovery_execution_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 6 module import(s), 2 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (2):** `config/project_layout_policy.json`, `manifests/te_v720_stage1222_independent_pair_recovery_execution_manifest.json`
- **Artifact/Audit References (7):** 7 item(s)
- **Subprocess Invocations:** 1 call(s) inside file

### `ntpe_te_v720_stage1223_minimal_excerpt_ab_quality_validation_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 6 module import(s), 2 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (2):** `config/project_layout_policy.json`, `manifests/te_v720_stage1223_minimal_excerpt_ab_quality_validation_manifest.json`
- **Artifact/Audit References (6):** 6 item(s)
- **Subprocess Invocations:** 1 call(s) inside file

### `ntpe_te_v720_stage122_controlled_provider_ab_validation_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 6 module import(s), 2 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (2):** `config/project_layout_policy.json`, `manifests/te_v720_stage122_controlled_provider_ab_validation_manifest.json`
- **Artifact/Audit References (6):** 6 item(s)
- **Subprocess Invocations:** 1 call(s) inside file

### `ntpe_te_v720_stage1251_controlled_canary_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 2 module import(s), 1 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (2):** `config/project_layout_policy.json`, `manifests/te_v720_controlled_canary_manifest.json`
- **Artifact/Audit References (4):** 4 item(s)
- **Subprocess Invocations:** 1 call(s) inside file

### `ntpe_te_v720_stage1254_prompt_contract_preservation_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 1 module import(s), 6 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (2):** `config/project_layout_policy.json`, `manifests/te_v720_stage1254_prompt_contract_preservation_manifest.json`
- **Artifact/Audit References (4):** 4 item(s)

### `ntpe_te_v720_stage1255_prompt_canary_readiness_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 1 module import(s), 2 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (4):** 4 item(s)

### `ntpe_te_v720_stage1256_prompt_verification_canary_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 2 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (4):** 4 item(s)

### `ntpe_te_v720_stage1256a_claim_safe_corpus_binding_remediation_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 2 module import(s), 2 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (2):** `config/project_layout_policy.json`, `manifests/te_v720_stage1256a_claim_safe_corpus_binding_remediation_manifest.json`
- **Artifact/Audit References (4):** 4 item(s)

### `ntpe_te_v720_stage1257_prompt_verification_canary_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 3 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (2):** `config/project_layout_policy.json`, `manifests/te_v720_stage1257a_execution_evidence_sealing_manifest.json`
- **Artifact/Audit References (4):** 4 item(s)

### `ntpe_te_v720_stage1257a_execution_evidence_sealing_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 1 module import(s), 2 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (2):** `config/project_layout_policy.json`, `manifests/te_v720_stage1257a_execution_evidence_sealing_manifest.json`
- **Artifact/Audit References (4):** 4 item(s)

### `ntpe_te_v720_stage1258_candidate_structural_verification_canary_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 1 module import(s), 2 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (2):** `config/project_layout_policy.json`, `manifests/te_v720_stage1258_candidate_structural_verification_canary_manifest.json`
- **Artifact/Audit References (4):** 4 item(s)

### `ntpe_te_v720_stage1258a_candidate_structural_failure_sealing_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 1 module import(s), 2 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (2):** `config/project_layout_policy.json`, `manifests/te_v720_stage1258_execution_manifest.json`
- **Artifact/Audit References (4):** 4 item(s)

### `ntpe_te_v720_stage1259_name_resolution_contract_remediation_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 1 module import(s), 2 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (2):** `config/project_layout_policy.json`, `manifests/te_v720_stage1259_name_resolution_contract_remediation_manifest.json`
- **Artifact/Audit References (5):** 5 item(s)

### `ntpe_ter_v11_translation_quality_foundation_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 2 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (5):** 5 item(s)
- **Test Suite References (1):** `verification/release/changelogs/CHANGELOG_TRANSLATION_ENGINE_REFACTOR_V1_1.md`

### `ntpe_ter_v12_literary_style_engine_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 3 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (5):** 5 item(s)
- **Test Suite References (1):** `verification/release/changelogs/CHANGELOG_TRANSLATION_ENGINE_REFACTOR_V1_2.md`

### `ntpe_ter_v13_speed_prompt_compression_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 2 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (5):** 5 item(s)
- **Test Suite References (1):** `verification/release/changelogs/CHANGELOG_TRANSLATION_ENGINE_REFACTOR_V1_3.md`

### `ntpe_ter_v14_speed_semantic_accuracy_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 3 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (5):** 5 item(s)

### `ntpe_ter_v15_literary_polish_v2_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 1 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (5):** 5 item(s)

### `ntpe_ter_v16_semantic_guard_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 1 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (5):** 5 item(s)
- **Test Suite References (1):** `verification/release/changelogs/CHANGELOG_TRANSLATION_ENGINE_REFACTOR_V1_6.md`

### `ntpe_ter_v17_narrative_naturalness_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 1 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (5):** 5 item(s)

### `ntpe_ter_v18_character_tone_api_stability_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 1 module import(s), 2 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (7):** 7 item(s)
- **Test Suite References (1):** `verification/release/changelogs/CHANGELOG_TRANSLATION_ENGINE_REFACTOR_V1_8.md`

### `ntpe_ter_v19_stability_repetition_guard_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 2 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (5):** 5 item(s)
- **Test Suite References (1):** `verification/release/changelogs/CHANGELOG_TRANSLATION_ENGINE_REFACTOR_V1_9.md`

### `ntpe_ter_v20_quality_lock_baseline_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 1 module import(s), 4 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (3):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`, `docs/releases/TE_v3_1_SCHEDULER_LAYER_FREEZE.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (7):** 7 item(s)
- **Test Suite References (1):** `verification/release/changelogs/CHANGELOG_TRANSLATION_ENGINE_REFACTOR_V2_0.md`

### `ntpe_ter_v21_provider_degraded_fallback_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 1 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (3):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`, `docs/releases/TE_v3_1_SCHEDULER_LAYER_FREEZE.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (6):** 6 item(s)

### `ntpe_ter_v22_runtime_quality_gate_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 3 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (3):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`, `docs/releases/TE_v3_1_SCHEDULER_LAYER_FREEZE.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (8):** 8 item(s)

### `ntpe_ter_v23_provider_configuration_audit_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 1 module import(s), 1 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (3):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`, `docs/releases/TE_v3_1_SCHEDULER_LAYER_FREEZE.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (6):** 6 item(s)

### `ntpe_ter_v24_runtime_provider_stability_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 2 module import(s), 6 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (3):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`, `docs/releases/TE_v3_1_SCHEDULER_LAYER_FREEZE.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (8):** 8 item(s)
- **Test Suite References (1):** `tests/integration/launcher_ter_v24_runtime_provider_stability_test.py`

### `ntpe_tic_batch1_translation_corpus_inventory_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 5 module import(s), 2 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (2):** `config/project_layout_policy.json`, `manifests/tic_batch1_translation_corpus_inventory_manifest.json`
- **Artifact/Audit References (12):** 12 item(s)
- **Subprocess Invocations:** 1 call(s) inside file

### `ntpe_tic_batch2_translation_case_extraction_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 5 module import(s), 2 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (2):** `config/project_layout_policy.json`, `manifests/tic_batch2_translation_case_extraction_manifest.json`
- **Artifact/Audit References (12):** 12 item(s)
- **Subprocess Invocations:** 1 call(s) inside file

### `ntpe_tic_batch3_manual_evidence_alignment_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 5 module import(s), 2 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (2):** `config/project_layout_policy.json`, `manifests/tic_batch3_manual_evidence_alignment_manifest.json`
- **Artifact/Audit References (15):** 15 item(s)
- **Subprocess Invocations:** 1 call(s) inside file

### `ntpe_tic_batch4_human_confirmed_failure_corpus_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 5 module import(s), 2 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (2):** `config/project_layout_policy.json`, `manifests/tic_batch4_human_confirmed_failure_corpus_manifest.json`
- **Artifact/Audit References (13):** 13 item(s)
- **Subprocess Invocations:** 1 call(s) inside file

### `ntpe_tic_batch5_historical_human_evidence_expansion_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 5 module import(s), 2 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (2):** `config/project_layout_policy.json`, `manifests/tic_batch5_historical_human_evidence_expansion_manifest.json`
- **Artifact/Audit References (12):** 12 item(s)
- **Subprocess Invocations:** 1 call(s) inside file

### `ntpe_tic_batch61_human_approval_regression_activation_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 5 module import(s), 2 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (2):** `config/project_layout_policy.json`, `manifests/tic_batch61_human_approval_regression_activation_manifest.json`
- **Artifact/Audit References (10):** 10 item(s)
- **Subprocess Invocations:** 1 call(s) inside file

### `ntpe_tic_batch6_human_correction_root_cause_regression_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 5 module import(s), 2 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (2):** `config/project_layout_policy.json`, `manifests/tic_batch6_human_correction_root_cause_regression_manifest.json`
- **Artifact/Audit References (11):** 11 item(s)
- **Subprocess Invocations:** 1 call(s) inside file

### `ntpe_tic_batch7_offline_translation_quality_gate_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 5 module import(s), 2 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (2):** `config/project_layout_policy.json`, `manifests/tic_batch7_offline_translation_quality_gate_manifest.json`
- **Artifact/Audit References (21):** 21 item(s)
- **Subprocess Invocations:** 1 call(s) inside file

### `ntpe_translate_batch.py`

- **Classification:** `KEEP_ROOT`
- **Reason:** Core production entrypoint, primary CLI launcher, or primary project validator referenced in repository root documentation and operational scripts.
- **Direct Imports:** 1 module import(s), 1 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (18):** `docs/archive/release_history/CHANGELOG_LTS_STAGE_06.md`, `docs/archive/release_history/CHANGELOG_LTS_STAGE_07.md`, `docs/archive/release_history/CHANGELOG_Stage_01_Translation_Runtime_Integration.md`, `docs/archive/release_history/CHANGELOG_Stage_02_Runtime_Contract_Stabilization.md`, `docs/archive/release_history/CHANGELOG_Stage_04_Runtime_Resume_Recovery_Layer.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (3):** 3 item(s)
- **Test Suite References (1):** `tests/lts_stage_06/launcher_batch_translation_test.py`

### `ntpe_translate_txt.py`

- **Classification:** `KEEP_ROOT`
- **Reason:** Core production entrypoint, primary CLI launcher, or primary project validator referenced in repository root documentation and operational scripts.
- **Direct Imports:** 1 module import(s), 1 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (29):** `docs/archive/release_history/CHANGELOG_LTS_Stage_02.md`, `docs/archive/release_history/CHANGELOG_NTPE_1_1_LTS_Stage_01.md`, `docs/archive/release_history/CHANGELOG_Stage_01_Translation_Runtime_Integration.md`, `docs/archive/release_history/CHANGELOG_Stage_02_Runtime_Contract_Stabilization.md`, `docs/archive/release_history/CHANGELOG_Stage_04_Runtime_Resume_Recovery_Layer.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (3):** 3 item(s)
- **Test Suite References (4):** `tests/lts_stage_01/launcher_txt_translation_entry_test.py`, `tests/lts_stage_03/launcher_glossary_character_memory_test.py`, `tests/lts_stage_04/launcher_translation_qa_test.py`, `tests/lts_stage_05/launcher_output_formatter_test.py`

### `ntpe_translation_engine_refactor_v1_test.py`

- **Classification:** `ARCHIVE_ONLY`
- **Reason:** Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/.
- **Direct Imports:** 0 module import(s), 4 `from` statement(s)
- **Imported By:** 0 other Python module(s)
- **Docs/README References (2):** `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`
- **Manifest/Config References (1):** `config/project_layout_policy.json`
- **Artifact/Audit References (5):** 5 item(s)

### `ntpe_validate.py`

- **Classification:** `KEEP_ROOT`
- **Reason:** Core production entrypoint, primary CLI launcher, or primary project validator referenced in repository root documentation and operational scripts.
- **Direct Imports:** 10 module import(s), 5 `from` statement(s)
- **Imported By:** 1 other Python module(s)
  - *Importers:* `tests/validation/test_ntpe_validate.py`
- **Docs/README References (69):** `README.md`, `docs/PROJECT_LAYOUT.md`, `docs/governance/audits/NTPE_GOVERNANCE_GAP_ANALYSIS.md`, `docs/governance/migration/rm_2_3b_scope.txt`, `docs/governance/repository/NTPE_REPOSITORY_STATUS_REPORT.md`
- **Manifest/Config References (30):** `config/project_layout_policy.json`, `manifests/ntpe_v20_stage0_project_layout_consolidation_manifest.json`, `manifests/ntpe_v20_stage1_translation_launcher_product_foundation_manifest.json`, `manifests/te_v32_runtime_scheduler_manifest.json`, `manifests/te_v33_runtime_integration_boundary_manifest.json`
- **Artifact/Audit References (44):** 44 item(s)
- **Test Suite References (65):** `tests/integration/translation_scheduler_stage331_runtime_integration_contract_test.py`, `tests/validation/test_ntpe_validate.py`, `verification/legacy/instructions/APPLY_STAGE_18_6_DOCUMENTATION_CENTER.bat`, `verification/legacy/instructions/APPLY_STAGE_18_8_ENTERPRISE_DEPLOYMENT_FREEZE.bat`, `verification/legacy/instructions/APPLY_STAGE_401.txt`
- **Subprocess Invocations:** 4 call(s) inside file
