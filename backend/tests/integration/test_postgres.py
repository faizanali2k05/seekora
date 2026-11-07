import os

import pytest
from sqlalchemy import create_engine, text


@pytest.mark.skipif(
    "SEEKORA_TEST_DATABASE_URL" not in os.environ,
    reason="set SEEKORA_TEST_DATABASE_URL to run PostgreSQL integration checks",
)
def test_pgvector_and_full_text_are_available() -> None:
    engine = create_engine(os.environ["SEEKORA_TEST_DATABASE_URL"])
    with engine.connect() as connection:
        assert connection.scalar(text("SELECT extversion FROM pg_extension WHERE extname='vector'"))
        assert connection.scalar(
            text("SELECT to_tsvector('english', 'hybrid search') @@ plainto_tsquery('hybrid')")
        )
