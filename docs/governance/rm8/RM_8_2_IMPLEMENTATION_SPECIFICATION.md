# RM-8.2 Implementation Specification

> **Authority**: This specification derives from RM-8.2 Core Principles and the RM-8.2 Pre-Implementation Audit.
> **Status**: Draft ??pending review. **No commits until approved.**
> **Revision**: Post-Conditional-Pass revisions applied per RM-8.2 Specification Review Audit (2026-08-10)

---

## 1. Scope & Non-Goals

### 1.1 In Scope
- Attach Scene/Chapter metadata to existing Production Chunks
- Context state propagation across chunks (N ??N+1)
- Scene/Chapter boundary detection (metadata only, no re-chunking)
- Token-budgeted context selection from `ContextMemoryStore`
- Prompt injection of selected context + scene + narrative state
- Checkpoint/resume of `ContextMemoryStore`
- Deterministic acceptance tests for 7 boundary scenarios

### 1.2 Explicitly Out of Scope
- ??New chunking engine or re-chunking by Scene/Chapter
- ??Modifying `split_text()` or `DEFAULT_CHUNK_SIZE`
- ??Modifying RM-7 Entity Resolution / Review / Learning pipeline
- ??Adding provider/LLM requests
- ??Output/layout/TOC generation (RM-8.3)
- ??Modifying `TranslationEngine` core logic
- ??Modifying QA, Retry, Resume logic

---

## 2. Architecture: Data Flow

```
?Œâ??€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€????                        PRODUCTION CHUNK LOOP                                ???? lts/txt_translation_runtime.py:_translate_txt_with_runtime_pipeline()      ???”â??€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€??                                     ??                                     ???Œâ??€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€???? FOR EACH CHUNK (idx, chunk_text):                                           ????                                                                             ???? 1. BOUNDARY DETECTION (metadata only)                                       ????    boundary = detect_boundary(prev_chunk_text, chunk_text)                 ????    ??BoundaryResult { type, scene_id?, chapter_id?, metadata }             ????                                                                             ???? 2. SCENE/CHAPTER TRANSITION (if boundary.type != SAME_SCENE)               ????    transition_scene(store, from_scene, boundary.type, to_scene, ...)       ????    ??expires SCENE_SCOPE / CHAPTER_SCOPE contexts                          ????    ??updates SceneMemoryRecord (participants, active_speaker, refs)        ????                                                                             ???? 3. CONTEXT SELECTION                                                        ????    selection = select_context_for_translation(                              ????        store, chapter_id, scene_id, sequence_index=idx,                    ????        character_ids=active_character_ids,                                 ????        token_budget=512, character_token_budget=256                        ????    )                                                                       ????    ??ContextSelectionResult { selected_records, selected_chars, fingerprint }????                                                                             ???? 4. NARRATIVE STATE UPDATE                                                   ????    narrative_engine.analyze_chunk(source=chunk_text, translation=prev_trans)????    narrative_engine.update_state(...)                                       ????    narrative_context = narrative_engine.get_context_for_prompt()           ????                                                                             ???? 5. PROMPT ASSEMBLY (feature-gated: enable_cross_chunk_context)             ????    builder = PromptBuilder(                                                 ????        chunk_text=chunk_text,                                              ????        context_selection=selection,                                        ????        scene_state=store.get_scene(scene_id),                              ????        narrative_state=narrative_context,                                  ????        entity_injection_set=entity_resolver.resolve(chunk_text),           ????        enable_cross_chunk_context=True  # When RM-8.2 enabled              ????    )                                                                       ????    assembly = builder.build(merged_runtime)                                ????                                                                             ???? 6. TRANSLATION REQUEST                                                      ????    context_state_metadata = {  # Composed dict, NO new dataclass           ????        "context_selection_fingerprint": selection.fingerprint,            ????        "scene_id": scene_id, scene_version=scene.scene_version,           ????        "narrative": narrative_context,                                    ????        "boundary": boundary.to_dict(),                                    ????        "selected_context_ids": [r.item_id for r in selection.selected_records]????    } if enable_cross_chunk_context else None                               ????    request = adapter.prepare(assembly, snapshot_id, metadata={             ????        "context_state": context_state_metadata,                            ????        ...                                                                 ????    })                                                                      ????                                                                             ???? 7. EXECUTION (unchanged)                                                    ????    result = orchestrator.execute(...) ??engine.translate_package_from_request()
??                                                                             ???? 8. POST-PROCESSING (unchanged)                                              ????    translation = result.response.translation                               ????    apply_locked_dictionary, format, QA, discipline                         ????                                                                             ???? 9. CONTEXT UPDATE (after successful translation)                           ????    // Extract new context from (source, translation) pair                  ????    // Via existing extractors or heuristic rules                           ????    // add_or_merge_context(store, new_record)                              ????                                                                             ???? 10. CHECKPOINT                                                               ????    checkpoint_mgr.create_checkpoint(                                        ????        session_id, idx, progress, metadata={                               ????            "context_store_snapshot": store.snapshot(),                     ????            "narrative_state_snapshot": narrative_engine.state.to_dict(),   ????            "current_scene_id": current_scene_id,                           ????            "current_chapter_id": current_chapter_id,                       ????            "prev_chunk_text": prev_chunk_text,                             ????        })                                                                  ????                                                                             ???? 11. NEXT CHUNK                                                               ???”â??€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€??```

---

## 3. New Types & Schemas

### 3.1 Boundary Detection Result

