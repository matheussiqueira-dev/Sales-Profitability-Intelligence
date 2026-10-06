import Link from "next/link";
import { loadAnalytics } from "@/lib/analytics";
import { money, percent } from "@/lib/format";
import { ChannelChart, ProductQuadrant, Trend } from "@/components/charts";

export default function Page() {
  const {
    summary: s,
    months,
    channels,
    products,
    segments,
    manifest,
  } = loadAnalytics();
  const bridge = [
    { label: "Receita bruta", value: s.gross_revenue, kind: "revenue" },
    { label: "Descontos", value: s.discount_value, kind: "cost" },
    { label: "Devoluções", value: s.return_value, kind: "cost" },
    { label: "CMV", value: s.total_product_cost, kind: "cost" },
    { label: "Frete", value: s.freight_allocated, kind: "cost" },
    { label: "Taxas e embalagem", value: s.variable_cost_value, kind: "cost" },
    { label: "Contribuição", value: s.contribution_margin, kind: "margin" },
  ];
  const best = [...channels].sort(
    (a, b) => Number(b.margin_percentage) - Number(a.margin_percentage),
  )[0];
  return (
    <main id="content">
      <section className="intro">
        <div>
          <p className="context">Case de Analytics Engineering · 2024–2025</p>
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
        <aside className="decision">
          <p>O que a base mostra</p>
          <h2>{best.channel_name} tem a maior margem.</h2>
          <p>
            {percent(best.margin_percentage)} da receita líquida permanece como
            contribuição. Volume de vendas e rentabilidade contam histórias
            diferentes.
          </p>
          <Link href="/methodology">Entender as premissas</Link>
        </aside>
      </section>
      <div className="provenance">
        <span>Dados sintéticos</span>
        <span>Contrato financeiro V2</span>
        <span>Conciliação em centavos aprovada</span>
        <span>
          Snapshot de{" "}
          {new Intl.DateTimeFormat("pt-BR", {
            dateStyle: "short",
            timeZone: "America/Fortaleza",
          }).format(new Date(manifest.completed_at))}
        </span>
      </div>
      <section aria-labelledby="bridge-title">
        <div className="section-heading">
          <h2 id="bridge-title">Da venda à contribuição</h2>
          <p>A receita líquida é a bruta menos descontos e devoluções.</p>
        </div>
        <div className="bridge">
          {bridge.map((item, i) => (
            <div className={`bridge-step ${item.kind}`} key={item.label}>
              <span className="operator" aria-hidden="true">
                {i === 0 ? "" : i === bridge.length - 1 ? "=" : "−"}
              </span>
              <div>
                <span>{item.label}</span>
                <strong>{money(item.value)}</strong>
                <div
                  className="bridge-bar"
                  style={{
                    width: `${Math.max(4, (Number(item.value) / Number(s.gross_revenue)) * 100)}%`,
                  }}
                />
              </div>
            </div>
          ))}
        </div>
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
        <article>
          <div className="section-heading">
            <h2>Receita e contribuição no tempo</h2>
            <p>
              Valores em reais. Cada mês mostra o efeito do mix, desconto e
              custos.
            </p>
          </div>
          <div className="legend">
            <span className="revenue-dot">Receita líquida</span>
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
                    <th>Mês</th>
                    <th>Receita</th>
                    <th>Contribuição</th>
                    <th>Margem</th>
                  </tr>
                </thead>
                <tbody>
                  {months.map((m) => (
                    <tr key={m.month}>
                      <td>{m.month.slice(0, 7)}</td>
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
        <article>
          <div className="section-heading">
            <h2>Vendas por canal</h2>
            <p>A maior receita nem sempre produz a maior margem.</p>
          </div>
          <ChannelChart channels={channels} />
          <table className="channel-table">
            <thead>
              <tr>
                <th>Canal</th>
                <th>Contribuição</th>
                <th>Margem</th>
              </tr>
            </thead>
            <tbody>
              {channels.map((c) => (
                <tr key={c.channel_name}>
                  <td>{c.channel_name}</td>
                  <td>{money(c.contribution_margin)}</td>
                  <td>{percent(c.margin_percentage)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </article>
      </section>
      <section className="products-section">
        <div className="section-heading">
          <h2>Onde receita e margem se encontram</h2>
          <p>
            Produtos com volume elevado merecem atenção quando a margem não
            acompanha.
          </p>
        </div>
        <ProductQuadrant products={products} />
      </section>
      <section className="segments">
        <h2>Clientes, por perfil de rentabilidade</h2>
        <p className="muted">
          Segmentação do snapshot completo, com receita P75, margem ponderada e
          recência.
        </p>
        <div className="segment-grid">
          {segments.map((x) => (
            <div key={x.segment}>
              <span>{x.segment}</span>
              <strong>{x.customers.toLocaleString("pt-BR")}</strong>
              <small>{money(x.contribution_margin)} em contribuição</small>
            </div>
          ))}
        </div>
      </section>
      <section className="method-preview">
        <div>
          <h2>Um número precisa de uma trilha.</h2>
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
