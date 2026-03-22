"""Mongo-backed storage for predefined and discovered sources."""

from __future__ import annotations

import os
from datetime import UTC, datetime
from typing import Any

from data.sources import PREDEFINED_SOURCES


DEFAULT_DB_NAME = "vision_1m"
PREDEFINED_COLLECTION = "predefined_sources"
DISCOVERED_COLLECTION = "discovered_sources"


def _utcnow() -> datetime:
    return datetime.now(UTC)


def mongo_configured() -> bool:
    return bool(os.getenv("MONGODB_URI"))


def _get_collection(name: str):
    from pymongo import MongoClient

    uri = os.getenv("MONGODB_URI")
    if not uri:
        raise RuntimeError("MONGODB_URI is not configured.")
    db_name = os.getenv("MONGODB_DB", DEFAULT_DB_NAME)
    client = MongoClient(uri)
    return client[db_name][name]


def _normalize_predefined_record(record: dict[str, Any], origin: str) -> dict[str, Any]:
    return {
        "url": record.get("url", ""),
        "source_type": record.get("source_type", "html"),
        "description": record.get("description", ""),
        "is_predefined": True,
        "origin": origin,
    }


def get_static_predefined_sources(initiative_id: str) -> list[dict[str, Any]]:
    record = PREDEFINED_SOURCES.get(initiative_id)
    if not record:
        return []
    if isinstance(record, list):
        return [_normalize_predefined_record(item, origin="static") for item in record]
    return [_normalize_predefined_record(record, origin="static")]


def list_human_predefined_sources(initiative_id: str | None = None) -> list[dict[str, Any]]:
    if not mongo_configured():
        return []

    query = {"kind": "human_predefined"}
    if initiative_id:
        query["initiative_id"] = initiative_id

    collection = _get_collection(PREDEFINED_COLLECTION)
    docs = list(collection.find(query, {"_id": 0}).sort("updated_at", -1))
    return [
        {
            "initiative_id": doc.get("initiative_id", ""),
            "category": doc.get("category", ""),
            "name": doc.get("name", ""),
            "metric_label": doc.get("metric_label", ""),
            "target_value": doc.get("target_value", ""),
            "url": doc.get("url", ""),
            "source_type": doc.get("source_type", "html"),
            "description": doc.get("description", ""),
            "is_predefined": True,
            "origin": "human",
            "notes": doc.get("notes", ""),
            "updated_at": doc.get("updated_at"),
        }
        for doc in docs
    ]


def get_predefined_sources(initiative_id: str) -> list[dict[str, Any]]:
    static_sources = get_static_predefined_sources(initiative_id)
    human_sources = [
        {
            "url": item["url"],
            "source_type": item["source_type"],
            "description": item["description"],
            "is_predefined": True,
            "origin": "human",
            "notes": item.get("notes", ""),
            "updated_at": item.get("updated_at"),
        }
        for item in list_human_predefined_sources(initiative_id)
    ]
    return static_sources + human_sources


def upsert_human_predefined_source(
    *,
    initiative_id: str,
    category: str,
    name: str,
    metric_label: str,
    target_value: str,
    url: str,
    source_type: str,
    description: str,
    notes: str = "",
) -> dict[str, Any]:
    if not mongo_configured():
        raise RuntimeError("MONGODB_URI is not configured.")

    collection = _get_collection(PREDEFINED_COLLECTION)
    now = _utcnow()
    doc = {
        "kind": "human_predefined",
        "initiative_id": initiative_id,
        "category": category,
        "name": name,
        "metric_label": metric_label,
        "target_value": target_value,
        "url": url,
        "source_type": source_type,
        "description": description,
        "notes": notes,
        "updated_at": now,
    }
    collection.update_one(
        {"kind": "human_predefined", "initiative_id": initiative_id, "url": url},
        {"$set": doc, "$setOnInsert": {"created_at": now}},
        upsert=True,
    )
    return doc


def save_discovered_sources(
    *,
    initiative: dict[str, Any],
    sources: list[dict[str, Any]],
    retry_count: int = 0,
) -> int:
    if not mongo_configured() or not sources:
        return 0

    collection = _get_collection(DISCOVERED_COLLECTION)
    now = _utcnow()
    docs = []
    for source in sources:
        docs.append(
            {
                "initiative_id": initiative.get("id", ""),
                "category": initiative.get("category", ""),
                "name": initiative.get("name", ""),
                "metric_label": initiative.get("metric_label", ""),
                "target_value": initiative.get("target_value", ""),
                "url": source.get("url", ""),
                "source_type": source.get("source_type", "html"),
                "description": source.get("description", ""),
                "is_predefined": bool(source.get("is_predefined", False)),
                "origin": source.get("origin", "dynamic"),
                "retry_count": retry_count,
                "discovered_at": now,
            }
        )

    for doc in docs:
        collection.update_one(
            {"initiative_id": doc["initiative_id"], "url": doc["url"], "origin": doc["origin"]},
            {"$set": doc, "$setOnInsert": {"created_at": now}},
            upsert=True,
        )
    return len(docs)


def list_discovered_sources(
    initiative_id: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    if not mongo_configured():
        return []

    query: dict[str, Any] = {}
    if initiative_id:
        query["initiative_id"] = initiative_id

    collection = _get_collection(DISCOVERED_COLLECTION)
    docs = list(collection.find(query, {"_id": 0}).sort("discovered_at", -1).limit(limit))
    return docs
