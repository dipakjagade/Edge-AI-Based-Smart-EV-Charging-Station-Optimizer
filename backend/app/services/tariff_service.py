"""
Electricity Tariff and Cost Analytics Service.
Calculates energy delivery costs, peak demand penalties, and compares
uncontrolled vs. smart-allocated vs. advanced time-of-use scheduled charging.
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta
import numpy as np


class TariffService:
    def __init__(self):
        # Default tariff schedule: off-peak ($0.12), mid-peak ($0.20), on-peak ($0.35)
        self.default_tariffs = {
            "off_peak": 0.12,
            "mid_peak": 0.20,
            "on_peak": 0.35,
            "demand_charge_usd_per_kw": 12.50
        }

    def get_hourly_rate(self, hour: int, custom_tariffs: Dict[str, float] = None) -> float:
        tariffs = custom_tariffs or self.default_tariffs
        if 22 <= hour or hour < 6:
            return tariffs.get("off_peak", 0.12)
        elif 14 <= hour < 20:
            return tariffs.get("on_peak", 0.35)
        else:
            return tariffs.get("mid_peak", 0.20)

    def calculate_cost_comparison(
        self,
        energy_kwh: float = 350.0,
        uncontrolled_peak_kw: float = 180.0,
        optimized_peak_kw: float = 120.0,
        station_limit_kw: float = 150.0,
        hours_distribution: List[int] = None
    ) -> Dict[str, Any]:
        """
        Compare three operating strategies:
        1. Uncontrolled Charging: Full rate immediately upon arrival (typically overlapping with peak hours).
        2. Basic Smart Allocation: Caps peak at station transformer limit.
        3. Advanced Time-of-Use Scheduling: Shifts flexible EV charging into off-peak valley hours.
        """
        # Baseline: 65% on-peak, 25% mid-peak, 10% off-peak
        uncontrolled_energy_cost = energy_kwh * (0.65 * 0.35 + 0.25 * 0.20 + 0.10 * 0.12)
        # Demand charge penalty for exceeding transformer limit (demand charge = $12.50/kW peak)
        uncontrolled_demand_charge = max(0.0, uncontrolled_peak_kw - station_limit_kw) * 25.0 + (uncontrolled_peak_kw * 12.50)
        uncontrolled_total = uncontrolled_energy_cost + uncontrolled_demand_charge

        # Basic Allocation: 50% on-peak, 35% mid-peak, 15% off-peak, peak strictly clamped at station limit
        basic_peak = min(uncontrolled_peak_kw, station_limit_kw)
        basic_energy_cost = energy_kwh * (0.50 * 0.35 + 0.35 * 0.20 + 0.15 * 0.12)
        basic_demand_charge = basic_peak * 12.50
        basic_total = basic_energy_cost + basic_demand_charge

        # Advanced TOU Scheduled: 10% on-peak, 30% mid-peak, 60% off-peak valley, peak shaved to 110 kW
        adv_peak = min(optimized_peak_kw, station_limit_kw * 0.80)
        adv_energy_cost = energy_kwh * (0.10 * 0.35 + 0.30 * 0.20 + 0.60 * 0.12)
        adv_demand_charge = adv_peak * 12.50
        adv_total = adv_energy_cost + adv_demand_charge

        savings_vs_uncontrolled = max(0.0, uncontrolled_total - adv_total)
        savings_pct = (savings_vs_uncontrolled / max(1.0, uncontrolled_total)) * 100.0

        # Hourly cost curve (24 hours)
        hourly_curve = []
        for h in range(24):
            rate = self.get_hourly_rate(h)
            # Simulated typical load
            uncontrolled_kw = round(float(25.0 + 130.0 * np.exp(-0.5 * ((h - 17.5) / 2.5) ** 2)), 1)
            adv_kw = round(float(20.0 + 65.0 * np.exp(-0.5 * ((h - 2) / 3.0) ** 2) + 40.0 * np.exp(-0.5 * ((h - 11) / 3.0) ** 2)), 1)
            hourly_curve.append({
                "hour": f"{h:02d}:00",
                "tariff_rate_usd": rate,
                "tier": "Off-Peak" if (22 <= h or h < 6) else ("On-Peak" if 14 <= h < 20 else "Mid-Peak"),
                "uncontrolled_load_kw": uncontrolled_kw,
                "optimized_load_kw": adv_kw,
                "uncontrolled_cost_usd": round(uncontrolled_kw * rate, 2),
                "optimized_cost_usd": round(adv_kw * rate, 2)
            })

        return {
            "comparison_summary": {
                "uncontrolled_baseline": {
                    "strategy": "Uncontrolled (Immediate Max Charging)",
                    "energy_cost_usd": round(uncontrolled_energy_cost, 2),
                    "demand_charge_usd": round(uncontrolled_demand_charge, 2),
                    "total_cost_usd": round(uncontrolled_total, 2),
                    "peak_demand_kw": round(uncontrolled_peak_kw, 2),
                    "transformer_overload": uncontrolled_peak_kw > station_limit_kw
                },
                "basic_power_allocation": {
                    "strategy": "Basic Water-Filling (Transformer Constrained)",
                    "energy_cost_usd": round(basic_energy_cost, 2),
                    "demand_charge_usd": round(basic_demand_charge, 2),
                    "total_cost_usd": round(basic_total, 2),
                    "peak_demand_kw": round(basic_peak, 2),
                    "transformer_overload": False
                },
                "advanced_tou_scheduling": {
                    "strategy": "Advanced 15-min Time-of-Use Scheduling",
                    "energy_cost_usd": round(adv_energy_cost, 2),
                    "demand_charge_usd": round(adv_demand_charge, 2),
                    "total_cost_usd": round(adv_total, 2),
                    "peak_demand_kw": round(adv_peak, 2),
                    "transformer_overload": False
                }
            },
            "simulated_savings": {
                "dollar_savings_usd": round(savings_vs_uncontrolled, 2),
                "percentage_savings": round(savings_pct, 1),
                "peak_shaved_kw": round(uncontrolled_peak_kw - adv_peak, 2),
                "peak_shaved_pct": round(((uncontrolled_peak_kw - adv_peak) / uncontrolled_peak_kw) * 100.0, 1)
            },
            "hourly_load_and_cost_curve": hourly_curve
        }


tariff_service = TariffService()
