"""Test glossary data pipeline compatibility."""
import sys
sys.path.insert(0, 'd:/Python/NTPE')

import re

# Debug the _contains logic directly
source = "UNHRDO"
text = "UNHRDO"

print(f"source = '{source}'")
print(f"text = '{text}'")
print(f"re.fullmatch(r'[A-Za-z0-9_\\-]+', source) = {re.fullmatch(r'[A-Za-z0-9_\-]+', source)}")

pattern = rf"\b{re.escape(source)}\b"
print(f"pattern = '{pattern}'")
result = re.search(pattern, text)
print(f"re.search(pattern, text) = {result}")
print(f"bool(result) = {bool(result)}")

# Test with spaces
text2 = "The UNHRDO organization"
result2 = re.search(pattern, text2)
print(f"re.search(pattern, '{text2}') = {result2}")

# Test without word boundary
result3 = source in text
print(f"source in text = {result3}")

# Test the GlossarySelector
from core.prompt_builder.loader import PromptBuilderLoader
from core.prompt_builder.glossary_selector import GlossarySelector

loader = PromptBuilderLoader('d:/Python/NTPE')
data = loader.load_all()
glossary = data['glossary']

selector = GlossarySelector(glossary)
print(f"\nselector.glossary keys: {list(selector.glossary.keys())}")

# Check what _contains does
for term in selector.glossary:
    result = selector._contains(text, term)
    print(f"  selector._contains('{text}', '{term}') = {result}")