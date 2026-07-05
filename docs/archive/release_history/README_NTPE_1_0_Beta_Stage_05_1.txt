NTPE 1.0 Beta — Stage-05.1 Runtime Benchmark

新增內容：
- benchmark/runtime/runtime_benchmark.py
- benchmark/runtime/pipeline_benchmark.py
- benchmark/runtime/session_benchmark.py
- benchmark/runtime/recovery_benchmark.py
- benchmark/runtime/manifest.py
- tests/beta_stage_05_1/launcher_runtime_benchmark_test.py

目的：
在 Stage-05.0 Benchmark Framework 之上建立 Runtime 效能基準，量測 Runtime startup、job creation、segment throughput、pipeline latency、session resume、recovery latency 與 JSON report。

不修改 Foundation v1.0 Frozen contract。
