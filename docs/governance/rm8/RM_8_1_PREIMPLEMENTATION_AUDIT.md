# RM-8.1 PREIMPLEMENTATION AUDIT
## Literary Quality Enforcement

### A. Current Quality Pipeline
The current quality pipeline in NTPE operates as follows:

1. **Translation Engine Phase** (`core/translation_engine/translation_engine.py`):
   - Provider generates translation
   - `BasicTranslationQA.check()` performs basic validation (Korean residue, length ratio, locked terms)
   - Returns QA report with `passed` boolean and issue list

2. **LTS TXT Runtime Phase** (`lts/txt_translation_runtime.py`):
   - Applies context intelligence via `apply_context_intelligence()` which:
     - Builds context snapshot including naturalness warnings via `detect_unnatural_phrases()`
     - Attaches these as `naturalness_warnings` to the package
   - Calls `orchestrate_runtime_discipline()` for discipline/local repair/retry logic
   - In QA retry loop (`translate_txt()`), calls `analyze_translation_quality()` which:
     - Processes basic QA checks (length ratio, Korean residue, etc.)
     - Evaluates naturalness hits via `RuntimeQAPolicy.naturalness_guard_policy`
     - Returns final QA report used for pass/fail/warn decisions
   - Quality gate decisions made in retry loop:
     - Break if QA passes OR `qa_fail_policy == "warn"`
     - Break if `qa_fail_policy == "fail"` OR max attempts reached
     - If QA fails and `qa_fail_policy != "warn"`: early return with `status = "failed"`
     - Only saves translation chunk if QA passes or policy is "warn"

3. **Final Output Phase**:
   - Combines all successful chunk translations
   - Applies final formatting and locked dictionary
   - Saves final output file only if all chunks succeeded

### B. Existing Components

#### 1. Literary Quality Check Patterns
- **Location**: `core/translation_engine/context_intelligence.py` lines 56-82
- **Component**: `_NATURALNESS_PATTERNS` tuple
- **Content**: 6 literary quality check patterns:
  1. `"人間"` → Should be `"人"/"正常人"/"人類"` unless meaning "human world"
  2. `"�嘔了一口氣"` → Should be `"倒�抽一口氣"/"�悶哼一聲"/"吸了口氣"/"�吐出一口氣"`
  3. `"可以用十個手指頭就能數得過來"` → Redundant counting
  4. `"觀光客人"` → Should be `"觀光客"/"遊客"/"旅客"`
  5. `"�纏�繞在一起"` → If not literal rope/limbs, should be `"交�錯"/"�糾�纏"/"混在一起"`

#### 2. Detection Functions
- **Location**: `core/translation_engine/context_intelligence.py`
- **Components**:
  - `detect_unnatural_phrases()` (lines 180-194): Returns list of detected issues with code, phrase, message, guidance
  - `detect_naturalness_warnings()` (lines 173-177): Converts to warning format
  - `build_context_snapshot()` (line 117): Integrates warnings into context
  - `apply_context_intelligence()` (lines 159-170): Attaches to package for prompt generation

#### 3. Naturalness Guard System (QA Evaluation)
- **Location**: `core/translation_runtime/runtime_qa.py`
- **Components**:
  - `RuntimeQAPolicy` (lines 16-34): Includes `naturalness_guard_policy` with values:
    - `"off"`, `"warn"`, `"high_confidence_only"`, `"quality_retry"`, `"literary_retry"`, `"fail"`
  - `_naturalness_severity()` (lines 220-226): 
    - Returns `"error"` if `naturalness_guard_policy == "fail"`
    - Returns `"error"` if `naturalness_guard_policy == "literary_retry"` AND `quality_profile` in `{"literary", "novel", "premium", "quality"}`
    - Otherwise returns `"warning"`
  - `analyze_runtime_quality()` (lines 116-217): 
    - Processes `naturalness_hits` from context intelligence
    - Applies severity based on `_naturalness_severity()` and `_retryable_naturalness_hits()`
    - Adds `NATURALNESS_GUARD` issues to QA report with appropriate severity
    - Determines `passed` based on absence of `"error"` severity issues

#### 4. Quality Gate Infrastructure
- **Location**: `lts/txt_translation_runtime.py` (QA retry loop)
- **Components**:
  - `qa_fail_policy` configuration (options: `"retry"`, `"fail"`, `"warn"`)
  - Retry logic with exponential backoff
  - Early return on failure when `qa_fail_policy != "warn"`
  - Translation chunk saving only when QA passes or policy is `"warn"`
  - Final output generation only if all chunks succeeded