```python
# core/translation_runtime/boundary_detector.py (NEW FILE)

from dataclasses import dataclass
from typing import Optional, Dict, Any
from core.context_scene_memory.models import BoundaryType

@dataclass(frozen=True)
class BoundaryResult:
    """Result of scene/chapter boundary detection between two chunks.

    Conservative: only explicit markers produce SCENE_TRANSITION/CHAPTER_TRANSITION.
    Heuristics (location/time/speaker) return UNKNOWN_TRANSITION.
    """
    type: BoundaryType
    scene_id: Optional[str] = None          # Target scene_id if explicit transition
    chapter_id: Optional[str] = None        # Target chapter_id if chapter transition
    confidence: float = 1.0                 # Detection confidence
    metadata: Dict[str, Any] = None         # Raw evidence (markers, keywords)

    def to_dict(self) -> dict:
        return {
            "type": self.type.value,
            "scene_id": self.scene_id,
            "chapter_id": self.chapter_id,
            "confidence": self.confidence,
            "metadata": self.metadata or {}
        }

# Detection priority (highest first):
# 1. Explicit Korean chapter markers: ?œN?? ç¬¬Nç«? Chapter N
# 2. Explicit Korean scene markers: ?œN?? ç¬¬Nç¯€, Scene N, ***
# 3. UNKNOWN_TRANSITION (conservative default for all heuristics)
# 4. SAME_SCENE (no boundary detected)
```

### 3.2 Context State Payload (in TranslationRequest.metadata)

```python
# core/translation_runtime/models.py (EXTEND TranslationRequest metadata schema)
# NO NEW DATACLASS ??compose from existing serializable objects

# ContextStatePayload is a typed dict composed from:
# - ContextSelectionResult.fingerprint (str)
# - SceneMemoryRecord.scene_id, scene_version (from store.get_scene())
# - NarrativeState.to_dict() (from narrative_engine.get_context_for_prompt())
# - BoundaryResult.to_dict() (from detect_boundary())
# - tuple(r.item_id for r in ContextSelectionResult.selected_records)

# Example composition in chunk loop:
context_state_metadata = {
    "context_selection_fingerprint": selection.fingerprint,
    "scene_id": current_scene_id,
    "scene_version": context_store.get_scene(current_scene_id).scene_version,
    "narrative": narrative_engine.get_context_for_prompt(),  # Already dict
    "boundary": boundary.to_dict(),
    "selected_context_ids": tuple(r.item_id for r in selection.selected_records),
}

# Extend TranslationRequest.metadata schema:
# metadata: Dict[str, Any] = {
#     ...,
#     "context_state": context_state_metadata,  # Composed dict, not new class
# }
```

### 3.3 PromptBuilder Extensions (Feature-Gated)

```python
# core/prompt_runtime/builder.py (MODIFY PromptBuilder.__init__)

class PromptBuilder:
    def __init__(
        self,
        chunk_text: str = "",
        system_metadata: Optional[Dict[str, Any]] = None,
        entity_injection_set: Optional[Any] = None,
        # RM-8.2 EXTENSIONS (feature-gated):
        context_selection: Optional[ContextSelectionResult] = None,
        scene_state: Optional[SceneMemoryRecord] = None,
        narrative_state: Optional[dict] = None,
        enable_cross_chunk_context: bool = False,  # FEATURE FLAG ??default OFF
    ):
        self._chunk_text = chunk_text
        self._system_metadata = system_metadata or {}
        self._entity_injection_set = entity_injection_set
        self._context_selection = context_selection
        self._scene_state = scene_state
        self._narrative_state = narrative_state
        self._enable_cross_chunk_context = enable_cross_chunk_context

    def build(self, runtime: MergedRuntime) -> PromptAssembly:
        sections: List[PromptSection] = []

        # System (always first)
        sections.append(build_system(runtime, self._system_metadata))

        # Character (parameterized with selected memories when enabled)
        sections.append(build_character(
            runtime,
            character_memories=self._context_selection.selected_character_memories if self._enable_cross_chunk_context and self._context_selection else None
        ))

        # Entity Mapping (RM-7.2)
        sections.append(build_entity_mapping(runtime, self._entity_injection_set))

        # Domain sections (fixed order)
        for section_name in SECTION_ORDER[3:-1]:
            if section_name == "Scene":
                sections.append(build_scene(
                    runtime,
                    scene_state=self._scene_state if self._enable_cross_chunk_context else None
                ))
            elif section_name == "Narrative":
                sections.append(build_narrative(
                    runtime,
                    narrative_state=self._narrative_state if self._enable_cross_chunk_context else None
                ))
            elif section_name == "Context":  # NEW SECTION ??only when enabled
                if self._enable_cross_chunk_context:
                    sections.append(build_context_selection(self._context_selection))
            else:
                builder = SECTION_BUILDERS[section_name]
                sections.append(builder(runtime))

        # Chunk (always last)
        sections.append(build_chunk(runtime, self._chunk_text))

        return PromptAssembly(sections=sections, metadata={...})
```

### 3.4 Section Builder Extensions (Parameterize Existing, No Parallel Builders)

