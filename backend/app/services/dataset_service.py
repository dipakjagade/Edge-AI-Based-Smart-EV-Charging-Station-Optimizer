"""
Dataset Management, Column Mapping, and Data Quality Service.
Handles CSV uploads, ACN-Data format adaptation, timestamp cleaning,
and data quality validation.
"""

import os
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
from app.config import settings
from app.models.dataset import DatasetQualityReport, DatasetSummaryResponse
from app.database import db_manager


class DatasetService:
    def __init__(self):
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    def analyze_csv_quality(self, file_path: str, dataset_name: str) -> DatasetQualityReport:
        """Inspect and score data quality of uploaded CSV file."""
        df = pd.read_csv(file_path)
        total_rows = len(df)
        total_cols = len(df.columns)
        
        # Check missing values
        missing_count = int(df.isnull().sum().sum())
        missing_pct = round((missing_count / max(1, total_rows * total_cols)) * 100.0, 2)
        
        # Check duplicates
        dup_count = int(df.duplicated().sum())
        
        # Check negative values in numeric columns
        num_cols = df.select_dtypes(include=[np.number]).columns
        negative_count = int((df[num_cols] < 0).sum().sum()) if len(num_cols) > 0 else 0
        
        # Format detection
        cols_lower = [c.lower() for c in df.columns]
        warnings: List[str] = []
        
        if any("session" in c for c in cols_lower) and any("kwh" in c for c in cols_lower):
            detected_format = "acn_data"
        elif any("station_demand" in c for c in cols_lower) or any("active_sessions" in c for c in cols_lower):
            detected_format = "time_series"
        else:
            detected_format = "generic_csv"
            warnings.append("Custom column names detected. Manual column mapping is recommended before training.")

        if missing_pct > 5.0:
            warnings.append(f"High missing value rate ({missing_pct}%). Automatic imputation or row filtering advised.")
        if negative_count > 0:
            warnings.append(f"Found {negative_count} negative measurements in numeric fields. Power and energy must be positive.")
        if dup_count > 0:
            warnings.append(f"Found {dup_count} duplicate rows in dataset.")

        # Compute Quality Score (0 - 100%)
        deductions = (missing_pct * 2.0) + (min(dup_count, 20) * 0.5) + (min(negative_count, 20) * 0.5)
        quality_score = max(10.0, round(100.0 - deductions, 1))
        
        is_valid_training = (detected_format == "time_series" or ("active_sessions" in df.columns)) and missing_pct < 15.0
        is_valid_scheduling = ("requested_energy_kwh" in cols_lower) or ("userinputs_kwhrequested" in cols_lower) or ("kwh" in "".join(cols_lower))

        column_types = {col: str(df[col].dtype) for col in df.columns}
        preview = df.head(5).fillna("").to_dict(orient="records")

        return DatasetQualityReport(
            dataset_name=dataset_name,
            total_rows=total_rows,
            total_columns=total_cols,
            detected_format=detected_format,
            missing_values_count=missing_count,
            missing_percentage=missing_pct,
            duplicate_rows_count=dup_count,
            negative_values_found=negative_count,
            quality_score_pct=quality_score,
            is_valid_for_training=is_valid_training,
            is_valid_for_scheduling=is_valid_scheduling,
            warnings=warnings,
            column_types=column_types,
            preview_rows=preview
        )

    def save_dataset_metadata(self, file_path: str, filename: str) -> DatasetSummaryResponse:
        quality_report = self.analyze_csv_quality(file_path, filename)
        file_size = os.path.getsize(file_path)
        doc_id = f"DS-{uuid.uuid4().hex[:8].upper()}"
        
        summary = DatasetSummaryResponse(
            id=doc_id,
            filename=filename,
            file_path=file_path,
            file_size_bytes=file_size,
            uploaded_at=datetime.now().isoformat(),
            row_count=quality_report.total_rows,
            column_count=quality_report.total_columns,
            quality_report=quality_report
        )
        
        try:
            col = db_manager.get_collection("datasets")
            col.insert_one(summary.dict())
        except Exception as e:
            print(f"[*] Dataset metadata persistence note: {e}")
            
        return summary


dataset_service = DatasetService()
