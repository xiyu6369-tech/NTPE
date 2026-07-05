NTPE 1.1 LTS Stage-03: Glossary / Character Memory Strengthening

This stage keeps NTPE 1.0 Stable and LTS Stage-01/02 command compatibility.

New optional arguments:

python ntpe_translate_txt.py input\小說.txt output --glossary glossary.txt --character-memory memory\character_memory_lts.json

Supported glossary formats:
- source=target
- source->target
- source → target

Behavior:
- Merges root glossary_override.json, character_override.json, glossary.txt, custom glossary, and character memory.
- Injects matched terms into prompt packages.
- Applies strict source-term normalization to translated chunks/final output.
- Persists matched terms to character memory after successful non-dry-run translation.
