NTPE 1.1 LTS Stage-07: Batch Progress / Summary Report
======================================================

Command:
python ntpe_translate_batch.py input output

Recursive:
python ntpe_translate_batch.py input output --recursive

Silent progress:
python ntpe_translate_batch.py input output --quiet-progress

Reports:
output/reports/Batch_Translation_Report.json
output/reports/Batch_Translation_Report.md

New report fields include:
- completed_files
- success_rate_percent
- completion_rate_percent
- elapsed_hms
- average_seconds_per_file
- average_chunks_per_file
- provider_attempts
- provider_retry_count
- qa_attempts
- qa_retry_count
- qa_issue_count
- korean_residue_issues
- progress_log
