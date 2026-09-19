from pathlib import Path


def test_alembic_foundation_files_exist() -> None:
    root = Path(__file__).resolve().parents[1]
    assert (root / "apps" / "api" / "alembic.ini").is_file()
    assert (root / "apps" / "api" / "alembic" / "versions" / "0001_initial_foundation.py").is_file()
    assert (root / "supabase" / "migrations" / "20260918000000_initial_foundation.sql").is_file()

