export default function Home() {
  return (
    <main className="shell">
      <section className="hero">
        <div className="eyebrow">OferBus 2026</div>
        <h1>Planejamento operacional urbano, reconstruído para a web.</h1>
        <p>
          Skeleton técnico inicial. O domínio, o motor computacional, a edição do gráfico de marcha,
          a persistência multiusuário e o OferBus Copilot serão materializados nas próximas fases.
        </p>
        <div className="status-grid" aria-label="Estado inicial da plataforma">
          <article><strong>Web</strong><span>Next.js 16 / React 19</span></article>
          <article><strong>API</strong><span>FastAPI / Python</span></article>
          <article><strong>Core</strong><span>legacy-exact · normalized · modern</span></article>
          <article><strong>Dados</strong><span>PostgreSQL — próxima subfase</span></article>
        </div>
      </section>
    </main>
  );
}
