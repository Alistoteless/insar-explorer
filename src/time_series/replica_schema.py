"""Shared schema helpers for Replica interval presets and marker symbols."""

import math

import numpy as np

# Replica intervals represent half the nominal radar wavelength (lambda / 2).
REPLICA_INTERVAL_PRESETS = (
    ("s1", "Sentinel-1", 27.8),
    ("tsx", "TerraSAR-X", 15.5),
    ("alos", "ALOS", 118.0),
    ("nisar_l", "NISAR (L-band)", 120.0),
)

REPLICA_INTERVAL_MATCH_TOLERANCE_MM = 0.05


def replica_preset_id_for_interval(interval_mm):
    """Return the matching preset identifier, or ``None`` for a custom interval."""
    try:
        interval = float(interval_mm)
    except (TypeError, ValueError):
        return None
    for preset_id, _label, preset_interval in REPLICA_INTERVAL_PRESETS:
        if math.isclose(
            interval,
            preset_interval,
            rel_tol=0.0,
            abs_tol=REPLICA_INTERVAL_MATCH_TOLERANCE_MM,
        ):
            return preset_id
    return None


def replica_interval_for_preset(preset_id):
    """Return the interval for a named preset, or ``None`` for Custom/unknown."""
    for candidate_id, _label, interval in REPLICA_INTERVAL_PRESETS:
        if candidate_id == preset_id:
            return interval
    return None


def residual_replica_value_pairs(residual_values, interval_mm, pair_count):
    """Return Replica values transformed into the canonical residual domain.

    Canonical residuals are ``observed - fitted``. Main-plot Replica values are
    ``observed ± offset``, therefore the aligned residual-domain values are
    ``residual ± offset``. Invalid/NaN samples remain invalid naturally and no
    interpolation is introduced.
    """
    if residual_values is None:
        return []
    try:
        interval = float(interval_mm)
        count = max(1, min(10, int(pair_count)))
    except (TypeError, ValueError, OverflowError):
        return []
    if not np.isfinite(interval):
        return []
    base = np.asarray(residual_values, dtype=np.float64)
    return [
        (base + interval * (index + 1), base - interval * (index + 1))
        for index in range(count)
    ]