#### 5. Reader Outcome Determination
- **Location**: `core/adaptive_context_production_rollout/outcome.py`
- **Component**: `ProductionOutcome` class (lines 10-32)
- **Metrics**: 
  - `qa_accepted`, `qa_retry_required`, `qa_failed` counts
  - `quality_scores`, `baseline_quality_scores` tuples
  - `qa_failure_rate` property (failed/total)
  - `evidence_complete` boolean
- **Usage**: `collect_production_outcome()` in `quality_bridge.py` uses these metrics to determine production readiness

#### 6. Entity/Consistency/Review/Learning Capabilities (RM-7)
- **Entity Resolution**: 
  - `core/entity_review/` module with review lifecycle
  - `artifacts/rm7_entity_canary/` showing entity resolution and normalization
- **Consistency Validation**: 
  - `translation/quality/consistency_validator.py`: Checks locked terms and repeated lines
  - Integrated into quality pipeline via `QualityComponent` interface
- **Review System**: 
  - `core/entity_review/review.py`: Review engine for knowledge evolution candidates
  - Accept/reject/supersede workflow with audit trail
- **Learning Capability**: 
  - Implicit in review system - accepted candidates become `KnowledgeEvolutionCandidate` for knowledge evolution pipeline

### C. Existing Tests

#### 1. Unit Tests
- **Translation Quality Canary**: `tests/unit/test_translation_quality_canary.py` (11 tests)
  - Tests QA candidate evaluation, flag handling, deterministic outputs
- **Quality Engine Freeze**: `tests/unit/test_stage15_8_quality_engine_freeze.py` 
  - Tests quality engine manifest and validation (currently failing due to missing imports)
- **Runtime QA**: Implied in various runtime tests

#### 2. Integration Tests
- **Literary Regression**: `ntpe_literary_regression.py` + `ntpe_literary_evaluation.py`
  - Full pipeline test with Smoke_Set/Golden_Set/Regression_Set
  - Evaluation via `evaluate_translation_text()` with 6 metrics:
    1. Plot/fidelity proxy (length ratio)
    2. Locked names/terms consistency
    3. Natural Chinese proxy (Korean residue, prefaces, density)
    4. Subject/pronoun proxy (demonstratives, Kyle confusion)
    5. Character voice/dialogue proxy (punctuation)
    6. Format/punctuation/simplified residue
- **Translation Engine Quality Tests**: 
  - `tests/integration/translation_engine_v720_stage12*_*_quality_validation_test.py`
  - Tests literary prompt quality candidates (v72.0)

#### 3. Smoke Tests
- Various launcher smoke tests for literary components

#### 4. LTS Validation
- `lts/quality_validation.py`: Validates QA files present and functional
- `lts/txt_translation_runtime.py`: Includes `analyze_translation_quality()` for QA validation

### D. Reader Outcome Gap
The current Reader Outcome determination (via `ProductionOutcome`) has a gap regarding explicit literary quality awareness:

**Current State**:
- Reader outcome is determined by general QA metrics:
  - `qa_accepted`/`qa_retry_required`/`qa_failed` counts
  - Quality score comparisons (`quality_scores` vs `baseline_quality_scores`)  
  - `evidence_complete` boolean
  - Specific issue code analysis (omission, unsupported details)
- No explicit literary quality metrics in the outcome determination
- Literary quality issues are subsumed under general `naturalness_hits` and `NATURALNESS_GUARD` issues

**Gap**:
- While literary quality issues can cause QA failures (and thus affect `qa_failed` count), there's no:
  - Explicit literary quality score in `ProductionOutcome`
  - Literary quality-specific thresholds in outcome determination
  - Separate tracking of literary vs other naturalness issues
  - Ability to set different quality gates for literary vs general quality

**Impact**:
- Production systems cannot make release decisions based solely on literary quality thresholds
- Literary quality improvements are not explicitly measured in outcome metrics
- Risk of releasing translations that pass general QA but have unacceptable literary quality

### E. Gate Insertion Point
The quality gate insertion point for RM-8.1 Literary Quality Enforcement is in the **QA evaluation phase** within `analyze_translation_quality()` in `core/translation_runtime/runtime_qa.py`.

**Current Flow**:
1. `analyze_translation_quality()` calls:
   - Basic QA checks (length ratio, Korean residue, etc.)
   - Context intelligence (adds `naturalness_warnings` via `detect_unnatural_phrases()`)
   - `analyze_runtime_quality()` evaluates these via `naturalness_guard_policy`
   
