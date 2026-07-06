from core.enterprise.deployment_profile_manager import EnterpriseDeploymentProfileManager
from core.enterprise.deployment_profiles import DeploymentProfile


def test_default_profiles_resolve():
    manager = EnterpriseDeploymentProfileManager()
    resolved = manager.resolve_profile("enterprise-controlled-host")
    assert resolved["enterprise"]["environment"] == "production"
    assert resolved["enterprise"]["deployment_profile"] == "enterprise-controlled-host"
    assert "config_lock" in resolved["enterprise"]["capabilities"]


def test_custom_profile_registration():
    manager = EnterpriseDeploymentProfileManager()
    manager.register_profile(DeploymentProfile(name="qa", target="team-shared-runtime", environment="staging"))
    assert "qa" in manager.available_profiles()
    assert manager.resolve_profile("qa")["enterprise"]["deployment_profile"] == "qa"


def test_profile_audit_hash():
    manager = EnterpriseDeploymentProfileManager()
    audit = manager.audit_profile("local-workstation")
    assert audit["stage"] == "Stage-18.3"
    assert len(audit["config_hash"]) == 64
