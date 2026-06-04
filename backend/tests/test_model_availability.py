from app.models.registry_types import ModelDescriptor
from app.services.model_catalog import builtin_by_id


def test_availability_flags_derived_from_editions():
    d = ModelDescriptor(id="m", name="m", description="d", provider="p",
                        editions=["community", "cloud"])
    assert d.available_in_ce is True
    assert d.available_in_cloud is True

    ce_only = ModelDescriptor(id="m2", name="m2", description="d", provider="p",
                              editions=["community"])
    assert ce_only.available_in_ce is True
    assert ce_only.available_in_cloud is False


def test_builtin_edition_availability_matches_licensing():
    base = builtin_by_id("omnivoice-base")
    assert base.available_in_ce is True
    assert base.available_in_cloud is True

    singing = builtin_by_id("omnivoice-singing")
    assert singing.available_in_ce is True
    assert singing.available_in_cloud is True

    fish = builtin_by_id("fish-audio-s2")
    assert fish.available_in_ce is True
    assert fish.available_in_cloud is False  # CE-only pending licensing review


def test_availability_flags_serialized_in_model_dump():
    d = builtin_by_id("fish-audio-s2").model_dump()
    assert d["available_in_ce"] is True
    assert d["available_in_cloud"] is False
