import random
import time


def analyze_building(
    lat: float, lon: float, tilt: float, azimuth: float, pv_kwp: float, losses: float
) -> dict:
    """Mock PVGIS analysis function."""
    time.sleep(random.uniform(0.1, 0.3))
    base_yield = 1100 + (40 - lat) * 15
    specific_yield = base_yield + random.uniform(-50, 50)
    total_production = specific_yield * pv_kwp
    import math

    monthly_series = []
    for i in range(12):
        month_factor = (1 - math.cos((i - 6) * math.pi / 6)) / 2
        monthly_production = total_production / 12 * (0.7 + month_factor * 0.6)
        monthly_series.append(round(monthly_production, 2))
    return {
        "pv_potential_kwh": round(total_production, 2),
        "pv_kwp": pv_kwp,
        "yield_kwh_per_kwp": round(specific_yield, 2),
        "confidence": round(random.uniform(0.85, 0.99), 2),
        "monthly_series": monthly_series,
        "dev_mode": True,
    }