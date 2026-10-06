"use client";
import { useState } from "react";
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
import type { Month, Channel, Product } from "@/lib/analytics";
import { compact, money, percent } from "@/lib/format";

export function Trend({ months }: { months: Month[] }) {
  const data = months.map((m) => ({
    month: m.month.slice(0, 7),
    receita: Number(m.net_revenue),
    contribuicao: Number(m.contribution_margin),
  }));
  return (
    <div
      className="chart-frame"
      role="img"
      aria-label="Receita líquida e contribuição mês a mês. Os valores completos estão na tabela abaixo."
    >
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart
          data={data}
          margin={{ top: 12, right: 12, left: 0, bottom: 8 }}
        >
          <CartesianGrid vertical={false} stroke="#e4e9ed" />
          <XAxis dataKey="month" tick={{ fontSize: 11 }} minTickGap={30} />
          <YAxis tickFormatter={compact} width={55} tick={{ fontSize: 11 }} />
          <Tooltip formatter={(v) => money(String(v))} />
          <Bar
            name="Receita líquida"
            dataKey="receita"
            fill="#d4e3f1"
            radius={[3, 3, 0, 0]}
            isAnimationActive={false}
          />
          <Line
            name="Contribuição"
            dataKey="contribuicao"
            stroke="#08745B"
            dot={false}
            strokeWidth={3}
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
      aria-label="Receita e contribuição por canal, com tabela de valores logo abaixo."
    >
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={data}
          layout="vertical"
          margin={{ top: 12, right: 12, bottom: 8, left: 8 }}
        >
          <CartesianGrid horizontal={false} stroke="#e4e9ed" />
          <YAxis
            type="category"
            dataKey="name"
            width={98}
            tick={{ fontSize: 11 }}
          />
          <XAxis
            type="number"
            tickFormatter={compact}
            tick={{ fontSize: 11 }}
          />
          <Tooltip formatter={(v) => money(String(v))} />
          <Bar
            name="Receita líquida"
            dataKey="receita"
            fill="#2463a6"
            isAnimationActive={false}
          />
          <Bar
            name="Contribuição"
            dataKey="contribuicao"
            fill="#08745b"
            isAnimationActive={false}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export function ProductQuadrant({ products }: { products: Product[] }) {
  const [category, setCategory] = useState("Todas");
  const filtered = products.filter(
    (p) => category === "Todas" || p.category === category,
  );
  const points = filtered
    .filter((p) => p.margin_percentage !== null)
    .map((p) => ({
      name: p.product_name,
      x: Number(p.net_revenue),
      y: Number(p.margin_percentage) * 100,
      z: Number(p.quantity),
    }));
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
          {Array.from(new Set(products.map((p) => p.category))).map((c) => (
            <option key={c}>{c}</option>
          ))}
        </select>
        <span>Referências: receita P75 e margem ponderada</span>
      </div>
      <div
        className="chart-frame quadrant"
        role="img"
        aria-label={`Quadrante de produtos de ${category}. Receita no eixo horizontal, margem no vertical; tamanho representa unidades.`}
      >
        <ResponsiveContainer width="100%" height="100%">
          <ScatterChart margin={{ top: 20, right: 30, bottom: 20, left: 10 }}>
            <CartesianGrid stroke="#e4e9ed" />
            <XAxis
              type="number"
              dataKey="x"
              name="Receita líquida"
              tickFormatter={compact}
              tick={{ fontSize: 11 }}
            />
            <YAxis
              type="number"
              dataKey="y"
              name="Margem"
              unit="%"
              width={50}
              tick={{ fontSize: 11 }}
            />
            <ZAxis
              type="number"
              dataKey="z"
              range={[22, 260]}
              name="Unidades"
            />
            <ReferenceLine
              x={revenueThreshold}
              stroke="#8a98a5"
              strokeDasharray="4 4"
            />
            <ReferenceLine
              y={averageMargin}
              stroke="#8a98a5"
              strokeDasharray="4 4"
            />
            <Tooltip
              cursor={{ strokeDasharray: "3 3" }}
              content={({ active, payload }) =>
                active && payload?.length ? (
                  <div className="chart-tooltip">
                    <strong>{payload[0].payload.name}</strong>
                    <p>{money(payload[0].payload.x)}</p>
                    <p>Margem {percent(payload[0].payload.y / 100)}</p>
                  </div>
                ) : null
              }
            />
            <Scatter
              data={points}
              fill="#2463a6"
              fillOpacity={0.55}
              isAnimationActive={false}
            />
          </ScatterChart>
        </ResponsiveContainer>
      </div>
      <p className="muted">
        Acima e à direita: receita e margem elevadas. Abaixo e à direita:
        produtos com receita elevada e contribuição percentual abaixo da média.
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
                <th>Produto</th>
                <th>Receita líquida</th>
                <th>Contribuição</th>
                <th>Margem</th>
              </tr>
            </thead>
            <tbody>
              {filtered
                .sort((a, b) => Number(b.net_revenue) - Number(a.net_revenue))
                .map((p) => (
                  <tr key={p.product_name}>
                    <td>{p.product_name}</td>
                    <td>{money(p.net_revenue)}</td>
                    <td
                      className={
                        Number(p.contribution_margin) < 0 ? "negative" : ""
                      }
                    >
                      {money(p.contribution_margin)}
                    </td>
                    <td>
                      {p.margin_percentage === null
                        ? "—"
                        : percent(p.margin_percentage)}
                    </td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
      </details>
    </>
  );
}
