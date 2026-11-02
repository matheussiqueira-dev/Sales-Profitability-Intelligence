import Link from "next/link";
import type { Channel, Segment } from "@/lib/analytics";
import { loadAnalytics } from "@/lib/analytics";
import { money, percent } from "@/lib/format";
import { ChannelChart, ProductQuadrant, Trend } from "@/components/charts";
import { Waterfall } from "@/components/waterfall";

/** Display order and Portuguese labels; keys stay as exported by the warehouse view. */
const SEGMENTS: Record<string, { label: string; description: string }> = {
  Champions: {
    label: "Campeões",
    description: "Receita no P75 e margem acima da média",
  },
  "High Margin": {
    label: "Alta margem",
    description: "Margem acima da média, receita menor",
  },
  "High Revenue / Low Margin": {
    label: "Receita alta, margem baixa",
    description: "Prioridade para rever condições comerciais",
  },
  "Low Value": {
    label: "Baixo valor",
    description: "Receita e margem abaixo das referências",
  },
  "At Risk": {
    label: "Em risco",
    description: "Sem pedido há mais de 90 dias",
  },
};
const SEGMENT_ORDER = Object.keys(SEGMENTS);

const byNumber =
  <T,>(pick: (item: T) => string | null) =>
  (a: T, b: T) =>
    Number(pick(b) ?? -Infinity) - Number(pick(a) ?? -Infinity);

function channelHeadline(channels: Channel[]) {
  const topRevenue = [...channels].sort(byNumber((c) => c.net_revenue))[0];
  const topMargin = [...channels].sort(byNumber((c) => c.margin_percentage))[0];
  return topRevenue.channel_name === topMargin.channel_name
    ? `${topRevenue.channel_name} lidera receita e margem.`
    : `${topRevenue.channel_name} lidera a receita; ${topMargin.channel_name}, a margem.`;
}

function orderedSegments(segments: Segment[]) {
  return [...segments].sort(
    (a, b) =>
      (SEGMENT_ORDER.indexOf(a.segment) + 1 || 99) -
      (SEGMENT_ORDER.indexOf(b.segment) + 1 || 99),
  );
}

