import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "integrations" in data
    assert "gemma" in data["integrations"]
    assert "tabpfn" in data["integrations"]

def test_sample_datasets():
    response = client.get("/api/sample-datasets")
    assert response.status_code == 200
    data = response.json()
    assert "candles" in data
    assert "leather" in data
    assert "digital" in data
    assert "default_candidate" in data["candles"]

def test_generate_listing():
    payload = {
        "title": "Nordic Pine Scented Soy Candle 8oz",
        "category": "Home & Living / Candles",
        "materials": "Soy Wax, Pine Essential Oil, Wooden Wick",
        "features": "50-hour burn time, crackling wick, gift box included",
        "target_audience": "Cabin decor lovers and aromatherapy enthusiasts",
        "tone": "Artisan & Authentic",
        "platform": "Etsy"
    }
    response = client.post("/api/generate-listing", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "optimized_title" in data
    assert "hook" in data
    assert "description" in data
    assert "seo_tags" in data
    assert len(data["seo_tags"]) > 0
    assert "bullet_points" in data
    assert "_meta" in data

def test_predict_pricing_candles():
    payload = {
        "dataset_type": "candles",
        "candidate_item": {
            "material_cost": 4.90,
            "labor_hours": 0.6,
            "competitor_avg_price": 25.00,
            "photo_count": 6,
            "is_q4_holiday": 1,
            "free_shipping": 1
        },
        "target_column": "final_price"
    }
    response = client.post("/api/predict-pricing", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "optimal_recommended_price" in data
    assert data["optimal_recommended_price"] > 0
    assert "estimated_units_sold" in data
    assert "projected_monthly_revenue" in data
    assert "elasticity_curve" in data
    assert len(data["elasticity_curve"]) == 7
    assert "_meta" in data

def test_generate_voice_promo():
    payload = {
        "script_text": "Check out our hand-poured autumn candles made with natural soy wax and crackling wood wicks!",
        "voice_preset": "warm_artisan"
    }
    response = client.post("/api/generate-voice", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "script" in data
    assert "voice_name" in data
    assert "engine" in data

def test_upload_csv():
    csv_content = b"item_id,material_cost,labor_hours,final_price\n1,5.0,0.5,22.0\n2,6.0,0.6,26.0\n3,4.5,0.4,19.0\n"
    response = client.post(
        "/api/upload-csv",
        files={"file": ("test.csv", csv_content, "text/csv")}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["row_count"] == 3
    assert "final_price" in data["columns"]
