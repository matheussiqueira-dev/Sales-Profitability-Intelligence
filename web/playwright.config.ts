import { defineConfig } from "@playwright/test";
// Dedicated port: reuseExistingServer must never attach to another local app on 3000.
const port = 3107;
// Unset in CI (Playwright's Chromium); locally, PLAYWRIGHT_CHANNEL picks an installed browser.
const channel = process.env.PLAYWRIGHT_CHANNEL || undefined;
export default defineConfig({
  testDir: "./tests",
  timeout: 30000,
  use: {
    baseURL: process.env.PLAYWRIGHT_BASE_URL || `http://127.0.0.1:${port}`,
    headless: true,
    channel,
  },
  projects: [
    { name: "desktop", use: { viewport: { width: 1440, height: 1000 } } },
    { name: "mobile", use: { viewport: { width: 390, height: 844 } } },
  ],
  webServer: process.env.PLAYWRIGHT_BASE_URL
    ? undefined
    : {
        command: `npm run start -- --port ${port}`,
        url: `http://127.0.0.1:${port}`,
        reuseExistingServer: !process.env.CI,
      },
});
