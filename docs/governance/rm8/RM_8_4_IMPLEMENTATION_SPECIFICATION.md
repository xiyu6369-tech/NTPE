# RM-8.4 — Reader Structure / Optional EPUB Packaging Layer (Revision 4.0)

這一版的核心不是再提高翻譯品質模型，也不是段落重組。**RM-8.4 Core 僅負責：建立 RM-8.3 TXT 正文 ↔ RM-8.2 chapter/scene provenance 之 deterministic chapter mapping。**

**RM-8.3 TXT 正文為 Immutable Source of Truth。RM-8.4 Core 不重新輸出、不修改、不重新整理 TXT 正文。**

目前 LCR/NTPE 的既有原則明確要求以實際讀者為中心：一般使用者應能直接匯入陌生小說，而不需要理解原文、角色名、程式或手動準備流程。
同時，專案要求品質優先、Fail Closed、Deterministic，以及歷史 Evidence 不可修改。

---

# RM-8.4 Implementation Specification (Revision 4)

## 1. Scope & Objective

### Objective

在 RM-8.3 的：

> assembled novel → polish → deterministic QC → metadata/TOC → delivery package

之後，增加一個 **Reader Structure Layer (Core)** 以及一個 **Optional EPUB Packaging Layer**：

### RM-8.4 Core (Required)

- 輸入：RM-8.3 finalized TXT (唯一正文 Source of Truth) + RM-8.2 context metadata
- 輸出：`ReaderChapterMap` (immutable, deterministic chapter boundary mapping)
- **不修改任何翻譯文字**
- **不重新翻譯、chunk、assembly、polish、canonicalize**

### Optional EPUB Packaging (使用者明確要求時才執行)

- 輸入：RM-8.3 finalized TXT (唯一正文 Source of Truth) + `ReaderChapterMap`
- 輸出：EPUB (1 chapter = 1 readable document) + TOC / Navigation
- **不修改任何翻譯文字**
- **不重新翻譯、chunk、assembly、polish、canonicalize**

### 核心原則

> **RM-8.4 Core 只做「chapter mapping」；Optional EPUB Packaging 只做「packaging」。兩者都不改變「翻譯了什麼」。**

---

# 2. Explicit Non-Goals

RM-8.4 **不得**：

- 修改 `split_text()`
- 修改 `DEFAULT_CHUNK_SIZE`
- 修改 provider request
- 修改 translation loop
- 重新翻譯任何 chunk
- 重新執行 Translation Engine
- 修改 RM-7 Entity / Knowledge / Learning pipeline
- 修改 RM-8.1 Literary Quality pipeline
- 修改 RM-8.2 Context Continuity pipeline
- 修改 RM-8.3 Polish / QC / Metadata / Delivery
- 重新組裝 translation chunks
- 以 filesystem directory 當章節來源
- 以猜測方式產生章節標題
- 使用 LLM 判斷章節
- 使用 LLM 判斷段落
- 為了「看起來像小說」而自行改寫正文
- 修改歷史 artifact
- 修改歷史 canary evidence
- 讓 EPUB/PDF 失敗阻塞 Core TXT delivery
- 建立新的 paragraph structure
- 建立新的 scene detector
- 重新 canonicalize 正文
- **EPUB 自動於每次翻譯後產生**
- **EPUB 成為 Core delivery prerequisite**
- **EPUB 自行猜測 chapter boundary**
- **EPUB 使用 AI/LLM 推測章節**
- **以 EPUB 作為 Source of Truth**

---

# 3. Architecture Boundary

