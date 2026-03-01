from typing import Dict, List, Optional
import numpy as np

from .TrainService import GEAR_MAP

class PredictService:
    def __init__(self, model_service=None):
        self.model_service = model_service

    @staticmethod
    def _add_bias(X: np.ndarray) -> np.ndarray:
        return np.column_stack([np.ones((X.shape[0], 1), dtype=float), X])

    @staticmethod
    def _gear_to_num(g) -> Optional[int]:
        if g is None:
            return None
        if isinstance(g, (int, float)):
            gg = int(g)
            return gg if gg in (0, 1) else None
        if isinstance(g, str):
            g = g.strip()
            if g in GEAR_MAP:
                return int(GEAR_MAP[g])
            # tolerate common strings
            low = g.lower()
            if "auto" in low or "อัตโน" in low:
                return 1
            if "man" in low or "ธรรมดา" in low:
                return 0
        return None

    def predict(self, model: Dict, items: List[Dict]) -> Dict:
        """
        items: [{year, gear, mile}, ...]
        return: {"y_pred": [float|None, ...]}
        """
        beta = np.asarray(model.get("beta", []), dtype=float)
        if beta.size == 0:
            return {"y_pred": [None for _ in items]}

        mu = np.asarray(model.get("mu", [0.0, 0.0, 0.0]), dtype=float)
        sigma = np.asarray(model.get("sigma", [1.0, 1.0, 1.0]), dtype=float)
        y_mean = float(model.get("y_mean", 0.0))
        standardize = bool(model.get("standardize", True))
        center_y = bool(model.get("center_y", True))

        X_list: List[Optional[List[float]]] = []
        ok_idx: List[int] = []

        for i, it in enumerate(items):
            try:
                year = float(it.get("year"))
                mile = float(it.get("mile"))
                gear_num = self._gear_to_num(it.get("gear"))
                if gear_num is None:
                    X_list.append(None)
                    continue

                X_list.append([year, float(gear_num), mile])
                ok_idx.append(i)
            except Exception:
                X_list.append(None)

        if not ok_idx:
            return {"y_pred": [None for _ in items]}

        X_ok = np.asarray([X_list[i] for i in ok_idx], dtype=float)

        if standardize:
            sigma_safe = sigma.copy()
            sigma_safe[sigma_safe == 0] = 1.0
            X_ok = (X_ok - mu) / sigma_safe

        Xb = self._add_bias(X_ok)
        yhat_centered = Xb @ beta
        yhat = yhat_centered + (y_mean if center_y else 0.0)

        out: List[Optional[float]] = [None for _ in items]
        for j, idx in enumerate(ok_idx):
            out[idx] = int(yhat[j])

        return {"y_pred": out}
