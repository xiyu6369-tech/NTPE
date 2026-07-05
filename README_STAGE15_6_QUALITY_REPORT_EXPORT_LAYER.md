# NTPE 1.2 Professional Stage-15.6

## Quality Report / Export Layer

Stage-15.6 adds a clean export layer for Translation Quality Engine results.

### Added

- `core.quality.export_layer`
- `QualityReportExporter`
- `QualityReportSerializer`
- `QualityExportOptions`
- `QualityExportBundle`
- secret masking for metadata fields
- JSON, summary TXT, metrics JSON, and issues CSV export

### Compatibility

- Does not modify Foundation v1.0
- Does not modify NTPE 1.1 LTS Frozen behavior
- Does not modify Stage-14 Provider Framework Freeze contracts
- Preserves Stage-15.1 to Stage-15.5 public APIs

### Clean package rule

The Stage-15.6 delta package contains only the files required for this stage.