```text
Input Novel
    │
    ▼
Existing Translation Runtime
    │
    ▼
RM-8.2 Context / Chunk Metadata
    │
    ▼
assembled_text
    │
    ▼
RM-8.3
    ├─ Canonicalization
    ├─ Polish
    ├─ Deterministic QC
    ├─ Metadata / TOC
    └─ Core TXT Delivery
    │
    ▼
RM-8.4 Core: Reader Structure
    ├─ Chapter Boundary Mapping (from RM-8.2 metadata + explicit markers)
    ├─ Chapter Position Mapping (start/end offsets in RM-8.3 TXT)
    └─ ReaderChapterMap (immutable, deterministic)
    │
    ▼
Core Reader Delivery (TXT unchanged + ReaderChapterMap)
    │
    ├──► (Optional) EPUB Packaging  ← 使用者明確要求時才執行
    │       └─ 1 chapter = 1 EPUB readable document
    │       └─ Navigation / Metadata
    │
    └──► (Optional) PDF Packaging   ← Truly Optional
            └─ Success → artifact; Failure → no blocking
```

### 重要 Boundary

RM-8.4 Core 的輸入**唯有**：

```text
RM-8.3 final TXT output (text content only, no metadata header)
+
existing RM-8.2 metadata (chunk_records[].metadata.context_state)
```

不是：

```text
raw source → split_text()
```

也不是：

```text
translated_chunks → re-join
```

也不是：

```text
RM-8.3 polished_text → re-polish / re-structure
```

---

# 4. Source of Truth

**明確定義：**

> **RM-8.3 Final TXT body = 唯一正文 Source of Truth。**

Reader Structure 與 Optional EPUB 都是 consumer：

```text
RM-8.3 Final TXT body
        |
        +--> ReaderChapterMap (Core)
        |
        +--> TXT delivery (RM-8.3 existing)
        |
        +--> Optional EPUB Packaging (使用者要求時)
        |
        +--> Optional PDF Packaging (Truly Optional)
```

**不得形成：**

- TXT → EPUB → TXT
- chunk_records → EPUB 重新組裝正文

---

# 5. Chapter Structure

## 5.1 Chapter Provenance (單一來源)

章節資訊**只**來自以下兩個來源，優先級固定：

### Priority 1 — RM-8.2 context_state (deterministic, 已經存在)

```text
chapter_id
scene_id
scene_version
boundary.type  (chapter_transition / scene_transition / same_scene)
```

RM-8.2 的 context metadata 已經被 RM-8.3 TOC 使用，RM-8.4 Core 直接延續。

### Priority 2 — Explicit marker in TXT (fallback only)

若 RM-8.2 metadata 缺失 `chapter_id` 或 `boundary.type`，僅掃描 TXT 尋找：

```text
第1章
第一章
第 1 章
Chapter 1
CHAPTER 1
```

**禁止**：根據文意、人物對話、場景猜測、字數、空白數量、AI inference 自行創造章節標題。

---

# 6. Chapter Position Mapping

將章節邊界映射為 **RM-8.3 TXT 正文的 character offsets**：

```text
start_position / end_position
```

- **基準**：RM-8.3 `inject_metadata_into_text()` 產出的 TXT 正文部分（不含 metadata header/TOC）
- **格式**：0-based UTF-8 code point offsets, end-exclusive
- `start_position` = 章節第一個字元在正文中的位置
- `end_position` = 章節最後一個字元的下一個位置 (= `start_position` + 章節字元長度)
- 必須 deterministic：相同輸入 → 相同 position
- 不得依賴 filesystem ordering、chunk 重組、或重新掃描正文推測

---

# 7. ReaderChapterMap (Core Output)

RM-8.4 Core 產出 `ReaderChapterMap` (immutable container)：

```text
chapters: tuple[ChapterBoundary, ...]

ChapterBoundary:
  chapter_id: str              (from RM-8.2)
  chapter_title: str           (from explicit marker 或 deterministic fallback)
  chapter_order: int           (0-based index, first appearance order)
  scene_count: int             (from RM-8.2 unique scene_ids per chapter)
  start_position: int          (RM-8.3 TXT 正文 0-based offset, inclusive)
  end_position: int            (RM-8.3 TXT 正文 0-based offset, exclusive)
  scene_ids: tuple[str, ...]   (from RM-8.2, TXT appearance order, deduped)
```

