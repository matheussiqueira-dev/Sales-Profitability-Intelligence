import "server-only";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { createHash } from "node:crypto";

/** Monetary/ratio values travel as decimal strings to preserve exact cents. */
type Decimal = string;

export type Summary = {
  gross_revenue: Decimal;
  discount_value: Decimal;
  return_value: Decimal;
  net_revenue: Decimal;
  total_product_cost: Decimal;
  freight_allocated: Decimal;
  variable_cost_value: Decimal;
  contribution_margin: Decimal;
  margin_percentage: Decimal | null;
  orders: number;
  customers: number;
  average_ticket: Decimal | null;
  discount_percentage: Decimal | null;
  return_rate: Decimal | null;
};
export type Month = {
  month: string;
  net_revenue: Decimal;
  contribution_margin: Decimal;
  margin_percentage: Decimal | null;
  variable_cost_value: Decimal;
};
export type Channel = {
  channel_name: string;
  net_revenue: Decimal;
  contribution_margin: Decimal;
  margin_percentage: Decimal | null;
  variable_cost_value: Decimal;
};
export type Product = {
  product_name: string;
  category: string;
  net_revenue: Decimal;
  contribution_margin: Decimal;
  margin_percentage: Decimal | null;
  quantity: number;
  variable_cost_value: Decimal;
  return_rate: Decimal | null;
};
export type Segment = {
  segment: string;
  customers: number;
  net_revenue: Decimal;
  contribution_margin: Decimal;
};
export type Manifest = {
  snapshot: string;
  contract_version: number;
  synthetic: boolean;
  reconciled: boolean;
  completed_at: string;
  sha256: Record<string, string>;
  period: { from: string; through_month: string };
};

type Kind = "decimal" | "decimal?" | "integer" | "text" | "date";
type Shape = Record<string, Kind>;

const DECIMAL = /^-?\d+(\.\d+)?$/;
const DATE = /^\d{4}-\d{2}-\d{2}$/;

function valid(value: unknown, kind: Kind): boolean {
  switch (kind) {
    case "decimal":
      return typeof value === "string" && DECIMAL.test(value);
    case "decimal?":
      return value === null || valid(value, "decimal");
    case "integer":
      return Number.isSafeInteger(value) && (value as number) >= 0;
    case "text":
      return typeof value === "string" && value.trim().length > 0;
    case "date":
      return typeof value === "string" && DATE.test(value);
  }
}

/** Fails the build when an exported snapshot drifts from the contract consumed here. */
function assertShape<T>(name: string, value: unknown, shape: Shape): T {
  if (typeof value !== "object" || value === null || Array.isArray(value))
    throw new Error(`Snapshot ${name}: registro inválido`);
  for (const [field, kind] of Object.entries(shape)) {
    if (!valid((value as Record<string, unknown>)[field], kind))
      throw new Error(`Snapshot ${name}: campo ${field} inválido`);
  }
  return value as T;
}

function assertRows<T>(name: string, value: unknown, shape: Shape): T[] {
  if (!Array.isArray(value) || value.length === 0)
    throw new Error(`Snapshot ${name}: lista vazia ou inválida`);
  return value.map((row) => assertShape<T>(name, row, shape));
}

const SUMMARY: Shape = {
  gross_revenue: "decimal",
  discount_value: "decimal",
  return_value: "decimal",
  net_revenue: "decimal",
  total_product_cost: "decimal",
  freight_allocated: "decimal",
  variable_cost_value: "decimal",
  contribution_margin: "decimal",
  margin_percentage: "decimal?",
  orders: "integer",
  customers: "integer",
  average_ticket: "decimal?",
  discount_percentage: "decimal?",
  return_rate: "decimal?",
};
const MONTH: Shape = {
  month: "date",
  net_revenue: "decimal",
  contribution_margin: "decimal",
  margin_percentage: "decimal?",
  variable_cost_value: "decimal",
};
const CHANNEL: Shape = {
  channel_name: "text",
  net_revenue: "decimal",
  contribution_margin: "decimal",
  margin_percentage: "decimal?",
  variable_cost_value: "decimal",
};
const PRODUCT: Shape = {
  product_name: "text",
  category: "text",
  net_revenue: "decimal",
  contribution_margin: "decimal",
  margin_percentage: "decimal?",
  quantity: "integer",
  variable_cost_value: "decimal",
  return_rate: "decimal?",
};
const SEGMENT: Shape = {
  segment: "text",
  customers: "integer",
  net_revenue: "decimal",
  contribution_margin: "decimal",
};

function readManifest(root: string): Manifest {
  const manifest = JSON.parse(
    readFileSync(join(root, "manifest.json"), "utf8"),
  ) as Partial<Manifest>;
  if (
    manifest.contract_version !== 2 ||
    manifest.synthetic !== true ||
    manifest.reconciled !== true ||
    typeof manifest.snapshot !== "string" ||
    !/^[a-f0-9]{16}$/.test(manifest.snapshot) ||
    typeof manifest.completed_at !== "string" ||
    Number.isNaN(Date.parse(manifest.completed_at)) ||
    typeof manifest.sha256 !== "object" ||
    manifest.sha256 === null ||
    !valid(manifest.period?.from, "date") ||
    !valid(manifest.period?.through_month, "date")
  )
    throw new Error("Snapshot inválido ou não conciliado");
  return manifest as Manifest;
}

export function loadAnalytics() {
  const root = join(process.cwd(), "public/data");
  const manifest = readManifest(root);
  function load(name: string): unknown {
    const expected = manifest.sha256[name];
    if (typeof expected !== "string" || !/^[a-f0-9]{64}$/.test(expected))
      throw new Error(`Snapshot sem hash: ${name}`);
    const content = readFileSync(
      join(root, "snapshots", manifest.snapshot, `${name}.json`),
      "utf8",
    );
    if (createHash("sha256").update(content).digest("hex") !== expected)
      throw new Error(`Snapshot inconsistente: ${name}`);
    return JSON.parse(content);
  }
  return {
    manifest,
    summary: assertShape<Summary>(
      "executive-summary",
      load("executive-summary"),
      SUMMARY,
    ),
    months: assertRows<Month>(
      "monthly-profitability",
      load("monthly-profitability"),
      MONTH,
    ),
    channels: assertRows<Channel>("channels", load("channels"), CHANNEL),
    products: assertRows<Product>("products", load("products"), PRODUCT),
    segments: assertRows<Segment>(
      "customer-segments",
      load("customer-segments"),
      SEGMENT,
    ),
  };
}
