NTPE 1.0 Beta — Stage-05.0 Benchmark Framework

This incremental update adds the base benchmark framework used by later Stage-05 performance work.

新增：
- benchmark/benchmark_case.py
- benchmark/benchmark_context.py
- benchmark/benchmark_manifest.py
- benchmark/benchmark_registry.py
- benchmark/benchmark_result.py
- benchmark/benchmark_runner.py
- benchmark/benchmark_suite.py
- benchmark/report_writer.py
- benchmark/metrics/
- tests/beta_stage_05_0/launcher_benchmark_framework_test.py

執行測試：
cd /d D:\Python\NTPE
python tests\beta_stage_05_0\launcher_benchmark_framework_test.py

Commit 建議：
git add .
git commit -m "feat(beta-stage-05.0): add benchmark framework"
git push origin main
