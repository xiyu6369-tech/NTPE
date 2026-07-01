NTPE Foundation-05.2 Pipeline Dependency Resolver
=================================================

增量更新內容：
- 新增 core/pipeline/dependency_resolver.py
- 新增 adapters/pipeline_dependency_resolver_adapter.py
- 新增 tests/launcher_pipeline_dependency_resolver_test.py

功能：
- 解析 Stage Registry 的 dependencies / requires
- 支援 metadata.before 與 metadata.after
- 支援停用 stage 偵測
- 支援 missing dependency 偵測
- 支援 cycle dependency 偵測
- 輸出可審計 dependency plan manifest

測試：
python tests\launcher_pipeline_dependency_resolver_test.py

預期：
PASS
