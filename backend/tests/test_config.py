import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_production_rejects_documented_placeholder_key() -> None:
    with pytest.raises(ValidationError, match="must be replaced"):
        Settings(env="production", admin_api_key="replace-with-a-long-random-secret")


def test_paid_provider_requires_nonempty_key() -> None:
    with pytest.raises(ValidationError, match="RAG_API_KEY"):
        Settings(rag_provider="openai-compatible", rag_api_key="")
