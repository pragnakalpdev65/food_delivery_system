import pytest
from rest_framework.test import APIClient


@pytest.fixture(autouse=True)
def inmemory_channel_layer(settings):
    """Use in-memory Channels backend so tests do not require Redis."""
    settings.CHANNEL_LAYERS = {
        "default": {"BACKEND": "channels.layers.InMemoryChannelLayer"},
    }
    from channels import layers

    layers.channel_layers = layers.ChannelLayerManager()


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