```python
# core/prompt_runtime/sections.py (MODIFY existing builders, ADD build_context_selection)

def build_context_selection(selection: Optional[ContextSelectionResult]) -> PromptSection:
    """Build Context section from token-budgeted selection. NEW SECTION for RM-8.2."""
    if not selection or not selection.selected_records:
        return PromptSection(
            name="Context",
            content="No relevant context from prior chunks.",
            metadata={"source": "context_selection", "record_count": 0}
        )

    lines = ["?Cross-Chunk Context??]
    for item in selection.selected_records:
        # item: SelectedContextItem { item_id, item_type, value, evidence_ids, estimated_tokens, priority }
        lines.append(f"- {item.value}")

    content = "\n".join(lines)
    return PromptSection(
        name="Context",
        content=content,
        metadata={
            "source": "context_selection",
            "record_count": len(selection.selected_records),
            "estimated_tokens": selection.estimated_tokens,
            "fingerprint": selection.deterministic_fingerprint,
        }
    )

# MODIFY existing build_character ??add optional character_memories parameter
def build_character(runtime: MergedRuntime, character_memories: Optional[tuple] = None) -> CharacterSection:
    """Build Character section, optionally extended with selected character memories."""
    base_content = _build_character_base_content(runtime)  # Extract existing logic

    if not character_memories:
        return CharacterSection(content=base_content, metadata={"domain": "character"})

    char_lines = [base_content] if base_content else []
    char_lines.append("\n?Active Character Memories??)
    for item in character_memories:
        # item: CharacterContextItem { memory_id, character_id, fact_type, value, evidence_ids, estimated_tokens }
        char_lines.append(f"- {item.character_id} ({item.fact_type}): {item.value}")

    return CharacterSection(
        content="\n".join(char_lines),
        metadata={
            "domain": "character",
            "selected_memory_count": len(character_memories),
            "character_tokens": sum(item.estimated_tokens for item in character_memories),
        }
    )

# MODIFY existing build_scene ??add optional scene_state parameter
def build_scene(runtime: MergedRuntime, scene_state: Optional[SceneMemoryRecord] = None) -> SceneSection:
    """Build Scene section, optionally extended with live SceneMemoryRecord."""
    if not scene_state:
        return _build_scene_base(runtime)  # Existing logic

    parts = []
    if scene_state.location:
        parts.append(f"?´æ™¯={scene_state.location}")
    if scene_state.time_state:
        parts.append(f"?‚é?={scene_state.time_state}")
    if scene_state.active_speaker:
        parts.append(f"?¼è???{scene_state.active_speaker}")
    if scene_state.point_of_view:
        parts.append(f"è¦–é?={scene_state.point_of_view}")
    if scene_state.event_state:
        parts.append(f"äº‹ä»¶={'??.join(scene_state.event_state[-5:])}")

    content = "ï¼?.join(parts) if parts else ""

    # Add participants
    if scene_state.participants:
        present = [p.character_id for p in scene_state.participants
                   if p.participant_status == ParticipantStatus.PRESENT]
        if present:
            content += f"\n?¨å ´äººç‰©ï¼š{'??.join(present)}"

    # Add unresolved references
    unresolved = [r for r in scene_state.unresolved_references
                  if r.resolution_status in {ResolutionStatus.UNRESOLVED, ResolutionStatus.CANDIDATE}]
    if unresolved:
        ref_lines = ["?ªè§£?æ?ä»??"]
        for r in unresolved[:5]:
            ref_lines.append(f"  {r.surface_form}" + (f"?’{r.resolved_target}" if r.resolved_target else ""))
        content += "\n" + "\n".join(ref_lines)

    return SceneSection(
        content=content,
        metadata={
            "domain": "scene",
            "scene_id": scene_state.scene_id,
            "scene_version": scene_state.scene_version,
            "chapter_id": scene_state.chapter_id,
            "participant_count": len(scene_state.participants),
            "unresolved_count": len(unresolved),
        }
    )

# MODIFY existing build_narrative ??add optional narrative_state parameter
def build_narrative(runtime: MergedRuntime, narrative_state: Optional[dict] = None) -> NarrativeSection:
    """Build Narrative section, optionally extended with NarrativeIntelligenceEngine context."""
    if not narrative_state:
        return _build_narrative_base(runtime)  # Existing logic

    lines = []
    if narrative_state.get("perspective"):
        lines.append(f"è¦–é?ï¼š{narrative_state['perspective']}")
    if narrative_state.get("voice"):
        lines.append(f"èªžæ°£ï¼š{narrative_state['voice']}")
    if narrative_state.get("tense"):
        lines.append(f"?‚åˆ¶ï¼š{narrative_state['tense']}")
    if narrative_state.get("emotional_tone"):
        lines.append(f"?…æ??ºèª¿ï¼š{narrative_state['emotional_tone']}")
    if narrative_state.get("focus"):
        lines.append(f"?˜ä??¦é?ï¼š{narrative_state['focus']}")
    if narrative_state.get("transitions"):
        lines.append(f"?´æ™¯è½‰æ?ï¼š{' ??'.join(narrative_state['transitions'][-3:])}")

    content = "\n".join(lines)
    return NarrativeSection(
        content=content,
        metadata={
            "domain": "narrative",
            "source": "narrative_intelligence",
            **narrative_state.get("metadata", {})
        }
    )

# Add to SECTION_BUILDERS and SECTION_ORDER:
SECTION_ORDER = (
    "System",
    "Character",
    "Entity Mapping",
    "Glossary",
    "Scene",
    "Narrative",
    "Style",
    "Context",      # NEW: between Style and Chunk (only rendered when enable_cross_chunk_context=True)
    "Chunk",
)

SECTION_BUILDERS["Context"] = build_context_selection
# Character, Scene, Narrative use SAME builders with optional parameters
```

---

## 4. Boundary Detection Algorithm (Conservative ??Explicit Markers Only)

