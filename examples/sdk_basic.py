from sdk import NTPEClient

client = NTPEClient(translator=lambda segment, ctx: {"translation": f"translated:{segment}"})
result = client.translate_text("sample")
print(result.text)
