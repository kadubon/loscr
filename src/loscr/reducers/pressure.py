"""Bottleneck-pressure reducer."""

from __future__ import annotations

from loscr.hashing import canonical_hash
from loscr.models import PressureReducerOutput, ServiceReducerOutput, WipReducerOutput


def pressure_reducer(
    wip: WipReducerOutput,
    service: ServiceReducerOutput,
    *,
    bottleneck_floor: float = 1.0,
) -> PressureReducerOutput:
    """Compute a lightweight deterministic bottleneck-pressure index."""
    pressure: dict[str, float] = {}
    for key, count in wip.unresolved_wip_by_scope_station_stratum.items():
        parts = key.split("|")
        station = parts[1] if len(parts) >= 2 else key
        pressure[station] = pressure.get(station, 0.0) + float(count)
    for queue in service.queue_states:
        station = queue.service_unit_id
        pressure[station] = pressure.get(station, 0.0) + queue.outstanding + queue.oldest_age
        if queue.overloaded:
            pressure[station] = pressure.get(station, 0.0) + bottleneck_floor
    bottlenecks = sorted(station for station, value in pressure.items() if value >= bottleneck_floor)
    output = PressureReducerOutput(
        pressure_by_station=dict(sorted(pressure.items())),
        bottleneck_stations=bottlenecks,
    )
    return output.model_copy(update={"output_hash": canonical_hash(output)})
