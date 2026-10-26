import { expect, test } from "@playwright/test";
import { readFileSync } from "node:fs";
import { join } from "node:path";

// Everything expected here comes from the active snapshot: publishing a new snapshot
// must not require editing this file.
const dataDir = join(__dirname, "..", "public", "data");
const readJson = <T>(...parts: string[]): T =>
  JSON.parse(readFileSync(join(dataDir, ...parts), "utf8")) as T;

type Summary = Record<
  | "gross_revenue"
  | "discount_value"
  | "return_value"
  | "net_revenue"
  | "total_product_cost"
  | "freight_allocated"
  | "variable_cost_value"
  | "contribution_margin"
  | "average_ticket"
  | "margin_percentage"
  | "discount_percentage",
  string
> & { orders: number };
type Channel = {
  channel_name: string;
  net_revenue: string;
  contribution_margin: string;
  margin_percentage: string | null;
};

const { snapshot } = readJson<{ snapshot: string }>("manifest.json");
const summary = readJson<Summary>(
  "snapshots",
  snapshot,
  "executive-summary.json",
);
const channels = readJson<Channel[]>("snapshots", snapshot, "channels.json");

/** Exact cents from a decimal string, without going through floating point. */
function cents(value: string): bigint {
  const negative = value.startsWith("-");
  const [whole, fraction = ""] = value.replace("-", "").split(".");
  const total =
    BigInt(whole) * BigInt(100) + BigInt(`${fraction}00`.slice(0, 2));
  return negative ? -total : total;
}

// Same presentation rules as lib/format.ts (whole reais, one decimal in percentages).
const money = (value: string | number) =>
  new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency: "BRL",
    maximumFractionDigits: 0,
  }).format(Number(value));
const percent = (value: string | number | null) =>
  value === null
    ? "—"
    : new Intl.NumberFormat("pt-BR", {
        style: "percent",
        maximumFractionDigits: 1,
      }).format(Number(value));
const normalize = (text: string | null) =>
  (text ?? "").replace(/\s+/g, " ").trim();

const bridge: Array<{ label: string; key: keyof Summary; deduction: boolean }> =
  [
    { label: "Receita bruta", key: "gross_revenue", deduction: false },
    { label: "Descontos", key: "discount_value", deduction: true },
    { label: "Devoluções", key: "return_value", deduction: true },
    { label: "Receita líquida", key: "net_revenue", deduction: false },
    {
      label: "CMV das unidades retidas",
      key: "total_product_cost",
      deduction: true,
    },
    { label: "Frete real", key: "freight_allocated", deduction: true },
    {
      label: "Taxas, comissões e embalagem",
      key: "variable_cost_value",
      deduction: true,
    },
    {
      label: "Margem de contribuição",
      key: "contribution_margin",
      deduction: false,
    },
  ];

test.describe("paridade entre a vitrine e o snapshot ativo", () => {
  test("o snapshot fecha em centavos", () => {
    const c = (key: keyof Summary) => cents(String(summary[key]));
    expect(c("gross_revenue") - c("discount_value") - c("return_value")).toBe(
      c("net_revenue"),
    );
    expect(
      c("net_revenue") -
        c("total_product_cost") -
        c("freight_allocated") -
        c("variable_cost_value"),
    ).toBe(c("contribution_margin"));
    expect(
      channels.reduce((sum, ch) => sum + cents(ch.net_revenue), BigInt(0)),
    ).toBe(c("net_revenue"));
    expect(
      channels.reduce(
        (sum, ch) => sum + cents(ch.contribution_margin),
        BigInt(0),
      ),
    ).toBe(c("contribution_margin"));
  });

  test("ponte, KPIs e canais exibem os valores do snapshot", async ({
    page,
  }) => {
    await page.goto("/");

    const rows = page.locator(".waterfall-row");
    await expect(rows).toHaveCount(bridge.length);
    for (const [index, step] of bridge.entries()) {
      const row = rows.nth(index);
      expect(
        normalize(await row.locator(".waterfall-label").textContent()),
      ).toContain(step.label);
      expect(
        normalize(await row.locator(".waterfall-value strong").textContent()),
      ).toBe(
        normalize(`${step.deduction ? "−" : ""}${money(summary[step.key])}`),
      );
    }

    const kpis = page.getByRole("region", { name: "Indicadores executivos" });
    const expectedKpis: Array<[string, string]> = [
      ["Receita líquida", money(summary.net_revenue)],
      ["Margem de contribuição", percent(summary.margin_percentage)],
      ["Pedidos não cancelados", summary.orders.toLocaleString("pt-BR")],
      ["Ticket médio", money(summary.average_ticket)],
      ["Desconto ponderado", percent(summary.discount_percentage)],
    ];
    const tiles = kpis.locator(":scope > div");
    await expect(tiles).toHaveCount(expectedKpis.length);
    for (const [index, [label, value]] of expectedKpis.entries()) {
      expect(
        normalize(await tiles.nth(index).locator("span").textContent()),
      ).toBe(label);
      expect(
        normalize(await tiles.nth(index).locator("strong").textContent()),
      ).toBe(normalize(value));
    }

    const channelRows = page.locator(".channel-table tbody tr");
    await expect(channelRows).toHaveCount(channels.length);
    for (const channel of channels) {
      const row = channelRows.filter({
        has: page.getByRole("rowheader", {
          name: channel.channel_name,
          exact: true,
        }),
      });
      const cells = row.locator("td");
      expect(normalize(await cells.nth(0).textContent())).toBe(
        normalize(money(channel.contribution_margin)),
      );
      expect(normalize(await cells.nth(1).textContent())).toBe(
        normalize(percent(channel.margin_percentage)),
      );
    }
  });
});
