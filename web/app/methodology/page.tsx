import { loadAnalytics } from "@/lib/analytics";

// Same order as the published contract; each file is verified against the manifest at build time.
const FILES = [
  "executive-summary",
  "monthly-profitability",
  "channels",
  "products",
  "customer-segments",
] as const;

export default function Methodology() {
  // Throws (and fails the build) if any file drifts from its manifest hash.
  const { manifest } = loadAnalytics();
  return (
    <main id="content" className="methodology">
      <h1>Como a rentabilidade é calculada</h1>
      <p className="lead">
        Este case usa dados sintéticos. Cada valor monetário foi calculado em
        centavos e conciliado no PostgreSQL antes da exportação.
      </p>
      <h2>Margem de contribuição</h2>
      <p>
        Receita líquida − CMV das unidades retidas − frete real − taxas e
        embalagem. Impostos, custos fixos e CAC não estão incluídos; o resultado
        não é lucro líquido.
      </p>
      <h2>Contrato V2</h2>
      <p>
        Taxas de pagamento, canal e comissão incidem sobre a receita líquida. A
        embalagem é um custo por item e permanece em devoluções. Essas taxas são
        hipóteses sintéticas, sem pretensão de representar preços de mercado.
      </p>
      <table>
        <thead>
          <tr>
            <th>Canal</th>
            <th>Pagamento</th>
            <th>Canal</th>
            <th>Comissão</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>Loja Física</td>
            <td>1,0%</td>
            <td>0%</td>
            <td>2,0%</td>
          </tr>
          <tr>
            <td>E-commerce</td>
            <td>3,2%</td>
            <td>0%</td>
            <td>0,5%</td>
          </tr>
          <tr>
            <td>Marketplace</td>
            <td>3,5%</td>
            <td>14,5%</td>
            <td>0,5%</td>
          </tr>
          <tr>
            <td>Venda Direta</td>
            <td>1,5%</td>
            <td>0%</td>
            <td>2,0%</td>
          </tr>
        </tbody>
      </table>
      <h2>Devolução e frete</h2>
      <p>
        Devoluções são atribuídas ao período da venda. O reembolso é
        proporcional ao valor descontado, e o CMV devolvido é recuperado. O
        frete permanece como custo e é distribuído por receita líquida; quando
        ela é zero, pela quantidade original.
      </p>
      <h2>Simulação e limite de desconto</h2>
      <p>
        Desconto uniforme substitui o desconto histórico e recalcula taxas sobre
        a nova receita. Quantidades retidas, mix e custos por volume ficam
        constantes. Para base B, custos C, taxa r e meta m, o teto analítico é 1
        − C / (B × (1 − r − m)). A taxa agregada é ponderada pela base sem
        desconto; cenários são conferidos em centavos.
      </p>
      <p>
        O crescimento compensatório de volume é um cenário matemático. Não
        modela demanda, elasticidade, capacidade ou estoque.
      </p>
      <h2>Limites e reprodução</h2>
      <p>
        Os gráficos leem cinco JSONs agregados identificados por hash. A
        aplicação não recebe senha de banco ou dados transacionais de clientes.
        O motor Power BI, sua conexão e testes visuais são verificados
        separadamente do build web.
      </p>
      <h2>Verificar o snapshot</h2>
      <p>
        Snapshot ativo <code>{manifest.snapshot}</code>. Cada arquivo abaixo é o
        mesmo lido pelos gráficos; o SHA-256 publicado no manifesto é conferido
        no build. Para conferir localmente, baixe o arquivo e compare com{" "}
        <code>sha256sum</code> (Linux/macOS) ou{" "}
        <code>Get-FileHash -Algorithm SHA256</code> (PowerShell).
      </p>
      <ul className="snapshot-files" aria-label="Arquivos do snapshot ativo">
        {FILES.map((name) => (
          <li key={name}>
            <a
              href={`/data/snapshots/${manifest.snapshot}/${name}.json`}
              download
            >
              {name}.json
            </a>
            <code className="hash" data-file={name}>
              {manifest.sha256[name]}
            </code>
          </li>
        ))}
      </ul>
      <a
        className="button"
        href="https://github.com/matheussiqueira-dev/Sales-Profitability-Intelligence"
      >
        Consultar código e instruções
      </a>
    </main>
  );
}
