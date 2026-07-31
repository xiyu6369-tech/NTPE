# RM-5 Scope

**Version**: RM-5.0  
**Purpose**: Defines what is IN and OUT of scope for RM-5.

---

## RM-5: Translation Quality Architecture

RM-5 is the first release milestone dedicated specifically and exclusively to translation quality enhancement.  
Prior milestones (RM-1 through RM-4) focused on repository cleanup, governance, and baseline stabilization.

RM-5 shifts to improving the **translation output quality** through structured pipeline optimization.

---

## IN SCOPE

### 1. Translation Quality

- Output readability improvements
- Stylistic consistency (tone, voice, register)
- Natural phrasing in target language (Traditional Chinese)
- Reduction of translated artifacts vs. natural writing

### 2. Runtime Efficiency

- Token usage optimization
- API call reduction without quality loss
- Caching strategies for repeated context

### 3. Context Optimization

- Scene-level context awareness
- Cross-chunk narrative continuity
- Context selection strategy
- Context window sizing

### 4. Character Memory

- Runtime character name consistency
- Character trait and tone preservation
- Dialogue attribution accuracy
- Cross-volume character continuity

### 5. Prompt Architecture

- Prompt template optimization
- Injection structure refinement
- Rule clarity and precision
- Prompt size vs. context budget tradeoffs

### 6. Quality Evaluation

- Post-translation quality measurement
- Semantic scoring
- Readability scoring
- Consistency scoring
- Regression testing framework

### 7. Evidence & Analytics

- Regression test suite for translation quality
- Benchmark data collection
- Quality reporting
- Performance tracking

---

## EXPLICITLY OUT OF SCOPE

The following are marked as **COMPLETE** from previous milestones (RM-1 through RM-4) and are excluded from any RM-5 activity:

### 1. Repository Cleanup
- File organization and restructuring
- Directory renaming or reorganization
- Legacy code cleanup
- Completed by: RM-1, RM-2, RM-3, RM-4

### 2. Governance Migration
- Governance document restructuring
- Migration reports and maps
- Audit and evidence scripting
- Completed by: RM-2, RM-3

### 3. Archive Reorganization
- Archive directory structure
- Historical preservation
- LTS duplicate management
- Completed by: RM-4

### 4. Build System
- CI/CD configuration
- Environment setup
- Dependency management
- Completed by: RM-3, RM-4

### 5. Testing Infrastructure
- Test framework setup
- Test runner configuration
- CI integration
- Completed by: RM-3, RM-4

---

## RM-5 Prohibited Operations

These operations are strictly prohibited during all RM-5 stages:

- Commit to repository
- Push to remote
- Tag to release
- Network requests (API calls to providers)
- Provider execution (NVIDIA API calls)
- Production Integration (environment modification)

**Forbidden until:** RM-5 Freeze milestone (RM-5.6)

---

## RM-5 Stage Roadmap

| Stage | Focus | Key Deliverable | Dependencies |
|---|---|---|---|
| **RM-5.0** | Architecture Baseline | Governance documents (this stage) | RM-4 Freeze |
| **RM-5.1** | Translation Pipeline Audit | Complete pipeline inventory, dead path identification | RM-5.0 |
| **RM-5.2** | Context & Memory Optimization | Scene-level context, character memory injection | RM-5.1 |
| **RM-5.3** | Prompt Architecture | Prompt optimization, quality-driven refactoring | RM-5.2 |
| **RM-5.4** | Quality Benchmark Framework | Quantitative quality standards, regression suite | RM-5.1 |
| **RM-5.5** | Evidence & Quality Reports | Baseline quality report, regression verification | RM-5.2, RM-5.4 |
| **RM-5.6** | RM-5 Freeze | Final validation, Commit, Push, Tag | All prior stages |

---

## Scope Boundary Diagram

```
┌─────────────────────────────────────────────────────┐
│                    RM-5 BOUNDARY                    │
├─────────────────────────────────────────────────────┤
│                                                     │
│  IN                    │         OUT                │
│                        │                            │
│  • Translation Quality │  • Repository Cleanup      │
│  • Context Optimization │  • Governance Migration   │
│  • Character Memory    │  • Archive Reorganization  │
│  • Prompt Engineering  │  • Build System            │
│  • Quality Evaluation  │  • Testing Infrastructure  │
│  • Runtime Efficiency  │  • RM-4 Code Modification  │
│  • Evidence/Analytics  │                            │
│                        │                            │
└─────────────────────────────────────────────────────┘
```

---

## "Do Not Touch" List (Frozen)

The following directories and files are **strictly read-only** throughout RM-5:

- `core/` — All .py files
- `lts/` — All .py files
- `tools/` — All .py files
- `tests/` — All existing .py files (new test directories allowed)
- `engine/` — All .py files
- `config/project_layout_policy.json`
- `ntpe_validate.py`