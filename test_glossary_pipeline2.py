"""Test glossary data pipeline compatibility v2."""
import sys
sys.path.insert(0, 'd:/Python/NTPE')

import re

# Debug the _contains logic directly
source = "UNHRDO"
text = "UNHRDO"

print(f"source = '{source}'")
print(f"text = '{text}'")
print(f"re.fullmatch(r'[A-Za-z0-9_\\-]+', source) = {re.fullmatch(r'[A-Za-z0-9_\\-]+', source)}")

pattern = rf"\b{re.escape(source)}\b"
print(f"pattern = '{pattern}'")
result = re.search(pattern, text)
print(f"re.search(pattern, text) = {result}")
print(f"bool(result) = {bool(result)}")

# Test the GlossarySelector
from core.prompt_builder.loader import PromptBuilderLoader
from core.prompt_builder.glossary_selector import GlossarySelector

loader = PromptBuilderLoader('d:/Python/NTPE')
data = loader.load_all()
glossary = data['glossary']

print(f"\nglossary type: {type(glossary)}")
print(f"glossary keys: {list(glossary.keys())}")
for k, v in glossary.items():
    print(f"  key='{k}' (repr={repr(k)}), value type={type(v)}")

selector = GlossarySelector(glossary)
print(f"\nselector.glossary type: {type(selector.glossary)}")
print(f"selector.glossary keys: {list(selector.glossary.keys())}")
for k, v in selector.glossary.items():
    print(f"  key='{k}' (repr={repr(k)}), value type={type(v)}")

# Check what _contains does
print("\n=== selector._contains ===")
for term in selector.glossary:
    print(f"  Calling _contains(text='UNHRDO', source='{term}')")
    result = selector._contains('UNHRDO', term)
    print(f"    result = {result}")

# Manual trace
print("\n=== Manual _contains trace ===")
test_text = 'UNHRDO'
test_source = 'UNHRDO'
print(f"test_text = '{test_text}'")
print(f"test_source = '{test_source}'")
print(f"not test_source = {not test_source}")
print(f"re.fullmatch(r'[A-Za-z0-9_\\-]+', test_source) = {re.fullmatch(r'[A-Za-z0-9_\\-]+', test_source)}")
if re.fullmatch(r'[A-Za-z0-9_\\-]+', test_source):
    pattern = rf"\b{re.escape(test_source)}\b"
    print(f"pattern = '{pattern}'")
    match = re.search(pattern, test_text)
    print(f"re.search(pattern, test_text) = {match}")
    print(f"is not None = {match is not None}")