---

# 8. Optional EPUB Packaging

EPUB 正式定位：**Optional EPUB Packaging**

### 規則

1. EPUB 只有在使用者明確要求時才產生。
2. 不要求每次翻譯都產生 EPUB。
3. 不要求 Core RM-8.4 acceptance 必須存在 EPUB。
4. EPUB 不是 TXT delivery 的必要依賴。
5. EPUB 不是翻譯 pipeline 的必要步驟。
6. EPUB 產生失敗不得使 TXT、Manifest、Quality Certificate 或 Core QC acceptance 失敗。
7. EPUB 只能使用既有 RM-8.3 Final TXT body + ReaderChapterMap。
8. EPUB 不得重新翻譯、重新 chunk、重新 assembly、重新 polish。
9. EPUB 不得自行猜測 chapter boundary。
10. EPUB chapter boundary 必須完全使用 ReaderChapterMap。
11. EPUB 每章仍應輸出為獨立 readable document。
12. EPUB 的所有正文文字必須來自既有 RM-8.3 TXT body。

### 目標 (使用者要求 EPUB 時)

```text
EPUB
  ├─ metadata (title, author, translator, date, model, pipeline)
  ├─ navigation (toc.ncx + nav.xhtml)
  ├─ chapter 1 (independent readable document)
  ├─ chapter 2 (independent readable document)
  └─ ...
```

### 強制要求

1. **1 chapter = 1 EPUB readable document** (對應 ReaderChapterMap 每一章)
2. **ReaderChapterMap 驅動 chapter document slicing**：使用 `start_position` / `end_position` 從 RM-8.3 TXT 正文切分
3. **Exporter 不得** 自行重新推測 chapter boundary
4. **Exporter 不得** 將整本小說塞入單一 chapter
5. **Exporter 不得** 修改正文文字
6. 無複雜 CSS，僅基本可讀性

### 禁止

- 複雜 CSS
- 自動插入不存在的章節
- AI-generated chapter titles
- 自動改寫正文
- 依 provider output 猜 chapter
- 忽略 ReaderChapterMap position 而自行切分

---

# 9. TXT Delivery

**RM-8.4 不輸出、不修改、不重新整理 TXT。**

RM-8.3 的 TXT delivery 維持原狀（含 `inject_metadata_into_text()`）。RM-8.4 Core 僅讀取其正文部分做 chapter mapping。

---

# 10. PDF

PDF 維持：

> Truly Optional / non-blocking

與 RM-8.3 一致：

```text
PDF success
    → artifact available

PDF failure
    → core delivery still PASS
```

---

# 11. Content Preservation Invariant

**RM-8.3 TXT 正文為唯一 Source of Truth**。RM-8.4 Core 與 Optional EPUB 都不修改正文，**content preservation 由 construction 保證**：

- EPUB chapter document = `RM-8.3_TXT_body[start_position:end_position]`
- 所有章節拼接 = 完整 RM-8.3 TXT 正文
- 無新增、無刪除、無重複、無修改

驗證方式（deterministic）：

```text
join(EPUB_chapter_texts) == RM-8.3_TXT_body
```

---

# 12. Deterministic Requirement

相同：

```text
RM-8.3 TXT body
+
RM-8.2 chunk_records metadata
+
configuration
```

必須得到相同：

```text
chapter structure (boundaries, titles)
ReaderChapterMap (with positions)
EPUB structure (documents, navigation) — if generated
```

不得依賴：

- timestamp
- random UUID
- filesystem ordering
- dictionary iteration order
- network response
- model response

---

# 13. Validation Gate

### RM-8.4 Core Validation (Required for Core PASS)

#### Critical

