"""Test MongoDB integration — config, client, Atlas Admin API."""

from __future__ import annotations

import pytest


class TestMongoDBConfig:
    """Test MongoDB configuration loads correctly."""

    def test_config_fields_exist(self):
        from titan.config import settings
        # Just verify the fields exist
        assert hasattr(settings, "MONGODB_URI")
        assert hasattr(settings, "MONGODB_DB_NAME")
        assert hasattr(settings, "MONGODB_PUBLIC_KEY")
        assert hasattr(settings, "MONGODB_PRIVATE_KEY")
        assert hasattr(settings, "MONGODB_PROJECT_ID")

    def test_default_db_name(self):
        from titan.config import settings
        assert settings.MONGODB_DB_NAME == "titan_aio"

    def test_public_key_loaded(self):
        from titan.config import settings
        key = settings.MONGODB_PUBLIC_KEY
        assert key, "MONGODB_PUBLIC_KEY should be set"
        assert len(key) > 5, "Public key should be a reasonable length"


class TestMongoDBClient:
    """Test MongoDB client (without actual connection)."""

    def test_client_import(self):
        from Services.mongodb.client import MongoDBClient
        assert MongoDBClient is not None

    def test_client_singleton(self):
        from Services.mongodb.client import MongoDBClient
        c1 = MongoDBClient.get_instance()
        c2 = MongoDBClient.get_instance()
        assert c1 is c2

    def test_client_no_uri_raises(self):
        from Services.mongodb.client import MongoDBClient
        # Force empty URI by passing None to bypass settings fallback
        MongoDBClient._instance = None
        c = MongoDBClient.__new__(MongoDBClient)
        c._uri = ""
        c._db_name = "test"
        c._sync_client = None
        c._async_client = None
        with pytest.raises(RuntimeError, match="MONGODB_URI not set"):
            _ = c.sync

    def test_client_with_uri(self):
        from Services.mongodb.client import MongoDBClient
        c = MongoDBClient(uri="mongodb://localhost:27017", db_name="test")
        assert c._uri == "mongodb://localhost:27017"
        assert c._db_name == "test"

    def test_collection_access(self):
        """Test MongoDBClient collections without connection."""
        from Services.mongodb.client import MongoDBClient
        c = MongoDBClient(uri="mongodb://localhost:27017", db_name="test")
        assert hasattr(c, "products")
        assert hasattr(c, "campaigns")
        assert hasattr(c, "knowledge")
        assert hasattr(c, "winning_hooks")


class TestAtlasAdminClient:
    """Test Atlas Admin API client."""

    def test_admin_client_import(self):
        from Services.mongodb.atlas_admin import AtlasAdminClient
        assert AtlasAdminClient is not None

    def test_admin_client_config(self):
        from Services.mongodb.atlas_admin import AtlasAdminClient
        client = AtlasAdminClient(
            public_key="al-test-public-key",
            private_key="test-private-key",
            project_id="test-project-id",
        )
        assert client.public_key == "al-test-public-key"
        assert client.private_key == "test-private-key"
        assert client.project_id == "test-project-id"

    def test_admin_client_loads_from_settings(self):
        from Services.mongodb.atlas_admin import AtlasAdminClient
        from titan.config import settings
        client = AtlasAdminClient()
        assert client.public_key == settings.MONGODB_PUBLIC_KEY
        assert client.private_key == settings.MONGODB_PRIVATE_KEY
