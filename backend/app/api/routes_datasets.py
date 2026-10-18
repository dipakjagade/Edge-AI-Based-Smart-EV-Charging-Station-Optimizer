"""
Dataset Management API Routes.
"""

import os
import shutil
import uuid
from typing import List
from fastapi import APIRouter, HTTPException, UploadFile, File, Query
from app.config import settings
from app.models.dataset import DatasetSummaryResponse
from app.services.dataset_service import dataset_service
from app.database import db_manager
from ml.generate_synthetic_data import generate_charging_time_series

router = APIRouter(prefix="/api/datasets", tags=["Datasets"])


@router.post("/upload", response_model=DatasetSummaryResponse)
async def upload_dataset(file: UploadFile = File(...)):
    """Upload and inspect a CSV dataset."""
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files (.csv) are currently supported.")
        
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    safe_filename = f"{uuid.uuid4().hex[:6]}_{file.filename}"
    saved_path = os.path.join(settings.UPLOAD_DIR, safe_filename)
    
    with open(saved_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    try:
        summary = dataset_service.save_dataset_metadata(saved_path, file.filename)
        return summary
    except Exception as e:
        if os.path.exists(saved_path):
            os.remove(saved_path)
        raise HTTPException(status_code=400, detail=f"Failed to parse CSV dataset: {str(e)}")


@router.get("", response_model=List[DatasetSummaryResponse])
def list_datasets():
    col = db_manager.get_collection("datasets")
    docs = col.find()
    
    # If empty, register default benchmark datasets if they exist on disk
    if not docs:
        default_files = [
            ("synthetic_ev_charging_data.csv", "Synthetic EV Charging Station Telemetry (90 Days)"),
            ("sample_acn_data.csv", "Caltech/JPL ACN-Data Sample Format")
        ]
        for fname, desc in default_files:
            fpath = os.path.join(settings.DATA_DIR, fname)
            if os.path.exists(fpath):
                try:
                    summary = dataset_service.save_dataset_metadata(fpath, fname)
                except Exception:
                    pass
        docs = col.find()
        
    return [DatasetSummaryResponse(**d) for d in docs]


@router.get("/{id}", response_model=DatasetSummaryResponse)
def get_dataset(id: str):
    col = db_manager.get_collection("datasets")
    doc = col.find_one({"id": id}) or col.find_one({"_id": id})
    if not doc:
        raise HTTPException(status_code=404, detail=f"Dataset record '{id}' not found.")
    return DatasetSummaryResponse(**doc)


@router.post("/generate-synthetic")
def generate_new_synthetic_dataset(days: int = Query(90, ge=7, le=365)):
    """Generate a new fresh synthetic time-series dataset."""
    try:
        df = generate_charging_time_series(days=days)
        filename = f"synthetic_{days}d_{uuid.uuid4().hex[:4]}.csv"
        filepath = os.path.join(settings.DATA_DIR, filename)
        df.to_csv(filepath, index=False)
        summary = dataset_service.save_dataset_metadata(filepath, filename)
        return {
            "message": f"Successfully generated {days} days ({len(df)} 15-min intervals) of synthetic data.",
            "dataset": summary
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Synthetic data generation failed: {str(e)}")
