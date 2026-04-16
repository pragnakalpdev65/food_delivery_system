import pytest
from rest_framework.test import APIClient


@pytest.fixture(autouse=True)
def clear_cache():
    """Clear Django cache before each test."""
    from django.core.cache import cache

    cache.clear()


@pytest.fixture
def api_client():
    """Fixture for DRF API Client."""
    return APIClient()


@pytest.fixture
def user(db):
    """Fixture for a standard user."""
    from apps.users.tests.factories import UserFactory

    return UserFactory()


