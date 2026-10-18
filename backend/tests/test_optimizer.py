"""
Automated Tests for Smart Charging Power Optimizer and Scheduling Algorithms.
"""

from datetime import datetime, timedelta
import pytest
from app.services.optimizer_service import optimizer_service
from app.models.optimization import OptimizationRequest, VehicleOptimizationInput


def test_station_capacity_and_charger_limits():
    """Verify total allocated power <= station capacity and each P_i <= max_kw."""
    now = datetime(2026, 10, 18, 9, 0, 0)
    sessions = [
        VehicleOptimizationInput(
            session_id=f"EV-TEST-{i}",
            arrival_time=(now - timedelta(minutes=15)).isoformat(),
            departure_time=(now + timedelta(hours=2)).isoformat(),
            max_power_kw=22.0,
            requested_energy_kwh=40.0,
            priority=3
        )
        for i in range(8)  # 8 * 22 kW = 176 kW uncapped > 100 kW station limit
    ]

    req = OptimizationRequest(
        station_power_limit_kw=100.0,
        mode="water_filling",
        sessions=sessions,
        current_time=now.isoformat()
    )
    res = optimizer_service.optimize(req)

    assert res.total_allocated_power_kw <= 100.0 + 1e-4
    for a in res.allocations:
        assert a.allocated_power_kw <= a.max_power_kw
        assert a.allocated_power_kw >= 0.0


def test_zero_energy_receives_zero_power():
    """Sessions with zero remaining energy must receive exactly 0 kW."""
    now = datetime(2026, 10, 18, 10, 0, 0)
    sessions = [
        VehicleOptimizationInput(
            session_id="EV-FULL-01",
            arrival_time=(now - timedelta(minutes=30)).isoformat(),
            departure_time=(now + timedelta(hours=2)).isoformat(),
            max_power_kw=22.0,
            requested_energy_kwh=30.0,
            already_delivered_kwh=30.0,  # 0 remaining
            priority=5
        ),
        VehicleOptimizationInput(
            session_id="EV-NEED-02",
            arrival_time=(now - timedelta(minutes=10)).isoformat(),
            departure_time=(now + timedelta(hours=2)).isoformat(),
            max_power_kw=22.0,
            requested_energy_kwh=35.0,
            already_delivered_kwh=5.0,
            priority=3
        )
    ]
    req = OptimizationRequest(
        station_power_limit_kw=150.0,
        sessions=sessions,
        current_time=now.isoformat()
    )
    res = optimizer_service.optimize(req)

    full_alloc = next(a for a in res.allocations if a.session_id == "EV-FULL-01")
    need_alloc = next(a for a in res.allocations if a.session_id == "EV-NEED-02")
    assert full_alloc.allocated_power_kw == 0.0
    assert need_alloc.allocated_power_kw > 0.0


def test_reject_duplicate_session_ids():
    """Duplicate session IDs must produce a clear validation error."""
    now = datetime.now()
    sessions = [
        VehicleOptimizationInput(
            session_id="EV-DUPLICATE",
            arrival_time=now.isoformat(),
            departure_time=(now + timedelta(hours=2)).isoformat(),
            max_power_kw=22.0,
            requested_energy_kwh=30.0
        ),
        VehicleOptimizationInput(
            session_id="EV-DUPLICATE",
            arrival_time=now.isoformat(),
            departure_time=(now + timedelta(hours=3)).isoformat(),
            max_power_kw=11.0,
            requested_energy_kwh=20.0
        )
    ]
    req = OptimizationRequest(
        station_power_limit_kw=150.0,
        sessions=sessions
    )
    with pytest.raises(ValueError) as excinfo:
        optimizer_service.optimize(req)
    assert "Duplicate session_id" in str(excinfo.value)


def test_infeasible_deadline_detection():
    """When vehicle needs 50 kWh in 1 hour but charger max is 22 kW, mark infeasible."""
    now = datetime(2026, 10, 18, 12, 0, 0)
    sessions = [
        VehicleOptimizationInput(
            session_id="EV-IMPOSSIBLE-01",
            arrival_time=now.isoformat(),
            departure_time=(now + timedelta(hours=1)).isoformat(),  # Only 1 hour
            max_power_kw=22.0,  # Max possible in 1h is 22 kWh
            requested_energy_kwh=50.0,  # 50 kWh requested
            priority=5
        )
    ]
    req = OptimizationRequest(
        station_power_limit_kw=150.0,
        sessions=sessions,
        current_time=now.isoformat()
    )
    res = optimizer_service.optimize(req)
    alloc = res.allocations[0]

    assert alloc.can_complete_before_departure is False
    assert alloc.unmet_energy_kwh > 20.0
    assert alloc.infeasibility_reason is not None
    assert "Hardware constraint" in alloc.infeasibility_reason


def test_advanced_15min_scheduler():
    """Verify multi-period time-slot schedule generation."""
    now = datetime(2026, 10, 18, 14, 0, 0)
    sessions = [
        VehicleOptimizationInput(
            session_id="EV-SCHED-01",
            arrival_time=now.isoformat(),
            departure_time=(now + timedelta(hours=4)).isoformat(),
            max_power_kw=22.0,
            requested_energy_kwh=35.0,
            priority=4
        )
    ]
    req = OptimizationRequest(
        station_power_limit_kw=150.0,
        mode="advanced_scheduler",
        sessions=sessions,
        current_time=now.isoformat()
    )
    res = optimizer_service.optimize(req)

    assert res.mode == "advanced_scheduler"
    assert res.time_slot_schedule is not None
    assert len(res.time_slot_schedule) > 0
    assert "optimized_total_cost_usd" in res.cost_summary