```python
# core/translation_runtime/boundary_detector.py

import re
from typing import Optional, Dict, Any
from core.context_scene_memory.models import BoundaryType

CHAPTER_PATTERNS = [
    r"^?œ\s*\d+\s*?¥\b",           # ???? ??2 ??    r"^ç¬¬\s*\d+\s*ç« \b",           # ç¬?ç«?    r"^Chapter\s+\d+\b",           # Chapter 1
    r"^CHAPTER\s+\d+\b",
]

SCENE_PATTERNS = [
    r"^?œ\s*\d+\s*?ˆ\b",           # ???? ??2 ??    r"^ç¬¬\s*\d+\s*ç¯€\b",           # ç¬?ç¯€
    r"^Scene\s+\d+\b",             # Scene 1
    r"^SCENE\s+\d+\b",
    r"^\s*[*?€=]{3,}\s*$",          # ***, ---, === (horizontal rules)
]

# Heuristic patterns ??for UNKNOWN_TRANSITION only, NOT for SCENE_TRANSITION
LOCATION_SHIFT_PATTERNS = [
    r"(?„ì°©|?„ì°©?ˆë‹¤|?„ì°©?´|?„ì°©??",      # Arrival
    r"(?´ë?|?´ë??ˆë‹¤|?´ë??´|?´ë???",      # Movement
    r"(?ˆë??´\s+?¥ì?|?¤ë¥¸\s+?¥ì?|?¥ì?\s*ë³€ê²?",
    r"(?„ê?|ê±°ì‹¤|ì¹¨ì‹¤|ì£¼ë°©|?¥ì?|ì§€?˜|?¬ë¬´?¤|?™ê?|ë³‘ì?|ê³µì?|?­|ê³µí•­)",
]

TIME_SHIFT_PATTERNS = [
    r"(?„ì¹¨|?¤ì?|?•ì˜¤|?¤í?|?€?|ë°¤|?ˆë²½|?œë°¤ì¤?",
    r"(\d{1,2}\s*?œ\s*\d{0,2}\s*ë¶?",     # 7?? 7??30ë¶?    r"(?œê??´\s*ì§€?˜|?œê??´\s*?ë¥´|ë©°ì?\s*?„|ëª‡\s*?œê?\s*??",
]

SPEAKER_CHANGE_PATTERN = re.compile(r"^\s*[?Œã€Ž\"]")  # Dialogue start

def detect_boundary(prev_chunk: str, curr_chunk: str) -> BoundaryResult:
    """
    Detect scene/chapter boundary between two consecutive chunks.

    CONSERVATIVE RULE:
    - Only EXPLICIT markers (CHAPTER_PATTERNS, SCENE_PATTERNS) produce
      CHAPTER_TRANSITION / SCENE_TRANSITION with scene_id/chapter_id.
    - All heuristics (location/time/speaker) return UNKNOWN_TRANSITION.
    - Default: SAME_SCENE.
    """
    curr_stripped = curr_chunk.lstrip()

    # 1. Chapter markers (highest priority) ??EXPLICIT ONLY
    for pattern in CHAPTER_PATTERNS:
        if re.search(pattern, curr_stripped, re.MULTILINE):
            chapter_num = _extract_number(curr_stripped, pattern)
            return BoundaryResult(
                type=BoundaryType.CHAPTER_TRANSITION,
                chapter_id=f"chapter_{chapter_num}",
                scene_id=f"scene_{chapter_num}_1",
                confidence=0.95,
                metadata={"marker": "chapter", "pattern": pattern}
            )

    # 2. Scene markers ??EXPLICIT ONLY
    for pattern in SCENE_PATTERNS:
        if re.search(pattern, curr_stripped, re.MULTILINE):
            scene_num = _extract_number(curr_stripped, pattern)
            return BoundaryResult(
                type=BoundaryType.SCENE_TRANSITION,
                scene_id=f"scene_{scene_num}",
                confidence=0.9,
                metadata={"marker": "scene", "pattern": pattern}
            )

    # 3. Heuristics ??return UNKNOWN_TRANSITION (conservative)
    # Location shift
    for pattern in LOCATION_SHIFT_PATTERNS:
        if re.search(pattern, curr_chunk):
            if _location_changed(prev_chunk, curr_chunk):
                return BoundaryResult(
                    type=BoundaryType.UNKNOWN_TRANSITION,
                    scene_id=None,  # NO auto-generated scene_id
                    confidence=0.4,
                    metadata={"marker": "location_shift", "pattern": pattern}
                )

    # Time shift + paragraph break
    for pattern in TIME_SHIFT_PATTERNS:
        if re.search(pattern, curr_chunk):
            if _paragraph_break(prev_chunk, curr_chunk):
                return BoundaryResult(
                    type=BoundaryType.UNKNOWN_TRANSITION,
                    scene_id=None,  # NO auto-generated scene_id
                    confidence=0.3,
                    metadata={"marker": "time_shift", "pattern": pattern}
                )

    # Speaker change at paragraph boundary
    if SPEAKER_CHANGE_PATTERN.search(curr_stripped[:50]):
        if _paragraph_break(prev_chunk, curr_chunk):
            return BoundaryResult(
                type=BoundaryType.UNKNOWN_TRANSITION,
                scene_id=None,  # NO auto-generated scene_id
                confidence=0.2,
                metadata={"marker": "speaker_change"}
            )

    # 4. Conservative default
    return BoundaryResult(
        type=BoundaryType.SAME_SCENE,
        confidence=1.0,
        metadata={"marker": "none"}
    )

def _extract_number(text: str, pattern: str) -> int:
    match = re.search(r"\d+", text)
    return int(match.group()) if match else 1

def _location_changed(prev: str, curr: str) -> bool:
    # Simple heuristic: different location keywords
    prev_locs = set(re.findall(r"(?„ê?|ê±°ì‹¤|ì¹¨ì‹¤|ì£¼ë°©|?¥ì?|ì§€?˜|?¬ë¬´?¤|?™ê?|ë³‘ì?|ê³µì?|?­|ê³µí•­)", prev))
    curr_locs = set(re.findall(r"(?„ê?|ê±°ì‹¤|ì¹¨ì‹¤|ì£¼ë°©|?¥ì?|ì§€?˜|?¬ë¬´?¤|?™ê?|ë³‘ì?|ê³µì?|?­|ê³µí•­)", curr))
    return bool(curr_locs - prev_locs)

def _paragraph_break(prev: str, curr: str) -> bool:
    return prev.rstrip().endswith("\n\n") or curr.startswith("\n\n")

# REMOVED: _generate_scene_id() ??NO auto scene ID generation from chunk hash
# Scene IDs ONLY come from explicit markers via transition_scene()/transition_chapter()
```

---

## 5. Integration Points (Exact File Edits)

### 5.1 `lts/txt_translation_runtime.py` ??Chunk Loop (Feature-Gated)

