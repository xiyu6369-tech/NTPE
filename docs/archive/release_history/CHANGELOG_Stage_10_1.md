# NTPE 1.0 Beta — Stage-10.1 Platform Service Configuration

## 新增

- `platform_services/platform_config.py`
- `PlatformConfigEntry`
- `PlatformConfigStore`
- `PlatformServiceConfig`
- `create_platform_config()`
- `create_service_config()`
- `tests/beta_stage_10_1/launcher_platform_config_test.py`

## 修改

- `platform_services/__init__.py`
  - 只新增 Stage-10.1 configuration public exports。

## 修正

- 無。

## 相容性

- Foundation v1.0：Frozen，不修改。
- CLI：Frozen，不修改。
- SDK：Complete，不修改。
- Integration：Frozen，不修改。
- Workflow：Frozen，不修改。

## 需覆蓋或新增檔案

```text
platform_services/platform_config.py
platform_services/__init__.py
tests/beta_stage_10_1/launcher_platform_config_test.py
README_NTPE_1_0_Beta_Stage_10_1.txt
CHANGELOG_Stage_10_1.md
```

## 測試

```bash
python tests/beta_stage_10_1/launcher_platform_config_test.py
python tests/beta_stage_10_0/launcher_platform_services_test.py
python tests/beta_stage_09_8/launcher_workflow_freeze_test.py
```

## Commit

```bash
git add platform_services/platform_config.py platform_services/__init__.py tests/beta_stage_10_1 README_NTPE_1_0_Beta_Stage_10_1.txt CHANGELOG_Stage_10_1.md
git commit -m "Stage-10.1 Platform Service Configuration"
git push
git tag beta-stage-10.1-platform-service-configuration
git push origin beta-stage-10.1-platform-service-configuration
```
