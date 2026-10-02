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
          A fundação multiusuário já separa experiência web, API Python, núcleo computacional
          determinístico e persistência PostgreSQL. O próximo marco materializa identidade,
          execução assíncrona e o OferBus Copilot antes do primeiro vertical slice de planejamento.
        </p>

        <div className="status-grid" aria-label="Estado da plataforma">
          <article><strong>Web</strong><span>Next.js 16 / React 19</span><small>Interface operacional e visualizações</small></article>
          <article><strong>API</strong><span>FastAPI / Python</span><small>Fronteira autoritativa do domínio</small></article>
          <article><strong>Core</strong><span>legacy-exact · normalized · modern</span><small>Modelos determinísticos versionados</small></article>
          <article className={readiness ? "status-online" : "status-pending"}>
            <strong>PostgreSQL</strong>
            <span>{readiness ? `conectado · ${readiness.database}` : "aguardando API / banco"}</span>
            <small>{readiness ? `PostgreSQL ${readiness.server_version} · migration ${readiness.migration}` : "Execute a migration A.2 para ativar a persistência local"}</small>
          </article>
        </div>

        <div className="architecture-strip" aria-label="Fluxo arquitetural">
          <span>Projetista</span><i>→</i><span>Web</span><i>→</i><span>API</span><i>→</i><span>OferBus Core</span><i>→</i><span>PostgreSQL</span>
        </div>
      </section>
    </main>
  );
}
