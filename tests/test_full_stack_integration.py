"""End-to-end integration test suite verifying DB, ML, Backend, and Frontend connectivity."""

import pytest
import sys
from pathlib import Path

# Add backend and root to sys.path
ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "backend"
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from fastapi.testclient import TestClient
import ml
from backend.mongodb_client import check_mongo_connection, get_mongo_db
from backend.main import app

client = TestClient(app)


def test_mongodb_atlas_connectivity():
    """Verify live connectivity, database schema, and record counts on MongoDB Atlas."""
    status = check_mongo_connection()
    assert status["connected"] is True, f"MongoDB Atlas not connected: {status.get('message')}"
    assert status["database"] == "menumind"
    assert status["collections_count"] >= 5

    # Verify core collections have expected seed data
    stats = status["collection_stats"]
    assert stats.get("sales_history", 0) >= 1000, "sales_history should have 16,814 operational records"
    assert stats.get("food_items", 0) >= 40, "food_items should have 51 dish catalog records"

    # Query MongoDB directly
    db = get_mongo_db()
    sample = db.sales_history.find_one({}, {"_id": 0})
    assert sample is not None
    assert "item_name" in sample
    assert "qty_sold" in sample


def test_ml_pipeline_integration():
    """Verify machine learning engine functions execute cleanly with loaded model artifacts."""
    # 1. 7-Day Recursive Horizon Forecasting
    forecast = ml.predict_7_day_demand(start_date="2025-05-12")
    assert forecast["start_date"] == "2025-05-12"
    assert len(forecast["daily_forecasts"]) == 7
    assert forecast["total_forecast_demand"] > 0
    assert forecast["total_forecast_preparation"] >= forecast["total_forecast_demand"]

    # 2. SciPy HiGHS Menu Mix Optimization
    menu = ml.generate_weekly_menu(start_date="2025-05-12", min_dishes_per_day=4, max_dishes_per_day=8)
    assert menu["days_planned"] == 7
    assert len(menu["daily_plans"]) == 7
    assert menu["baseline_comparison"]["impact_improvements"]["profit_increase_pct"].startswith("+")

    # 3. Regret Meter Calculation
    regret = ml.calculate_regret_metrics()
    assert 0.0 <= regret["regret_index_score"] <= 100.0
    assert regret["total_avoidable_financial_loss_inr"] > 0
    assert regret["currency"] == "INR"


def test_backend_api_integration():
    """Verify FastAPI backend endpoints serve live data from MongoDB Atlas and ML Engine."""
    # 1. Health and System Status
    r = client.get("/api/system/status")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "HEALTHY"
    assert data["architecture"]["database"]["mongodb_atlas"]["connected"] is True
    assert data["architecture"]["ml_engine"]["status"] == "ONLINE"
    assert data["architecture"]["backend"]["framework"] == "FastAPI"

    # 2. MongoDB Data Endpoints
    r_sales = client.get("/api/db/sales-history?limit=10")
    assert r_sales.status_code == 200
    sales_data = r_sales.json()
    assert sales_data["count"] == 10
    assert sales_data["total_in_collection"] >= 1000

    r_items = client.get("/api/db/food-items")
    assert r_items.status_code == 200
    items_data = r_items.json()
    assert items_data["count"] >= 40

    # 3. ML Endpoints
    r_fc = client.post("/api/ml/forecast-7days", json={"start_date": "2025-05-12"})
    assert r_fc.status_code == 200
    assert len(r_fc.json()["daily_forecasts"]) == 7

    r_opt = client.post("/api/ml/optimize-menu", json={"start_date": "2025-05-12", "min_dishes_per_day": 8})
    assert r_opt.status_code == 200
    assert r_opt.json()["days_planned"] == 7

    r_reg = client.get("/api/ml/regret-meter")
    assert r_reg.status_code == 200
    assert r_reg.json()["total_avoidable_financial_loss_inr"] > 0

    r_surplus = client.get("/api/surplus/ai-recommendations?current_time_str=17:00")
    assert r_surplus.status_code == 200
    assert r_surplus.json()["discount_percentage"] > 0


def test_frontend_build_and_launcher_configuration():
    """Verify frontend build artifacts exist and launchers properly point to frontend01."""
    # 1. Build bundle check
    dist_index = ROOT_DIR / "frontend01" / "dist" / "index.html"
    assert dist_index.exists(), "Frontend build bundle dist/index.html must exist"

    # 2. Vite config proxy check
    vite_config = (ROOT_DIR / "frontend01" / "vite.config.ts").read_text(encoding="utf-8")
    assert "http://127.0.0.1:8000" in vite_config
    assert "'/api'" in vite_config or '"/api"' in vite_config

    # 3. Launchers target check
    start_bat = (ROOT_DIR / "start_dev.bat").read_text(encoding="utf-8")
    assert "cd frontend01" in start_bat
    assert ".venv" in start_bat

    start_ps1 = (ROOT_DIR / "start_dev.ps1").read_text(encoding="utf-8")
    assert "frontend01" in start_ps1
    assert ".venv" in start_ps1
