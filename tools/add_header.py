# Add header docstring
with open("D:/Python/NTPE/core/knowledge/compatibility/provider.py", "r", encoding="utf-8") as f:
    content = f.read()

header = '"""\\nRM-5.7.5 Knowledge Package Provider.\\n\\nREAD-ONLY provider for Translation Runtime.\\nThis is the ONLY interface Runtime may use to access Knowledge Packages.\\n\\nPROHIBITED for Runtime:\\n- Extractor (core.knowledge_generation)\\n- Compiler (core.knowledge_compilation)\\n- Review Engine (core.knowledge_review)\\n- Validator (core.knowledge_validation)\\n- Any generation pipeline component\\n"""\\n\\n'

content = header + content

with open("D:/Python/NTPE/core/knowledge/compatibility/provider.py", "w", encoding="utf-8") as f:
    f.write(content)

print("Header added")