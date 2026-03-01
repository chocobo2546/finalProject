# app/Service/Controller.py
from __future__ import annotations

import json
import logging
import os
from typing import List, Literal, Optional

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field, ConfigDict

from app.db.database import Database
from app.Service.Model import ModelService
from app.Service.PredictionService import PredictService
from app.Service.ScrappingInterface import ScrappingService
from app.Service.TrainService import RegType, TrainConfig, TrainService
from app.Service.TuneAlphaService import TunAlphaService

logger = logging.getLogger(__name__)


# =========================
# Pydantic Models (GLOBAL ONLY)
# =========================
class PredictItem(BaseModel):
    year: int
    gear: Literal["ธรรมดา", "อัตโนมัติ"] | int | str
    mile: int


class PredictBatchRequest(BaseModel):
    items: List[PredictItem]


class TrainRequest(BaseModel):
    reg: RegType = "ridge"
    alpha: Optional[float] = None
    lambda_: Optional[float] = Field(default=None, alias="lambda")
    epochs: int = 20000
    standardize: bool = True
    center_y: bool = True
    auto_tune: bool = True
    k_fold: int = 5
    tune_epochs: int = 800

    # Pydantic v2 config (แก้ warning + รองรับ alias)
    model_config = ConfigDict(populate_by_name=True)


def _parse_cors_origins() -> List[str]:
    raw = os.environ.get(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173,http://frontend:5173",
    )
    return [o.strip() for o in raw.split(",") if o.strip()]


