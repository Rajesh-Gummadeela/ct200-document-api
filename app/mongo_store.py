"""
MongoDB connection for LLM-generated output storage.
Falls back to a JSON file store if MongoDB is not available.
This design decision is explicit: MongoDB Atlas free tier is preferred,
but the fallback lets the system run without a MongoDB instance.
"""
import json
import os
import time
from datetime import datetime
from typing import Optional
from bson import ObjectId

MONGO_URL = os.getenv("MONGO_URL", "")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "ct200")
MONGO_COLLECTION = "generations"

# JSON fallback path
JSON_STORE_PATH = os.getenv("JSON_STORE_PATH", "./generation_store.json")


def _load_json_store() -> dict:
    if os.path.exists(JSON_STORE_PATH):
        with open(JSON_STORE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save_json_store(store: dict):
    with open(JSON_STORE_PATH, "w", encoding="utf-8") as f:
        json.dump(store, f, indent=2, default=str)


def _new_id() -> str:
    return f"json_{int(time.time() * 1000)}_{os.getpid()}"


class GenerationStore:
    """
    Unified interface for storing and retrieving LLM generation documents.
    Tries MongoDB first; falls back to JSON file store.
    """

    def __init__(self):
        self._mongo = None
        self._col = None
        self._using_mongo = False
        self._init()

    def _init(self):
        if MONGO_URL:
            try:
                from pymongo import MongoClient
                from pymongo.errors import ConnectionFailure
                client = MongoClient(MONGO_URL, serverSelectionTimeoutMS=3000)
                client.admin.command("ping")
                self._mongo = client[MONGO_DB_NAME]
                self._col = self._mongo[MONGO_COLLECTION]
                self._using_mongo = True
                print("[GenerationStore] Connected to MongoDB.")
            except Exception as e:
                print(f"[GenerationStore] MongoDB unavailable ({e}). Using JSON fallback.")
        else:
            print("[GenerationStore] MONGO_URL not set. Using JSON fallback.")

    def insert(self, document: dict) -> str:
        """Insert a generation document and return its ID."""
        document["created_at"] = datetime.utcnow().isoformat()
        if self._using_mongo:
            result = self._col.insert_one(document)
            return str(result.inserted_id)
        else:
            store = _load_json_store()
            doc_id = _new_id()
            document["_id"] = doc_id
            store[doc_id] = document
            _save_json_store(store)
            return doc_id

    def get(self, doc_id: str) -> Optional[dict]:
        """Retrieve a generation document by ID."""
        if self._using_mongo:
            try:
                result = self._col.find_one({"_id": ObjectId(doc_id)})
                if result:
                    result["_id"] = str(result["_id"])
                return result
            except Exception:
                return None
        else:
            store = _load_json_store()
            return store.get(doc_id)

    def find_by_selection(self, selection_id: int) -> list:
        """Find all generations for a selection ID."""
        if self._using_mongo:
            results = list(self._col.find({"selection_id": selection_id}))
            for r in results:
                r["_id"] = str(r["_id"])
            return results
        else:
            store = _load_json_store()
            return [v for v in store.values() if v.get("selection_id") == selection_id]

    def find_by_node(self, node_id: int) -> list:
        """Find all generations that include a given node ID."""
        if self._using_mongo:
            results = list(self._col.find({"node_ids": node_id}))
            for r in results:
                r["_id"] = str(r["_id"])
            return results
        else:
            store = _load_json_store()
            return [v for v in store.values() if node_id in v.get("node_ids", [])]

    @property
    def using_mongo(self) -> bool:
        return self._using_mongo


# Singleton
_store: Optional[GenerationStore] = None


def get_generation_store() -> GenerationStore:
    global _store
    if _store is None:
        _store = GenerationStore()
    return _store
