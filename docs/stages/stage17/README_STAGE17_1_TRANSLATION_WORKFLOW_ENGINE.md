# NTPE 1.2 Professional - Stage-17.1 Translation Workflow Engine

Stage-17.1 introduces the production workflow layer for NTPE. It connects preparation, intelligence analysis, translation, quality checking, auto-repair, review gating, and export through a deterministic workflow pipeline.

## Public entry point

```python
from core.workflow import TranslationWorkflowEngine

engine = TranslationWorkflowEngine()
result = engine.run("source text")
```

## Default workflow

1. Prepare
2. Intelligence Analysis
3. Translate
4. Quality Check
5. Auto Repair
6. Review Gate
7. Export

## Compatibility

This stage adds `core.workflow` and does not modify frozen Provider Framework, Translation Quality Engine, or Advanced Translation Intelligence APIs.