```python
# In _translate_txt_with_runtime_pipeline(), REPLACE the chunk loop (lines ~649-833)

# NEW IMPORTS at top of function:
from core.translation_runtime.boundary_detector import detect_boundary, BoundaryResult
from core.context_scene_memory.scene_state import transition_scene, transition_chapter
from core.context_scene_memory.context_selection import select_context_for_translation
from core.intelligence.narrative_engine import NarrativeIntelligenceEngine
from core.prompt_runtime.builder import PromptBuilder
from core.runtime_orchestrator.manager import RuntimeOrchestrator

# INITIALIZATION before loop:
narrative_engine = NarrativeIntelligenceEngine()
current_scene_id = "scene_1"
current_chapter_id = "chapter_1"
prev_chunk_text = ""
active_character_ids = ()  # Could be derived from character_selector

# RM-8.2 FEATURE FLAG ??from TxtTranslationOptions.quality_context_scene_v72
enable_cross_chunk_context = getattr(options, "quality_context_scene_v72", False)

for idx, chunk in enumerate(chunks, start=1):
    # 1. BOUNDARY DETECTION
    boundary: BoundaryResult = detect_boundary(prev_chunk_text, chunk)

    # 2. SCENE/CHAPTER TRANSITION
    if boundary.type != BoundaryType.SAME_SCENE:
        if boundary.type == BoundaryType.CHAPTER_TRANSITION:
            transition_chapter(
                store=context_store,  # Need access to ContextMemoryStore
                from_scene_id=current_scene_id,
                to_scene_id=boundary.scene_id or f"scene_{idx}",
                to_chapter_id=boundary.chapter_id,
                evidence=create_evidence_from_chunk(chunk),
            )
            current_chapter_id = boundary.chapter_id
        elif boundary.type == BoundaryType.SCENE_TRANSITION:
            transition_scene(
                store=context_store,
                from_scene_id=current_scene_id,
                boundary=boundary.type,
                to_scene_id=boundary.scene_id,
                evidence=create_evidence_from_chunk(chunk),
            )
        # UNKNOWN_TRANSITION: no transition, no expiry (conservative)
        current_scene_id = boundary.scene_id or current_scene_id

    # 3. CONTEXT SELECTION
    selection = select_context_for_translation(
        context_store=context_store,
        chapter_id=current_chapter_id,
        scene_id=current_scene_id,
        sequence_index=idx,
        character_ids=active_character_ids,
        token_budget=512,
        character_token_budget=256,
    )

    # 4. NARRATIVE STATE
    prev_translation = translated_chunks[-1] if translated_chunks else ""
    narrative_engine.analyze_chunk(source=chunk, translation=prev_translation)
    narrative_context = narrative_engine.get_context_for_prompt()

    # 5. ENTITY INJECTION (RM-7.2) - optional, None if not available
    entity_injection_set = None
    # if entity_resolver_available:
    #     entity_injection_set = entity_resolver.resolve(chunk)

    # 6. PROMPT ASSEMBLY (via orchestrator with extended metadata)
    # Compose context_state metadata (NO new dataclass)
    context_state_metadata = {
        "context_selection_fingerprint": selection.fingerprint,
        "scene_id": current_scene_id,
        "scene_version": context_store.get_scene(current_scene_id).scene_version,
        "narrative": narrative_context,
        "boundary": boundary.to_dict(),
        "selected_context_ids": tuple(r.item_id for r in selection.selected_records),
    } if enable_cross_chunk_context else None

    execution_result = orchestrator.execute(
        chunk_text=chunk,
        session_id=session_id,
        snapshot_id=snapshot_id,
        current_chunk=idx,
        total_chunks=len(chunks),
        metadata={
            "context_state": context_state_metadata,
            "entity_injection_set": entity_injection_set,
            "context_selection": selection if enable_cross_chunk_context else None,
            "scene_state": context_store.get_scene(current_scene_id) if enable_cross_chunk_context else None,
            "narrative_state": narrative_context if enable_cross_chunk_context else None,
            "enable_cross_chunk_context": enable_cross_chunk_context,
        },
    )

    # ... rest of loop unchanged ...

    prev_chunk_text = chunk
```

### 5.2 `core/runtime_orchestrator/manager.py` ??Execute Method (Feature-Gated)

```python
# In RuntimeOrchestrator.execute(), MODIFY to accept extended metadata

def execute(
    self,
    chunk_text: str = "",
    session_id: str = "",
    snapshot_id: str = "",
    current_chunk: int = 0,
    total_chunks: int = 0,
    metadata: Optional[Dict[str, Any]] = None,
    engine_kwargs: Optional[Dict[str, Any]] = None,
) -> RuntimeExecutionResult:
    metadata = dict(metadata or {})
    engine_kwargs = dict(engine_kwargs or {})

    # Extract RM-8.2 extensions (feature-gated)
    enable_cross_chunk_context = metadata.pop("enable_cross_chunk_context", False)
    context_selection = metadata.pop("context_selection", None) if enable_cross_chunk_context else None
    scene_state = metadata.pop("scene_state", None) if enable_cross_chunk_context else None
    narrative_state = metadata.pop("narrative_state", None) if enable_cross_chunk_context else None
    entity_injection_set = metadata.pop("entity_injection_set", None)

    # ... existing code ...

    # 2. Prompt Builder ??PromptAssembly (EXTENDED when enabled)
    builder = PromptBuilder(
        chunk_text=chunk_text,
        entity_injection_set=entity_injection_set,
        context_selection=context_selection,
        scene_state=scene_state,
        narrative_state=narrative_state,
        enable_cross_chunk_context=enable_cross_chunk_context,
    )
    assembly = builder.build(merged)

    # ... rest unchanged ...
```

### 5.3 `core/runtime_checkpoint/manager.py` ??Checkpoint Context Store + Narrative State

```python
# In RuntimeCheckpointManager.create_checkpoint(), ADD context_store + narrative_state snapshot

def create_checkpoint(
    self,
    session_id: str,
    chunk_index: int,
    progress: ProgressState,
    metadata: Optional[Dict[str, Any]] = None,
) -> RuntimeCheckpoint:
    metadata = dict(metadata or {})

    # NEW: Capture ContextMemoryStore snapshot if present
    context_store = metadata.get("_context_store")
    if context_store is not None:
        metadata["context_store_snapshot"] = context_store.snapshot()

    # NEW: Capture NarrativeIntelligenceEngine state if present
    narrative_engine = metadata.get("_narrative_engine")
    if narrative_engine is not None:
        metadata["narrative_state_snapshot"] = narrative_engine.state.to_dict()

    # NEW: Capture current scene/chapter IDs and prev_chunk_text for boundary detection continuity
    metadata["current_scene_id"] = metadata.get("current_scene_id")
    metadata["current_chapter_id"] = metadata.get("current_chapter_id")
    metadata["prev_chunk_text"] = metadata.get("prev_chunk_text")

    # ... existing checkpoint creation ...
```

