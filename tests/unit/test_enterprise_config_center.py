from core.enterprise.config_center import EnterpriseConfigCenter, ConfigValidator, ConfigValidationError


def test_enterprise_config_center_loads_default_profile():
    center = EnterpriseConfigCenter()
    config = center.load(environment="development")
    assert config["enterprise"]["environment"] == "development"
    assert center.validate(config) is True


def test_enterprise_config_validator_rejects_missing_sections():
    validator = ConfigValidator()
    try:
        validator.validate({"enterprise": {}})
    except ConfigValidationError:
        assert True
    else:
        assert False