2. `analyze_runtime_quality()`:
   - Processes `naturalness_hits` from context intelligence
   - Applies `_naturalness_severity()` based on `naturalness_guard_policy` and `quality_profile`
   - For `naturalness_guard_policy == "literary_retry"` + `quality_profile` in `{"literary","novel","premium","quality"}`: sets severity to `"error"`
   - Otherwise: severity = `"warning"`
   - Adds `NATURALNESS_GUARD` issues with appropriate severity
   - Returns QA report with `passed` = no `"error"` severity issues

3. **Decision Point**: In `lts/txt_translation_runtime.py` lines 2086-2088:
   ```python
   if qa_report.get("passed") or options.qa_fail_policy == "warn":
       break  # Continue to save translation
   if options.qa_fail_policy == "fail" or qa_attempt >= qa_attempts:
       break  # Exit retry loop
   ```

**Insertion Opportunity**: 
The literary quality check is already happening but is implicit within the naturalness guard system. To make RM-8.1 explicit, we could:

1. **Option A (Enhance Existing)**: Add explicit `"literary_quality"` value to `naturalness_guard_policy` that behaves like `"literary_retry"` but with clearer semantics
2. **Option B (Add Separate Check)**: Insert a dedicated literary quality evaluation step after context intelligence but before general naturalness guard evaluation
3. **Option C (Enhance Reporting)**: Add explicit literary quality metrics to QA reports while keeping current logic

The insertion point would be in `analyze_runtime_quality()` after line 194 (where `NATURALNESS_GUARD` issues are added) to add explicit literary quality tracking.

### F. Reusable Components
All core components for RM-8.1 Literary Quality Enforcement already exist and are reusable:

1. **Detection Engine**:
   - `_NATURALNESS_PATTERNS` in `core/translation_engine/context_intelligence.py` (6 literary quality patterns)
   - `detect_unnatural_phrases()` function 
   - Context intelligence integration pipeline

2. **Evaluation Logic**:
   - `RuntimeQAPolicy.naturalness_guard_policy` with `"literary_retry"` value
   - `_naturalness_severity()` function that elevates to `"error"` for literary profiles
   - `_retryable_naturalness_hits()` for retry logic determination
   - QA report structure that tracks issue severity and `passed` status

3. **Quality Gate Infrastructure**:
   - `qa_fail_policy` options (`"retry"`, `"fail"`, `"warn"`)
   - Retry loop with early termination on failure
   - Translation chunk/output saving gated on QA results
   - Final manifest generation with QA metadata

4. **Reporting & Metrics**:
   - `ProductionOutcome` class for reader outcome determination
   - Existing metrics collection in `collect_production_outcome()`
   - Manifest and report generation pipeline

5. **Configuration System**:
   - Environment variables and CLI args for:
     - `quality_profile` (already supports `"literary"`, `"novel"`, etc.)
     - `naturalness_guard_policy` (already supports `"literary_retry"`)
     - `qa_fail_policy` 
   - Translation options propagation through pipeline

**Reusability Assessment**: 100% of core detection, evaluation, and gating logic is reusable. Only enhancements for explicitness, reporting, and configuration clarity are needed.

### G. Missing Components
While the core functionality exists, these components would need enhancement for a complete, explicit RM-8.1 Literary Quality Enforcement system:

1. **Explicit Literary Quality Policy**:
   - Missing: Dedicated `"literary_quality"` value in `naturalness_guard_policy`
   - Current: Literary quality checking is implicit via `"literary_retry"` + specific `quality_profile`

2. **Explicit Literary Quality Metrics**:
   - Missing: Separate literary quality score in QA reports and `ProductionOutcome`
   - Current: Literary quality issues are subsumed under general `naturalness_hits` metrics

3. **Literary Quality-Specific Configuration**:
   - Missing: Explicit `literary_quality_enabled` or similar boolean flag
   - Current: Controlled implicitly through `naturalness_guard_policy` and `quality_profile` combination

4. **Enhanced Reporting**:
   - Missing: Literary quality breakdown in manifests and reports
   - Current: Only overall naturalness metrics and issue codes

5. **Validation Tests**:
   - Missing: Specific tests for literary quality enforcement behavior
   - Current: General QA tests exist but literary quality specifics not isolated

6. **Documentation**:
   - Missing: Clear documentation of literary quality enforcement mechanisms
   - Current: Mechanisms exist but are not explicitly documented as literary quality gate

### H. Minimum Implementation Plan
For a future implementation phase (after this audit), the minimal changes to enable explicit RM-8.1 Literary Quality Enforcement would be:

