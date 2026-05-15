"""Pytest configuration and fixtures."""

import pytest

pytest_plugins = ("pytest_asyncio",)


@pytest.fixture(scope="session")
def anyio_backend():
    """Configure pytest-asyncio backend."""
    return "asyncio"
