from app.core.features import Features


def test_community_disables_all_commercial_features():
    f = Features.for_edition("community")
    assert not any([f.auth, f.tenancy, f.billing, f.marketplace, f.creators, f.payouts])


def test_cloud_enables_ecosystem_features():
    f = Features.for_edition("cloud")
    assert all([f.auth, f.tenancy, f.billing, f.marketplace, f.creators, f.payouts])


def test_enterprise_enables_ecosystem_features():
    f = Features.for_edition("enterprise")
    assert all([f.auth, f.tenancy, f.billing, f.marketplace, f.creators, f.payouts])


def test_unknown_edition_defaults_to_community():
    assert Features.for_edition("banana") == Features.for_edition("community")


def test_settings_exposes_features_for_default_edition():
    from app.core.config import settings
    assert settings.EDITION == "community"
    assert settings.features.marketplace is False