1. `content_preservation` — `join(chapters_from_ReaderChapterMap) == RM-8.3_TXT_body`
2. `chapter_completeness` — 無遺漏章節
3. `chapter_uniqueness` — 無重複章節
4. `position_integrity` — `start_position < end_position`，連續章節 `end_position[i] == start_position[i+1]`
5. `first_chapter_starts_at_zero` — `chapters[0].start_position == 0`
6. `last_chapter_ends_at_body_length` — `chapters[-1].end_position == len(RM-8.3_TXT_body)`

#### Major

7. `toc_consistency` — TOC count == ReaderChapterMap chapter count == RM-8.2 chapter count
8. `no_text_mutation` — TXT body unchanged after mapping

#### Info

9. `deterministic_mapping` — 相同輸入 → 相同 ReaderChapterMap

**Core PASS 門檻：**

```text
All Critical PASS
AND
no critical failure
```

### Optional EPUB Validation (僅當使用者要求 EPUB 時適用)

#### Critical

1. `epub_chapter_count` == `ReaderChapterMap.chapter_count`
2. `epub_chapter_order` == `ReaderChapterMap.chapter_order`
3. `epub_chapter_boundaries` 完全來自 `ReaderChapterMap` (start_position, end_position)
4. `epub_no_overlap` — 相鄰章節無重疊
5. `epub_no_gap` — 相鄰章節無縫隙
6. `epub_first_starts_at_zero` — 第一章 start_position == 0
7. `epub_last_ends_at_body_length` — 最後一章 end_position == len(RM-8.3_TXT_body)
8. `epub_content_preservation` — `join(EPUB_chapters) == RM-8.3_TXT_body`
9. `epub_no_text_mutation` — 無文字修改
10. `epub_no_duplicate_chapter` — 無重複章節
11. `epub_no_missing_chapter` — 無遺漏章節
12. `epub_no_provider_network_request` — Provider/Network = 0

#### Major

13. `epub_structure` — 每章為獨立 document，navigation 可達

#### Info

14. `epub_availability` — PASS 或 graceful fallback (dependency missing)

**EPUB PASS 門檻：**

```text
All Critical PASS
AND
no critical failure
```

**關鍵規則：EPUB failure 不得使 Core delivery FAIL。**

---

# 14. Core / Optional Boundary

### Core (RM-8.4 Core — Required for acceptance)

```text
Chapter Boundary Mapping (from RM-8.2 + explicit markers)
+
Chapter Position Mapping (start/end offsets)
+
ReaderChapterMap (immutable, deterministic)
+
Deterministic QC (content preservation, position integrity, completeness, uniqueness)
+
No text modification
+
No provider/network/translation/retranslation/rechunk/reassembly/repolish
```

### Optional (使用者明確要求時才執行)

| Format | Classification | Requirement |
|--------|----------------|-------------|
| EPUB   | **Optional EPUB Packaging** (graceful fallback on dependency failure) | 1 chapter = 1 doc; ReaderChapterMap-driven slicing; All Critical validation PASS |
| PDF    | **Truly Optional** | Success → artifact; Failure → no blocking |

**EPUB 是 Optional EPUB Packaging，而非 Required。**

- EPUB 失敗若因 **缺少依賴** → graceful fallback (artifact 缺失但 Core PASS)
- EPUB 失敗若因 **Core Structure 錯誤** → Core FAIL (EPUB validation 不觸發 Core FAIL)
- PDF 完全 Optional，失敗從不阻塞 Core
- **Core acceptance 不要求 EPUB 存在**

---

# 15. Provider / Network Contract

RM-8.4 (Core + Optional)：

```text
Provider Requests = 0
Network Requests = 0
Translation Requests = 0
```

所有 structure generation / packaging：

```text
deterministic local processing
```

禁止：

```text
LLM chapter detection
LLM paragraph detection
LLM title generation
LLM structure repair
```

---

# 16. Historical Evidence

延續 NTPE 固定規則：

- 不修改歷史 artifact
- 不重用 historical canary root
- 不刪除 evidence
- 新 canary 使用新的 artifact root

---

# 17. CLI / API Conceptual Separation

### Core Delivery Flag

