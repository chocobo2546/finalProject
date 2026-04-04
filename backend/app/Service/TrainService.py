from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Literal, Tuple
import numpy as np

RegType = Literal["none", "ridge", "lasso", "elasticnet"]

GEAR_MAP: Dict[str, int] = {"ธรรมดา": 0, "อัตโนมัติ": 1}


def _add_bias(X: np.ndarray) -> np.ndarray:
    return np.column_stack([np.ones((X.shape[0], 1)), X])


def _soft_threshold(z: np.ndarray, t: float) -> np.ndarray:
    return np.sign(z) * np.maximum(np.abs(z) - t, 0.0)


def _loss_sse(y, yhat):
    return float(np.sum((y - yhat) ** 2))


def _loss_ridge(y, Xb, beta, lam):
    return _loss_sse(y, Xb @ beta) + lam * np.sum(beta[1:] ** 2)


def _loss_lasso(y, Xb, beta, lam):
    return _loss_sse(y, Xb @ beta) + lam * np.sum(np.abs(beta[1:]))


def _loss_elasticnet(y, Xb, beta, lam, alpha_en):
    l1 = np.sum(np.abs(beta[1:]))
    l2 = np.sum(beta[1:] ** 2)
    return _loss_sse(y, Xb @ beta) + lam * (
        alpha_en * l1 + (1 - alpha_en) * l2
    )


@dataclass
class TrainConfig:
    reg: RegType = "ridge"
    alpha: float = 1e-6              # learning rate
    lam: float = 10.0
    elastic_alpha: float = 0.5       # only for elasticnet
    epochs: int = 20000
    standardize: bool = True
    center_y: bool = True
    early_stop_tol: float = 1e-10
    early_stop_patience: int = 500
    seed: int = 42


class TrainService:
    feature_order = ["year", "gear_bin", "mile"]

    def __init__(self, normalizer) -> None:
        self._normalize = normalizer

    def build_xy(self, rows: List[Dict]) -> Tuple[np.ndarray, np.ndarray]:
        X, y = [], []

        for r in rows:
            norm = self._normalize(r)
            if not norm:
                continue
            try:
                year = int(norm["year"])
                price = int(norm["price"])
                mile = int(norm["mile"])
                gear = norm["gear"]
                if gear not in GEAR_MAP:
                    continue
                X.append([year, GEAR_MAP[gear], mile])
                y.append(price)
            except Exception:
                continue

        if not X:
            return np.empty((0, 3)), np.empty((0,))
        return np.asarray(X, float), np.asarray(y, float)

    def fit(self, rows: List[Dict], cfg: TrainConfig) -> Dict:
        X, y = self.build_xy(rows)
        if X.size == 0:
            return {"beta": None, "details": "no_valid_rows"}

        rng = np.random.default_rng(cfg.seed)
        idx = rng.permutation(len(y))
        X, y = X[idx], y[idx]

        # standardize
        if cfg.standardize:
            mu, sigma = X.mean(0), X.std(0)
            sigma[sigma == 0] = 1
            Xs = (X - mu) / sigma
        else:
            mu = np.zeros(X.shape[1])
            sigma = np.ones(X.shape[1])
            Xs = X

        # center y
        if cfg.center_y:
            y_mean = y.mean()
            yc = y - y_mean
        else:
            y_mean = 0.0
            yc = y

        Xb = _add_bias(Xs)
        beta = np.zeros(Xb.shape[1])

        best = float("inf")
        stall = 0

        for ep in range(cfg.epochs):
            yhat = Xb @ beta

            if cfg.reg == "none":
                grad = -2 * Xb.T @ (yc - yhat)
                beta -= cfg.alpha * grad
                loss = _loss_sse(yc, yhat)

            elif cfg.reg == "ridge":
                grad = -2 * Xb.T @ (yc - yhat)
                grad[1:] += 2 * cfg.lam * beta[1:]
                beta -= cfg.alpha * grad
                loss = _loss_ridge(yc, Xb, beta, cfg.lam)

            elif cfg.reg == "lasso":
                grad = -2 * Xb.T @ (yc - yhat)
                beta_tmp = beta - cfg.alpha * grad
                beta_tmp[1:] = _soft_threshold(beta_tmp[1:], cfg.alpha * cfg.lam)
                beta = beta_tmp
                loss = _loss_lasso(yc, Xb, beta, cfg.lam)

            else:  # elasticnet
                grad = -2 * Xb.T @ (yc - yhat)
                grad[1:] += 2 * cfg.lam * (1 - cfg.elastic_alpha) * beta[1:]
                beta_tmp = beta - cfg.alpha * grad
                beta_tmp[1:] = _soft_threshold(
                    beta_tmp[1:], cfg.alpha * cfg.lam * cfg.elastic_alpha
                )
                beta = beta_tmp
                loss = _loss_elasticnet(
                    yc, Xb, beta, cfg.lam, cfg.elastic_alpha
                )

            if loss + cfg.early_stop_tol < best:
                best = loss
                stall = 0
            else:
                stall += 1
                if stall >= cfg.early_stop_patience:
                    break

        # -------- คำนวณ R^2 --------
        yhat_final = Xb @ beta
        ss_res = float(np.sum((yc - yhat_final) ** 2))
        ss_tot = float(np.sum(yc ** 2))
        r2 = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
        # ----------------------------------------

        return {
            "beta": beta.tolist(),
            "mu": mu.tolist(),
            "sigma": sigma.tolist(),
            "y_mean": float(y_mean),
            "reg": cfg.reg,
            "lambda": cfg.lam,
            "elastic_alpha": cfg.elastic_alpha,
            "epochs_trained": ep + 1,
            "final_loss": float(best),
            "r2": r2,  
            "feature_order": self.feature_order,
        }