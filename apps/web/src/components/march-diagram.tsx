import type { MarchDirection, MarchPlan, MarchTerminal } from "../lib/oferbus-api";
import styles from "./march-diagram.module.css";

function terminalKey(terminal: MarchTerminal): string {
  return terminal.id ?? `name:${terminal.name}`;
}

function serviceTime(value: number): string {
  const day = Math.floor(value / 1440);
  const minuteOfDay = ((value % 1440) + 1440) % 1440;
  const hours = Math.floor(minuteOfDay / 60);
  const minutes = minuteOfDay % 60;
  const clock = `${String(hours).padStart(2, "0")}:${String(minutes).padStart(2, "0")}`;
  return day > 0 ? `${clock} D+${day}` : clock;
}

function tickStep(span: number): number {
  if (span <= 120) return 10;
  if (span <= 240) return 20;
  if (span <= 480) return 30;
  if (span <= 960) return 60;
  return 120;
}

function directionLabel(direction: MarchDirection): string {
  const line = [direction.line_public_code, direction.line_name].filter(Boolean).join(" · ");
  return `${line} · ${direction.origin.name} → ${direction.destination.name}`;
}

export function MarchDiagram({ plan }: { plan: MarchPlan }) {
  const directionByKey = new Map(plan.directions.map((direction) => [direction.direction_key, direction]));
  const terminalByKey = new Map<string, MarchTerminal>();

  for (const direction of plan.directions) {
    terminalByKey.set(terminalKey(direction.origin), direction.origin);
    terminalByKey.set(terminalKey(direction.destination), direction.destination);
  }

  const terminals = [...terminalByKey.entries()];
  const blocks = [...new Set(plan.trips.map((trip) => trip.vehicle_block).filter((block) => block > 0))].sort(
    (a, b) => a - b,
  );

  const width = 1180;
  const left = 190;
  const right = 42;
  const top = 68;
  const bottom = 58;
  const railSpacing = terminals.length <= 2 ? 156 : 112;
  const height = Math.max(330, top + bottom + Math.max(1, terminals.length - 1) * railSpacing);
  const plotWidth = width - left - right;
  const plotHeight = height - top - bottom;

  const rawSpan = Math.max(1, plan.service_end_minute - plan.service_start_minute);
  const step = tickStep(rawSpan);
  const start = Math.floor(plan.service_start_minute / step) * step;
  const end = Math.ceil(plan.service_end_minute / step) * step;
  const span = Math.max(step, end - start);
  const x = (minute: number) => left + ((minute - start) / span) * plotWidth;
  const yByTerminal = new Map(
    terminals.map(([key], index) => [
      key,
      terminals.length === 1 ? top + plotHeight / 2 : top + (index / (terminals.length - 1)) * plotHeight,
    ]),
  );

  const ticks: number[] = [];
  for (let value = start; value <= end; value += step) ticks.push(value);

  return (
    <section className={`panel ${styles.panel}`} id="marcha">
      <div className="panel-heading">
        <div>
          <span className="section-kicker">Engenharia operacional</span>
          <h2>Gráfico de Marcha</h2>
        </div>
        <div className={styles.statusGroup}>
          <span className="panel-count">revisão {plan.revision_no}</span>
          <span className={styles.readOnly}>somente leitura · C.1</span>
        </div>
      </div>

      <div className={styles.metaBar}>
        <span>{serviceTime(plan.service_start_minute)} — {serviceTime(plan.service_end_minute)}</span>
        <span>{plan.trips.length} viagens</span>
        <span>{blocks.length} blocos</span>
        <span>{plan.source_kind === "computed" ? "plano computado" : "plano manual"}</span>
      </div>

      <div className={styles.directionStrip} aria-label="Sentidos representados">
        {plan.directions.map((direction) => (
          <span key={direction.direction_key} title={directionLabel(direction)}>
            <b>{direction.direction_key}</b>
            <i aria-hidden="true">→</i>
            {direction.origin.name} / {direction.destination.name}
          </span>
        ))}
      </div>

      <div className={styles.canvasWrap}>
        <svg
          className={styles.svg}
          viewBox={`0 0 ${width} ${height}`}
          role="img"
          aria-labelledby="march-title march-description"
        >
          <title id="march-title">Gráfico de Marcha da revisão {plan.revision_no}</title>
          <desc id="march-description">
            Eixo horizontal de tempo e trajetórias de viagens entre terminais. Cada trajetória identifica viagem,
            sentido e bloco de veículo. Linhas tracejadas representam tempos virtuais quando diferentes dos reais.
          </desc>

          <rect className={styles.plotBackground} x={left} y={top} width={plotWidth} height={plotHeight} rx="10" />

          {ticks.map((tick) => {
            const tickX = x(tick);
            return (
              <g key={tick}>
                <line className={styles.timeGrid} x1={tickX} y1={top} x2={tickX} y2={height - bottom} />
                <text className={styles.timeLabel} x={tickX} y={top - 18} textAnchor="middle">
                  {serviceTime(tick)}
                </text>
                <text className={styles.timeLabelBottom} x={tickX} y={height - bottom + 30} textAnchor="middle">
                  {serviceTime(tick)}
                </text>
              </g>
            );
          })}

          {terminals.map(([key, terminal], index) => {
            const railY = yByTerminal.get(key) ?? top;
            return (
              <g key={key}>
                <line className={styles.terminalRail} x1={left} y1={railY} x2={width - right} y2={railY} />
                <circle className={styles.terminalNode} cx={left - 18} cy={railY} r="5" />
                <text className={styles.terminalLabel} x={left - 32} y={railY - 4} textAnchor="end">
                  {terminal.name}
                </text>
                <text className={styles.terminalIndex} x={left - 32} y={railY + 14} textAnchor="end">
                  terminal {index + 1}
                </text>
              </g>
            );
          })}

          {plan.trips.map((trip) => {
            const direction = directionByKey.get(trip.direction_key);
            if (!direction) return null;
            const originY = yByTerminal.get(terminalKey(direction.origin));
            const destinationY = yByTerminal.get(terminalKey(direction.destination));
            if (originY === undefined || destinationY === undefined) return null;

            const classIndex = trip.vehicle_block > 0 ? ((trip.vehicle_block - 1) % 6) + 1 : 0;
            const blockClass = classIndex === 0 ? styles.blockUnassigned : styles[`block${classIndex}` as keyof typeof styles];
            const virtualDiffers =
              trip.virtual_departure_service_minute !== trip.departure_service_minute ||
              trip.virtual_arrival_service_minute !== trip.arrival_service_minute;
            const midX = (x(trip.departure_service_minute) + x(trip.arrival_service_minute)) / 2;
            const midY = (originY + destinationY) / 2;
            const tripTitle = [
              `Viagem ${trip.sequence_no}`,
              `${serviceTime(trip.departure_service_minute)} → ${serviceTime(trip.arrival_service_minute)}`,
              `${direction.origin.name} → ${direction.destination.name}`,
              `sentido ${trip.direction_key}`,
              trip.vehicle_block > 0 ? `veículo ${trip.vehicle_block}` : "sem bloco",
              trip.is_express ? "expresso" : "regular",
              trip.service_level === null ? "nível de serviço não informado" : `nível de serviço ${trip.service_level}`,
            ].join(" · ");

            return (
              <g className={styles.tripGroup} key={trip.sequence_no}>
                {virtualDiffers ? (
                  <line
                    className={styles.virtualTrip}
                    x1={x(trip.virtual_departure_service_minute)}
                    y1={originY}
                    x2={x(trip.virtual_arrival_service_minute)}
                    y2={destinationY}
                  />
                ) : null}
                <line
                  className={`${styles.tripLine} ${blockClass} ${trip.is_express ? styles.express : ""}`}
                  x1={x(trip.departure_service_minute)}
                  y1={originY}
                  x2={x(trip.arrival_service_minute)}
                  y2={destinationY}
                >
                  <title>{tripTitle}</title>
                </line>
                <circle className={`${styles.tripPoint} ${blockClass}`} cx={x(trip.departure_service_minute)} cy={originY} r="4">
                  <title>{tripTitle}</title>
                </circle>
                <circle className={`${styles.tripPoint} ${blockClass}`} cx={x(trip.arrival_service_minute)} cy={destinationY} r="4">
                  <title>{tripTitle}</title>
                </circle>
                <text className={styles.tripLabel} x={midX + 7} y={midY - 7}>
                  {trip.sequence_no}
                </text>
              </g>
            );
          })}
        </svg>
      </div>

      <div className={styles.legend}>
        <span className={styles.legendTitle}>Blocos</span>
        {blocks.map((block) => {
          const classIndex = ((block - 1) % 6) + 1;
          const blockClass = styles[`block${classIndex}` as keyof typeof styles];
          return (
            <span key={block} className={styles.legendItem}>
              <i className={`${styles.legendSwatch} ${blockClass}`} aria-hidden="true" /> V{block}
            </span>
          );
        })}
        <span className={styles.legendNote}>linha tracejada = horário virtual distinto</span>
      </div>
    </section>
  );
}