#### Phase 1: Make Literary Quality Explicit (Backward Compatible)
1. **Extend `naturalness_guard_policy`** (`core/translation_runtime/runtime_qa.py` line 33):
   - Add `"literary_quality"` as valid policy value
   - Modify `_naturalness_severity()`:
     ```python
     if guard_policy == "fail":
         return "error"
     if guard_policy in ["literary_retry", "literary_quality"] and (policy.quality_profile or "").lower() in {"literary", "novel", "premium", "quality"}:
         return "error"
     return "warning"
     ```
   - Update `_retryable_naturalness_hits()` similarly for consistency

2. **Add Literary Quality Metrics to QA Reports**:
   - In `analyze_runtime_quality()` after processing `naturalness_hits` (around line 194):
     - Count literary quality-specific hits (could reuse same detection but track separately)
     - Add `literary_quality_hits` count to metrics
     - Add `literary_quality_passed` boolean based on no literary quality errors

3. **Enhance Production Outcome Reporting**:
   - In `core/adaptive_context_production_rollout/outcome.py`:
     - Add `literary_quality_score` property or similar
     - Update `to_dict()` to include literary quality metrics
   - In `quality_bridge.py`: Pass through literary quality metrics

#### Phase 2: Configuration and Validation (Optional Enhancements)
1. **Add Explicit Configuration**:
   - CLI arg: `--literary-quality-enabled` (defaults to `True` when `quality_profile` in literary set)
   - Environment variable: `NTPE_LITERARY_QUALITY_ENABLED`
   - Translation option: `literary_quality_enabled`

2. **Add Validation Tests**:
   - Unit tests for literary quality policy behavior
   - Integration tests showing literary quality gating
   - Regression tests for literary quality metrics in manifests

3. **Enhance Documentation**:
   - Update docs to explicitly document literary quality enforcement
   - Add examples of literary quality patterns and expected corrections

**Key Benefits of This Approach**:
- � ✅ Zero changes to core detection logic (`_NATURALNESS_PATTERNS`, `detect_unnatural_phrases`)
- � ✅ Zero changes to quality gate infrastructure (reuse existing retry/fail/warn logic)
- � ✅ Zero changes to production output flow (reuse existing saving mechanisms)
- � ✅ 100% backward compatible (existing `"literary_retry"` behavior unchanged)
- � ✅ Minimal code changes (mostly policy extensions and metric additions)
- � ✅ Clear, explicit literary quality enforcement mechanism
- � ✅ Proper gating via existing quality infrastructure
- � ✅ Measurable outcomes via enhanced metrics

### I. Regression Risk
The regression risk for implementing the minimum plan is **VERY LOW** because:

1. **Detection Logic Unchanged**: 
   - `_NATURALNESS_PATTERNS` and `detect_unnatural_phrases()` remain identical
   - No changes to how literary quality issues are detected

2. **Evaluation Logic Extended, Not Changed**:
   - Adding `"literary_quality"` to `naturalness_guard_policy` values
   - Existing `"literary_retry"` behavior preserved exactly
   - New value behaves identically to `"literary_retry"` for target profiles

3. **Metrics Are Additive**:
   - New literary quality metrics are additional fields
   - Existing metrics and report structure unchanged
   - No impact on existing consumers of QA reports

4. **Quality Gate Logic Unchanged**:
   - QA pass/fail determination logic identical
   - `qa_fail_policy` handling unchanged
   - Translation saving/gating behavior preserved

5. **Backward Compatibility**:
   - Existing configurations using `"literary_retry"` work identically
   - Default behavior unchanged (still `"warn"` for `naturalness_guard_policy`)
   - No required configuration changes for existing systems

**Specific Risk Areas and Mitigations**:
- **Risk**: Typos in new policy value string
  - **Mitigation**: Unit tests validate policy value handling
- **Risk**: Metrics field name conflicts
  - **Mitigation**: Use prefixed names like `literary_quality_hits` 
- **Risk**: Documentation mismatch
  - **Mitigation**: Update docs alongside code changes

**Regression Test Strategy**:
1. Run existing translation quality canary tests - should all pass
2. Run literary regression tests - should show no behavior change for existing configs
3. Add specific tests for `"literary_quality"` policy 
4. Verify manifests still generate correctly with new fields (optional)

### J. Acceptance Criteria
RM-8.1 Literary Quality Enforcement will be considered complete when:

1. **Functional Correctness**:
   - When `naturalness_guard_policy == "literary_quality"` and `quality_profile` in `{"literary","novel","premium","quality"}`:
     - Detected literary quality issues (per `_NATURALNESS_PATTERNS`) are marked as `"error"` severity
     - QA `passed` = `False` when such errors exist
     - Translation chunks are NOT saved when `qa_fail_policy` in `{"retry","fail"}`
   - When `naturalness_guard_policy != "literary_quality"` OR `quality_profile` not in literary set:
     - Same issues are marked as `"warning"` severity (preserving current behavior)
   - When `naturalness_guard_policy == "off"`:
     - No literary quality issues are flagged (preserving current behavior)

