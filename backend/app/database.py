"""
Resilient Database Layer for Edge AI EV Optimizer.
Connects to MongoDB when available; seamlessly falls back to persistent local JSON/memory
storage if MongoDB is offline or unavailable.
"""

import os
import json
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
import pymongo
from pymongo.errors import PyMongoError, ConnectionFailure
from app.config import settings


class LocalCollection:
    """A resilient in-memory collection with JSON file persistence fallback."""
    def __init__(self, name: str, storage_dir: str):
        self.name = name
        self.file_path = os.path.join(storage_dir, f"{name}.json")
        self.documents: Dict[str, Dict[str, Any]] = {}
        self._load()

    def _load(self):
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        self.documents = {d.get("id", d.get("_id", str(uuid.uuid4()))): d for d in data}
                    elif isinstance(data, dict):
                        self.documents = data
            except Exception:
                self.documents = {}

    def _save(self):
        try:
            os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
            with open(self.file_path, "w") as f:
                json.dump(list(self.documents.values()), f, indent=2, default=str)
        except Exception:
            pass

    def insert_one(self, doc: Dict[str, Any]):
        doc_copy = dict(doc)
        doc_id = str(doc_copy.get("_id", doc_copy.get("id", uuid.uuid4().hex[:12])))
        doc_copy["_id"] = doc_id
        doc_copy["id"] = doc_id
        if "created_at" not in doc_copy:
            doc_copy["created_at"] = datetime.now().isoformat()
        self.documents[doc_id] = doc_copy
        self._save()
        return type("InsertResult", (), {"inserted_id": doc_id})()

    def find_one(self, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        for doc in self.documents.values():
            match = True
            for k, v in query.items():
                if k == "_id" and doc.get("_id") != str(v) and doc.get("id") != str(v):
                    match = False
                    break
                elif k != "_id" and doc.get(k) != v:
                    match = False
                    break
            if match:
                return dict(doc)
        return None

    def find(self, query: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        if not query:
            return [dict(d) for d in self.documents.values()]
        results = []
        for doc in self.documents.values():
            match = True
            for k, v in query.items():
                if doc.get(k) != v:
                    match = False
                    break
            if match:
                results.append(dict(doc))
        return results

    def update_one(self, query: Dict[str, Any], update: Dict[str, Any]):
        doc = self.find_one(query)
        if not doc:
            return type("UpdateResult", (), {"modified_count": 0})()
        doc_id = doc.get("id") or doc.get("_id")
        set_vals = update.get("$set", update)
        for k, v in set_vals.items():
            self.documents[doc_id][k] = v
        self.documents[doc_id]["updated_at"] = datetime.now().isoformat()
        self._save()
        return type("UpdateResult", (), {"modified_count": 1})()

    def delete_one(self, query: Dict[str, Any]):
        doc = self.find_one(query)
        if not doc:
            return type("DeleteResult", (), {"deleted_count": 0})()
        doc_id = doc.get("id") or doc.get("_id")
        if doc_id in self.documents:
            del self.documents[doc_id]
            self._save()
            return type("DeleteResult", (), {"deleted_count": 1})()
        return type("DeleteResult", (), {"deleted_count": 0})()

    def count_documents(self, query: Optional[Dict[str, Any]] = None) -> int:
        return len(self.find(query))


class DatabaseManager:
    """Manages connection to MongoDB or transparent local fallback."""
    def __init__(self):
        self.is_connected = False
        self.is_fallback = False
        self.client: Optional[pymongo.MongoClient] = None
        self.db = None
        self.fallback_dir = os.path.join(settings.BASE_DIR, "data", "db_fallback")
        os.makedirs(self.fallback_dir, exist_ok=True)
        self.local_collections: Dict[str, LocalCollection] = {}

    def connect(self):
        try:
            # Short timeout to avoid blocking edge computer boot
            self.client = pymongo.MongoClient(
                settings.MONGODB_URI,
                serverSelectionTimeoutMS=1500,
                connectTimeoutMS=1500
            )
            # Test connection
            self.client.admin.command("ping")
            self.db = self.client[settings.DATABASE_NAME]
            self.is_connected = True
            self.is_fallback = False
            print(f"[+] Connected to MongoDB at: {settings.MONGODB_URI} (DB: {settings.DATABASE_NAME})")
            self._ensure_indexes()
        except (ConnectionFailure, PyMongoError, Exception) as e:
            self.is_connected = False
            self.is_fallback = True
            print(f"[!] MongoDB unavailable ({type(e).__name__}). Activated local resilient persistence fallback at: {self.fallback_dir}")

    def _ensure_indexes(self):
        if self.is_connected and self.db is not None:
            try:
                self.db.sessions.create_index("session_id", unique=True)
                self.db.predictions.create_index("created_at")
                self.db.optimizations.create_index("created_at")
                self.db.alerts.create_index("created_at")
            except Exception as e:
                print(f"[*] Note on indexes: {e}")

    def get_collection(self, collection_name: str):
        if self.is_connected and self.db is not None:
            return self.db[collection_name]
        if collection_name not in self.local_collections:
            self.local_collections[collection_name] = LocalCollection(collection_name, self.fallback_dir)
        return self.local_collections[collection_name]

    def check_health(self) -> Dict[str, Any]:
        return {
            "status": "connected" if self.is_connected else "fallback_local_storage",
            "type": "mongodb" if self.is_connected else "persistent_json_cache",
            "uri": settings.MONGODB_URI if self.is_connected else self.fallback_dir,
            "database": settings.DATABASE_NAME
        }


db_manager = DatabaseManager()
