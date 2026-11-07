import { expect, test } from "@playwright/test";

test("ingests documents and renders a grounded answer with real API citations", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: /Search beyond/i })).toBeVisible();

  await page.getByRole("button", { name: "ADMIN CONSOLE" }).click();
  await page.getByPlaceholder("SEEKORA_ADMIN_API_KEY").fill("seekora-e2e-key");
  await page.getByRole("button", { name: /INGEST DEMO CORPUS/ }).click();
  await expect(page.getByText("Demo corpus is indexed and ready to query.")).toBeVisible();
  await expect(page.getByText("3", { exact: true }).first()).toBeVisible();
  await page.getByRole("button", { name: "Close admin console" }).click();

  await page.getByLabel("Search query").fill("How does Seekora keep RAG answers traceable?");
  await page.getByRole("button", { name: "ASK↗", exact: true }).click();

  await expect(page.getByText("GROUNDED", { exact: true })).toBeVisible();
  await expect(page.getByRole("complementary", { name: "Citations" })).toContainText(
    "Traceable citations in RAG",
  );
  await expect(page.getByText(/\[1\]/).first()).toBeVisible();
  await page.screenshot({ path: "../artifacts/screenshots/seekora-answer.png", fullPage: true });
});
