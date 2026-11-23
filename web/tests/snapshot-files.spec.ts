import { expect, test } from "@playwright/test";
import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { join } from "node:path";

// Expectations come from the manifest, so publishing a new snapshot needs no test edit.
const manifest = JSON.parse(
  readFileSync(
    join(__dirname, "..", "public", "data", "manifest.json"),
    "utf8",
  ),
) as { snapshot: string; sha256: Record<string, string> };

test("metodologia publica os arquivos do snapshot ativo com SHA-256 conferível", async ({
  page,
  request,
}) => {
  await page.goto("/methodology");
  const list = page.getByRole("list", { name: "Arquivos do snapshot ativo" });
  await expect(list.getByRole("listitem")).toHaveCount(
    Object.keys(manifest.sha256).length,
  );
  for (const [name, expected] of Object.entries(manifest.sha256)) {
    const link = list.getByRole("link", { name: `${name}.json`, exact: true });
    await expect(link).toHaveAttribute(
      "href",
      `/data/snapshots/${manifest.snapshot}/${name}.json`,
    );
    await expect(list.locator(`code[data-file="${name}"]`)).toHaveText(
      expected,
    );
    const response = await request.get(
      (await link.getAttribute("href")) as string,
    );
    expect(response.status()).toBe(200);
    const digest = createHash("sha256")
      .update(await response.body())
      .digest("hex");
    expect(digest).toBe(expected);
  }
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
});
