"""Test glossary data pipeline compatibility v3."""
import sys
sys.path.insert(0, 'd:/Python/NTPE')

import re

# Test the GlossarySelector directly
from core.prompt_builder.glossary_selector import GlossarySelector

g = {'UNHRDO': {}}
s = GlossarySelector(g)

print("=== Direct test ===")
result = s._contains('UNHRDO', 'UNHRDO')
print(f"_contains('UNHRDO', 'UNHRDO') = {result}")

print("\n=== Manual trace ===")
test_text = 'UNHRDO'
test_source = 'UNHRDO'
print(f"not test_source = {not test_source}")
import re
print(f"re.fullmatch = {re.fullmatch(r'[A-Za-z0-9_\\-]+', test_source)}")
if re.fullmatch(r'[A-Za-z0-9_\\-]+', test_source):
    pattern = rf"\b{re.escape(test_source)}\b"
    print(f"pattern = '{pattern}'")
    match = re.search(pattern, test_text)
    print(f"re.search = {match}")
    print(f"is not None = {match is not None}")

print("\n=== select() test ===")
matches = s.select("UNHRDO")
print(f"matches = {matches}")

matches2 = s.select("The UNHRDO organization")
print(f"matches2 = {matches2}")