```python
# In RuntimeCheckpointManager.restore(), ADD context_store + narrative_state restore

def restore_checkpoint(self, session_id: str, checkpoint_id: str) -> Optional[Dict[str, Any]]:
    checkpoint = self.latest_checkpoint(session_id)
    if checkpoint is None:
        return None

    # NEW: Restore ContextMemoryStore if snapshot present
    snapshot_data = checkpoint.metadata.get("context_store_snapshot")
    if snapshot_data:
        metadata["_restored_context_store"] = snapshot_data

    # NEW: Restore NarrativeIntelligenceEngine state if snapshot present
    narrative_snapshot = checkpoint.metadata.get("narrative_state_snapshot")
    if narrative_snapshot:
        metadata["_restored_narrative_state"] = narrative_snapshot

    # NEW: Restore scene/chapter IDs and prev_chunk_text
    metadata["_restored_current_scene_id"] = checkpoint.metadata.get("current_scene_id")
    metadata["_restored_current_chapter_id"] = checkpoint.metadata.get("current_chapter_id")
    metadata["_restored_prev_chunk_text"] = checkpoint.metadata.get("prev_chunk_text")

    return {
        "checkpoint_id": checkpoint.checkpoint_id,
        "session_id": checkpoint.session_id,
        "snapshot_id": checkpoint.snapshot_id,
        "chunk_index": checkpoint.chunk_index,
        "progress": {...},
        "_restored_context_store": snapshot_data,
        "_restored_narrative_state": narrative_snapshot,
        "_restored_current_scene_id": checkpoint.metadata.get("current_scene_id"),
        "_restored_current_chapter_id": checkpoint.metadata.get("current_chapter_id"),
        "_restored_prev_chunk_text": checkpoint.metadata.get("prev_chunk_text"),
    }
```

### 5.4 `core/translation_runtime/models.py` ??TranslationRequest Metadata Schema Documentation

```python
# ADD to core/translation_runtime/models.py ??DOCUMENTATION ONLY, no new class

# TranslationRequest.metadata schema extended with:
# "context_state": {
#     "context_selection_fingerprint": str,      # From ContextSelectionResult.fingerprint
#     "scene_id": str,                           # Current scene_id
#     "scene_version": int,                      # SceneMemoryRecord.scene_version
#     "narrative": dict,                         # NarrativeIntelligenceEngine.get_context_for_prompt()
#     "boundary": dict,                          # BoundaryResult.to_dict()
#     "selected_context_ids": list[str],         # For audit trail
# }

# This is a composed dict, not a new dataclass. Assembled in txt_translation_runtime.py chunk loop.
```

---

## 6. Checkpoint/Resume Protocol

### 6.1 Checkpoint Payload (Extended)

```json
{
  "checkpoint_id": "chk_abc123",
  "session_id": "sess_xyz789",
  "snapshot_id": "snap_001",
  "chunk_index": 5,
  "progress": {
    "current_chunk": 5,
    "completed_chunks": 5,
    "total_chunks": 20,
    "status": "ACTIVE"
  },
  "metadata": {
    "context_state": { ... },
    "context_store_snapshot": {
      "schema_version": "1.0",
      "contexts": [...],
      "scenes": [...],
      "context_history": {...},
      "scene_history": {...},
      "conflicts": {...},
      "snapshot_version": 42
    },
    "narrative_state_snapshot": {
      "last_perspective": "third_person_limited",
      "last_voice": "formal",
      "last_tense": "past",
      "last_emotional_tone": "tense",
      "scene_history": ["scene_1", "scene_2"],
      "counters": {"scene_transitions": 1}
    },
    "current_scene_id": "scene_2",
    "current_chapter_id": "chapter_1",
    "prev_chunk_text": "...last 500 chars of chunk 5...",
    "_context_store": "<reference to in-memory store>",
    "_narrative_engine": "<reference to in-memory engine>"
  },
  "state_hash": "sha256...",
  "created_at": "2026-08-10T03:00:00Z"
}
```

### 6.2 Resume Flow

```
Resuming session at chunk 6:
1. Load checkpoint ??get context_store_snapshot, narrative_state_snapshot, current_scene_id, current_chapter_id, prev_chunk_text
2. Restore ContextMemoryStore from snapshot
3. Restore NarrativeIntelligenceEngine state from narrative_state_snapshot
4. Restore current_scene_id, current_chapter_id, prev_chunk_text
5. Continue chunk loop from chunk 6 with restored store and state
6. Boundary detection uses restored prev_chunk_text from chunk 5
```

### 6.3 NarrativeIntelligenceEngine Persistence (Existing, Already Has to_dict/from_dict)

```python
# core/intelligence/narrative_state.py ??ALREADY EXISTS (from Stage 16.2)
# Verify existing NarrativeState has to_dict()/from_dict() for checkpoint/restore

@dataclass
class NarrativeState:
    last_perspective: str = "unknown"
    last_voice: str = "neutral"
    last_tense: str = "undetermined"
    last_emotional_tone: str = "neutral"
    scene_history: List[str] = field(default_factory=list)
    counters: Dict[str, int] = field(default_factory=dict)

    # For checkpoint/restore ??VERIFY these exist
    def to_dict(self) -> dict:
        return {
            "last_perspective": self.last_perspective,
            "last_voice": self.last_voice,
            "last_tense": self.last_tense,
            "last_emotional_tone": self.last_emotional_tone,
            "scene_history": self.scene_history,
            "counters": self.counters,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "NarrativeState":
        state = cls()
        state.last_perspective = data.get("last_perspective", "unknown")
        state.last_voice = data.get("last_voice", "neutral")
        state.last_tense = data.get("last_tense", "undetermined")
        state.last_emotional_tone = data.get("last_emotional_tone", "neutral")
        state.scene_history = data.get("scene_history", [])
        state.counters = data.get("counters", {})
        return state
```

---

## 7. Prompt Injection Policy (Enforced)