2. **Explicit Metrics**:
   - QA reports include `literary_quality_hits` count in `metrics`
   - QA reports include `literary_quality_passed` boolean 
   - `ProductionOutcome` and manifests reflect literary quality metrics
   - These metrics are zero when literary quality checking is disabled/effective warning

3. **Configuration Clarity**:
   - `"literary_quality"` is a valid value for `naturalness_guard_policy`
   - CLI/environment/translation options properly propagate literary quality setting
   - Default behavior unchanged for existing configurations

4. **Integration & Reporting**:
   - Final translation manifests include literary quality metrics
   - `ntpe_literary_evaluation.py` can report on literary quality specifically
   - Reader outcome determination can incorporate literary quality awareness

5. **Quality Assurance**:
   - All existing unit and integration tests pass (no regressions)
   - New tests verify literary quality enforcement behavior
   - Literary quality patterns from `_NATURALNESS_PATTERNS` are correctly detected and handled

### K. Explicit Non-Goals
The following are explicitly **NOT** part of RM-8.1 Literary Quality Enforcement:

1. **���🚫 New Literary Quality Detection Patterns**:
   - Will NOT add new patterns to `_NATURALNESS_PATTERNS` 
   - Will NOT create new detection functions for literary quality
   - Reason: Existing 6 patterns are sufficient foundation; expansion can be future work

2. **���🚫 Changes to Core Translation Logic**:
   - Will NOT modify `translation_engine.py` provider call logic
   - Will NOT alter `BasicTranslationQA` core checks
   - Will NOT modify context intelligence application timing
   - Reason: Preserve stability of core translation pipeline

3. **���🚫 New Quality Gate Infrastructure**:
   - Will NOT create new QA retry mechanisms
   - Will NOT add new quality gate layers or decision points
   - Will NOT modify the fundamental pass/fail/warn decision logic
   - Reason: Reuse existing, proven quality gate infrastructure

4. **���🚫 Standalone Literary Quality Service**:
   - Will NOT create separate literary quality microservice or API
   - Will NOT add external model calls for literary quality assessment
   - Reason: Keep deterministic, offline, fixed-cost evaluation as core NTPE principle

5. **���🚫 RM-8.2 or RM-8.3 Functionality**:
   - Will NOT implement cross-chunk continuity checks (RM-8.2)
   - Will NOT implement output/delivery gates (RM-8.3)
   - Will NOT implement provider resilience or DEFER mechanisms (RM-8.4)
   - Reason: RM-8.1 is strictly literary quality enforcement within single chunks

6. **���🚫 Breaking Changes**:
   - Will NOT change existing QA report structure in breaking way
   - Will NOT alter default values of existing configuration options
   - Will NOT remove or deprecate existing policy values
   - Reason: Maintain backward compatibility for all existing integrations

7. **���🚫 Performance Optimizations**:
   - Will NOT attempt to optimize detection performance beyond current levels
   - Will NOT add caching or parallelization for literary quality checks
   - Reason: Premature optimization; current performance is acceptable for gate function

8. **���🚫 Human-in-the-Loop Features**:
   - Will NOT add literary quality review interfaces or manual override mechanisms
   - Will NOT create literary quality appeal or exception processes
   - Reason: Focus on automated enforcement; human review is separate concern (RM-7 review system)

### L. Additional Notes
**Relationship to Existing Systems**:
- RM-8.1 builds directly on RM-7 (Entity/Consistency/Review/Learning) 
- Uses same entity resolution and consistency checking infrastructure
- Complements RM-7 review system by providing automated quality gate
- Feeds into RM-8.2 (cross-chunk continuity) and RM-8.3 (output gate) pipelines

**Deployment Considerations**:
- Can be deployed gradually via `naturalness_guard_policy` configuration
- Safe to test in shadow/canary modes before production rollout
- Metrics backward compatible - existing consumers ignore new fields
- No changes required to provider contracts or prompt specifications

**Alignment with NTPE Principles**:
- � ✅ Deterministic: Same input → same literary quality assessment
- � ✅ Offline-Friendly: No external API calls required
- � ✅ Fixed-Cost: Evaluation time bounded by input size
- � ✅ Fail-Safe: Exceptions default to safe behavior (warn/pass)
- � ✅ Incremental: Can be adopted via configuration changes only