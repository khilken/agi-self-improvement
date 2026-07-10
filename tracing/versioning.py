"""
Prompt & Skill Versioning System
================================

Tracks versions of prompts, agent instructions, and reusable skills.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional, List
import json
from pathlib import Path
import uuid


@dataclass
class VersionedItem:
    id: str
    item_type: str          # "prompt", "skill", "agent_instruction"
    name: str
    content: str
    version: int
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""

    def to_dict(self):
        return {
            "id": self.id,
            "item_type": self.item_type,
            "name": self.name,
            "content": self.content,
            "version": self.version,
            "created_at": self.created_at,
            "notes": self.notes
        }


class VersionStore:
    def __init__(self, storage_dir: str = "logs/versions"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def save_version(self, item_type: str, name: str, content: str, notes: str = "") -> VersionedItem:
        # Find latest version
        existing = self.list_versions(name, item_type)
        next_version = max([v.version for v in existing], default=0) + 1

        item = VersionedItem(
            id=str(uuid.uuid4()),
            item_type=item_type,
            name=name,
            content=content,
            version=next_version,
            notes=notes
        )

        filepath = self.storage_dir / f"{item_type}_{name}_v{next_version}.json"
        with open(filepath, "w") as f:
            json.dump(item.to_dict(), f, indent=2)

        return item

    def list_versions(self, name: str, item_type: str) -> List[VersionedItem]:
        items = []
        for f in self.storage_dir.glob(f"{item_type}_{name}_v*.json"):
            with open(f) as file:
                data = json.load(file)
                items.append(VersionedItem(**data))
        return sorted(items, key=lambda x: x.version, reverse=True)

    def get_latest(self, name: str, item_type: str) -> Optional[VersionedItem]:
        versions = self.list_versions(name, item_type)
        return versions[0] if versions else None