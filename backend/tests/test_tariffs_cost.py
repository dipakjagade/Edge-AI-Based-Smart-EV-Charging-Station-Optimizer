"""
Automated Tests for Electricity Tariffs, Cost Analytics, and Baseline Comparison.
"""

import pytest
from app.services.tariff_service import tariff_service


def test_time_of_use_tariff_schedule():
    """Verify tariff rates reflect off-peak, mid-peak, and on-peak hours."""
    assert tariff_service.get_hourly_rate(2) == 0.12   # 02:00 Off-peak
    assert tariff_service.get_hourly_rate(10) == 0.20  # 10:00 Mid-peak
    assert tariff_service.get_hourly_rate(17) == 0.35  # 17:00 On-peak


def test_cost_comparison_analytics():
    """Verify cost comparison between uncontrolled, basic, and advanced strategies."""
    res = tariff_service.calculate_cost_comparison(
        energy_kwh=400.0,
        uncontrolled_peak_kw=180.0,
        optimized_peak_kw=120.0,
        station_limit_kw=150.0
    )
    summary = res["comparison_summary"]
    uncontrolled = summary["uncontrolled_baseline"]
    basic = summary["basic_power_allocation"]
    advanced = summary["advanced_tou_scheduling"]

    # Advanced schedule must yield lowest energy procurement cost
    assert advanced["total_cost_usd"] < uncontrolled["total_cost_usd"]
    assert uncontrolled["transformer_overload"] is True
    assert basic["transformer_overload"] is False
    assert res["simulated_savings"]["percentage_savings"] > 0.0
    assert len(res["hourly_load_and_cost_curve"]) == 24
