from performance.stabilization import PerformanceBaseline

def test_no_api_or_product_feature_change():
    validation = PerformanceBaseline.default().validate()
    assert validation["product_feature_added"] is False
    assert validation["valid"] is True
