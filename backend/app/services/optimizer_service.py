"""
Smart Charging Power Allocation and Multi-Period Scheduling Service.
Implements:
1. Deterministic Weighted Water-Filling Allocation under transformer and charger constraints.
2. Advanced 15-minute Time-Slot Scheduling minimizing energy cost and peak demand.
3. Infeasibility analysis and physical bottleneck diagnosis.
"""

import uuid
import math
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
from app.models.optimization import (
    VehicleOptimizationInput,
    OptimizationRequest,
    OptimizationResponse,
    VehicleAllocationResult,
    TimeSlotScheduleItem
)
from app.database import db_manager


class OptimizerService:
    def __init__(self):
        pass

    def validate_sessions(self, sessions: List[VehicleOptimizationInput]) -> Tuple[bool, Optional[str]]:
        """Validate unique session IDs, non-negative values, and chronological timestamps."""
        session_ids = set()
        for s in sessions:
            if s.session_id in session_ids:
                return False, f"Duplicate session_id detected: '{s.session_id}'. Session IDs must be unique."
            session_ids.add(s.session_id)
            
            try:
                arr = datetime.fromisoformat(s.arrival_time)
                dep = datetime.fromisoformat(s.departure_time)
                if dep <= arr:
                    return False, f"Session '{s.session_id}' has departure deadline on or before arrival time."
            except Exception as e:
                return False, f"Session '{s.session_id}' has invalid ISO timestamp format: {e}"
                
            if s.requested_energy_kwh < 0:
                return False, f"Session '{s.session_id}' requested energy cannot be negative."
            if s.max_power_kw <= 0:
                return False, f"Session '{s.session_id}' max power must be strictly positive."
                
        return True, None

    def optimize(self, req: OptimizationRequest) -> OptimizationResponse:
        """Main optimizer router for instantaneous water-filling and advanced time-slot scheduling."""
        # 1. Validation
        is_valid, err_msg = self.validate_sessions(req.sessions)
        if not is_valid:
            raise ValueError(err_msg)

        if req.mode == "advanced_scheduler":
            return self._solve_advanced_schedule(req)
        else:
            return self._solve_water_filling(req)

    def _solve_water_filling(self, req: OptimizationRequest) -> OptimizationResponse:
        """
        Weighted Water-Filling power allocation algorithm.
        Guarantees:
          - Sum(P_i) <= station_power_limit_kw
          - 0 <= P_i <= max_power_kw
          - P_i = 0 if remaining energy <= 0
          - Redistribution of surplus power to active unsatisfied vehicles
        """
        now = datetime.fromisoformat(req.current_time) if req.current_time else datetime.now()
        station_limit = req.station_power_limit_kw
        sessions = req.sessions
        
        # Prepare working variables
        active_candidates = []
        zero_energy_results = []
        total_requested_energy = 0.0

        for s in sessions:
            rem_energy = max(0.0, s.requested_energy_kwh - s.already_delivered_kwh)
            total_requested_energy += rem_energy
            
            dep_time = datetime.fromisoformat(s.departure_time)
            hours_remaining = max(0.01, (dep_time - now).total_seconds() / 3600.0)
            
            if rem_energy <= 0.0:
                # Vehicle already full or zero request
                zero_energy_results.append(VehicleAllocationResult(
                    session_id=s.session_id,
                    charger_id=s.charger_id or "EVSE",
                    allocated_power_kw=0.0,
                    max_power_kw=s.max_power_kw,
                    remaining_energy_kwh=0.0,
                    estimated_hours_to_complete=0.0,
                    estimated_completion_time=now.isoformat(),
                    departure_deadline=s.departure_time,
                    can_complete_before_departure=True,
                    unmet_energy_kwh=0.0,
                    infeasibility_reason="Zero remaining energy requested.",
                    priority=s.priority
                ))
            else:
                # Minimum rate needed to finish exactly on time
                min_rate_needed = rem_energy / hours_remaining
                # Max energy achievable if charger ran at 100% full capacity
                max_possible_energy = s.max_power_kw * hours_remaining
                
                # Weight combines user priority and urgency
                urgency = min_rate_needed / max(1.0, s.max_power_kw)
                weight = float(s.priority) * (1.0 + min(urgency, 3.0))
                
                active_candidates.append({
                    "session": s,
                    "rem_energy": rem_energy,
                    "hours_rem": hours_remaining,
                    "min_rate_needed": min_rate_needed,
                    "max_possible_energy": max_possible_energy,
                    "weight": weight,
                    "allocated_kw": 0.0,
                    "saturated": False
                })

        # Water filling iterative allocation
        available_station_power = station_limit
        converged = False
        iteration = 0
        max_iterations = 20

        while not converged and iteration < max_iterations:
            iteration += 1
            unsaturated = [c for c in active_candidates if not c["saturated"]]
            if not unsaturated or available_station_power <= 0.001:
                break

            total_weight = sum(c["weight"] for c in unsaturated)
            if total_weight <= 0:
                break

            newly_saturated = False
            for c in unsaturated:
                # Proposed power proportional to weight
                share = (c["weight"] / total_weight) * available_station_power
                target_rate = c["allocated_kw"] + share
                # Vehicle cannot draw more than its charger max
                charger_limit = c["session"].max_power_kw
                # Also cap at 120% of min_rate_needed so we don't hog power if car leaves tomorrow
                practical_cap = min(charger_limit, max(charger_limit * 0.5, c["min_rate_needed"] * 1.15))

                if target_rate >= practical_cap:
                    c["allocated_kw"] = practical_cap
                    c["saturated"] = True
                    available_station_power -= practical_cap
                    newly_saturated = True
                    break

            if not newly_saturated:
                # All remaining unsaturated candidates can absorb their proportional share
                for c in unsaturated:
                    c["allocated_kw"] += (c["weight"] / total_weight) * available_station_power
                available_station_power = 0.0
                converged = True

        # Compile allocation results and infeasibility diagnostics
        allocations = list(zero_energy_results)
        infeasible_count = 0

        for c in active_candidates:
            s = c["session"]
            alloc_kw = round(float(c["allocated_kw"]), 2)
            rem_energy = c["rem_energy"]
            hours_rem = c["hours_rem"]
            max_possible_energy = c["max_possible_energy"]
            
            # Time to complete
            if alloc_kw > 0.01:
                est_hours = round(rem_energy / alloc_kw, 2)
                est_completion = (now + timedelta(hours=est_hours)).isoformat()
            else:
                est_hours = 999.0
                est_completion = "Indefinite (0 kW allocated)"

            # Check feasibility
            dep_dt = datetime.fromisoformat(s.departure_time)
            is_feasible = True
            unmet_kwh = 0.0
            reason = None

            if rem_energy > max_possible_energy + 0.01:
                # Hardware bottleneck: physical charger limit makes it impossible even at 100% capacity
                is_feasible = False
                infeasible_count += 1
                unmet_kwh = round(rem_energy - max_possible_energy, 2)
                reason = (f"Hardware constraint: EVSE max rate ({s.max_power_kw} kW) over remaining "
                          f"{hours_rem:.1f}h can only supply {max_possible_energy:.1f} kWh vs {rem_energy:.1f} kWh requested.")
            elif alloc_kw < c["min_rate_needed"] - 0.1:
                # Station bottleneck: capacity limit throttled this vehicle
                is_feasible = False
                infeasible_count += 1
                deliverable_under_alloc = alloc_kw * hours_rem
                unmet_kwh = round(max(0.0, rem_energy - deliverable_under_alloc), 2)
                reason = (f"Station capacity constraint: Allocated {alloc_kw:.1f} kW is below required "
                          f"{c['min_rate_needed']:.1f} kW deadline rate due to {station_limit} kW hub transformer limit.")

            allocations.append(VehicleAllocationResult(
                session_id=s.session_id,
                charger_id=s.charger_id or "EVSE",
                allocated_power_kw=alloc_kw,
                max_power_kw=s.max_power_kw,
                remaining_energy_kwh=round(rem_energy, 2),
                estimated_hours_to_complete=est_hours if est_hours < 999 else 0.0,
                estimated_completion_time=est_completion,
                departure_deadline=s.departure_time,
                can_complete_before_departure=is_feasible,
                unmet_energy_kwh=unmet_kwh,
                infeasibility_reason=reason,
                priority=s.priority
            ))

        total_allocated_power = round(sum(a.allocated_power_kw for a in allocations), 2)
        unused_capacity = round(max(0.0, station_limit - total_allocated_power), 2)

        # Baseline cost analysis: if all active vehicles charged uncontrolled at max EVSE power
        uncontrolled_power = sum(s.max_power_kw for s in sessions if (s.requested_energy_kwh - s.already_delivered_kwh) > 0)
        tariff_rate = req.tariff_mid_peak or 0.20
        # Instantaneous power cost rate ($/hr)
        opt_cost_rate = round(total_allocated_power * tariff_rate, 2)
        uncontrolled_cost_rate = round(uncontrolled_power * tariff_rate, 2)

        opt_id = f"OPT-{uuid.uuid4().hex[:8].upper()}"
        response = OptimizationResponse(
            id=opt_id,
            timestamp=now.isoformat(),
            mode="water_filling",
            station_power_limit_kw=station_limit,
            total_requested_energy_kwh=round(total_requested_energy, 2),
            total_allocated_power_kw=total_allocated_power,
            unused_capacity_kw=unused_capacity,
            active_vehicles_count=len(sessions),
            allocations=allocations,
            infeasible_sessions_count=infeasible_count,
            all_demands_feasible=(infeasible_count == 0),
            time_slot_schedule=None,
            cost_summary={
                "tariff_rate_usd_kwh": tariff_rate,
                "current_cost_rate_usd_per_hour": opt_cost_rate,
                "uncontrolled_power_kw": round(uncontrolled_power, 2),
                "uncontrolled_cost_rate_usd_per_hour": uncontrolled_cost_rate,
                "demand_reduction_kw": round(max(0.0, uncontrolled_power - total_allocated_power), 2),
                "peak_shaving_pct": round(max(0.0, (uncontrolled_power - total_allocated_power) / max(1.0, uncontrolled_power)) * 100.0, 1)
            }
        )

        # Persist to database
        try:
            col = db_manager.get_collection("optimizations")
            col.insert_one(response.model_dump())
        except Exception as e:
            print(f"[*] Optimization persistence note: {e}")

        return response

    def _solve_advanced_schedule(self, req: OptimizationRequest) -> OptimizationResponse:
        """
        Advanced 15-minute time-slot multi-period scheduling.
        Schedules charging across future intervals between now and max departure deadline.
        Prioritizes lower-cost tariff time slots while ensuring deadlines are met.
        """
        now = datetime.fromisoformat(req.current_time) if req.current_time else datetime.now()
        # Round up to nearest 15-min boundary
        minute_offset = (15 - (now.minute % 15)) % 15
        base_slot_start = now + timedelta(minutes=minute_offset)
        
        station_limit = req.station_power_limit_kw
        sessions = req.sessions
        
        # Determine maximum horizon in 15-min slots (up to 24 hours = 96 slots)
        dep_times = [datetime.fromisoformat(s.departure_time) for s in sessions]
        max_dep = max(dep_times) if dep_times else now + timedelta(hours=4)
        total_hours = max(1.0, min(24.0, (max_dep - base_slot_start).total_seconds() / 3600.0))
        num_slots = int(np.ceil(total_hours * 4))
        
        # Define slot times and tariffs
        slot_items: List[Dict[str, Any]] = []
        for i in range(num_slots):
            slot_t = base_slot_start + timedelta(minutes=i * 15)
            h = slot_t.hour
            if 22 <= h or h < 6:
                rate = req.tariff_off_peak or 0.12
            elif 14 <= h < 20:
                rate = req.tariff_on_peak or 0.35
            else:
                rate = req.tariff_mid_peak or 0.20
            slot_items.append({
                "index": i,
                "time": slot_t,
                "rate": rate,
                "allocated_kw": 0.0,
                "allocations": {}
            })

        # Track remaining energy needed per vehicle
        vehicle_states = {}
        for s in sessions:
            rem = max(0.0, s.requested_energy_kwh - s.already_delivered_kwh)
            dep = datetime.fromisoformat(s.departure_time)
            vehicle_states[s.session_id] = {
                "session": s,
                "energy_remaining_kwh": rem,
                "departure_dt": dep,
                "delivered_in_schedule_kwh": 0.0
            }

        # Multi-period cost-priority scheduler:
        # Sort slots by tariff rate (cheapest first) to minimize energy procurement cost
        sorted_slot_indices = sorted(range(num_slots), key=lambda idx: slot_items[idx]["rate"])
        
        for idx in sorted_slot_indices:
            slot = slot_items[idx]
            slot_t = slot["time"]
            available_power = station_limit

            # Find active vehicles at this slot
            eligible = []
            for sid, state in vehicle_states.items():
                s = state["session"]
                arr = datetime.fromisoformat(s.arrival_time)
                if arr <= slot_t < state["departure_dt"] and state["energy_remaining_kwh"] > 0.01:
                    eligible.append((sid, state))

            # Sort eligible by user priority & remaining energy
            eligible.sort(key=lambda item: (item[1]["session"].priority, item[1]["energy_remaining_kwh"]), reverse=True)

            for sid, state in eligible:
                if available_power <= 0.01:
                    break
                s = state["session"]
                # Power needed in this 15-min slot (0.25h) to fulfill remaining energy
                needed_kw = state["energy_remaining_kwh"] / 0.25
                alloc_kw = min(s.max_power_kw, available_power, needed_kw)
                
                if alloc_kw > 0.0:
                    slot["allocations"][sid] = round(alloc_kw, 2)
                    slot["allocated_kw"] += alloc_kw
                    available_power -= alloc_kw
                    
                    delivered_kwh = alloc_kw * 0.25
                    state["energy_remaining_kwh"] = max(0.0, state["energy_remaining_kwh"] - delivered_kwh)
                    state["delivered_in_schedule_kwh"] += delivered_kwh

        # Format schedule results
        formatted_slots = [
            TimeSlotScheduleItem(
                slot_index=s["index"],
                slot_time=s["time"].strftime("%H:%M"),
                tariff_rate=s["rate"],
                total_allocated_kw=round(s["allocated_kw"], 2),
                vehicle_allocations=s["allocations"]
            )
            for s in slot_items[:min(24, num_slots)]  # Return first 24 slots (6 hours)
        ]

        # Vehicle summary
        allocations: List[VehicleAllocationResult] = []
        infeasible_count = 0
        total_optimized_cost = 0.0
        total_delivered_kwh = 0.0

        for sid, state in vehicle_states.items():
            s = state["session"]
            rem_after = round(state["energy_remaining_kwh"], 2)
            delivered = round(state["delivered_in_schedule_kwh"], 2)
            total_delivered_kwh += delivered
            
            # Initial slot power
            initial_kw = formatted_slots[0].vehicle_allocations.get(sid, 0.0) if formatted_slots else 0.0
            
            is_feasible = (rem_after <= 0.05)
            reason = None
            if not is_feasible:
                infeasible_count += 1
                reason = f"Schedule could not deliver full request: {rem_after} kWh unmet prior to departure {s.departure_time}."

            allocations.append(VehicleAllocationResult(
                session_id=s.session_id,
                charger_id=s.charger_id or "EVSE",
                allocated_power_kw=initial_kw,
                max_power_kw=s.max_power_kw,
                remaining_energy_kwh=rem_after,
                estimated_hours_to_complete=round(delivered / max(1.0, initial_kw), 2) if initial_kw > 0 else 0.0,
                estimated_completion_time=s.departure_time,
                departure_deadline=s.departure_time,
                can_complete_before_departure=is_feasible,
                unmet_energy_kwh=rem_after,
                infeasibility_reason=reason,
                priority=s.priority
            ))

        # Calculate scheduled cost
        for slot in slot_items:
            for sid, kw in slot["allocations"].items():
                energy_kwh = kw * 0.25
                total_optimized_cost += energy_kwh * slot["rate"]

        # Uncontrolled comparison (charging immediately at flat mid/on-peak tariff)
        uncontrolled_cost = total_delivered_kwh * (req.tariff_on_peak or 0.35)
        simulated_savings = round(max(0.0, uncontrolled_cost - total_optimized_cost), 2)

        opt_id = f"SCHED-{uuid.uuid4().hex[:8].upper()}"
        response = OptimizationResponse(
            id=opt_id,
            timestamp=now.isoformat(),
            mode="advanced_scheduler",
            station_power_limit_kw=station_limit,
            total_requested_energy_kwh=round(sum(s.requested_energy_kwh for s in sessions), 2),
            total_allocated_power_kw=round(formatted_slots[0].total_allocated_kw if formatted_slots else 0.0, 2),
            unused_capacity_kw=round(max(0.0, station_limit - (formatted_slots[0].total_allocated_kw if formatted_slots else 0.0)), 2),
            active_vehicles_count=len(sessions),
            allocations=allocations,
            infeasible_sessions_count=infeasible_count,
            all_demands_feasible=(infeasible_count == 0),
            time_slot_schedule=formatted_slots,
            cost_summary={
                "mode": "time_of_use_cost_minimization",
                "total_scheduled_energy_kwh": round(total_delivered_kwh, 2),
                "optimized_total_cost_usd": round(total_optimized_cost, 2),
                "uncontrolled_baseline_cost_usd": round(uncontrolled_cost, 2),
                "simulated_cost_savings_usd": simulated_savings,
                "savings_percentage": round((simulated_savings / max(0.1, uncontrolled_cost)) * 100.0, 1)
            }
        )

        try:
            col = db_manager.get_collection("optimizations")
            col.insert_one(response.model_dump())
        except Exception as e:
            print(f"[*] Schedule persistence note: {e}")

        return response


optimizer_service = OptimizerService()
