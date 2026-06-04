from app.core.database import Base
import app.models.db  # noqa: F401


def test_voice_and_variant_tables_registered():
    tables = set(Base.metadata.tables.keys())
    assert {"voices", "voice_variants"} <= tables


def test_voice_has_identity_columns():
    cols = {c.name for c in Base.metadata.tables["voices"].columns}
    assert {
        "id", "public_voice_id", "creator_id", "owner_id", "name", "language",
        "preview_audio", "characteristics", "royalty_config", "is_public", "status",
    } <= cols


def test_variant_has_realization_columns_and_unique_pair():
    table = Base.metadata.tables["voice_variants"]
    cols = {c.name for c in table.columns}
    assert {"id", "voice_id", "model_id", "model_version", "artifact_type",
            "artifacts", "params", "source", "status"} <= cols
    uniques = [
        tuple(c.name for c in con.columns)
        for con in table.constraints
        if con.__class__.__name__ == "UniqueConstraint"
    ]
    assert ("voice_id", "model_id") in uniques
