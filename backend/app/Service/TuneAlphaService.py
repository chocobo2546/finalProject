from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import numpy as np

from app.Service.TrainService import RegType, _add_bias, _loss_lasso, _loss_ridge, _soft_threshold


class TunAlphaService:
    """Hyperparameter tuning helpers (alpha and lambda) for GD training."""

    @staticmethod
    def _standardize(X: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        mu = X.mean(axis=0)
        sigma = X.std(axis=0)
        sigma[sigma == 0] = 1.0
        return (X - mu) / sigma, mu, sigma

    @staticmethod
    def _safe_alpha_grid(Xs: np.ndarray, lam: float, reg: RegType, n: int = 13) -> np.ndarray:
        if Xs.size == 0:
            return np.logspace(-10, -2, n)

        try:
            s = np.linalg.svd(Xs, compute_uv=False)
            smax = float(s[0]) if s.size else 1.0
        except Exception:
            smax = 1.0

        # Lipschitz constant for gradient of SSE is 2*smax^2.
        # - Ridge adds +2*lam for the penalized part (approx).
        # - Lasso uses proximal step, so we only need the SSE Lipschitz.
        if reg == "ridge":
            L = 2.0 * (smax ** 2 + float(lam))
        else:
            L = 2.0 * (smax ** 2)

        base = 1.0 / max(L, 1e-12)
        return base * np.logspace(-3, 3, n)

    @staticmethod
    def _epochs_to_target(losses: np.ndarray, ratio: float = 0.1) -> Optional[int]:
        if losses.size == 0:
            return None
        target = losses[0] * ratio
        hit = np.where(losses <= target)[0]
        return int(hit[0]) if hit.size else None

    @staticmethod
    def _is_stable(losses: np.ndarray, max_up_frac: float = 0.2) -> bool:
        if losses.size < 5:
            return True
        up_steps = np.sum(losses[1:] > losses[:-1])
        return (up_steps / max(losses.size - 1, 1)) <= max_up_frac

    def tune_alpha(
        self,
        X: np.ndarray,
        y: np.ndarray,
        reg: RegType = "ridge",
        lam: float = 10.0,
        alphas: Optional[np.ndarray] = None,
        epochs: int = 800,
        seed: int = 42,
    ) -> Dict:
        """Pick a stable learning rate (alpha) for a fixed lambda."""
        if X.size == 0 or y.size == 0:
            return {"best_alpha": None, "candidates": []}

        rng = np.random.default_rng(seed)
        idx = np.arange(len(y))
        rng.shuffle(idx)
        X, y = X[idx], y[idx]

        Xs, _, _ = self._standardize(X)
        yc = y - y.mean()

        if alphas is None:
            alphas = self._safe_alpha_grid(Xs, lam=lam, reg=reg, n=13)

        results: List[Dict] = []

        for a in alphas:
            a = float(a)
            Xb = _add_bias(Xs)
            beta = np.zeros(Xb.shape[1], dtype=float)
            losses = np.empty(int(epochs), dtype=float)

            exploded = False
            for ep in range(int(epochs)):
                yhat = Xb @ beta
                if reg == "ridge":
                    grad = -2.0 * (Xb.T @ (yc - yhat))
                    grad[1:] += 2.0 * float(lam) * beta[1:]
                    beta = beta - a * grad
                    loss = _loss_ridge(yc, Xb, beta, lam)
                else:
                    grad_sse = -2.0 * (Xb.T @ (yc - yhat))
                    beta_tmp = beta - a * grad_sse
                    beta_tmp[1:] = _soft_threshold(beta_tmp[1:], a * float(lam))
                    beta = beta_tmp
                    loss = _loss_lasso(yc, Xb, beta, lam)

                losses[ep] = float(loss)
                if not np.isfinite(loss) or loss > 1e20:
                    exploded = True
                    losses = losses[: ep + 1]
                    break

            final_loss = float(losses[-1]) if losses.size else float("inf")
            stable = (not exploded) and self._is_stable(losses, max_up_frac=0.2)
            ep10 = self._epochs_to_target(losses, ratio=0.1)
            results.append(
                {
                    "alpha": a,
                    "final_loss": final_loss if not exploded else float("inf"),
                    "epochs_to_10pct": ep10,
                    "stable": bool(stable),
                    "n_epochs": int(losses.size),
                }
            )

        stable_list = [r for r in results if r["stable"] and np.isfinite(r["final_loss"])]
        if stable_list:
            stable_list.sort(key=lambda r: (r["final_loss"], r["epochs_to_10pct"] or 1e9))
            return {"best_alpha": stable_list[0]["alpha"], "candidates": results}

        ok = [r for r in results if np.isfinite(r["final_loss"])]
        if ok:
            ok.sort(key=lambda r: (r["final_loss"], r["epochs_to_10pct"] or 1e9))
            return {"best_alpha": ok[0]["alpha"], "candidates": results}

        return {"best_alpha": None, "candidates": results}

    def tune_lambda(
        self,
        X: np.ndarray,
        y: np.ndarray,
        reg: RegType,
        alpha: float,
        lambdas: Optional[np.ndarray] = None,
        k: int = 5,
        epochs: int = 1500,
        seed: int = 42,
    ) -> Dict:
        """Pick lambda via k-fold CV (minimizing MSE)."""
        if X.size == 0 or y.size == 0:
            return {"best_lambda": None, "candidates": []}

        if lambdas is None:
            lambdas = np.logspace(-3, 3, 13)

        n = len(y)
        rng = np.random.default_rng(seed)
        idx = np.arange(n)
        rng.shuffle(idx)
        folds = np.array_split(idx, int(k))

        cand_summary: List[Dict] = []
        for lam in lambdas:
            lam = float(lam)
            mse_sum = 0.0
            fold_mse: List[float] = []

            for val_idx in folds:
                tr_idx = np.setdiff1d(idx, val_idx)
                Xtr, ytr = X[tr_idx], y[tr_idx]
                Xva, yva = X[val_idx], y[val_idx]

                Xtr_s, mu, sigma = self._standardize(Xtr)
                Xva_s = (Xva - mu) / sigma

                yc = ytr - ytr.mean()
                Xb_tr = _add_bias(Xtr_s)
                beta = np.zeros(Xb_tr.shape[1], dtype=float)

                for _ in range(int(epochs)):
                    yhat = Xb_tr @ beta
                    if reg == "ridge":
                        grad = -2.0 * (Xb_tr.T @ (yc - yhat))
                        grad[1:] += 2.0 * lam * beta[1:]
                        beta = beta - float(alpha) * grad
                    else:
                        grad_sse = -2.0 * (Xb_tr.T @ (yc - yhat))
                        beta_tmp = beta - float(alpha) * grad_sse
                        beta_tmp[1:] = _soft_threshold(beta_tmp[1:], float(alpha) * lam)
                        beta = beta_tmp

                # evaluate on validation
                Xb_va = _add_bias(Xva_s)
                y_pred_c = Xb_va @ beta
                y_pred = y_pred_c + ytr.mean()
                mse = float(np.mean((yva - y_pred) ** 2))
                mse_sum += mse
                fold_mse.append(mse)

            avg_mse = mse_sum / max(int(k), 1)
            cand_summary.append({"lambda": lam, "cv_mse": float(avg_mse), "fold_mse": fold_mse})

        cand_summary.sort(key=lambda r: r["cv_mse"])
        best_lambda = cand_summary[0]["lambda"] if cand_summary else None
        return {"best_lambda": best_lambda, "candidates": cand_summary}
