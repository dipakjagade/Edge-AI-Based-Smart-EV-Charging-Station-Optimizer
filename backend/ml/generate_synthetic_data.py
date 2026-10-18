"""
Synthetic Data Generator for Edge AI Smart EV Charging Station Optimizer.
Generates realistic, physically plausible EV charging telemetry and demand time-series data.
"""

import os
import argparse
from datetime import datetime, timedelta
import numpy as np
import pandas as pd


def generate_charging_time_series(
    start_date: str = "2026-01-01",
    days: int = 90,
    interval_minutes: int = 15,
    station_capacity_kw: float = 150.0,
    random_seed: int = 42
) -> pd.DataFrame:
    """
    Generate 15-minute interval time series simulating an EV charging hub.
    Features:
      - Daily diurnal traffic peaks (morning commute 07:00-10:00, evening commute 16:00-20:00)
      - Weekend vs weekday profile variations
      - Active sessions, requested energy, average SOC
      - Lagged demands (1h and 24h prior)
      - Time-of-use tariffs
      - Target: station_demand_kw (constrained by station transformer capacity)
    """
    np.random.seed(random_seed)
    start_dt = datetime.fromisoformat(start_date)
    total_steps = int((days * 24 * 60) / interval_minutes)
    
    timestamps = [start_dt + timedelta(minutes=i * interval_minutes) for i in range(total_steps)]
    
    df = pd.DataFrame({"timestamp": timestamps})
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["hour"] = df["timestamp"].dt.hour
    df["minute"] = df["timestamp"].dt.minute
    df["day_of_week"] = df["timestamp"].dt.dayofweek
    df["is_weekend"] = (df["day_of_week"] >= 5).astype(int)
    
    # Calculate base expected demand based on time of day and weekend factor
    # Morning peak around 8-9am, evening peak around 17-19pm
    morning_peak = np.exp(-0.5 * ((df["hour"] + df["minute"]/60.0 - 8.5) / 1.5) ** 2)
    evening_peak = np.exp(-0.5 * ((df["hour"] + df["minute"]/60.0 - 18.0) / 2.0) ** 2)
    midday_activity = 0.4 * np.exp(-0.5 * ((df["hour"] + df["minute"]/60.0 - 13.0) / 3.0) ** 2)
    night_trough = 0.05
    
    weekday_profile = morning_peak * 0.85 + evening_peak * 0.95 + midday_activity + night_trough
    # Weekend: peaks shift later (11:00 - 16:00 shopping/leisure)
    weekend_peak = np.exp(-0.5 * ((df["hour"] + df["minute"]/60.0 - 13.5) / 3.5) ** 2)
    weekend_profile = weekend_peak * 0.70 + 0.1
    
    activity_intensity = np.where(df["is_weekend"] == 1, weekend_profile, weekday_profile)
    # Add random fluctuation
    noise = np.random.normal(0, 0.08, size=total_steps)
    activity_factor = np.clip(activity_intensity + noise, 0.02, 1.0)
    
    # Max EVSE ports at station = 10
    max_chargers = 10
    df["active_sessions"] = np.round(activity_factor * max_chargers).astype(int)
    df["active_sessions"] = np.clip(df["active_sessions"], 0, max_chargers)
    
    # Requested energy across active vehicles
    # Average EV needs ~25-45 kWh per session
    energy_per_active = np.random.uniform(20.0, 45.0, size=total_steps)
    df["total_requested_energy_kwh"] = np.round(df["active_sessions"] * energy_per_active, 2)
    
    # Average incoming SOC (typically lower during evening commute)
    base_soc = 35.0 - (activity_factor * 10.0) + np.random.normal(0, 4.0, size=total_steps)
    df["avg_battery_soc"] = np.round(np.clip(base_soc, 10.0, 85.0), 1)
    # When active_sessions is 0, default SOC to neutral 50.0
    df.loc[df["active_sessions"] == 0, "avg_battery_soc"] = 50.0
    
    # Time-of-Use Tariff ($/kWh)
    # Off-peak (22:00 - 06:00): $0.12
    # Mid-peak (06:00 - 14:00, 20:00 - 22:00): $0.20
    # Peak (14:00 - 20:00): $0.35
    def compute_tariff(hour):
        if 22 <= hour or hour < 6:
            return 0.12
        elif 14 <= hour < 20:
            return 0.35
        else:
            return 0.20
            
    df["tariff_rate"] = df["hour"].apply(compute_tariff)
    
    # Outdoor ambient temperature (seasonal sinusoid + daily curve)
    day_indices = np.array([(t - start_dt).days for t in df["timestamp"]])
    daily_temp_cycle = 8.0 * np.sin(2 * np.pi * (df["hour"] - 9) / 24.0)
    seasonal_temp = 18.0 + 10.0 * np.sin(2 * np.pi * (day_indices - 30) / 365.0)
    df["temperature_c"] = np.round(seasonal_temp + daily_temp_cycle + np.random.normal(0, 1.2, size=total_steps), 1)
    
    # Raw demand generation (kW)
    # Each vehicle typically consumes between 7.4 kW (AC Level 2) and 22 kW / 50 kW fast charge
    avg_kw_per_session = np.random.uniform(10.5, 14.5, size=total_steps)
    raw_demand = df["active_sessions"] * avg_kw_per_session
    # Power factor and charger efficiency losses (~92%)
    raw_demand = raw_demand / 0.92
    # Apply hard physical station capacity limit
    df["station_demand_kw"] = np.round(np.clip(raw_demand, 0.0, station_capacity_kw), 2)
    
    # Create Lagged demand features strictly chronologically (prevents data leakage)
    # 1 hour prior (4 steps of 15 min)
    df["lagged_demand_1h_kw"] = df["station_demand_kw"].shift(4).bfill()
    # 24 hours prior (96 steps of 15 min)
    df["lagged_demand_24h_kw"] = df["station_demand_kw"].shift(96).bfill()
    
    # Rolling 3-hour mean demand
    df["rolling_mean_3h_kw"] = df["station_demand_kw"].shift(1).rolling(window=12, min_periods=1).mean().bfill()
    df["rolling_mean_3h_kw"] = np.round(df["rolling_mean_3h_kw"], 2)
    
    return df


