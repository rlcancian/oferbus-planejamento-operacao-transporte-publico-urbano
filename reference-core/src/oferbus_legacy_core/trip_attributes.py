from __future__ import annotations
from dataclasses import dataclass
from typing import Mapping, Sequence

from .numeric import vb_bankers_round
from .operations import OperationalTrip
from .timetable import DirectionPlanningData, MinimumTimetableConfig, PlannedTrip
from .virtual_time import virtual_arrival_legacy, virtual_departure_legacy


@dataclass(frozen=True)
class ExpressTravelParameters:
    base_express_minutes: float
    residual_percent: float


def complete_trip_attributes_legacy(
    planned_trips: Sequence[PlannedTrip],
    *,
    directions: Mapping[int, DirectionPlanningData],
    config: MinimumTimetableConfig,
    line_number: int = 0,
    express_parameters: Mapping[int, ExpressTravelParameters] | None = None,
) -> list[OperationalTrip]:
    """Port the normal execution path of ``Preenche_Todos_Atributos_Viagens``.

    The result intentionally resets links, vehicle, driver and conductor just as
    ``Preenche_Atributos_Viagem(..., Opcao=0)`` does before the march-diagram
    linking stage.
    """
    express_parameters = express_parameters or {}
    result: list[OperationalTrip] = []
    for planned in planned_trips:
        d = directions[planned.direction]
        departure = planned.real_departure
        idx = departure - d.start + 1
        if not 1 <= idx < len(d.travel_time_curve) - 1:
            raise IndexError("departure outside reconstructed travel-time curve")

        if (planned.trip_type % 2) == 0:
            virtual_departure = virtual_departure_legacy(
                real_departure=departure,
                start=d.start,
                end=d.end,
                demand_curve=list(d.demand_curve),
                ir_curve=list(d.ir_curve),
                maximum=d.maximum,
                project_capacity=config.project_capacity,
                valley_capacity=config.valley_capacity,
                boarding_seconds=config.boarding_seconds,
            )
            real_arrival = vb_bankers_round(departure + d.travel_time_curve[idx])
            virtual_arrival = virtual_arrival_legacy(
                real_departure=departure,
                start=d.start,
                end=d.end,
                demand_curve=list(d.demand_curve),
                ir_curve=list(d.ir_curve),
                travel_time_curve=list(d.travel_time_curve),
                maximum=d.maximum,
                project_capacity=config.project_capacity,
                valley_capacity=config.valley_capacity,
                alighting_seconds=config.alighting_seconds,
            )
        else:
            if planned.direction not in express_parameters:
                raise KeyError(f"express parameters missing for direction {planned.direction}")
            p = express_parameters[planned.direction]
            virtual_departure = departure
            duration = p.base_express_minutes + (
                d.travel_time_curve[idx] - p.base_express_minutes
            ) * p.residual_percent / 100.0
            real_arrival = vb_bankers_round(departure + duration)
            virtual_arrival = real_arrival

        result.append(
            OperationalTrip(
                line=line_number,
                direction=planned.direction,
                real_departure=departure,
                virtual_departure=virtual_departure,
                real_arrival=real_arrival,
                virtual_arrival=virtual_arrival,
                trip_type=planned.trip_type,
            )
        )
    return result
