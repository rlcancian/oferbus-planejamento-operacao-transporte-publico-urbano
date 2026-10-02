from __future__ import annotations

from dataclasses import asdict

from oferbus_legacy_core import (
    CostParameters,
    DirectionPlanningData,
    MinimumTimetableConfig,
    TripObservation,
    VehicleModel,
    assign_service_levels_legacy,
    build_basic_link_graph_legacy,
    calculate_project_metrics_distance_corrected,
    calculate_project_metrics_legacy,
    complete_trip_attributes_legacy,
    minimum_timetable_2007_legacy,
    projected_mean_occupancy_rate_legacy,
    projected_mean_occupancy_rate_normalized,
    vehicle_blocks,
)

from .contracts import (
    PlannedTripResult,
    PlanningInput,
    PlanningMetricsResult,
    PlanningResult,
    SemanticLayer,
)
from .fingerprint import fingerprint
from .validation import validate_planning_input


ENGINE_ID = "reference-bridge"
ENGINE_VERSION = "0.1.0"


class ReferencePlanningAdapter:
    """Temporary execution bridge over characterized archaeological routines.

    This adapter exists to stabilize production input/output contracts before
    individual algorithms are deliberately promoted into `oferbus-core`.
    It must not gain database, HTTP or UI dependencies.
    """

    def execute(self, planning_input: PlanningInput) -> PlanningResult:
        validate_planning_input(planning_input)

        direction_numbers = sorted(item.legacy_direction_number for item in planning_input.directions)
        if direction_numbers != list(range(1, max(direction_numbers) + 1)):
            raise ValueError("reference bridge requires contiguous legacy direction numbers starting at 1")

        direction_by_number = {item.legacy_direction_number: item for item in planning_input.directions}
        direction_key_by_number = {item.legacy_direction_number: item.direction_key for item in planning_input.directions}

        directions = {
            number: DirectionPlanningData(
                observed=tuple(
                    TripObservation(
                        minute=item.departure_service_minute,
                        passengers=item.passengers,
                        critical_passengers=item.critical_passengers,
                        travel_time=item.travel_time_min,
                    )
                    for item in source.observations
                ),
                demand_curve=source.demand_passengers_per_minute,
                ir_curve=source.renewal_index_curve,
                travel_time_curve=source.travel_time_min_curve,
                start=source.service_start_minute,
                end=source.service_end_minute,
                maximum=source.demand_maximum_passengers_per_minute,
                storage_at_departure_terminal=source.storage_at_departure_terminal,
            )
            for number, source in direction_by_number.items()
        }

        spec = planning_input.specification
        preserve_replay_bug = planning_input.semantic_layer is SemanticLayer.LEGACY_EXACT
        config = MinimumTimetableConfig(
            max_interval=spec.max_headway_min,
            project_capacity=spec.project_capacity_passengers,
            valley_capacity=spec.valley_capacity_passengers,
            boarding_seconds=spec.boarding_seconds_per_passenger,
            alighting_seconds=spec.alighting_seconds_per_passenger,
            radial=spec.radial,
            create_express_returns=spec.create_express_returns,
            preserve_return_replay_bug=preserve_replay_bug,
        )

        planned = minimum_timetable_2007_legacy(directions, config)
        operational = complete_trip_attributes_legacy(planned, directions=directions, config=config)
        effective_fleet = build_basic_link_graph_legacy(operational, radial=spec.radial)
        if effective_fleet <= 0:
            raise ValueError("planning produced no effective fleet")

        vehicle = VehicleModel(
            seats=planning_input.vehicle.seats,
            free_area_m2=planning_input.vehicle.free_area_m2,
        )
        vehicle_models = {vehicle_number: vehicle for vehicle_number in range(1, effective_fleet + 1)}
        demand_curves = {number: source.demand_passengers_per_minute for number, source in direction_by_number.items()}
        ir_curves = {number: source.renewal_index_curve for number, source in direction_by_number.items()}
        direction_starts = {number: source.service_start_minute for number, source in direction_by_number.items()}

        assign_service_levels_legacy(
            operational,
            demand_curves=demand_curves,
            ir_curves=ir_curves,
            direction_starts=direction_starts,
            vehicle_models=vehicle_models,
        )

        occupancy_kwargs = dict(
            trips_in_pipeline_order=operational,
            demand_curves=demand_curves,
            ir_curves=ir_curves,
            direction_starts=direction_starts,
            vehicle_models=vehicle_models,
            default_vehicle=vehicle,
            capacity_level=planning_input.vehicle.capacity_level,
        )
        if planning_input.semantic_layer is SemanticLayer.LEGACY_EXACT:
            occupancy = projected_mean_occupancy_rate_legacy(**occupancy_kwargs)
        else:
            occupancy = projected_mean_occupancy_rate_normalized(**occupancy_kwargs)

        cost = CostParameters(
            mode=planning_input.cost.mode,
            cost_per_km=planning_input.cost.cost_per_km,
            fixed_cost_per_vehicle=planning_input.cost.fixed_cost_per_vehicle,
            variable_cost_per_km=planning_input.cost.variable_cost_per_km,
        )
        metrics_kwargs = dict(
            trips=operational,
            total_passengers_by_direction={
                number: int(round(sum(source.demand_passengers_per_minute[1 : source.service_minutes + 1])))
                for number, source in direction_by_number.items()
            },
            extension_km_by_direction={number: source.extension_km for number, source in direction_by_number.items()},
            effective_fleet=effective_fleet,
            mean_renewal_index=spec.mean_renewal_index,
            mean_occupancy_rate=occupancy,
            cost=cost,
            typical_day_participation=spec.typical_day_participation,
            equivalent_passenger_index=spec.equivalent_passenger_index,
        )
        if planning_input.semantic_layer is SemanticLayer.LEGACY_EXACT:
            metrics = calculate_project_metrics_legacy(**metrics_kwargs)
        else:
            metrics = calculate_project_metrics_distance_corrected(**metrics_kwargs)

        trip_results = tuple(
            PlannedTripResult(
                direction_key=direction_key_by_number[item.direction],
                legacy_direction_number=item.direction,
                departure_service_minute=item.real_departure,
                arrival_service_minute=item.real_arrival,
                virtual_departure_service_minute=item.virtual_departure,
                virtual_arrival_service_minute=item.virtual_arrival,
                trip_type=item.trip_type,
                is_express=item.is_express,
                vehicle_block=item.vehicle,
                service_level=item.service_level,
            )
            for item in operational
        )
        blocks = {
            number: tuple(operational.index(item) for item in items)
            for number, items in vehicle_blocks(operational).items()
        }
        metrics_result = PlanningMetricsResult(**asdict(metrics))
        input_fingerprint = fingerprint(planning_input)
        provenance_notes = self._provenance_notes(planning_input.semantic_layer)
        output_payload = {
            "semantic_layer": planning_input.semantic_layer,
            "engine_id": ENGINE_ID,
            "engine_version": ENGINE_VERSION,
            "input_fingerprint": input_fingerprint,
            "trips": trip_results,
            "effective_fleet": effective_fleet,
            "vehicle_blocks": blocks,
            "metrics": metrics_result,
            "provenance_notes": provenance_notes,
        }

        return PlanningResult(
            semantic_layer=planning_input.semantic_layer,
            engine_id=ENGINE_ID,
            engine_version=ENGINE_VERSION,
            input_fingerprint=input_fingerprint,
            output_fingerprint=fingerprint(output_payload),
            trips=trip_results,
            effective_fleet=effective_fleet,
            vehicle_blocks=blocks,
            metrics=metrics_result,
            provenance_notes=provenance_notes,
        )

    @staticmethod
    def _provenance_notes(layer: SemanticLayer) -> tuple[str, ...]:
        common = (
            "temporary production-contract bridge over characterized reference-core routines",
            "basic link graph excludes unpromoted Cria_1/Cria_2/garage-check/fine-adjustment stages",
        )
        if layer is SemanticLayer.LEGACY_EXACT:
            return common + (
                "preserves characterized return passenger-replay defect where applicable",
                "uses legacy projected occupancy and legacy distance semantics",
            )
        return common + (
            "corrects characterized return passenger-replay indexing defect",
            "express trips carry zero passenger demand in normalized occupancy semantics",
            "uses direction-weighted distance metrics instead of BC-005 legacy distance formula",
        )
