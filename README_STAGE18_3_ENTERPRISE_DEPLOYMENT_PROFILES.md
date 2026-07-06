# NTPE 1.2 Professional — Stage-18.3 Enterprise Deployment Profiles

Stage-18.3 adds an enterprise deployment profile layer. It is additive and does not modify Foundation v1.0, NTPE 1.1 LTS, Stage-17 production runtime, or Stage-18.2 configuration center contracts.

## Added

- `core.enterprise.deployment_profile_manager.EnterpriseDeploymentProfileManager`
- `core.enterprise.deployment_profiles.DeploymentProfile`
- `DeploymentProfileCatalog`
- `DeploymentProfileResolver`
- deployment profile audit hash support

## Built-in Profiles

- `local-workstation`
- `team-shared-runtime`
- `enterprise-controlled-host`

## Validation

```bat
python ntpe_stage18_3_enterprise_deployment_profiles_test.py
python tests\integration\launcher_stage18_3_enterprise_deployment_profiles_test.py
python tests\smoke\launcher_stage18_3_enterprise_deployment_profiles_smoke_test.py
python ntpe_validate.py
```
