from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from time import time
from typing import Dict, List, Optional


DEFAULT_HISTORY_PATH = Path("logs") / "studio" / "studio_generation_history.json"


@dataclass(frozen=True)
class StudioHistoryItem:
    item_id: str
    prompt: str
    negative_prompt: str
    workflow: str
    image_path: Optional[str] = None
    image_paths: List[str] = field(default_factory=list)
    seed: Optional[int] = None
    rating: Optional[int] = None
    notes: str = ""
    metadata: Dict[str, str] = field(default_factory=dict)
    created_at: float = field(default_factory=time)


@dataclass(frozen=True)
class StudioHistoryStore:
    items: List[StudioHistoryItem] = field(default_factory=list)

    def add(self, item: StudioHistoryItem) -> "StudioHistoryStore":
        return StudioHistoryStore(items=[item, *self.items])

    def by_workflow(self, workflow: str) -> List[StudioHistoryItem]:
        return [item for item in self.items if item.workflow == workflow]

    def favorites(self) -> List[StudioHistoryItem]:
        return [item for item in self.items if item.rating is not None and item.rating >= 4]

    def latest(self, limit: int = 20) -> List[StudioHistoryItem]:
        return self.items[: max(0, limit)]

    def to_dict(self) -> dict[str, object]:
        return {"items": [asdict(item) for item in self.items]}

    def save(self, path: Path | str = DEFAULT_HISTORY_PATH) -> Path:
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")
        return output_path

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "StudioHistoryStore":
        raw_items = data.get("items", [])
        items: list[StudioHistoryItem] = []
        if isinstance(raw_items, list):
            for raw_item in raw_items:
                if not isinstance(raw_item, dict):
                    continue
                image_paths = raw_item.get("image_paths") or []
                if not isinstance(image_paths, list):
                    image_paths = []
                metadata = raw_item.get("metadata") or {}
                if not isinstance(metadata, dict):
                    metadata = {}
                items.append(
                    StudioHistoryItem(
                        item_id=str(raw_item.get("item_id", "unknown")),
                        prompt=str(raw_item.get("prompt", "")),
                        negative_prompt=str(raw_item.get("negative_prompt", "")),
                        workflow=str(raw_item.get("workflow", "unknown")),
                        image_path=raw_item.get("image_path") if raw_item.get("image_path") is not None else None,
                        image_paths=[str(path) for path in image_paths],
                        seed=raw_item.get("seed") if isinstance(raw_item.get("seed"), int) else None,
                        rating=raw_item.get("rating") if isinstance(raw_item.get("rating"), int) else None,
                        notes=str(raw_item.get("notes", "")),
                        metadata={str(key): str(value) for key, value in metadata.items()},
                        created_at=float(raw_item.get("created_at", time())),
                    )
                )
        return cls(items=items)



def load_history(path: Path | str = DEFAULT_HISTORY_PATH) -> StudioHistoryStore:
    input_path = Path(path)
    if not input_path.exists():
        return StudioHistoryStore()
    try:
        data = json.loads(input_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return StudioHistoryStore()
    if not isinstance(data, dict):
        return StudioHistoryStore()
    return StudioHistoryStore.from_dict(data)



def save_history(store: StudioHistoryStore, path: Path | str = DEFAULT_HISTORY_PATH) -> Path:
    return store.save(path)



def create_history_item(
    item_id: str,
    prompt: str,
    negative_prompt: str,
    workflow: str,
    image_path: Optional[str] = None,
    image_paths: Optional[List[str]] = None,
    seed: Optional[int] = None,
    metadata: Optional[Dict[str, str]] = None,
) -> StudioHistoryItem:
    output_paths = image_paths or ([image_path] if image_path else [])
    return StudioHistoryItem(
        item_id=item_id,
        prompt=prompt,
        negative_prompt=negative_prompt,
        workflow=workflow,
        image_path=image_path,
        image_paths=output_paths,
        seed=seed,
        metadata=metadata or {},
    )