```text
--quality-delivery-v83 (or existing RM-8.3 flag)
    = Core RM-8.3 delivery (TXT + Manifest + QC Certificate)
    = RM-8.4 Core (ReaderChapterMap) included
```

### Optional EPUB Packaging Flag

```text
--export-epub
    = Optional EPUB Packaging
    = 要求：ReaderChapterMap 必須存在 (由 Core 產出)
    = 不重新執行翻譯流程
    = 失敗不阻塞 Core delivery
```

### Optional PDF Flag

```text
--export-pdf
    = Truly Optional PDF Packaging
    = 失敗不阻塞 Core delivery
```

**概念分離：**

- `quality_delivery_v83=True` → Core delivery (包含 ReaderChapterMap)
- `--export-epub` → Optional EPUB (需 Core 先完成)
- `--export-pdf` → Optional PDF (需 Core 先完成)

不得讓 `quality_delivery_v83=True` 自動代表一定要產生 EPUB。

---

# 18. Acceptance Requirements

### RM-8.4 Core DoD (Required)

| Gate | Requirement |
|---|---|
| Structure unit tests | PASS |
| ReaderChapterMap generation | PASS |
| Content preservation (`join(chapters) == TXT_body`) | PASS |
| Chapter completeness | PASS |
| Chapter uniqueness | PASS |
| Position integrity | PASS |
| First chapter starts at 0 | PASS |
| Last chapter ends at len(TXT_body) | PASS |
| No text mutation | PASS |
| Deterministic mapping | PASS |
| compileall | PASS |
| `ntpe_validate.py` | PASS / 明確既有例外 |
| `git diff --check` | PASS |
| Provider | 0 |
| Network | 0 |
| Translation | 0 |
| Historical artifacts modified | 0 |
| Commit | ChatGPT CLEAR 後才允許 |

### Optional EPUB DoD (僅當使用者要求 EPUB 時適用)

| Gate | Requirement |
|---|---|
| EPUB chapter count == ReaderChapterMap count | PASS |
| EPUB chapter order == ReaderChapterMap order | PASS |
| EPUB boundaries from ReaderChapterMap | PASS |
| No overlap | PASS |
| No gap | PASS |
| First chapter starts at 0 | PASS |
| Last chapter ends at len(TXT_body) | PASS |
| EPUB content preservation (`join(EPUB) == TXT_body`) | PASS |
| No text mutation | PASS |
| No duplicate chapter | PASS |
| No missing chapter | PASS |
| No provider/LLM/network | PASS |
| EPUB structure (1 chapter = 1 doc, nav) | PASS 或 graceful fallback |
| EPUB failure does not invalidate Core | PASS |

---

# 19. Phase Plan

## Phase 1 — Chapter Mapper / Reader Structure Core

建立：

- `ChapterBoundary` (chapter_id, title, order, scene_ids, start_pos, end_pos)
- `ReaderChapterMap` builder (input: RM-8.3 TXT body + RM-8.2 metadata → output: ReaderChapterMap)

驗證：

- immutable
- deterministic
- `join(TXT_body[cp.start_pos:cp.end_pos] for cp in map) == TXT_body`
- All Core validation gates PASS

---

## Phase 2 — Optional EPUB Packager

建立：

- `EpubPackager` (input: TXT body + ReaderChapterMap + metadata → output: .epub)

驗證：

- 每章獨立 document
- navigation 可達
- 無文字修改
- All EPUB validation gates PASS
- dependency missing → graceful fallback
- **Phase 2 不得成為 Core acceptance prerequisite**

---

## Phase 3 — Validation / Acceptance Integration

加入：

- `content_preservation` check (Core)
- `position_integrity` check (Core)
- `chapter_completeness` check (Core)
- `chapter_uniqueness` check (Core)
- EPUB validation suite (Optional)

---

## Phase 4 — Production Integration

修改 `translate_txt()` 接入 RM-8.4 Core (feature-gated `quality_delivery_v83`)。

