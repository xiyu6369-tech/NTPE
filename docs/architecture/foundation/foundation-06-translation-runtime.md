# NTPE Foundation-06 Translation Runtime

Foundation-06 introduces the translation-specific runtime contract on top of the Foundation-05 Production Runtime.

## 06.0 Scope

Foundation-06.0 defines the stable data contracts only. It does not call an AI model yet.

Included contracts:

- Translation Job
- Translation Segment
- Translation Context
- Translation Result
- Translation Error
- Translation Manifest
- Translation Runtime Adapter

## Runtime Flow

```text
TXT / source text
  -> Translation Job
  -> Translation Segments
  -> Translation Context
  -> Production Runtime Payload
  -> Foundation-05 Runtime
  -> Translation Result
```

## Contract Rules

### Translation Job

A job represents one translation task. It contains source language, target language, job metadata, context, and ordered segments.

### Translation Segment

A segment is the smallest translation execution unit. Segment status is one of:

```text
pending | running | completed | failed | skipped
```

### Translation Result

A result normalizes final output into:

```text
ok, status, job_id, output_text, segments, context, metrics, errors, metadata
```

## Foundation-05 Integration

`build_production_runtime_payload(job)` converts a Translation Job into the dictionary payload expected by Foundation-05 Production Runtime:

```text
source
context
metadata.translation_job
metadata.contract
metadata.contract_version
```

This preserves backward compatibility because the Production Runtime continues to receive a normal payload dictionary.

## Non-goals for 06.0

The following are intentionally deferred:

- File chunking
- Prompt building
- Model adapter execution
- Quality repair
- Resume/runtime session management

These are planned for later Foundation-06.x stages.
