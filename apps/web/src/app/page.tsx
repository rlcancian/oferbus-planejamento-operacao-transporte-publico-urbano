type Readiness = {
  status: string;
  database: string;
  schema_name: string;
  server_version: string;
  migration: string;
};

export const dynamic = "force-dynamic";

async function loadReadiness(): Promise<Readiness | null> {
  const apiBase = process.env.OFERBUS_API_URL ?? "http://127.0.0.1:8010";

  try {
    const response = await fetch(`${apiBase}/ready`, { cache: "no-store" });
    if (!response.ok) return null;
    return (await response.json()) as Readiness;
  } catch {
    return null;
  }
}

export default async function Home() {
  const readiness = await loadReadiness();

  return (
    <main className="shell">
      <section className="hero">
        <div className="eyebrow">OferBus 2026 · plataforma em rematerialização</div>
        <h1>Planejamento operacional urbano, reconstruído para a web.</h1>
        <p>
          A fundação multiusuário já separa experiência web, API Python, identidade por organização,
          execução assíncrona, núcleo computacional determinístico e persistência PostgreSQL.
          O próximo marco cria a fronteira nativa do OferBus Copilot antes do quality gate local.
        </p>

        <div className="status-grid" aria-label="Estado da plataforma">
          <article><strong>Web</strong><span>Next.js 16 / React 19</span><small>Interface operacional e visualizações</small></article>
          <article><strong>API</strong><span>FastAPI / Python</span><small>Fronteira autoritativa do domínio</small></article>
          <article><strong>Identidade</strong><span>Organizações · RBAC · auditoria</span><small>Provedor de login permanece substituível</small></article>
          <article><strong>Jobs</strong><span>PostgreSQL · worker Python</span><small>Lease, heartbeat, retries e progresso SSE</small></article>
          <article><strong>Core</strong><span>legacy-exact · normalized · modern</span><small>Modelos determinísticos versionados</small></article>
          <article className={readiness ? "status-online" : "status-pending"}>
            <strong>PostgreSQL</strong>
            <span>{readiness ? `conectado · ${readiness.database}` : "aguardando API / banco"}</span>
            <small>{readiness ? `PostgreSQL ${readiness.server_version} · migration ${readiness.migration}` : "Aplique as migrations da Phase A para ativar a persistência local"}</small>
          </article>
        </div>

        <div className="architecture-strip" aria-label="Fluxo arquitetural">
          <span>Projetista</span><i>→</i><span>Web</span><i>→</i><span>API</span><i>→</i><span>ComputationRun</span><i>→</i><span>Worker</span><i>→</i><span>OferBus Core</span><i>→</i><span>PostgreSQL</span>
        </div>
      </section>
    </main>
  );
}
