# LCR Batch 10.7 manual real-provider command

Status: `authorized execution consumed; provider failed; do not run again`

The command below was consumed once. The at-most-once execution claim now blocks all repeated execution for this execution ID. It is retained only as historical audit evidence and must not be run again.

```powershell
python ntpe_lcr_batch107_real_provider_validation.py `
  --execute `
  --package artifacts/lcr_batch107/LCR_BATCH107_REAL_PROVIDER_EXECUTION_PACKAGE.json `
  --authorization <SEALED_EXACT_AUTHORIZATION_JSON> `
  --confirm-execution-id lcr-batch107-tic-case-b2-8ae44c56c7ad3de4a6fd-chunk-000001
```

The authorization must bind the package's document, chunk, source hash, production translation hash, rollback baseline hash, NVIDIA provider, model, two-request budget, and expiration. The API key is read only from `NVIDIA_API_KEY`; it must never be placed in the command or authorization JSON.

Without `--execute`, the entrypoint performs only the prepared-package check and reports zero Provider and Network requests:

```powershell
python ntpe_lcr_batch107_real_provider_validation.py
```