### 7.1 Allowed Sections & Fields

| Section | Allowed Content | Token Budget |
|---------|-----------------|--------------|
| System | Static role definition | Fixed |
| Character | Profiles + selected memories | ??512 |
| Entity Mapping | RM-7.2 resolved entities | ??256 |
| Glossary | Matched terms only | ??256 |
| Scene | Live state + participants + unresolved refs | ??256 |
| Narrative | Intelligence summary only | ??256 |
| Style | Rules + examples | ??256 |
| **Context** (NEW) | Selected context records | ??512 |
| Chunk | Source text only | Variable |

### 7.2 Forbidden (Never in Prompt)

- Raw evidence arrays (evidence_id, source_case_id, hashes, rule_ids)
- Confidence scores, approval_status, version, expiry_policy
- SceneMemoryRecord.evidence, scene_version, status
- UnresolvedReference.candidate_targets, evidence, confidence
- NarrativeState.counters, raw scene_history
- Provider metadata (prompt_hash, token_count, snapshot_id)
- Resume state internals (SHA256, chunk status)

**Enforcement**: Only `PromptBuilder.build()` and `core/prompt_runtime/sections.py` builders construct prompts. No other code path.

---

## 8. Acceptance Test Specification

### 8.1 Test Matrix (7 Required Scenarios)

| Scenario | Description | Verification |
|----------|-------------|--------------|
| **same-scene** | Continuous chunks within same scene | Context accumulates; scene_version stable; fingerprint evolves |
| **scene-break** | Explicit scene marker (`***`, `???ˆ`) | `transition_scene()` called; SCENE_SCOPE contexts expired; new scene_id |
| **chapter-break** | Explicit chapter marker (`???¥`) | `transition_chapter()` called; SCENE_SCOPE + CHAPTER_SCOPE expired; new chapter_id |
| **unknown-boundary** | Heuristic detection (location/time shift) | `UNKNOWN_TRANSITION` or `SCENE_TRANSITION` with confidence < 0.7; conservative expiry |
| **checkpoint/resume** | Stop at chunk N, resume | ContextMemoryStore restored; narrative state restored; prompt hashes match |
| **chunk-crosses-scene** | Single chunk contains scene boundary | Boundary recorded in metadata; NO re-chunking; transition applied before NEXT chunk |
| **scene-crosses-chunks** | Scene spans 3+ chunks | scene_id stable across chunks; context accumulates; participants persist |

### 8.2 Golden Master Test

```python
# tests/acceptance/rm8_context_propagation_test.py

import pytest
from core.translation_runtime import TranslationRuntime
from lts.txt_translation_runtime import TxtTranslationOptions
from pathlib import Path

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "rm8"

@pytest.fixture
def runtime():
    return TranslationRuntime()

@pytest.fixture
def options():
    return TxtTranslationOptions(
        input_path=FIXTURE_DIR / "chapter1.txt",
        output_dir=FIXTURE_DIR / "output",
        chunk_size=1000,
        model="test-model",
        quality_profile="novel",
        resume=True,
        dry_run=False,
        quality_context_scene_v72=True,  # Enable RM-8.2 for test
    )

def test_deterministic_prompt_hashes(runtime, options):
    """Two consecutive runs produce identical prompt hashes per chunk."""
    result1 = runtime.translate_txt(options)
    result2 = runtime.translate_txt(options)

    hashes1 = [r["prompt_hash"] for r in result1["records"] if r["status"] == "success"]
    hashes2 = [r["prompt_hash"] for r in result2["records"] if r["status"] == "success"]

    assert hashes1 == hashes2, "Prompt hashes must be deterministic across runs"

def test_context_fingerprint_continuity(runtime, options):
    """Context selection fingerprint evolves deterministically."""
    result = runtime.translate_txt(options)

    for i in range(1, len(result["records"])):
        ctx_i = result["records"][i]["metadata"]["context_state"]
        ctx_i_1 = result["records"][i-1]["metadata"]["context_state"]

        # Same scene ??fingerprint should incorporate previous
        if ctx_i["boundary"]["type"] == "same_scene":
            assert ctx_i["scene_id"] == ctx_i_1["scene_id"]
            assert ctx_i["scene_version"] == ctx_i_1["scene_version"]
        # Scene transition ??version must advance
        elif ctx_i["boundary"]["type"] in {"scene_transition", "chapter_transition"}:
            assert ctx_i["scene_version"] > ctx_i_1["scene_version"]

def test_scene_transition_expires_context(runtime, options):
    """SCENE_SCOPE contexts expire at scene boundary."""
    result = runtime.translate_txt(options)

    # Find scene transition chunk
    for i, record in enumerate(result["records"]):
        boundary = record["metadata"]["context_state"]["boundary"]
        if boundary["type"] == "scene_transition":
            # Next chunk's context selection should not include expired records
            next_ctx = result["records"][i+1]["metadata"]["context_state"]
            # Verify via fingerprint difference
            assert next_ctx["context_selection_fingerprint"] != record["metadata"]["context_state"]["context_selection_fingerprint"]

def test_resume_restores_context_store(runtime, options):
    """Resume from checkpoint restores ContextMemoryStore + NarrativeState."""
    # Run to chunk 3
    options.max_chunks = 3  # Hypothetical option for test
    result1 = runtime.translate_txt(options)
    checkpoint_path = result1["records"][2]["checkpoint_id"]

    # Resume
    options.resume_from_checkpoint = checkpoint_path
    result2 = runtime.translate_txt(options)

    # Context store state should match
    assert result2["records"][3]["metadata"]["context_state"]["context_selection_fingerprint"] == \
           result1["records"][3]["metadata"]["context_state"]["context_selection_fingerprint"]

# ADVISORY: Reader-outcome continuity tests (recommended)
def test_pronoun_resolution_across_chunks(runtime, options):
    """Pronouns (ä»?å¥????™è£¡/??£¡) resolve correctly across chunk boundaries."""
    result = runtime.translate_txt(options)
    # Verify pronoun consistency in translations across chunks
    # This requires fixture with known pronoun references
    pass  # Implement when fixture has pronoun test cases

def test_dialogue_speaker_continuity(runtime, options):
    """Dialogue speaker attribution consistent across chunks."""
    result = runtime.translate_txt(options)
    # Verify speaker IDs don't flip incorrectly at chunk boundaries
    pass  # Implement when fixture has dialogue continuity cases

def test_narrative_pov_stability(runtime, options):
    """Narrative POV (third/first person) stable across chunks."""
    result = runtime.translate_txt(options)
    # Verify narrative_context["perspective"] consistent within scene
    pass  # Implement when fixture has POV test cases
```

