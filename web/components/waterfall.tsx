import type { Summary } from "@/lib/analytics";
import { money, percent } from "@/lib/format";

type Step = {
  label: string;
  value: number;
  kind: "total" | "deduction" | "subtotal" | "result";
};

/**
 * Revenue-to-contribution bridge on one shared scale: every bar is positioned
 * against gross revenue, so the length of each deduction is directly comparable
 * (no per-row normalisation, baseline at zero).
 */
export function Waterfall({ summary: s }: { summary: Summary }) {
  const steps: Step[] = [
    { label: "Receita bruta", value: Number(s.gross_revenue), kind: "total" },
    { label: "Descontos", value: Number(s.discount_value), kind: "deduction" },
    { label: "Devoluções", value: Number(s.return_value), kind: "deduction" },
    {
      label: "Receita líquida",
      value: Number(s.net_revenue),
      kind: "subtotal",
    },
    {
      label: "CMV das unidades retidas",
      value: Number(s.total_product_cost),
      kind: "deduction",
    },
    {
      label: "Frete real",
      value: Number(s.freight_allocated),
      kind: "deduction",
    },
    {
      label: "Taxas, comissões e embalagem",
      value: Number(s.variable_cost_value),
      kind: "deduction",
    },
    {
      label: "Margem de contribuição",
      value: Number(s.contribution_margin),
      kind: "result",
    },
  ];
  const gross = steps[0].value;
  // A negative contribution extends the domain left of zero instead of clipping.
  const low = Math.min(0, steps[steps.length - 1].value);
  const span = gross - low || 1;
  const position = (value: number) => ((value - low) / span) * 100;

  let running = 0;
  const rows = steps.map((step) => {
    let from: number;
    let to: number;
    if (step.kind === "deduction") {
      from = running - step.value;
      to = running;
      running = from;
    } else {
      from = Math.min(0, step.value);
      to = Math.max(0, step.value);
      running = step.value;
    }
    return {
      ...step,
      left: position(from),
      width: position(to) - position(from),
    };
  });

  return (
    <ol className="waterfall" aria-describedby="bridge-scale">
      {rows.map((row) => (
        <li className={`waterfall-row ${row.kind}`} key={row.label}>
          <span className="waterfall-label">
            <span className="operator" aria-hidden="true">
              {row.kind === "deduction" ? "−" : row.kind === "total" ? "" : "="}
            </span>
            {row.label}
          </span>
          <span className="waterfall-track" aria-hidden="true">
            <span
              className="waterfall-bar"
              style={{ left: `${row.left}%`, width: `${row.width}%` }}
            />
          </span>
          <span className="waterfall-value">
            <strong>
              {row.kind === "deduction" ? "−" : ""}
              {money(row.value)}
            </strong>
            <small>{percent(gross ? row.value / gross : null)} da bruta</small>
          </span>
        </li>
      ))}
    </ol>
  );
}