def generate_sample_acn_sessions(num_sessions: int = 120, random_seed: int = 42) -> pd.DataFrame:
    """
    Generate sample ACN-Data format session records (similar to Caltech / JPL ACN dataset).
    Fields:
      - sessionID, connectionTime, disconnectTime, kWhDelivered, userInputs_kWhRequested, stationID
    """
    np.random.seed(random_seed)
    base_date = datetime(2026, 3, 1, 8, 0, 0)
    
    records = []
    station_ids = [f"EVSE-0{i}" for i in range(1, 9)]
    
    for i in range(num_sessions):
        # Arrival offset within a 2-week period
        arrival_delta = timedelta(days=np.random.randint(0, 14), hours=np.random.randint(6, 21), minutes=np.random.randint(0, 59))
        conn_time = base_date + arrival_delta
        # Stay duration between 1.5 hours and 8 hours
        duration_hours = np.random.uniform(1.5, 7.5)
        disc_time = conn_time + timedelta(hours=duration_hours)
        
        requested_kwh = round(float(np.random.uniform(15.0, 55.0)), 2)
        # Delivered kWh might be equal to or slightly lower than requested
        delivered_kwh = round(min(requested_kwh, requested_kwh * np.random.uniform(0.85, 1.0)), 2)
        
        records.append({
            "sessionID": f"ACN-{1000 + i}",
            "stationID": np.random.choice(station_ids),
            "connectionTime": conn_time.strftime("%Y-%m-%d %H:%M:%S"),
            "disconnectTime": disc_time.strftime("%Y-%m-%d %H:%M:%S"),
            "userInputs_kWhRequested": requested_kwh,
            "kWhDelivered": delivered_kwh,
            "maxPower_kW": np.random.choice([11.0, 22.0, 50.0])
        })
        
    return pd.DataFrame(records)


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic EV charging datasets.")
    parser.add_argument("--days", type=int, default=90, help="Number of days to simulate")
    parser.add_argument("--out-dir", type=str, default="backend/data", help="Output directory")
    args = parser.parse_args()
    
    os.makedirs(args.out_dir, exist_ok=True)
    
    # 1. Generate station time series
    print(f"[*] Generating {args.days} days of 15-minute EV charging telemetry...")
    ts_df = generate_charging_time_series(days=args.days)
    ts_path = os.path.join(args.out_dir, "synthetic_ev_charging_data.csv")
    ts_df.to_csv(ts_path, index=False)
    print(f"[+] Saved time series dataset ({len(ts_df)} rows) to: {ts_path}")
    
    # 2. Generate ACN sample format
    print("[*] Generating sample ACN-Data format session logs...")
    acn_df = generate_sample_acn_sessions(num_sessions=150)
    acn_path = os.path.join(args.out_dir, "sample_acn_data.csv")
    acn_df.to_csv(acn_path, index=False)
    print(f"[+] Saved ACN format dataset ({len(acn_df)} rows) to: {acn_path}")


if __name__ == "__main__":
    main()