def create_app() -> FastAPI:
    logging.basicConfig(level=logging.INFO)

    app = FastAPI(title="Second-hand Car Price Prediction API")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=_parse_cors_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    db_path = os.environ.get("DB_PATH", "/app/data/data.db")
    db = Database(db_path=db_path)

    scrapping_service = ScrappingService()
    train_service = TrainService(scrapping_service.normalize_and_validate)
    tuner = TunAlphaService()
    model_service = ModelService()

    # ✅ ทำให้ robust: ถ้า PredictService รับ model_service ไม่ได้ ก็ยังรันได้
    try:
        predictor = PredictService(model_service)
    except TypeError:
        predictor = PredictService()

    @app.on_event("startup")
    def startup_event():
        logger.info("Initializing DB at %s", db_path)
        db.init_db()
        model_service.load()

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.get("/")
    def root():
        return {
            "message": "Car price prediction API is running",
            "endpoints": [
                "/cars",
                "/cars/stream",
                "/tune/alpha",
                "/tune/lambda",
                "/model/train",
                "/model/predict",
                "/model",
            ],
        }

    # ------------------------------
    # Scraping / Data APIs
    # ------------------------------
    @app.get("/cars")
    def get_cars():
        raw_items = db.get_all()
        data = []
        for r in raw_items:
            norm = scrapping_service.normalize_and_validate(r)
            if norm:
                data.append(norm)
        return {"data": data}

    @app.delete("/cars")
    def clear_cars():
        db.clear()
        return {"ok": True}

    @app.post("/cars/clear")
    def clear_cars_post():
        db.clear()
        return {"ok": True}

    @app.get("/cars/stream")
    def stream_cars(request: Request, base_url: str | None = Query(default=None)):
        def event_generator():
            try:
                for item in scrapping_service.stream_scrape(base_url=base_url):
                    try:
                        db.save_item(item)
                    except Exception as e:
                        logger.exception("DB save error: %s", e)

                    yield f"data: {json.dumps(item, default=str)}\n\n"
                    if request.client is None:
                        break
            except Exception as e:
                logger.exception("Stream error: %s", e)
                yield f"data: {json.dumps({'error': str(e)})}\n\n"

        return StreamingResponse(event_generator(), media_type="text/event-stream")

    # ------------------------------
    # Tuning APIs
    # ------------------------------
    @app.get("/tune/alpha")
    def tune_alpha(
        reg: RegType = Query("ridge"),
        lam: float = Query(10.0),
        epochs: int = Query(800),
    ):
        rows = db.get_all()
        X, y = train_service.build_xy(rows)
        if X.size == 0 or y.size == 0:
            raise HTTPException(status_code=400, detail="No valid rows. Please scrape more data.")
        out = tuner.tune_alpha(X, y, reg=reg, lam=lam, epochs=epochs)
        best = out.get("best_alpha")
        if best is None:
            raise HTTPException(status_code=422, detail="Unable to determine best alpha. Try more data.")
        return JSONResponse(content={"alpha": float(best)})

    @app.get("/tune/lambda")
    def tune_lambda(
        reg: RegType = Query("ridge"),
        alpha: float = Query(1e-6),
        k: int = Query(5),
        epochs: int = Query(1500),
    ):
        rows = db.get_all()
        X, y = train_service.build_xy(rows)
        if X.size == 0 or y.size == 0:
            raise HTTPException(status_code=400, detail="No valid rows. Please scrape more data.")
        out = tuner.tune_lambda(X, y, reg=reg, alpha=alpha, k=k, epochs=epochs)
        best = out.get("best_lambda")
        if best is None:
            raise HTTPException(status_code=422, detail="Unable to determine best lambda.")
        return JSONResponse(content={"lambda": float(best)})

    # ------------------------------
    # Model APIs
    # ------------------------------
    @app.get("/model")
    def get_model():
        m = model_service.get_model()
        return {"model": m}

    @app.post("/model/train")
    def train_model(req: TrainRequest):
        rows = db.get_all()
        X, y = train_service.build_xy(rows)
        if X.size == 0 or y.size == 0:
            raise HTTPException(status_code=400, detail="No valid rows. Please scrape more data.")

        lam = float(req.lambda_ if req.lambda_ is not None else 10.0)
        alpha = req.alpha

        if req.auto_tune:
            if alpha is None:
                out_a = tuner.tune_alpha(X, y, reg=req.reg, lam=lam, epochs=req.tune_epochs)
                alpha = out_a.get("best_alpha")
                if alpha is None:
                    raise HTTPException(status_code=422, detail="Unable to auto-tune alpha. Try more data.")
            if req.lambda_ is None:
                out_l = tuner.tune_lambda(X, y, reg=req.reg, alpha=float(alpha), k=req.k_fold, epochs=1500)
                lam_best = out_l.get("best_lambda")
                if lam_best is None:
                    raise HTTPException(status_code=422, detail="Unable to auto-tune lambda. Try more data.")
                lam = float(lam_best)
        else:
            if alpha is None:
                raise HTTPException(status_code=400, detail="alpha is required when auto_tune=false")

        cfg = TrainConfig(
            reg=req.reg,
            alpha=float(alpha),
            lam=float(lam),
            epochs=int(req.epochs),
            standardize=bool(req.standardize),
            center_y=bool(req.center_y),
        )

        model = train_service.fit(rows, cfg)
        if not model or model.get("beta") is None:
            raise HTTPException(status_code=422, detail=f"Training failed: {model.get('details', 'unknown')}")

        model_service.set_model(model)
        return JSONResponse(content=model)

    @app.post("/model/predict")
    def model_predict(req: PredictBatchRequest):
        model = model_service.get_model()
        if not model:
            raise HTTPException(status_code=400, detail="Model not trained. Please train first.")

        items = [
            (it.model_dump() if hasattr(it, "model_dump") else it.dict())
            for it in req.items
        ]
        return predictor.predict(model, items)

    # ------------------------------
    # Backward-compatible endpoints
    # ------------------------------
    @app.post("/model/train-price")
    def train_price_model(
        epochs: int = Query(20000),
        standardize: bool = Query(True),
        center_y: bool = Query(True),
    ):
        req = TrainRequest(
            reg="ridge",
            epochs=epochs,
            standardize=standardize,
            center_y=center_y,
            auto_tune=True,
        )
        return train_model(req)

    @app.post("/model/predict-price")
    def predict_price_legacy(req: PredictBatchRequest):
        # ✅ call the correct predict endpoint
        return model_predict(req)

    return app
