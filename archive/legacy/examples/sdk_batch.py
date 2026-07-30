from sdk import SDKBatchAPI, BatchRequest, BatchItem

api = SDKBatchAPI(translator=lambda text, options: f"translated:{text}")
response = api.translate(BatchRequest(items=[BatchItem(id="1", text="sample")]))
print(response.results[0].text)
