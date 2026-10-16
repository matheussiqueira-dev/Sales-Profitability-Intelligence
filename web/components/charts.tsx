"use client";
import { useMemo, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ComposedChart,
  Line,
  ReferenceLine,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
  ZAxis,
} from "recharts";
import type { Channel, Month, Product } from "@/lib/analytics";
import { compact, money, percent } from "@/lib/format";
import { chart } from "@/lib/tokens";

const tick = { fontSize: 11, fill: chart.axis };
const MONTHS = [
  "jan",
  "fev",
  "mar",
  "abr",
  "mai",
  "jun",
  "jul",
  "ago",
  "set",
  "out",
  "nov",
  "dez",
];
/** "2025-03-01" → "mar/25", parsed from the ISO string to avoid timezone drift. */
const monthLabel = (iso: string) =>
  `${MONTHS[Number(iso.slice(5, 7)) - 1]}/${iso.slice(2, 4)}`;

export function Trend({ months }: { months: Month[] }) {
  const data = months.map((m) => ({
    month: monthLabel(m.month),
    receita: Number(m.net_revenue),
    contribuicao: Number(m.contribution_margin),
  }));
  return (
    <div
      className="chart-frame"
      role="img"
      aria-label="Receita líquida em barras e contribuição em linha, mês a mês. Os valores completos estão na tabela abaixo."
    >
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart
          data={data}
          margin={{ top: 12, right: 12, left: 0, bottom: 8 }}
        >
          <CartesianGrid vertical={false} stroke={chart.grid} />
          <XAxis
            dataKey="month"
            tick={tick}
            tickLine={false}
            axisLine={{ stroke: chart.grid }}
            minTickGap={24}
          />
          <YAxis
            tickFormatter={compact}
            width={52}
            tick={tick}
            tickLine={false}
            axisLine={false}
          />
          <Tooltip formatter={(v) => money(String(v))} />
          <Bar
            name="Receita líquida"
            dataKey="receita"
            fill={chart.revenueSoft}
            radius={[3, 3, 0, 0]}
            isAnimationActive={false}
          />
          <Line
            name="Contribuição"
            dataKey="contribuicao"
            stroke={chart.margin}
            dot={false}
            strokeWidth={2.5}
            isAnimationActive={false}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}

export function ChannelChart({ channels }: { channels: Channel[] }) {
  const data = channels.map((c) => ({
    name: c.channel_name,
    receita: Number(c.net_revenue),
    contribuicao: Number(c.contribution_margin),
  }));
  return (
    <div
      className="chart-frame"
      role="img"
      aria-label="Receita líquida e contribuição por canal, na mesma escala. A tabela logo abaixo traz os valores."
    >
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={data}
          layout="vertical"
          barGap={2}
          margin={{ top: 4, right: 12, bottom: 8, left: 4 }}
        >
          <CartesianGrid horizontal={false} stroke={chart.grid} />
          <YAxis
            type="category"
            dataKey="name"
            width={96}
            tick={tick}
            tickLine={false}
            axisLine={false}
          />
          <XAxis
            type="number"
            tickFormatter={compact}
            tick={tick}
            tickLine={false}
            axisLine={{ stroke: chart.grid }}
          />
          <Tooltip formatter={(v) => money(String(v))} />
          <Bar
            name="Receita líquida"
            dataKey="receita"
            fill={chart.revenue}
            radius={[0, 3, 3, 0]}
            isAnimationActive={false}
          />
          <Bar
            name="Contribuição"
            dataKey="contribuicao"
            fill={chart.margin}
            radius={[0, 3, 3, 0]}
            isAnimationActive={false}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

type Point = { name: string; x: number; y: number; z: number };

export function ProductQuadrant({ products }: { products: Product[] }) {
  const [category, setCategory] = useState("Todas");
  const categories = useMemo(
    () =>
      Array.from(new Set(products.map((p) => p.category))).sort((a, b) =>
        a.localeCompare(b, "pt-BR"),
      ),
    [products],
  );
  const filtered = products.filter(
    (p) => category === "Todas" || p.category === category,
  );
  const points: Point[] = filtered
    .filter((p) => p.margin_percentage !== null)
    .map((p) => ({
      name: p.product_name,
      x: Number(p.net_revenue),
      y: Number(p.margin_percentage) * 100,
      z: Number(p.quantity),
    }));
  // Losses get their own series so the sign is carried by colour and position.
  const gains = points.filter((p) => p.y >= 0);
  const losses = points.filter((p) => p.y < 0);
  const sorted = points.map((p) => p.x).sort((a, b) => a - b);
  const revenueThreshold = sorted.length
    ? sorted[Math.floor((sorted.length - 1) * 0.75)]
    : 0;
  const totalRevenue = filtered.reduce((a, p) => a + Number(p.net_revenue), 0);
  const averageMargin = totalRevenue
    ? (filtered.reduce((a, p) => a + Number(p.contribution_margin), 0) /
        totalRevenue) *
      100
    : 0;
  const ranked = [...filtered].sort(
    (a, b) => Number(b.net_revenue) - Number(a.net_revenue),
  );
  return (
    <>
      <div className="section-tools">
        <label htmlFor="category">Categoria</label>
        <select
          id="category"
          value={category}
          onChange={(e) => setCategory(e.target.value)}
        >
          <option>Todas</option>
          {categories.map((c) => (
            <option key={c}>{c}</option>
          ))}
        </select>
        <div className="legend">
          <span className="revenue-dot">Contribuição positiva</span>
          <span className="loss-dot">Contribuição negativa</span>
        </div>
        <span className="tools-note">
          Tracejado: receita P75 e margem ponderada
        </span>
      </div>
      <div
        className="chart-frame quadrant"
        role="img"
        aria-label={`Quadrante de produtos (${category}): receita líquida no eixo horizontal, margem no vertical, tamanho proporcional às unidades. ${losses.length} produto(s) com contribuição negativa.`}
      >
        <ResponsiveContainer width="100%" height="100%">
          <ScatterChart margin={{ top: 24, right: 28, bottom: 16, left: 4 }}>
            <CartesianGrid stroke={chart.grid} />
            <XAxis
              type="number"
              dataKey="x"
              name="Receita líquida"
              tickFormatter={compact}
              tick={tick}
              tickLine={false}
              axisLine={{ stroke: chart.grid }}
            />
            <YAxis
              type="number"
              dataKey="y"
              name="Margem"
              unit="%"
              width={48}
              tick={tick}
              tickLine={false}
              axisLine={false}
            />
            <ZAxis
              type="number"
              dataKey="z"
              range={[22, 260]}
              name="Unidades"
            />
            <ReferenceLine y={0} stroke={chart.axis} strokeWidth={1} />
            <ReferenceLine
              x={revenueThreshold}
              stroke={chart.reference}
              strokeDasharray="4 4"
              label={{
                value: "P75",
                position: "top",
                fill: chart.axis,
                fontSize: 11,
              }}
            />
            <ReferenceLine
              y={averageMargin}
              stroke={chart.reference}
              strokeDasharray="4 4"
              label={{
                value: "média",
                position: "insideTopRight",
                fill: chart.axis,
                fontSize: 11,
              }}
            />
            <Tooltip
              cursor={{ strokeDasharray: "3 3" }}
              content={({ active, payload }) => {
                const point = payload?.[0]?.payload as Point | undefined;
                return active && point ? (
                  <div className="chart-tooltip">
                    <strong>{point.name}</strong>
                    <p>Receita {money(point.x)}</p>
                    <p>Margem {percent(point.y / 100)}</p>
                    <p>{point.z.toLocaleString("pt-BR")} unidades</p>
                  </div>
                ) : null;
              }}
            />
            <Scatter
              data={gains}
              fill={chart.revenue}
              fillOpacity={0.55}
              isAnimationActive={false}
            />
            <Scatter
              data={losses}
              fill={chart.loss}
              fillOpacity={0.7}
              isAnimationActive={false}
            />
          </ScatterChart>
        </ResponsiveContainer>
      </div>
      <p className="muted">
        Acima e à direita: receita e margem elevadas. Abaixo e à direita:
        receita elevada com contribuição percentual abaixo da média. Abaixo da
        linha de 0%: cada venda reduz o resultado.
      </p>
      <details>
        <summary>Consultar os {filtered.length} produtos em tabela</summary>
        <div
          className="table-scroll"
          tabIndex={0}
          role="region"
          aria-label="Rentabilidade dos produtos"
        >
          <table>
            <thead>
              <tr>
                <th scope="col">Produto</th>
                <th scope="col">Receita líquida</th>
                <th scope="col">Contribuição</th>
                <th scope="col">Margem</th>
              </tr>
            </thead>
            <tbody>
              {ranked.map((p) => (
                <tr key={`${p.category}-${p.product_name}`}>
                  <th scope="row">{p.product_name}</th>
                  <td>{money(p.net_revenue)}</td>
                  <td
                    className={
                      Number(p.contribution_margin) < 0 ? "negative" : ""
                    }
                  >
                    {money(p.contribution_margin)}
                  </td>
                  <td>{percent(p.margin_percentage)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>
    </>
  );
}
