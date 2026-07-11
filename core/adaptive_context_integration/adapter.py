from __future__ import annotations

from collections.abc import Mapping, Sequence
from core.adaptive_context import ContextItem

_KIND_MAP = {'character','dialogue','narrative','glossary','scene','other'}

def adapt_runtime_context(context: Mapping[str, object]) -> tuple[ContextItem, ...]:
    rows: list[ContextItem] = []
    for index, (key, value) in enumerate(context.items()):
        if value in (None, '', [], {}, ()):
            continue
        metadata: dict[str, object] = {}
        kind = _kind_for(str(key))
        required = False
        characters: tuple[str, ...] = ()
        content: str
        if isinstance(value, Mapping):
            content = str(value.get('content') or value.get('text') or _stable_text(value))
            required = bool(value.get('required', False))
            locked = bool(value.get('locked', False))
            if locked:
                required = True
            metadata = {'locked': locked, 'source_key': str(key)}
            raw_chars = value.get('characters', ())
            if isinstance(raw_chars, Sequence) and not isinstance(raw_chars, (str, bytes)):
                characters = tuple(str(x) for x in raw_chars)
        elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
            content = '\n'.join(str(x) for x in value)
        else:
            content = str(value)
        rows.append(ContextItem(
            item_id=f'{index:04d}:{key}', kind=kind, content=content,
            characters=characters, relevance=_relevance(kind), recency=0.5,
            continuity=0.8 if kind in {'dialogue','narrative','scene'} else 0.4,
            required=required, metadata=metadata,
        ))
    return tuple(rows)

def _kind_for(key: str) -> str:
    lower = key.lower()
    for kind in ('glossary','character','dialogue','narrative','scene'):
        if kind in lower or (kind == 'narrative' and 'previous' in lower):
            return kind
    return 'other'

def _relevance(kind: str) -> float:
    return {'glossary':1.0,'character':0.9,'dialogue':0.95,'narrative':0.8,'scene':0.7,'other':0.4}[kind]

def _stable_text(value: Mapping[str, object]) -> str:
    return '\n'.join(f'{k}: {value[k]}' for k in sorted(value))
