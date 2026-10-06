import "server-only";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { createHash } from "node:crypto";

export type Summary = {
  gross_revenue: string;
  discount_value: string;
  return_value: string;
  net_revenue: string;
  total_product_cost: string;
  freight_allocated: string;
  variable_cost_value: string;
  contribution_margin: string;
  margin_percentage: string;
  orders: number;
  customers: number;
  average_ticket: string;
  discount_percentage: string;
  return_rate: string;
};
export type Month = {
  month: string;
  net_revenue: string;
  contribution_margin: string;
  margin_percentage: string;
  variable_cost_value: string;
};
export type Channel = {
  channel_name: string;
  net_revenue: string;
  contribution_margin: string;
  margin_percentage: string;
  variable_cost_value: string;
};
export type Product = {
  product_name: string;
  category: string;
  net_revenue: string;
  contribution_margin: string;
  margin_percentage: string | null;
  quantity: number;
  variable_cost_value: string;
  return_rate: string;
};
export type Segment = {
  segment: string;
  customers: number;
  net_revenue: string;
  contribution_margin: string;
};
export function loadAnalytics() {
  const root = join(process.cwd(), "public/data");
  const manifest = JSON.parse(
    readFileSync(join(root, "manifest.json"), "utf8"),
  ) as {
    snapshot: string;
    contract_version: number;
    synthetic: boolean;
    reconciled: boolean;
    completed_at: string;
    sha256: Record<string, string>;
  };
  if (
    manifest.contract_version !== 2 ||
    !manifest.synthetic ||
    !manifest.reconciled ||
    !/^[a-f0-9]{16}$/.test(manifest.snapshot)
  )
    throw new Error("Snapshot inválido ou não conciliado");
  function load<T>(name: string): T {
    const content = readFileSync(
      join(root, "snapshots", manifest.snapshot, `${name}.json`),
      "utf8",
    );
    if (
      createHash("sha256").update(content).digest("hex") !==
      manifest.sha256[name]
    )
      throw new Error(`Snapshot inconsistente: ${name}`);
    return JSON.parse(content) as T;
  }
  return {
    manifest,
    summary: load<Summary>("executive-summary"),
    months: load<Month[]>("monthly-profitability"),
    channels: load<Channel[]>("channels"),
    products: load<Product[]>("products"),
    segments: load<Segment[]>("customer-segments"),
  };
}
