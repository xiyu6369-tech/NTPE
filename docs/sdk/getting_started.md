# NTPE SDK Getting Started

NTPE SDK provides a stable Python interface over the frozen NTPE Foundation v1.0 runtime.

```python
from sdk import NTPEClient
client = NTPEClient(translator=lambda segment, ctx: {"translation": str(segment)})
result = client.translate_text("안녕하세요")
print(result.text)
```

Stage-07.8 adds documentation, examples, package metadata, and packaging validation without changing runtime or CLI contracts.
