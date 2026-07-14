"""
Skill Marketplace
=================

Allows agents to publish, discover, and version reusable skills.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
import json
from pathlib import Path
import uuid


@dataclass
class Skill:
    id: str
    name: str
    description: str
    code: str
    version: int = 1
    author: str = "system"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "code": self.code,
            "version": self.version,
            "author": self.author,
            "created_at": self.created_at
        }


class SkillMarketplace:
    def __init__(self, storage_dir: str = "logs/skills"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def publish(self, name: str, description: str, code: str, author: str = "system") -> Skill:
        skill = Skill(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            code=code,
            author=author
        )
        filepath = self.storage_dir / f"{name}_v{skill.version}.json"
        with open(filepath, "w") as f:
            json.dump(skill.to_dict(), f, indent=2)
        return skill

    def find(self, name: str) -> Optional[Skill]:
        files = sorted(self.storage_dir.glob(f"{name}_v*.json"), reverse=True)
        if not files:
            return None
        with open(files[0]) as f:
            return Skill(**json.load(f))

    def list_all(self) -> List[Skill]:
        skills = []
        for f in self.storage_dir.glob("*.json"):
            with open(f) as file:
                skills.append(Skill(**json.load(file)))
        return skills