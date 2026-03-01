from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional


class ModelService:
    """Persist the latest trained model to disk (JSON) and keep it in memory."""

    def __init__(self, model_path: Optional[str] = None) -> None:
        self.model_path = model_path or os.environ.get("MODEL_PATH", "/app/data/model.json")
        self._model: Optional[Dict[str, Any]] = None
        self.load()

    def load(self) -> Optional[Dict[str, Any]]:
        try:
            if not os.path.exists(self.model_path):
                return None
            with open(self.model_path, "r", encoding="utf-8") as f:
                self._model = json.load(f)
            return self._model
        except Exception:
            # Keep the API resilient: treat failures as "no model".
            self._model = None
            return None

    def save(self) -> None:
        if self._model is None:
            return
        os.makedirs(os.path.dirname(self.model_path) or ".", exist_ok=True)
        with open(self.model_path, "w", encoding="utf-8") as f:
            json.dump(self._model, f, ensure_ascii=False, indent=2)

    def set_model(self, model: Dict[str, Any]) -> None:
        self._model = model
        self.save()

    def get_model(self) -> Optional[Dict[str, Any]]:
        return self._model
