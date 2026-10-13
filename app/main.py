import os
import io
import time
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import pandas as pd

from app.config import settings
from app.engines.gemma_engine import gemma_engine
from app.engines.tabpfn_engine import tabpfn_engine
from app.engines.elevenlabs_engine import elevenlabs_engine

# Sentry Agent Tracing initialization
if settings.sentry_dsn:
    try:
        import sentry_sdk
        sentry_sdk.init(
            dsn=settings.sentry_dsn,
            traces_sample_rate=1.0,
            environment=settings.environment,
            send_default_pii=False
        )
        print("[Sentry] Tracing initialized successfully.")
    except Exception as e:
        print(f"[Sentry] Initialization warning: {e}")

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=settings.app_description
)

# Enable CORS for local testing & embedding
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Request Models
class ListingRequest(BaseModel):
    title: str
    category: str
    materials: str
    features: str
    target_audience: str
    tone: Optional[str] = "Artisan & Authentic"
    platform: Optional[str] = "Etsy"

class PricingPredictRequest(BaseModel):
    dataset_type: Optional[str] = "candles"  # candles, leather, digital, custom
    custom_csv_data: Optional[str] = None
    candidate_item: Dict[str, Any]
    target_column: Optional[str] = "final_price"

class VoiceRequest(BaseModel):
    script_text: str
    voice_preset: Optional[str] = "warm_artisan"
    custom_voice_id: Optional[str] = None

# Routes
@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index_file = os.path.join(static_dir, "index.html")
    if os.path.exists(index_file):
        with open(index_file, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse("<h1>HustlePulse AI is starting up...</h1>")

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": settings.app_version,
        "integrations": {
            "gemma": {
                "model": settings.gemma_model,
                "provider": settings.gemma_provider,
                "local_ollama": settings.ollama_base_url
            },
            "tabpfn": {
                "active": True,
                "foundation_model": "TabPFN-3.5 Prior Labs",
                "api_key_configured": bool(settings.tabpfn_api_key or settings.hf_token)
            },
            "elevenlabs": {
                "active": True,
                "configured": bool(settings.elevenlabs_api_key),
                "default_voice": settings.elevenlabs_voice_id
            },
            "sentry": {
                "tracing": bool(settings.sentry_dsn)
            }
        }
    }

@app.get("/api/sample-datasets")
async def get_sample_datasets():
    datasets = {
        "candles": {
            "name": "Handcrafted Soy Candles (Etsy Shop)",
            "file": "data/sample_candles.csv",
            "description": "Historical sales for artisanal scented soy candles with material costs, Q4 holiday flags, and units sold.",
            "default_candidate": {
                "material_cost": 4.90,
                "labor_hours": 0.6,
                "competitor_avg_price": 25.00,
                "photo_count": 6,
                "is_q4_holiday": 1,
                "free_shipping": 1
            }
        },
        "leather": {
            "name": "Custom Leathercraft & EDC Wallets",
            "file": "data/sample_leather_wallets.csv",
            "description": "Handmade Horween and Buttero leather wallets, custom engraving options, and labor times.",
            "default_candidate": {
                "material_cost": 12.50,
                "labor_hours": 1.5,
                "competitor_avg_price": 55.00,
                "photo_count": 7,
                "is_custom_engraved": 1,
                "free_shipping": 1
            }
        },
        "digital": {
            "name": "Digital Notion & Productivity Templates",
            "file": "data/sample_digital_templates.csv",
            "description": "Digital download templates with creation hours, template pages, and bonus assets.",
            "default_candidate": {
                "creation_hours": 15.0,
                "template_pages": 12,
                "competitor_avg_price": 32.00,
                "preview_images": 8,
                "includes_video_guide": 1,
                "free_bonus_assets": 1
            }
        }
    }
    return datasets

@app.post("/api/generate-listing")
async def api_generate_listing(payload: ListingRequest):
    try:
        result = await gemma_engine.generate_listing(payload.model_dump())
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Listing generation error: {str(e)}")

@app.post("/api/predict-pricing")
async def api_predict_pricing(payload: PricingPredictRequest):
    try:
        # Determine CSV source
        csv_path = None
        if payload.dataset_type == "candles":
            csv_path = "data/sample_candles.csv"
        elif payload.dataset_type == "leather":
            csv_path = "data/sample_leather_wallets.csv"
        elif payload.dataset_type == "digital":
            csv_path = "data/sample_digital_templates.csv"
        elif payload.custom_csv_data:
            csv_path = payload.custom_csv_data
        else:
            csv_path = "data/sample_candles.csv"

        result = tabpfn_engine.analyze_and_predict(
            csv_source=csv_path,
            candidate_item=payload.candidate_item,
            target_col=payload.target_column or "final_price"
        )
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TabPFN prediction error: {str(e)}")

@app.post("/api/upload-csv")
async def api_upload_csv(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        df = pd.read_csv(io.BytesIO(contents))
        preview = df.head(5).to_dict(orient="records")
        numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
        
        return {
            "filename": file.filename,
            "row_count": len(df),
            "columns": list(df.columns),
            "numeric_columns": numeric_cols,
            "preview": preview,
            "raw_csv": contents.decode("utf-8", errors="ignore")
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse CSV: {str(e)}")

@app.post("/api/generate-voice")
async def api_generate_voice(payload: VoiceRequest):
    try:
        result = await elevenlabs_engine.generate_promo_voice(
            script_text=payload.script_text,
            voice_preset=payload.voice_preset or "warm_artisan",
            custom_voice_id=payload.custom_voice_id
        )
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Voice synthesis error: {str(e)}")
