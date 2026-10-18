"""
Pydantic Models for Dataset Management, Column Mapping, and Data Quality.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class ColumnMappingRequest(BaseModel):
    timestamp_col: Optional[str] = "timestamp"
    session_id_col: Optional[str] = "sessionID"
    power_col: Optional[str] = "station_demand_kw"
    energy_col: Optional[str] = "userInputs_kWhRequested"
    arrival_col: Optional[str] = "connectionTime"
    departure_col: Optional[str] = "disconnectTime"


class DatasetQualityReport(BaseModel):
    dataset_name: str
    total_rows: int
    total_columns: int
    detected_format: str  # "time_series", "acn_data", "generic_csv"
    missing_values_count: int
    missing_percentage: float
    duplicate_rows_count: int
    negative_values_found: int
    quality_score_pct: float
    is_valid_for_training: bool
    is_valid_for_scheduling: bool
    warnings: List[str]
    column_types: Dict[str, str]
    preview_rows: List[Dict[str, Any]]


class DatasetSummaryResponse(BaseModel):
    id: str
    filename: str
    file_path: str
    file_size_bytes: int
    uploaded_at: str
    row_count: int
    column_count: int
    quality_report: DatasetQualityReport
