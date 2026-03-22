"""Tests for the FastAPI service."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from api.main import app


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    @patch("api.main.get_mongo_connection_status")
    @patch("api.main.is_mongo_configured")
    def test_health(self, mock_is_mongo_configured, mock_get_status):
        mock_is_mongo_configured.return_value = True
        mock_get_status.return_value = (True, "MongoDB is reachable.")

        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")
        self.assertTrue(response.json()["mongo_ok"])

    def test_sections(self):
        response = self.client.get("/sections")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 5)


if __name__ == "__main__":
    unittest.main()