### 8.3 Fixture: `tests/acceptance/fixtures/rm8/chapter1.txt`

Korean text with:
- Chunk 1-2: Scene 1 (same scene)
- Chunk 3: Scene break marker (`***`)
- Chunk 4-5: Scene 2 (same scene)
- Chunk 6: Chapter break marker (`???¥`)
- Chunk 7-8: Chapter 2, Scene 1
- Chunk 9: Location shift heuristic (no explicit marker)
- Chunk 10: End

---

## 9. File Edit Summary

| File | Priority | Changes |
|------|----------|---------|
| `lts/txt_translation_runtime.py` | P0 | Chunk loop: boundary detection, transition, context selection, narrative engine, **feature-gated** extended metadata |
| `core/runtime_orchestrator/manager.py` | P0 | `execute()`: accept `context_selection`, `scene_state`, `narrative_state`, `entity_injection_set`, `enable_cross_chunk_context`; pass to `PromptBuilder` |
| `core/prompt_runtime/builder.py` | P0 | `PromptBuilder.__init__`: add `context_selection`, `scene_state`, `narrative_state`, **`enable_cross_chunk_context`**; `build()`: parameterize existing builders, conditional Context section |
| `core/prompt_runtime/sections.py` | P0 | **ADD** `build_context_selection`; **MODIFY** `build_character`, `build_scene`, `build_narrative` with optional params; update `SECTION_ORDER` |
| `core/translation_runtime/boundary_detector.py` | P0 | **NEW FILE**: `detect_boundary()`, `BoundaryResult` ??**conservative, explicit markers only** |
| `core/runtime_checkpoint/manager.py` | P1 | `create_checkpoint()`: snapshot `ContextMemoryStore` + `NarrativeState` + scene/chapter IDs + prev_chunk_text; `restore_checkpoint()`: restore all |
| `core/translation_runtime/models.py` | P1 | **DOCUMENTATION ONLY** ??extend `TranslationRequest.metadata` schema for `context_state` composed dict |
| `core/intelligence/narrative_state.py` | P1 | **VERIFY** existing `to_dict()`/`from_dict()` for `NarrativeState` (Stage 16.2) |
| `tests/acceptance/rm8_context_propagation_test.py` | P2 | **NEW FILE**: Golden master + 7 scenario tests |
| `tests/acceptance/fixtures/rm8/chapter1.txt` | P2 | **NEW FILE**: Test fixture with all boundary types |

---

## 10. Rollout Plan

| Phase | Action | Validation |
|-------|--------|------------|
| **Phase 1** | Implement `boundary_detector.py` + unit tests | `pytest tests/unit/translation_runtime/test_boundary_detector.py` |
| **Phase 2** | Extend `PromptBuilder` + section builders | `pytest tests/unit/prompt_runtime/test_builder.py` |
| **Phase 3** | Wire into `txt_translation_runtime.py` chunk loop | Manual run on fixture; verify prompt hashes |
| **Phase 4** | Checkpoint `ContextMemoryStore` | `pytest tests/unit/runtime_checkpoint/test_context_store_checkpoint.py` |
| **Phase 5** | NarrativeEngine integration + persistence | `pytest tests/unit/intelligence/test_narrative_persistence.py` |
| **Phase 6** | Full acceptance test suite | `pytest tests/acceptance/rm8_context_propagation_test.py -v` |
| **Phase 7** | RM-8.2 Specification review ??**then commit** | All tests pass; no production behavior regression |

---

## 11. Compliance Checklist (Core Principles)

| Principle | Addressed By |
|-----------|--------------|
| 1. No Production Chunking modification | `split_text()` untouched; boundary detection is metadata only |
| 2. Chunk = execution unit | Loop unchanged; orchestration per-chunk |
| 3. Scene/Chapter ??Chunk | Boundary detection never re-chunks |
| 4. Metadata on existing chunks | `BoundaryResult`, composed `context_state` dict attached per chunk |
| 5. Boundary uses listed | Context continuity, transition, selection, injection, QA |
| 6. Scene across chunks | `scene_id` stable until explicit transition |
| 7. Chunk crosses boundary | Recorded in metadata; next chunk handles transition |
| 8. Document structure for RM-8.3 | `scene_id`, `chapter_id` available for future TOC/index |
| 9. No reverse chunking modification | Boundary detector reads chunks, never modifies them |
| 10. Data flow implemented | Spec Â§2 matches principle diagram |
| 11. No second chunking engine | **Enforced**: `_generate_scene_id()` removed; heuristics ??`UNKNOWN_TRANSITION` |
| 12. No RM-7 modification | Entity injection optional, read-only |
| 13. No new provider requests | Same `orchestrator.execute()` ??`engine.translate_package_from_request()` |
| 14. Checkpoint/resume preserves context | `context_store_snapshot` + `narrative_state_snapshot` + scene/chapter IDs + prev_chunk_text in checkpoint |
| 15. 7 acceptance scenarios | Â§8.1 test matrix covers all |
| 16. Feature-gated (NEW) | `enable_cross_chunk_context` default OFF; existing prompts unchanged when disabled |
| 17. Conservative boundary (NEW) | Only explicit markers ??`SCENE/CHAPTER_TRANSITION`; heuristics ??`UNKNOWN_TRANSITION` |

---

**End of Specification**
**Status**: Post-Conditional-Pass revisions applied (2026-08-10)
**Next**: Re-review ??CLEAR ??Phase 1 Implementation
