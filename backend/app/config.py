"""
Configuration settings for Edge AI Smart EV Charging Station Optimizer.
"""

import os
from pydantic import BaseModel


class Settings(BaseModel):
    PROJECT_NAME: str = "Edge AI Smart EV Charging Station Optimizer"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    
    # Host & Port
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # Station Default Configuration
    DEFAULT_STATION_CAPACITY_KW: float = float(os.getenv("STATION_CAPACITY_KW", "150.0"))
    DEFAULT_MAX_CHARGERS: int = int(os.getenv("MAX_CHARGERS", "10"))
    DEFAULT_CHARGER_MAX_KW: float = float(os.getenv("DEFAULT_CHARGER_MAX_KW", "22.0"))
    
    # MongoDB Settings
    MONGODB_URI: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "smart_ev_charging_db")
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "super-secret-edge-ev-optimizer-key-change-in-prod-2026")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # Paths
    BASE_DIR: str = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    MODEL_DIR: str = os.path.join(BASE_DIR, "saved_models")
    MODEL_PATH: str = os.path.join(MODEL_DIR, "rf_demand_model.joblib")
    MODEL_METADATA_PATH: str = os.path.join(MODEL_DIR, "model_metadata.json")
    DATA_DIR: str = os.path.join(BASE_DIR, "data")
    UPLOAD_DIR: str = os.path.join(DATA_DIR, "uploads")
    
    # Fallback / Demo mode
    DEMO_MODE: bool = True
    EDGE_MODE: bool = True


settings = Settings()
