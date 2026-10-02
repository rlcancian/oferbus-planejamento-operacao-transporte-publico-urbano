import type { PersistedPlanningResult, Readiness } from "../lib/oferbus-api";

const numberFormatter = new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 2 });
const integerFormatter = new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 0 });

function number(value: number, digits = 2): string {
  return new Intl.NumberFormat("pt-BR", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  }).format(value);
}

function serviceTime(value: number): string {
  const day = Math.floor(value / 1440);
  const minuteOfDay = ((value % 1440) + 1440) % 1440;
  const hours = Math.floor(minuteOfDay / 60);
  const minutes = minuteOfDay % 60;
  const clock = `${String(hours).padStart(2, "0")}:${String(minutes).padStart(2, "0")}`;
  return day > 0 ? `${clock} · D+${day}` : clock;
}

function shortHash(value: string): string {
  return `${value.slice(0, 8)}…${value.slice(-8)}`;
}

function layerLabel(layer: string): string {
  if (layer === "normalized") return "Normalizado";
  if (layer === "legacy-exact") return "Legado exato";
  if (layer === "modern") return "Moderno";
  return layer;
}

function tripKind(isExpress: boolean, tripType: number): string {
  if (isExpress) return "Expresso";
  return tripType === 0 ? "Regular" : `Tipo ${tripType}`;
}

function metricPercent(value: number | null): string {
  if (value === null) return "—";
  return `${number(value * 100, 1)}%`;
}

function lineLabel(result: PersistedPlanningResult): string {
  if (result.context.lines.length === 0) return "Linha não identificada";
  return result.context.lines
    .map((line) => [line.public_code, line.name].filter(Boolean).join(" · "))
    .join(" / ");
}

