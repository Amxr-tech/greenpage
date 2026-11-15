"""Carbon estimation based on the Sustainable Web Design Model (v4).

The SWD model converts bytes transferred into energy across three system
segments (data centres, networks, user devices), each split into
operational and embodied energy, then multiplies by grid carbon intensity.

Reference: https://sustainablewebdesign.org/estimating-digital-emissions/
All constants live here so they can be audited and updated in one place.
"""

from __future__ import annotations

from dataclasses import dataclass

BYTES_PER_GB = 1_000_000_000

# kWh per GB transferred, SWD v4.
OPERATIONAL_KWH_PER_GB = {
    "data_centre": 0.055,
    "network": 0.059,
    "user_device": 0.080,
}
EMBODIED_KWH_PER_GB = {
    "data_centre": 0.012,
    "network": 0.013,
    "user_device": 0.081,
}

# Global average grid intensity in gCO2e/kWh (Ember, used by SWD v4).
GLOBAL_GRID_INTENSITY = 494.0
# Intensity applied to data-centre operational energy for verified green hosts.
RENEWABLE_GRID_INTENSITY = 50.0

# SWD v4 digital carbon rating: upper bound in grams CO2e per page view.
RATINGS = (
    ("A+", 0.040),
    ("A", 0.079),
    ("B", 0.145),
    ("C", 0.209),
    ("D", 0.278),
    ("E", 0.359),
)


@dataclass(frozen=True)
class Estimate:
    bytes: int
    energy_kwh: float
    grams_co2e: float

    @property
    def rating(self) -> str:
        return rating_for(self.grams_co2e)


def rating_for(grams: float) -> str:
    for label, upper in RATINGS:
        if grams <= upper:
            return label
    return "F"


def estimate(
    num_bytes: int,
    *,
    green_hosting: bool = False,
    grid_intensity: float = GLOBAL_GRID_INTENSITY,
) -> Estimate:
    """Estimate the emissions of transferring ``num_bytes`` for one page view."""
    if num_bytes < 0:
        raise ValueError("num_bytes must be non-negative")
    if grid_intensity < 0:
        raise ValueError("grid_intensity must be non-negative")

    gb = num_bytes / BYTES_PER_GB
    total_kwh = 0.0
    grams = 0.0
    for segment in OPERATIONAL_KWH_PER_GB:
        op_kwh = gb * OPERATIONAL_KWH_PER_GB[segment]
        emb_kwh = gb * EMBODIED_KWH_PER_GB[segment]
        op_intensity = (
            RENEWABLE_GRID_INTENSITY
            if green_hosting and segment == "data_centre"
            else grid_intensity
        )
        total_kwh += op_kwh + emb_kwh
        # Embodied emissions happened at manufacture, so use the global grid.
        grams += op_kwh * op_intensity + emb_kwh * GLOBAL_GRID_INTENSITY
    return Estimate(bytes=num_bytes, energy_kwh=total_kwh, grams_co2e=grams)
