import { expect, test } from "@playwright/test";
import { mkdirSync, readFileSync } from "node:fs";
import { join } from "node:path";

// The headline margin comes from the active snapshot, never from a literal in the test.
const dataDir = join(__dirname, "..", "public", "data");
const { snapshot } = JSON.parse(
  readFileSync(join(dataDir, "manifest.json"), "utf8"),
) as { snapshot: string };
const { margin_percentage: marginPercentage } = JSON.parse(
  readFileSync(
    join(dataDir, "snapshots", snapshot, "executive-summary.json"),
    "utf8",
  ),
) as { margin_percentage: string };
const marginText = new Intl.NumberFormat("pt-BR", {
  style: "percent",
  maximumFractionDigits: 1,
}).format(Number(marginPercentage));
test("dados conciliados, filtros e navegação sem overflow", async ({
  page,
}, testInfo) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  const response = await page.goto("/");
  expect(response?.headers()["x-content-type-options"]).toBe("nosniff");
  expect(response?.headers()["x-frame-options"]).toBe("DENY");
  expect(response?.headers()["content-security-policy"]).toContain(
    "frame-ancestors 'none'",
  );
  await expect(
    page.getByRole("heading", { name: "Vender mais. Contribuir quanto?" }),
  ).toBeVisible();
  await expect(
    page.getByText("Conciliação em centavos aprovada"),
  ).toBeVisible();
  await expect(page.getByText(marginText, { exact: true })).toBeVisible();
  await page
    .getByLabel("Categoria", { exact: true })
    .selectOption("Acessórios");
  await page.getByText(/Consultar os .* produtos em tabela/).click();
  await expect(
    page.getByRole("region", { name: "Rentabilidade dos produtos" }),
  ).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
  expect(errors).toEqual([]);
  await page.getByLabel("Categoria", { exact: true }).selectOption("Todas");
  await page.getByText(/Consultar os .* produtos em tabela/).click();
  await page.evaluate(() => window.scrollTo(0, 0));
  mkdirSync("../artifacts/web", { recursive: true });
  await page.screenshot({
    path: `../artifacts/web/${testInfo.project.name}.png`,
    fullPage: true,
  });
  await page.getByRole("link", { name: "Metodologia", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Como a rentabilidade é calculada" }),
  ).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
});
