"""
Automated Unit Tests for Dataset Validation and Quality Scoring.
"""

import os
import pytest
import pandas as pd
from app.services.dataset_service import dataset_service
from ml.generate_synthetic_data import generate_charging_time_series, generate_sample_acn_sessions


def test_synthetic_data_generation():
    """Verify synthetic time-series generator output properties."""
    df = generate_charging_time_series(days=2, interval_minutes=15)
    assert len(df) == 2 * 24 * 4  # 192 intervals
    assert "station_demand_kw" in df.columns
    assert "active_sessions" in df.columns
    assert (df["station_demand_kw"] >= 0).all()
    assert (df["station_demand_kw"] <= 150.0).all()  # Transformer limit respected


def test_sample_acn_dataset_properties():
    """Verify sample ACN session generation schema."""
    acn_df = generate_sample_acn_sessions(num_sessions=20)
    assert len(acn_df) == 20
    assert "sessionID" in acn_df.columns
    assert "kWhDelivered" in acn_df.columns
    assert "userInputs_kWhRequested" in acn_df.columns
    assert (acn_df["userInputs_kWhRequested"] > 0).all()


def test_dataset_quality_inspection(tmp_path):
    """Test data quality metrics and missing value detection."""
    test_csv = tmp_path / "test_data.csv"
    df = pd.DataFrame({
        "timestamp": ["2026-10-18 08:00:00", "2026-10-18 08:15:00", "2026-10-18 08:30:00"],
        "active_sessions": [4, None, 5],
        "station_demand_kw": [45.2, 52.1, -5.0],  # Has 1 negative and 1 NaN
        "tariff_rate": [0.20, 0.20, 0.20]
    })
    df.to_csv(test_csv, index=False)

    report = dataset_service.analyze_csv_quality(str(test_csv), "test_data.csv")
    assert report.total_rows == 3
    assert report.missing_values_count == 1
    assert report.negative_values_found == 1
    assert report.quality_score_pct < 100.0
    assert len(report.warnings) >= 1
