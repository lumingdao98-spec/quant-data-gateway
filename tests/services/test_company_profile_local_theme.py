from quant_data.services.company_profile_service import CompanyProfileService


def test_known_company_profile_is_immediate_and_structured(tmp_path):
    service = CompanyProfileService(db_path=tmp_path / "profiles.sqlite")

    profile = service.get_local_profile("300274")

    assert profile["name"] == "阳光电源"
    assert "光伏" in profile["business_tags"]
    assert "储能" in profile["business_tags"]
    assert profile["industry"] == "光伏逆变器/储能"
    assert "300274" not in profile
    assert profile["cache_info"]["network_used"] is False


def test_unknown_company_profile_reports_missing_instead_of_guessing(tmp_path):
    service = CompanyProfileService(db_path=tmp_path / "profiles.sqlite")

    profile = service.get_local_profile("600000")

    assert profile["quality_status"] == "missing"
    assert profile["business_tags"] == []
    assert profile["missing_reasons"]