export default function Page() {
  const {
    summary: s,
    months,
    channels,
    products,
    segments,
    manifest,
  } = loadAnalytics();
  const best = [...channels].sort(byNumber((c) => c.margin_percentage))[0];
  const margins = months
    .map((m) => m.margin_percentage)
    .filter((m): m is string => m !== null)
    .map(Number);
  const lossProducts = products.filter(
    (p) => Number(p.contribution_margin) < 0,
  ).length;
  const segmentTotal = segments.reduce(
    (total, x) => total + Math.max(0, Number(x.contribution_margin)),
    0,
  );
  const gross = Number(s.gross_revenue);
  const perHundred = gross
    ? (Number(s.contribution_margin) / gross) * 100
    : null;
  const snapshotDate = new Intl.DateTimeFormat("pt-BR", {
    dateStyle: "short",
    timeZone: "America/Fortaleza",
  }).format(new Date(manifest.completed_at));
  const period = `de ${manifest.period.from.slice(0, 4)} a ${manifest.period.through_month.slice(0, 4)}`;

  return (
    <main id="content">
      <section className="intro">
        <div>
          <p className="context">
            Case de Analytics Engineering com vendas {period}
          </p>
          <h1>
            Vender mais.
            <br />
            Contribuir quanto?
          </h1>
          <p className="lead">
            Descontos, devoluções e custos mudam o resultado. Explore quanto da
            receita permanece como margem de contribuição em cada produto e
            canal.
          </p>
          <Link className="button" href="#analysis">
            Explorar a rentabilidade
          </Link>
        </div>
        <aside className="decision" aria-labelledby="decision-title">
          <h2 id="decision-title">{best.channel_name} tem a maior margem.</h2>
          <p>
            <strong className="decision-figure">
              {percent(best.margin_percentage)}
            </strong>{" "}
            da receita líquida permanece como contribuição. Volume de vendas e
            rentabilidade contam histórias diferentes.
          </p>
          <Link className="text-link" href="/methodology">
            Entender as premissas
          </Link>
        </aside>
      </section>

      <ul className="provenance" aria-label="Procedência dos dados">
        <li>Dados sintéticos</li>
        <li>Contrato financeiro V2</li>
        <li>Conciliação em centavos aprovada</li>
        <li>
          Snapshot <code>{manifest.snapshot.slice(0, 8)}</code> de{" "}
          {snapshotDate}
        </li>
      </ul>

      <section className="bridge-section" aria-labelledby="bridge-title">
        <div className="section-heading">
          <h2 id="bridge-title">
            {perHundred === null
              ? "Da venda à contribuição"
              : `De cada R$ 100 vendidos, ${money(perHundred)} viram contribuição.`}
          </h2>
          <p id="bridge-scale">
            Todas as barras usam a mesma escala da receita bruta. A receita
            líquida é a bruta menos descontos e devoluções.
          </p>
        </div>
        <Waterfall summary={s} />
      </section>

      <section className="kpi-strip" aria-label="Indicadores executivos">
        <div>
          <span>Receita líquida</span>
          <strong>{money(s.net_revenue)}</strong>
        </div>
        <div>
          <span>Margem de contribuição</span>
          <strong className="margin-text">
            {percent(s.margin_percentage)}
          </strong>
        </div>
        <div>
          <span>Pedidos não cancelados</span>
          <strong>{s.orders.toLocaleString("pt-BR")}</strong>
        </div>
        <div>
          <span>Ticket médio</span>
          <strong>{money(s.average_ticket)}</strong>
        </div>
        <div>
          <span>Desconto ponderado</span>
          <strong>{percent(s.discount_percentage)}</strong>
        </div>
      </section>

      <section id="analysis" className="analysis-grid">
        <article aria-labelledby="trend-title">
          <div className="section-heading">
            <h2 id="trend-title">
              {margins.length
                ? `Margem mensal oscila entre ${percent(Math.min(...margins))} e ${percent(Math.max(...margins))}.`
                : "Receita e contribuição no tempo"}
            </h2>
            <p>
              Valores em reais. Cada mês reflete mix, desconto e custos do
              período.
            </p>
          </div>
          <div className="legend" aria-hidden="true">
            <span className="revenue-soft-dot">Receita líquida</span>
            <span className="margin-dot">Contribuição</span>
          </div>
          <Trend months={months} />
          <details>
            <summary>Ver valores mensais</summary>
            <div
              className="table-scroll"
              role="region"
              tabIndex={0}
              aria-label="Valores mensais"
            >
              <table>
                <thead>
                  <tr>
                    <th scope="col">Mês</th>
                    <th scope="col">Receita</th>
                    <th scope="col">Contribuição</th>
                    <th scope="col">Margem</th>
                  </tr>
                </thead>
                <tbody>
                  {months.map((m) => (
                    <tr key={m.month}>
                      <th scope="row">{m.month.slice(0, 7)}</th>
                      <td>{money(m.net_revenue)}</td>
                      <td>{money(m.contribution_margin)}</td>
                      <td>{percent(m.margin_percentage)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </details>
        </article>
        <article aria-labelledby="channel-title">
          <div className="section-heading">
            <h2 id="channel-title">{channelHeadline(channels)}</h2>
            <p>A maior receita nem sempre produz a maior margem.</p>
          </div>
          <div className="legend" aria-hidden="true">
            <span className="revenue-dot">Receita líquida</span>
            <span className="margin-dot">Contribuição</span>
          </div>
          <ChannelChart channels={channels} />
          <table className="channel-table">
            <thead>
              <tr>
                <th scope="col">Canal</th>
                <th scope="col">Contribuição</th>
                <th scope="col">Margem</th>
              </tr>
            </thead>
            <tbody>
              {channels.map((c) => (
                <tr key={c.channel_name}>
                  <th scope="row">{c.channel_name}</th>
                  <td>{money(c.contribution_margin)}</td>
                  <td>{percent(c.margin_percentage)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </article>
      </section>

      <section className="products-section" aria-labelledby="products-title">
        <div className="section-heading">
          <h2 id="products-title">
            {lossProducts
              ? `${lossProducts} de ${products.length} produtos vendem com contribuição negativa.`
              : "Onde receita e margem se encontram"}
          </h2>
          <p>
            Produtos com volume elevado merecem atenção quando a margem não
            acompanha.
          </p>
        </div>
        <ProductQuadrant products={products} />
      </section>

      <section className="segments" aria-labelledby="segments-title">
        <div className="section-heading">
          <h2 id="segments-title">Clientes, por perfil de rentabilidade</h2>
          <p>
            Segmentação do snapshot completo, com receita P75, margem ponderada
            e recência. Barra: participação na contribuição positiva.
          </p>
        </div>
        <div className="segment-grid">
          {orderedSegments(segments).map((x) => {
            const meta = SEGMENTS[x.segment];
            const share = segmentTotal
              ? Math.max(0, Number(x.contribution_margin)) / segmentTotal
              : 0;
            return (
              <div key={x.segment}>
                <span className="segment-name">{meta?.label ?? x.segment}</span>
                <strong>{x.customers.toLocaleString("pt-BR")}</strong>
                <small>{meta?.description ?? "Clientes"}</small>
                <span className="share-track" aria-hidden="true">
                  <span style={{ width: `${share * 100}%` }} />
                </span>
                <small>
                  {money(x.contribution_margin)} em contribuição (
                  {percent(share)})
                </small>
              </div>
            );
          })}
        </div>
      </section>

      <section className="method-preview" aria-labelledby="method-title">
        <div>
          <h2 id="method-title">Um número precisa de uma trilha.</h2>
          <p>
            Os mesmos totais atravessam origem, Python e PostgreSQL. A aplicação
            apresenta somente dados agregados do snapshot aprovado.
          </p>
          <Link className="button" href="/methodology">
            Consultar a metodologia
          </Link>
        </div>
        <ol className="architecture">
          <li>Transações sintéticas</li>
          <li>Contratos Pandera e regras relacionais</li>
          <li>PostgreSQL: raw → staging → analytics</li>
          <li>Reconciliação Python e SQL</li>
          <li>Power BI e showcase</li>
        </ol>
      </section>
    </main>
  );
}
