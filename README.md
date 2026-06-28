# NTPE 1.0 Beta 1 Base

這是 NTPE 1.0 Beta 的最小基礎骨架。

目前包含：

- config/
- core/
- logs/
- launcher.py

## 執行方式

```bat
cd /d D:\Python\NTPE
python launcher.py
```

第一次執行會自動確認設定並建立 logs/app.log。

## API Key

目前先不用輸入。之後 GUI 設定頁會負責寫入 config/config.json。
NTPE

Novel Translation Professional Engine

AI-powered platform for long-form novel translation

NTPE (Novel Translation Professional Engine) is a modular translation platform designed for long-form fiction. Instead of relying only on prompts, NTPE combines document preprocessing, structured knowledge, character management, glossary management, prompt generation, and automated quality assurance into a complete translation workflow.

Current Status

* Version: v0.5.0-alpha
* Status: Alpha
* Platform: Windows
* Language: Python 3.12+

⸻

Project Goals

NTPE aims to provide a professional translation pipeline for novels by focusing on:

* Publication-grade Traditional Chinese output
* Consistent character names
* Consistent terminology
* Long-context translation
* Automatic translation quality checking
* Modular architecture
* Future support for multiple AI models

⸻

Architecture

                NTPE
────────────────────────────────
Document Layer
    Document Normalizer
            │
            ▼
    Document Analyzer
────────────────────────────────
Knowledge Layer
    Character Database
    Glossary Builder
    Knowledge Base
────────────────────────────────
AI Layer
    Prompt Builder
    Translation Engine
    QA Engine
    Context Manager
────────────────────────────────
Application Layer
    GUI
    Batch Translation
    EPUB Export
    DOCX Export

⸻

Completed Modules

Document Layer

* ✅ Document Normalizer v1.0
* ✅ Document Analyzer v1.0

Knowledge Layer

* ✅ Character Memory Engine
* ✅ Glossary Builder
* ✅ Knowledge Base Builder
* ✅ Character Database v2.0

AI Foundation

* ✅ Prompt Package Specification v1.0
* ✅ Prompt Package Validator

⸻

Core Features

Character Database

* Character ID management
* Full name → Full name
* First name → First name
* Last name → Last name
* Korean names without spaces remain intact
* Alias management
* Regex-safe matching

⸻

Glossary

* Automatic glossary generation
* Locked terminology
* Manual override support
* Cross-book statistics

⸻

Knowledge Base

Unified knowledge source shared by every module.

Includes:

* Characters
* Glossary
* Alias index
* Locked dictionary
* Prompt dictionary

⸻

Prompt Package

A standardized interface shared by:

* Prompt Builder
* Translation Engine
* QA Engine
* Context Manager

⸻

Project Structure

NTPE/
├── analysis/
├── backup/
├── cache/
├── config/
├── core/
├── data/
├── engine/
├── gui/
├── input/
├── logs/
├── memory/
├── output/
├── rules/
├── tests/
├── launcher.py
├── launcher_analyzer.py
├── launcher_memory.py
├── launcher_glossary.py
├── launcher_kb.py
├── launcher_character_db.py

⸻

Development Roadmap

Phase 1 — Document Layer

* ✅ Document Normalizer
* ✅ Document Analyzer

Phase 2 — Knowledge Layer

* ✅ Character Memory
* ✅ Glossary Builder
* ✅ Knowledge Base
* ✅ Character Database

Phase 3 — AI Layer

* ✅ Prompt Package Specification
* ⏳ Prompt Builder
* ⏳ Translation Engine
* ⏳ QA Engine
* ⏳ Context Manager

Phase 4 — Application Layer

* ⏳ Professional GUI
* ⏳ Batch Translation
* ⏳ EPUB Export
* ⏳ DOCX Export

⸻

Design Principles

* Modular architecture
* Knowledge-driven translation
* AI model independent
* Consistent terminology
* Automatic quality assurance
* Resume-safe workflow
* Project-based configuration

⸻

Planned AI Workflow

Document
    │
    ▼
Normalizer
    │
    ▼
Analyzer
    │
    ▼
Knowledge Base
    │
    ▼
Character Database
    │
    ▼
Prompt Builder
    │
    ▼
Translation Engine
    │
    ▼
QA Engine
    │
PASS
    │
    ▼
Output

⸻

Requirements

* Python 3.12+
* Windows 10 / Windows 11

Install dependencies:

pip install -r requirements.txt

⸻

License

This project is currently under active development.

Copyright © NTPE Project.
