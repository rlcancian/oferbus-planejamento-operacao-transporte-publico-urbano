export type Readiness = {
  status: string;
  database: string;
  schema_name: string;
  server_version: string;
  migration: string;
};

export type PlanningLineContext = {
  public_code: string | null;
  name: string;
};

export type PlanningResultContext = {
  project_id: string;
  project_name: string;
  scenario_id: string;
  scenario_name: string;
  scenario_revision_id: string;
  scenario_revision_no: number;
  lines: PlanningLineContext[];
};

export type PlannedTrip = {
  sequence_no: number;
  direction_key: string;
  legacy_direction_number: number;
  departure_service_minute: number;
  arrival_service_minute: number;
  virtual_departure_service_minute: number;
  virtual_arrival_service_minute: number;
  trip_type: number;
  is_express: boolean;
  vehicle_block: number;
  service_level: number | null;
};

export type VehicleBlock = {
  block_no: number;
  trip_sequence_nos: number[];
};

export type PlanningMetrics = {
  total_passengers: number;
  total_trips: number;
  mean_extension_km: number;
  total_distance_km: number;
  effective_fleet: number;
  mean_daily_distance_per_vehicle_km: number;
  mean_passengers_per_trip: number;
  mean_critical_passengers_per_trip: number;
  mean_occupancy_rate: number | null;
  passengers_per_km: number;
  daily_total_cost: number;
  mean_cost_per_vehicle: number;
  cost_per_trip: number;
  cost_per_equivalent_passenger: number;
  mean_trips_per_vehicle: number;
  mean_travel_time_min: number;
  mean_speed_kmh: number;
  distance_semantics: string;
};

export type PersistedPlanningResult = {
  computation_run_id: string;
  plan_revision_id: string;
  result_snapshot_id: string;
  plan_revision_no: number;
  context: PlanningResultContext;
  semantic_layer: string;
  engine_id: string;
  engine_version: string;
  input_fingerprint: string;
  output_fingerprint: string;
  effective_fleet: number;
  trips: PlannedTrip[];
  vehicle_blocks: VehicleBlock[];
  metrics: PlanningMetrics;
  provenance_notes: string[];
};

export type MarchTerminal = {
  id: string | null;
  name: string;
};

export type MarchDirection = {
  direction_key: string;
  legacy_direction_number: number | null;
  line_id: string;
  line_public_code: string | null;
  line_name: string;
  origin: MarchTerminal;
  destination: MarchTerminal;
  extension_km: number | null;
};

export type MarchTrip = PlannedTrip;

export type MarchPlan = {
  plan_revision_id: string;
  parent_plan_revision_id: string | null;
  scenario_revision_id: string;
  revision_no: number;
  source_kind: string;
  semantic_layer: string;
  output_fingerprint: string;
  service_start_minute: number;
  service_end_minute: number;
  directions: MarchDirection[];
  trips: MarchTrip[];
};

export type LatestResultLoad = {
  readiness: Readiness | null;
  result: PersistedPlanningResult | null;
  march: MarchPlan | null;
  resultStatus: "available" | "empty" | "unavailable";
  resultError: string | null;
  marchError: string | null;
};

const DEVELOPMENT_ORGANIZATION_ID = "d0568fff-011a-55a6-9083-321a787ad79d";
const DEVELOPMENT_SUBJECT = "dev:rafael";

function apiBase(): string {
  return process.env.OFERBUS_API_URL || "http://127.0.0.1:8010";
}

function resultHeaders(): HeadersInit {
  const environment = (process.env.OFERBUS_ENV || "development").toLowerCase();
  if (environment === "production" || environment === "prod") return {};

  return {
    "X-OferBus-Subject": process.env.OFERBUS_WEB_DEV_SUBJECT || DEVELOPMENT_SUBJECT,
    "X-OferBus-Organization-Id":
      process.env.OFERBUS_WEB_DEV_ORGANIZATION_ID || DEVELOPMENT_ORGANIZATION_ID,
    "X-Correlation-Id": "web-planning-workspace",
  };
}

async function loadReadiness(): Promise<Readiness | null> {
  try {
    const response = await fetch(`${apiBase()}/ready`, { cache: "no-store" });
    if (!response.ok) return null;
    return (await response.json()) as Readiness;
  } catch {
    return null;
  }
}

async function responseError(response: Response): Promise<string> {
  try {
    const body = (await response.json()) as { detail?: unknown };
    if (typeof body.detail === "string") return `HTTP ${response.status} — ${body.detail}`;
  } catch {
    // Fall through to the status text when the response is not JSON.
  }
  return `HTTP ${response.status}${response.statusText ? ` — ${response.statusText}` : ""}`;
}

async function loadLatestResult(): Promise<Pick<LatestResultLoad, "result" | "resultStatus" | "resultError">> {
  try {
    const response = await fetch(`${apiBase()}/results/latest`, {
      cache: "no-store",
      headers: resultHeaders(),
    });
    if (response.status === 404) {
      return { result: null, resultStatus: "empty", resultError: null };
    }
    if (!response.ok) {
      return {
        result: null,
        resultStatus: "unavailable",
        resultError: await responseError(response),
      };
    }
    return {
      result: (await response.json()) as PersistedPlanningResult,
      resultStatus: "available",
      resultError: null,
    };
  } catch (error) {
    return {
      result: null,
      resultStatus: "unavailable",
      resultError: error instanceof Error ? error.message : "Falha de conexão com a API de resultados",
    };
  }
}

async function loadMarchPlan(planRevisionId: string): Promise<{ march: MarchPlan | null; marchError: string | null }> {
  try {
    const response = await fetch(`${apiBase()}/plans/${planRevisionId}/march`, {
      cache: "no-store",
      headers: resultHeaders(),
    });
    if (!response.ok) {
      return { march: null, marchError: await responseError(response) };
    }
    return { march: (await response.json()) as MarchPlan, marchError: null };
  } catch (error) {
    return {
      march: null,
      marchError: error instanceof Error ? error.message : "Falha de conexão com a API do Gráfico de Marcha",
    };
  }
}

export async function loadPlanningWorkspace(): Promise<LatestResultLoad> {
  const [readiness, latest] = await Promise.all([loadReadiness(), loadLatestResult()]);
  if (!latest.result) {
    return { readiness, ...latest, march: null, marchError: null };
  }
  const march = await loadMarchPlan(latest.result.plan_revision_id);
  return { readiness, ...latest, ...march };
}
