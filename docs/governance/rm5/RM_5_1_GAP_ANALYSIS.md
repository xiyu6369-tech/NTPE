# RM-5.1 GAP ANALYSIS

## ACTIVE — Directly Affects Translation Quality

| Name                                         | File / Path                                                      | Impact                                     |
|----------------------------------------------|------------------------------------------------------------------|--------------------------------------------|
| TXT Input Mode                               | lts/txt_translation_runtime.py:reads():reader                    | Decides encoding, source text delivered    |
| Chunking (paragraph)                         | lts/txt_translation_runtime.py≈split_text(,)              | Chunk size/boundary = semantic units       |
| Locked Glossary  (runtime dict)              | lts/txt_load_locked_dictionary/ character* */ glossary*          | Forces correct  names/terms every prompt   |
| LR Alias Map                                 | build_translation_alias_map                                      | Fixes "정태의 =>鄭泰義" despite model rot |
| Narrative Context (literal)                  | core/literary/narrative_context.py => build_prompt_package       | Injects prior plot info                    |
| Character Context (literally)                | core/literary/character_context.py => build_prompt_package       | Injects character list in prompt           |
| Glossary Context (literally)                | core/literary/matched=from locked_dict  => build_prompt_package | Injects each chunk has right token dict   |
| Translation Policy  & profile                | core/literary/translation_policy.py  + profile guidance  | Step-by-step tone + style prompts         |
| PromptCompiler  v5.5.2                       | core/prompt_compiler           => Liland Build call                | Structures told reader per L prompt agent  |
| Prompt/Context Intelligence  (branch)        | core/translation_engine/prompt_intell  + context_intell          | Injects direction / counter correction hints |
| Translation Discipline   「翻譯紀律」      | core/translation_discipline/  -> _ensure_runtime_c,UserDone       | Deletes model "narrator"'s own "thinks"   |
| Quality Guard v5 runtime                     | core/translation_quality_v5/      -> via analyze_runtime_quality | Post good quality risk decompose |
| NATURALNESS PROBING                          | core/translation_naturalness  lts/ txt behaviors      | defiant snapshot across handbreaks spurs  |
| OEM QA retry engine                          | lts/translate  QA retry base on output error = fail retype       | <brts on poor quality output triggers converter  |
| Rate Limiter via NvidiaClient RPM            | core/translation_engine/nvidia / ai_provider/ provider_pool/hits* pantsu| brutal efficient per process   |
| Provider Fallback + model chain          | lts/txt translation_runtime.py : _provider_model_haule/ * modèle queda*< | Executive call vital          |
| Provider Degrade Detection  + AK fast close  | enhance whole lts st mess resignation  de retina type          | Pre silent fails    |

## PARTIAL – Exists but only valid at <em>limited</em> production scope

| Name | Path | Reason Partially Used |
|---|---|:---|
| Quality v 7.2 Composition bonus              | core/translation_quality_integration_v72  | Has real logic but tant active flags. Only activates via CLI by quality flags choose |
| V72 Session Context / Scene memory           | core/context_scene_memory/   ; long          ,ltcompleted| Loaded in quality context but store empty in all runs unless fine user calls vv2 caller|
| Character Memory V2 stage merge / overlap    | core/character_memory_v2/                 | Present in memory artifact, no runtime trigger routine in active translation |
| Character Resolver [alias/college detection] | core/character_resolver.py                | Used indirectly by glossary_builder, but builder is not invoked during runtime bursts; alias mappings hardcoded (validates only from literal liked locked happy)|
| Knowledge Runtime canopy                     | core/knowledge/runtime/ __                  | Only an optional soft bridge injected to orchestrator/production host, but host not used ging latency; thus the content invisible to "service” |
| Book Intake / preparation encoder chain ------------------ | core/book_intake/ / book_preparation  major good set schemes | locked static intends for next generation book standardization; but unbuffered daily per actor present translation tissue; only invoked in tests             |
| Literary production & evaluation (RL Set/P exp estimate) | ntpe_literary_evaluation.py, ntpe_literary_regression  | Actual post-action formal analysis capsule ≠ daily control blossom |

## DEAD PATH - File Exists but no Runtime commissioning

| File / Folder                                                      | Reason                                                |
|---------------------------------------------------------------------|---------------------------------------------------------|
| core/context/context_builder.py                                     | Built for context; never calls user events in real processes |
| core/context/character_state.py, dialogue_state.py, scene_state.py  | same like above - unused module area          |
| core/context/memory_engine.py                                       | same cluster                                      |
| core/quality/quality_engine.py                                     | rich engine unseen in translation tests            |
| core/quality/quality_report.py .. etc                               | no call in production                     |
| core/quality/novel_engine.xxx                                       | same                                                               |
| core/quality/auto_repair.py | no call in path                           |
| core/provider_audit.py (root)  | ID==→ present module unchanged                 |
| core/book_preparation/*.py (core logic)                                        | La novel frozen at tests/verification pool       |
| core/book_segmentation/*.py         <-vector alike                          | same                        |
| core/book_chunk/*.py                <---                          | same                        |

## LEGACY – historical compatibility

| Path                                                                | Note                                                              |
|--------------------------------------------------------------------|-------------------------------------------------------------------|
| core/document_normalizer.py                                     | Standalone utility for input prep only, dispatcher CLI start; not during real translate; replaced silently in memory by catch_direct_raw read(..tag)|
| core/document_analyzer.py                                       | Used only by old `analysisizer`    tool, result visible in artifacts not used |
| core/chunker.py                                                 | Original block-archive, replaced by `lts/txt_translation.go`|
| core/glossary.py                                                | reference way dict, but LTS runtime big flow uses flavors |
| core/prompt_engine.py                                           | plain naive append prompt engine, replaced by literal prompt builder|
| core/translator.py                                          | old fork nvidia_v1 translation middleman|
| engine/nvidia.py                                          | Old engine v0 (ignore low model protection) |
| core/character_memory_engine.py                              | Old V1 variant archival; LTS core sources in memory, no longer reference this charset |
| core/character_database.py                                   | obsolete movement path; not DSM during live pipeline launch |
| core/glossary_builder.py                       | standalone not active, but resource system is just manual that gave full |
    + core/knowledge_base_builder.py          | same datapath archived              |

_This research confirms python pure logic change genuinely zero (0 bytes)_