export function PlanningWorkspace({
  result,
  readiness,
}: {
  result: PersistedPlanningResult;
  readiness: Readiness | null;
}) {
  const metrics = result.metrics;

  return (
    <main className="workspace-shell">
      <header className="topbar">
        <div className="brand-lockup">
          <span className="brand-mark" aria-hidden="true">O</span>
          <div>
            <strong>OferBus</strong>
            <small>planejamento operacional</small>
          </div>
        </div>
        <nav className="topnav" aria-label="Seções do workspace">
          <a href="#quadro">Horários</a>
          <a href="#blocos">Blocos</a>
          <a href="#indicadores">Indicadores</a>
          <a href="#provenance">Provenance</a>
        </nav>
        <div className={`system-pill ${readiness ? "system-online" : "system-offline"}`}>
          <span aria-hidden="true" />
          {readiness ? `PostgreSQL ${readiness.server_version}` : "API indisponível"}
        </div>
      </header>

      <section className="workspace-heading">
        <div>
          <div className="breadcrumb">
            <span>{result.context.project_name}</span>
            <i>/</i>
            <span>{result.context.scenario_name}</span>
            <i>/</i>
            <strong>revisão {result.context.scenario_revision_no}</strong>
          </div>
          <h1>{lineLabel(result)}</h1>
          <p>
            Plano computado · revisão {result.plan_revision_no} · resultado persistido e verificado por fingerprint.
          </p>
        </div>
        <div className="heading-badges">
          <span className="semantic-badge">{layerLabel(result.semantic_layer)}</span>
          <span className="integrity-badge"><i aria-hidden="true">✓</i> íntegro</span>
        </div>
      </section>

      <section className="metric-ribbon" aria-label="Resumo operacional">
        <article>
          <small>Frota efetiva</small>
          <strong>{integerFormatter.format(result.effective_fleet)}</strong>
          <span>veículos</span>
        </article>
        <article>
          <small>Viagens</small>
          <strong>{integerFormatter.format(metrics.total_trips)}</strong>
          <span>programadas</span>
        </article>
        <article>
          <small>Passageiros</small>
          <strong>{integerFormatter.format(metrics.total_passengers)}</strong>
          <span>dia típico</span>
        </article>
        <article>
          <small>Quilometragem</small>
          <strong>{numberFormatter.format(metrics.total_distance_km)}</strong>
          <span>km / dia</span>
        </article>
        <article>
          <small>Ocupação média</small>
          <strong>{metricPercent(metrics.mean_occupancy_rate)}</strong>
          <span>projetada</span>
        </article>
        <article>
          <small>Custo diário</small>
          <strong>{number(metrics.daily_total_cost)}</strong>
          <span>unid. monetária</span>
        </article>
      </section>

      <div className="workspace-grid">
        <section className="panel timetable-panel" id="quadro">
          <div className="panel-heading">
            <div>
              <span className="section-kicker">Quadro operacional</span>
              <h2>Horários planejados</h2>
            </div>
            <span className="panel-count">{metrics.total_trips} viagens</span>
          </div>

          <div className="table-wrap">
            <table className="timetable">
              <thead>
                <tr>
                  <th>#</th>
                  <th>Partida</th>
                  <th>Chegada</th>
                  <th>Sentido</th>
                  <th>Operação</th>
                  <th>Bloco</th>
                  <th>Nível</th>
                </tr>
              </thead>
              <tbody>
                {result.trips.map((trip) => (
                  <tr key={trip.sequence_no}>
                    <td><span className="sequence-cell">{String(trip.sequence_no).padStart(2, "0")}</span></td>
                    <td>
                      <strong className="time-cell">{serviceTime(trip.departure_service_minute)}</strong>
                      {trip.virtual_departure_service_minute !== trip.departure_service_minute && (
                        <small>virtual {serviceTime(trip.virtual_departure_service_minute)}</small>
                      )}
                    </td>
                    <td>
                      <strong className="time-cell">{serviceTime(trip.arrival_service_minute)}</strong>
                      {trip.virtual_arrival_service_minute !== trip.arrival_service_minute && (
                        <small>virtual {serviceTime(trip.virtual_arrival_service_minute)}</small>
                      )}
                    </td>
                    <td>
                      <span className="direction-cell">{trip.direction_key}</span>
                      <small>sentido {trip.legacy_direction_number}</small>
                    </td>
                    <td><span className={trip.is_express ? "trip-tag express" : "trip-tag"}>{tripKind(trip.is_express, trip.trip_type)}</span></td>
                    <td><span className="block-chip">V{trip.vehicle_block || "—"}</span></td>
                    <td>{trip.service_level ?? "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <section className="panel blocks-panel" id="blocos">
          <div className="panel-heading">
            <div>
              <span className="section-kicker">Circulação</span>
              <h2>Blocos de veículo</h2>
            </div>
            <span className="panel-count">{result.vehicle_blocks.length} blocos</span>
          </div>

          <div className="block-list">
            {result.vehicle_blocks.map((block) => {
              const trips = block.trip_sequence_nos
                .map((sequence) => result.trips.find((trip) => trip.sequence_no === sequence))
                .filter((trip): trip is NonNullable<typeof trip> => Boolean(trip));
              const first = trips[0];
              const last = trips[trips.length - 1];
              return (
                <article className="vehicle-block-card" key={block.block_no}>
                  <div className="vehicle-block-title">
                    <span className="vehicle-icon" aria-hidden="true">▰</span>
                    <div><strong>Veículo {block.block_no}</strong><small>{block.trip_sequence_nos.length} viagens</small></div>
                    <span>{first && last ? `${serviceTime(first.departure_service_minute)} — ${serviceTime(last.arrival_service_minute)}` : "—"}</span>
                  </div>
                  <div className="block-track" aria-label={`Sequência do veículo ${block.block_no}`}>
                    {block.trip_sequence_nos.map((sequence, index) => (
                      <span key={sequence}>
                        <b>{sequence}</b>
                        {index < block.trip_sequence_nos.length - 1 && <i aria-hidden="true" />}
                      </span>
                    ))}
                  </div>
                </article>
              );
            })}
          </div>
          <div className="march-preview-note">
            <span aria-hidden="true">↗</span>
            <p><strong>Gráfico de Marcha</strong> A estrutura de viagens e vínculos já está pronta para a superfície gráfica interativa da Phase C.</p>
          </div>
        </section>

        <section className="panel indicators-panel" id="indicadores">
          <div className="panel-heading">
            <div>
              <span className="section-kicker">Resultado técnico</span>
              <h2>Indicadores</h2>
            </div>
          </div>
          <div className="indicator-groups">
            <div className="indicator-group">
              <h3>Operação</h3>
              <dl>
                <div><dt>Viagens / veículo</dt><dd>{number(metrics.mean_trips_per_vehicle)}</dd></div>
                <div><dt>Km / veículo</dt><dd>{number(metrics.mean_daily_distance_per_vehicle_km)} km</dd></div>
                <div><dt>Tempo médio</dt><dd>{number(metrics.mean_travel_time_min)} min</dd></div>
                <div><dt>Velocidade média</dt><dd>{number(metrics.mean_speed_kmh)} km/h</dd></div>
              </dl>
            </div>
            <div className="indicator-group">
              <h3>Demanda</h3>
              <dl>
                <div><dt>Passageiros / viagem</dt><dd>{number(metrics.mean_passengers_per_trip)}</dd></div>
                <div><dt>Passageiros críticos / viagem</dt><dd>{number(metrics.mean_critical_passengers_per_trip)}</dd></div>
                <div><dt>IPK</dt><dd>{number(metrics.passengers_per_km, 3)}</dd></div>
                <div><dt>Extensão média</dt><dd>{number(metrics.mean_extension_km)} km</dd></div>
              </dl>
            </div>
            <div className="indicator-group">
              <h3>Custos</h3>
              <dl>
                <div><dt>Por veículo</dt><dd>{number(metrics.mean_cost_per_vehicle)}</dd></div>
                <div><dt>Por viagem</dt><dd>{number(metrics.cost_per_trip)}</dd></div>
                <div><dt>Por passageiro equivalente</dt><dd>{number(metrics.cost_per_equivalent_passenger, 3)}</dd></div>
                <div><dt>Semântica de distância</dt><dd className="text-value">{metrics.distance_semantics}</dd></div>
              </dl>
            </div>
          </div>
        </section>

        <section className="panel provenance-panel" id="provenance">
          <div className="panel-heading">
            <div>
              <span className="section-kicker">Reprodutibilidade</span>
              <h2>Provenance</h2>
            </div>
            <span className="verified-label">fingerprint verificado</span>
          </div>
          <div className="provenance-grid">
            <div><small>Engine</small><strong>{result.engine_id}</strong><span>v{result.engine_version}</span></div>
            <div><small>Semantic layer</small><strong>{result.semantic_layer}</strong><span>contrato explícito</span></div>
            <div><small>Input fingerprint</small><code title={result.input_fingerprint}>{shortHash(result.input_fingerprint)}</code><span>SHA-256 canônico</span></div>
            <div><small>Output fingerprint</small><code title={result.output_fingerprint}>{shortHash(result.output_fingerprint)}</code><span>reconstruído do PostgreSQL</span></div>
          </div>
          <details className="provenance-notes">
            <summary>Notas técnicas do modelo</summary>
            <ul>{result.provenance_notes.map((note) => <li key={note}>{note}</li>)}</ul>
          </details>
          <div className="run-footer">
            <span>run <code>{shortHash(result.computation_run_id.replaceAll("-", ""))}</code></span>
            <span>plan <code>{shortHash(result.plan_revision_id.replaceAll("-", ""))}</code></span>
            <span>snapshot <code>{shortHash(result.result_snapshot_id.replaceAll("-", ""))}</code></span>
          </div>
        </section>
      </div>
    </main>
  );
}
