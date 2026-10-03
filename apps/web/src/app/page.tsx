import { PlanningWorkspace } from "../components/planning-workspace";
import { loadPlanningWorkspace } from "../lib/oferbus-api";

export const dynamic = "force-dynamic";

function EmptyWorkspace({ unavailable, error }: { unavailable: boolean; error: string | null }) {
  return (
    <main className="workspace-shell empty-workspace">
      <header className="topbar">
        <div className="brand-lockup">
          <span className="brand-mark" aria-hidden="true">O</span>
          <div>
            <strong>OferBus</strong>
            <small>planejamento operacional</small>
          </div>
        </div>
        <div className={`system-pill ${unavailable ? "system-offline" : "system-online"}`}>
          <span aria-hidden="true" />
          {unavailable ? "API / identidade indisponível" : "Plataforma pronta"}
        </div>
      </header>

      <section className="empty-stage">
        <div className="empty-orbit" aria-hidden="true"><i /><i /><i /></div>
        <span className="section-kicker">Workspace operacional</span>
        <h1>{unavailable ? "O resultado ainda não pode ser carregado." : "Ainda não há um plano calculado."}</h1>
        <p>
          {unavailable
            ? "O frontend está operacional, mas a API autenticada de resultados não respondeu corretamente. O diagnóstico abaixo mostra a resposta concreta recebida pelo workspace."
            : "Execute uma computação core-planning para materializar a primeira revisão. O workspace aparecerá automaticamente com horários, blocos, frota, indicadores e provenance."}
        </p>
        {unavailable && error ? <code className="workspace-error-detail">{error}</code> : null}
        <div className="empty-flow" aria-label="Fluxo para gerar o primeiro resultado">
          <span>ScenarioRevision</span><i>→</i><span>core-planning</span><i>→</i><span>PlanRevision</span><i>→</i><span>Workspace</span>
        </div>
      </section>
    </main>
  );
}

export default async function Home() {
  const workspace = await loadPlanningWorkspace();

  if (!workspace.result) {
    return (
      <EmptyWorkspace
        unavailable={workspace.resultStatus === "unavailable"}
        error={workspace.resultError}
      />
    );
  }

  return (
    <PlanningWorkspace
      result={workspace.result}
      readiness={workspace.readiness}
      march={workspace.march}
      marchError={workspace.marchError}
    />
  );
}
