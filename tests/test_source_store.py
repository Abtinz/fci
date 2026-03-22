"""Tests for Mongo-backed source store helpers."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from storage.source_store import get_predefined_sources, save_discovered_sources


class SourceStoreTests(unittest.TestCase):
    @patch("storage.source_store.list_human_predefined_sources")
    @patch(
        "storage.source_store.PREDEFINED_SOURCES",
        {"housing-4": {"url": "https://static.example", "source_type": "xlsx", "description": "Static"}},
    )
    def test_get_predefined_sources_combines_static_and_human(self, mock_human):
        mock_human.return_value = [
            {
                "initiative_id": "housing-4",
                "url": "https://human.example",
                "source_type": "csv",
                "description": "Human source",
                "notes": "verified",
                "updated_at": None,
            }
        ]

        results = get_predefined_sources("housing-4")

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["origin"], "static")
        self.assertEqual(results[1]["origin"], "human")

    @patch("storage.source_store.mongo_configured")
    def test_save_discovered_sources_returns_zero_when_mongo_unconfigured(self, mock_configured):
        mock_configured.return_value = False

        saved = save_discovered_sources(
            initiative={"id": "housing-4", "category": "Housing", "name": "Rental vacancy rate"},
            sources=[{"url": "https://example.com", "source_type": "csv", "description": "x"}],
        )

        self.assertEqual(saved, 0)


if __name__ == "__main__":
    unittest.main()