保持：

```text
quality_delivery_v83=False
```

時：**RM-8.4 Core 完全不執行。**

Optional EPUB Packaging 由 `--export-epub` 獨立觸發。

---

# 20. 禁止事項總表 (整合)

### Core 禁止

- 重新翻譯
- 重新 chunk
- 重新 assembly
- 重新 polish
- 修改 RM-8.3 TXT
- 建立第二套正文來源
- 修改既有 RM-8.2/8.3 implementation
- Provider/Network/Translation requests

### Optional EPUB 禁止

- 成為 Core delivery prerequisite
- 自動於每次翻譯後產生
- 修改 RM-8.3 TXT
- 重新整理正文內容
- 重新 polish
- 重新 assembly
- 重新 chunk
- 重新翻譯
- 自行猜測 chapter boundary
- 使用 AI/LLM 推測章節
- 以 EPUB 作為 Source of Truth
- 忽略 ReaderChapterMap 而自行切分
- 讓 EPUB failure 阻塞 Core delivery

---

# 21. Definition of Done

RM-8.4 Core 完成條件：

1. **Chapter boundaries deterministic from RM-8.2 + explicit markers**
2. **Chapter positions = RM-8.3 TXT 正文 0-based UTF-8 offsets, end-exclusive**
3. **ReaderChapterMap immutable, deterministic, content-preserving**
4. **No text modification: `join(chapters) == RM-8.3_TXT_body`**
5. **TXT unchanged (RM-8.3 delivery untouched)**
6. **PDF truly optional, non-blocking**
7. **Provider / Network / Translation = 0**
8. **RM-7 / RM-8.1 / RM-8.2 / RM-8.3 無 scope creep**
9. **Flag OFF 完全 backward-compatible**
10. **完整 Core regression suite PASS**
11. **ChatGPT Final Acceptance CLEAR**
12. **才允許 single implementation commit**

Optional EPUB 完成條件 (使用者要求時)：

13. **EPUB: 1 chapter = 1 independent readable document**
14. **EPUB slicing driven by ReaderChapterMap positions only**
15. **EPUB content preservation: `join(EPUB_chapters) == RM-8.3_TXT_body`**
16. **EPUB failure does not invalidate Core delivery**

---

# 22. 最重要的 Scope Decision

RM-8.4 Core **不是**品質處理層，**是**Reader Structure 映射層。

> **Input: RM-8.3 TXT + RM-8.2 metadata → Output: ReaderChapterMap**

Optional EPUB Packaging **不是**翻譯層，**是**打包層。

> **Input: RM-8.3 TXT + ReaderChapterMap → Output: EPUB**

這樣既能解決「一般讀者拿到 EPUB 是否真的像小說」的問題，又完全不觸碰翻譯品質 pipeline。

**建議下一步不是立刻實作 Phase 2。**

先把上面這份作為 **`RM_8_4_IMPLEMENTATION_SPECIFICATION.md` Revision 4**，交給 Codex 做一次 **Specification Consistency Audit (Revision 4)**，只檢查：

1. Chapter boundary 是否完全依賴 RM-8.2 metadata + explicit markers（無新推測）
2. Position mapping 是否為 RM-8.3 TXT 正文 0-based UTF-8 offsets, end-exclusive
3. ReaderChapterMap 是否 immutable、deterministic、content-preserving
4. EPUB (if generated) 是否 1 chapter = 1 doc，且 slicing 由 ReaderChapterMap position 驅動
5. Content preservation 是否由 construction 保證（join(chapters) == TXT_body）
6. TXT 是否完全不被修改
7. 所有 Core acceptance criteria 是否全部可實際驗證
8. Optional EPUB acceptance 是否完整且不阻塞 Core
9. 無 scope creep 到 RM-7/8.1/8.2/8.3
10. Core acceptance 不要求 EPUB 存在

**Audit CLEAR 後才授權 Phase 1 實作 (已完成) 與 Phase 2 實作。**