-- OferBus — PostgreSQL Logical DDL v0.1
-- Status: logical/reference schema only; NOT a production migration.
-- Date: 2026-10-02
-- Scope: persistence model only. No ORM/framework/auth/deploy decision is implied.

CREATE SCHEMA IF NOT EXISTS oferbus;
SET search_path TO oferbus, public;

CREATE TABLE organization (
    id uuid PRIMARY KEY,
    name text NOT NULL,
    organization_type text NOT NULL,
    status text NOT NULL DEFAULT 'active',
    created_at timestamptz NOT NULL DEFAULT now(),
    archived_at timestamptz
);

CREATE TABLE app_user (
    id uuid PRIMARY KEY,
    display_name text NOT NULL,
    email text,
    external_subject text,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (external_subject)
);

CREATE TABLE organization_membership (
    organization_id uuid NOT NULL REFERENCES organization(id),
    user_id uuid NOT NULL REFERENCES app_user(id),
    role_key text NOT NULL,
    status text NOT NULL DEFAULT 'active',
    created_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (organization_id, user_id)
);

CREATE TABLE municipality (
    id uuid PRIMARY KEY,
    organization_id uuid NOT NULL REFERENCES organization(id),
    name text NOT NULL,
    state_region text,
    country_code char(2) NOT NULL DEFAULT 'BR',
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE transit_operator (
    id uuid PRIMARY KEY,
    organization_id uuid NOT NULL REFERENCES organization(id),
    name text NOT NULL,
    municipality_id uuid REFERENCES municipality(id),
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE terminal (
    id uuid PRIMARY KEY,
    organization_id uuid NOT NULL REFERENCES organization(id),
    municipality_id uuid REFERENCES municipality(id),
    name text NOT NULL,
    allows_storage boolean,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE garage (
    id uuid PRIMARY KEY,
    organization_id uuid NOT NULL REFERENCES organization(id),
    operator_id uuid REFERENCES transit_operator(id),
    name text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE vehicle_type (
    id uuid PRIMARY KEY,
    organization_id uuid NOT NULL REFERENCES organization(id),
    operator_id uuid REFERENCES transit_operator(id),
    name text NOT NULL,
    seats integer NOT NULL CHECK (seats >= 0),
    free_standing_area_m2 numeric(12,4) NOT NULL CHECK (free_standing_area_m2 >= 0),
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE vehicle (
    id uuid PRIMARY KEY,
    organization_id uuid NOT NULL REFERENCES organization(id),
    operator_id uuid REFERENCES transit_operator(id),
    vehicle_type_id uuid NOT NULL REFERENCES vehicle_type(id),
    fleet_code text,
    status text NOT NULL DEFAULT 'active',
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE transit_line (
    id uuid PRIMARY KEY,
    organization_id uuid NOT NULL REFERENCES organization(id),
    municipality_id uuid REFERENCES municipality(id),
    operator_id uuid REFERENCES transit_operator(id),
    public_code text,
    name text NOT NULL,
    legacy_operation_type_code integer,
    status text NOT NULL DEFAULT 'active',
    created_at timestamptz NOT NULL DEFAULT now(),
    archived_at timestamptz
);

CREATE TABLE line_direction (
    id uuid PRIMARY KEY,
    organization_id uuid NOT NULL REFERENCES organization(id),
    line_id uuid NOT NULL REFERENCES transit_line(id),
    direction_key text NOT NULL,
    origin_terminal_id uuid REFERENCES terminal(id),
    destination_terminal_id uuid REFERENCES terminal(id),
    extension_km numeric(12,3) CHECK (extension_km >= 0),
    legacy_direction_number integer,
    UNIQUE (line_id, direction_key)
);

CREATE TABLE planning_project (
    id uuid PRIMARY KEY,
    organization_id uuid NOT NULL REFERENCES organization(id),
    name text NOT NULL,
    description text,
    status text NOT NULL DEFAULT 'active',
    created_by uuid REFERENCES app_user(id),
    created_at timestamptz NOT NULL DEFAULT now(),
    archived_at timestamptz
);

CREATE TABLE project_line (
    organization_id uuid NOT NULL REFERENCES organization(id),
    project_id uuid NOT NULL REFERENCES planning_project(id),
    line_id uuid NOT NULL REFERENCES transit_line(id),
    PRIMARY KEY (project_id, line_id)
);

CREATE TABLE scenario (
    id uuid PRIMARY KEY,
    organization_id uuid NOT NULL REFERENCES organization(id),
    project_id uuid NOT NULL REFERENCES planning_project(id),
    name text NOT NULL,
    description text,
    status text NOT NULL DEFAULT 'active',
    created_by uuid REFERENCES app_user(id),
    created_at timestamptz NOT NULL DEFAULT now(),
    archived_at timestamptz
);

CREATE TABLE scenario_revision (
    id uuid PRIMARY KEY,
    organization_id uuid NOT NULL REFERENCES organization(id),
    scenario_id uuid NOT NULL REFERENCES scenario(id),
    revision_no integer NOT NULL CHECK (revision_no > 0),
    parent_revision_id uuid REFERENCES scenario_revision(id),
    created_by uuid REFERENCES app_user(id),
    created_at timestamptz NOT NULL DEFAULT now(),
    reason text,
    input_fingerprint text,
    UNIQUE (scenario_id, revision_no)
);

CREATE TABLE dataset (
    id uuid PRIMARY KEY,
    organization_id uuid NOT NULL REFERENCES organization(id),
    project_id uuid REFERENCES planning_project(id),
    line_id uuid REFERENCES transit_line(id),
    dataset_kind text NOT NULL,
    name text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE dataset_version (
    id uuid PRIMARY KEY,
    organization_id uuid NOT NULL REFERENCES organization(id),
    dataset_id uuid NOT NULL REFERENCES dataset(id),
    version_no integer NOT NULL CHECK (version_no > 0),
    content_digest text,
    observed_from date,
    observed_to date,
    source_description text,
    created_by uuid REFERENCES app_user(id),
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (dataset_id, version_no)
);

CREATE TABLE scenario_dataset_binding (
    organization_id uuid NOT NULL REFERENCES organization(id),
    scenario_revision_id uuid NOT NULL REFERENCES scenario_revision(id),
    dataset_version_id uuid NOT NULL REFERENCES dataset_version(id),
    binding_role text NOT NULL,
    PRIMARY KEY (scenario_revision_id, binding_role)
);

CREATE TABLE trip_observation (
    id uuid PRIMARY KEY,
    organization_id uuid NOT NULL REFERENCES organization(id),
    dataset_version_id uuid NOT NULL REFERENCES dataset_version(id),
    line_direction_id uuid NOT NULL REFERENCES line_direction(id),
    service_minute integer NOT NULL,
    passengers integer NOT NULL CHECK (passengers >= 0),
    critical_section_passengers integer CHECK (critical_section_passengers >= 0),
    travel_time_min numeric(10,3) CHECK (travel_time_min >= 0),
    source_sequence integer
);

CREATE TABLE monthly_demand_point (
    id uuid PRIMARY KEY,
    organization_id uuid NOT NULL REFERENCES organization(id),
    dataset_version_id uuid NOT NULL REFERENCES dataset_version(id),
    line_id uuid NOT NULL REFERENCES transit_line(id),
    month_start date NOT NULL,
    passenger_count numeric(18,3) NOT NULL CHECK (passenger_count >= 0),
    UNIQUE (dataset_version_id, line_id, month_start)
);

CREATE TABLE planning_specification (
    id uuid PRIMARY KEY,
    organization_id uuid NOT NULL REFERENCES organization(id),
    scenario_revision_id uuid NOT NULL UNIQUE REFERENCES scenario_revision(id),
    project_date date,
    service_level_code text,
    maximum_headway_min numeric(10,3),
    demand_method text,
    use_forecast boolean NOT NULL DEFAULT false,
    create_deadhead_returns boolean NOT NULL DEFAULT false,
    valley_level numeric(12,4),
    align_departures_to_0_5 boolean NOT NULL DEFAULT false,
    equivalent_passenger_index numeric(12,6),
    reserve_fleet_percent numeric(12,6),
    description text
);

CREATE TABLE planning_direction_specification (
    id uuid PRIMARY KEY,
    organization_id uuid NOT NULL REFERENCES organization(id),
    planning_specification_id uuid NOT NULL REFERENCES planning_specification(id),
    line_direction_id uuid NOT NULL REFERENCES line_direction(id),
    demand_adjustment_level integer,
    travel_time_adjustment_level integer,
    renewal_index_adjustment_level integer,
    typical_period_adjustment integer,
    constant_renewal_index numeric(12,6),
    UNIQUE (planning_specification_id, line_direction_id)
);

CREATE TABLE model_release (
    id uuid PRIMARY KEY,
    model_key text NOT NULL,
    version_label text NOT NULL,
    semantic_layer text NOT NULL CHECK (semantic_layer IN ('legacy-exact','normalized','modern')),
    source_revision text,
    algorithm_digest text,
    status text NOT NULL DEFAULT 'active',
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (model_key, version_label, semantic_layer)
);

CREATE TABLE scenario_model_binding (
    id uuid PRIMARY KEY,
    organization_id uuid NOT NULL REFERENCES organization(id),
    scenario_revision_id uuid NOT NULL REFERENCES scenario_revision(id),
    purpose_key text NOT NULL,
    model_release_id uuid NOT NULL REFERENCES model_release(id),
    parameters jsonb NOT NULL DEFAULT '{}'::jsonb,
    UNIQUE (scenario_revision_id, purpose_key)
);

CREATE TABLE computation_run (
    id uuid PRIMARY KEY,
    organization_id uuid NOT NULL REFERENCES organization(id),
    scenario_revision_id uuid NOT NULL REFERENCES scenario_revision(id),
    run_kind text NOT NULL,
    semantic_layer text NOT NULL CHECK (semantic_layer IN ('legacy-exact','normalized','modern')),
    engine_version text NOT NULL,
    engine_source_revision text,
    deterministic_seed bigint,
    status text NOT NULL,
    started_at timestamptz,
    completed_at timestamptz,
    input_fingerprint text,
    output_fingerprint text,
    diagnostics jsonb
);

CREATE TABLE curve_series (
    id uuid PRIMARY KEY,
    organization_id uuid NOT NULL REFERENCES organization(id),
    computation_run_id uuid NOT NULL REFERENCES computation_run(id),
    line_direction_id uuid NOT NULL REFERENCES line_direction(id),
    model_release_id uuid REFERENCES model_release(id),
    curve_kind text NOT NULL,
    unit text NOT NULL,
    semantic_layer text NOT NULL CHECK (semantic_layer IN ('legacy-exact','normalized','modern')),
    start_service_minute integer NOT NULL,
    end_service_minute integer NOT NULL,
    CHECK (end_service_minute >= start_service_minute)
);

CREATE TABLE curve_point (
    organization_id uuid NOT NULL REFERENCES organization(id),
    curve_series_id uuid NOT NULL REFERENCES curve_series(id),
    service_minute integer NOT NULL,
    value_numeric numeric(24,10) NOT NULL,
    PRIMARY KEY (curve_series_id, service_minute)
);

CREATE TABLE plan_revision (
    id uuid PRIMARY KEY,
    organization_id uuid NOT NULL REFERENCES organization(id),
    scenario_revision_id uuid NOT NULL REFERENCES scenario_revision(id),
    source_run_id uuid REFERENCES computation_run(id),
    parent_plan_revision_id uuid REFERENCES plan_revision(id),
    revision_no integer NOT NULL CHECK (revision_no > 0),
    revision_kind text NOT NULL CHECK (revision_kind IN ('generated','manual','imported','migrated')),
    service_day_type text,
    created_by uuid REFERENCES app_user(id),
    created_at timestamptz NOT NULL DEFAULT now(),
    reason text,
    content_fingerprint text,
    UNIQUE (scenario_revision_id, revision_no)
);

CREATE TABLE planned_trip (
    id uuid PRIMARY KEY,
    organization_id uuid NOT NULL REFERENCES organization(id),
    plan_revision_id uuid NOT NULL REFERENCES plan_revision(id),
    line_id uuid NOT NULL REFERENCES transit_line(id),
    line_direction_id uuid NOT NULL REFERENCES line_direction(id),
    parent_trip_id uuid REFERENCES planned_trip(id),
    sequence_no integer NOT NULL,
    real_departure_minute integer NOT NULL,
    virtual_departure_minute integer NOT NULL,
    real_arrival_minute integer NOT NULL,
    virtual_arrival_minute integer NOT NULL,
    movement_kind text NOT NULL CHECK (movement_kind IN ('revenue-service','deadhead-express')),
    origin_kind text NOT NULL CHECK (origin_kind IN ('generated','manual','imported','migrated')),
    service_level_code text,
    legacy_type_bits integer,
    UNIQUE (plan_revision_id, sequence_no)
);

CREATE TABLE movement_connection (
    id uuid PRIMARY KEY,
    organization_id uuid NOT NULL REFERENCES organization(id),
    plan_revision_id uuid NOT NULL REFERENCES plan_revision(id),
    predecessor_trip_id uuid REFERENCES planned_trip(id),
    successor_trip_id uuid REFERENCES planned_trip(id),
    connection_kind text NOT NULL CHECK (connection_kind IN ('direct-trip','storage','garage')),
    terminal_id uuid REFERENCES terminal(id),
    garage_id uuid REFERENCES garage(id),
    manual_override boolean NOT NULL DEFAULT false,
    created_at timestamptz NOT NULL DEFAULT now(),
    CHECK (predecessor_trip_id IS NOT NULL OR successor_trip_id IS NOT NULL)
);

CREATE UNIQUE INDEX uq_movement_connection_outgoing
    ON movement_connection(plan_revision_id, predecessor_trip_id)
    WHERE predecessor_trip_id IS NOT NULL;

CREATE UNIQUE INDEX uq_movement_connection_incoming
    ON movement_connection(plan_revision_id, successor_trip_id)
    WHERE successor_trip_id IS NOT NULL;

CREATE TABLE vehicle_block (
    id uuid PRIMARY KEY,
    organization_id uuid NOT NULL REFERENCES organization(id),
    plan_revision_id uuid NOT NULL REFERENCES plan_revision(id),
    block_no integer NOT NULL,
    assigned_vehicle_id uuid REFERENCES vehicle(id),
    start_service_minute integer,
    end_service_minute integer,
    UNIQUE (plan_revision_id, block_no)
);

CREATE TABLE vehicle_block_trip (
    organization_id uuid NOT NULL REFERENCES organization(id),
    vehicle_block_id uuid NOT NULL REFERENCES vehicle_block(id),
    planned_trip_id uuid NOT NULL UNIQUE REFERENCES planned_trip(id),
    sequence_no integer NOT NULL,
    PRIMARY KEY (vehicle_block_id, sequence_no)
);

CREATE TABLE fleet_plan (
    id uuid PRIMARY KEY,
    organization_id uuid NOT NULL REFERENCES organization(id),
    plan_revision_id uuid NOT NULL UNIQUE REFERENCES plan_revision(id),
    effective_fleet integer NOT NULL CHECK (effective_fleet >= 0),
    reserve_percent numeric(12,6) CHECK (reserve_percent >= 0),
    reserve_fleet integer CHECK (reserve_fleet >= 0),
    total_fleet integer CHECK (total_fleet >= 0)
);

CREATE TABLE result_snapshot (
    id uuid PRIMARY KEY,
    organization_id uuid NOT NULL REFERENCES organization(id),
    plan_revision_id uuid NOT NULL REFERENCES plan_revision(id),
    computation_run_id uuid REFERENCES computation_run(id),
    semantic_layer text NOT NULL CHECK (semantic_layer IN ('legacy-exact','normalized','modern')),
    model_set_fingerprint text,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE metric_definition (
    id uuid PRIMARY KEY,
    metric_key text NOT NULL UNIQUE,
    name text NOT NULL,
    canonical_unit text,
    description text
);

CREATE TABLE result_metric (
    id uuid PRIMARY KEY,
    organization_id uuid NOT NULL REFERENCES organization(id),
    result_snapshot_id uuid NOT NULL REFERENCES result_snapshot(id),
    metric_definition_id uuid NOT NULL REFERENCES metric_definition(id),
    line_direction_id uuid REFERENCES line_direction(id),
    value_numeric numeric(24,10),
    value_text text,
    unit text,
    CHECK ((value_numeric IS NOT NULL) <> (value_text IS NOT NULL))
);

CREATE UNIQUE INDEX uq_result_metric_scope
    ON result_metric(result_snapshot_id, metric_definition_id, COALESCE(line_direction_id, '00000000-0000-0000-0000-000000000000'::uuid));

CREATE TABLE plan_change (
    id uuid PRIMARY KEY,
    organization_id uuid NOT NULL REFERENCES organization(id),
    plan_revision_id uuid NOT NULL REFERENCES plan_revision(id),
    entity_type text NOT NULL,
    entity_id uuid,
    operation text NOT NULL,
    field_name text,
    before_value jsonb,
    after_value jsonb,
    changed_by uuid REFERENCES app_user(id),
    changed_at timestamptz NOT NULL DEFAULT now(),
    reason text
);

CREATE TABLE audit_event (
    id uuid PRIMARY KEY,
    organization_id uuid NOT NULL REFERENCES organization(id),
    actor_user_id uuid REFERENCES app_user(id),
    event_type text NOT NULL,
    entity_type text NOT NULL,
    entity_id uuid,
    event_at timestamptz NOT NULL DEFAULT now(),
    details jsonb NOT NULL DEFAULT '{}'::jsonb
);

-- Reference indexes for the dominant access paths.
CREATE INDEX ix_scenario_revision_scenario ON scenario_revision(scenario_id, revision_no DESC);
CREATE INDEX ix_trip_observation_dataset_direction_time ON trip_observation(dataset_version_id, line_direction_id, service_minute);
CREATE INDEX ix_computation_run_scenario_revision ON computation_run(scenario_revision_id, started_at DESC);
CREATE INDEX ix_curve_series_run_kind ON curve_series(computation_run_id, curve_kind, line_direction_id);
CREATE INDEX ix_planned_trip_plan_direction_departure ON planned_trip(plan_revision_id, line_direction_id, real_departure_minute);
CREATE INDEX ix_vehicle_block_plan ON vehicle_block(plan_revision_id, block_no);
CREATE INDEX ix_result_snapshot_plan_layer ON result_snapshot(plan_revision_id, semantic_layer, created_at DESC);
CREATE INDEX ix_audit_event_org_time ON audit_event(organization_id, event_at DESC);

-- IMPORTANT v0.1 physical-schema note:
-- Every tenant-owned relationship above carries organization_id on the child row,
-- but this logical DDL intentionally uses simple id FKs for readability. Before a
-- production migration is accepted, cross-tenant FK consistency MUST be enforced
-- at PostgreSQL level (e.g. composite (organization_id,id) candidate keys/FKs and/or
-- a PostgreSQL-native isolation policy chosen in the later architecture phase).
-- This file is therefore a formal logical schema, not yet the production hardening migration.
