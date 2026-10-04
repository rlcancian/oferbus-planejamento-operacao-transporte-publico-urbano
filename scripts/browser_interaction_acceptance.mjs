import { chromium } from "playwright";

const baseUrl = process.env.OFERBUS_WEB_URL ?? "http://127.0.0.1:3010";
const browser = await chromium.launch({ headless: true });
try {
  const page = await browser.newPage();
  await page.goto(baseUrl, { waitUntil: "networkidle" });
  const row = page.locator("#quadro tbody tr").first();
  await row.waitFor({ state: "visible" });
  const sequenceText = (await row.locator("td").first().innerText()).trim();
  const sequence = Number.parseInt(sequenceText, 10);
  if (!Number.isInteger(sequence)) throw new Error("invalid first trip sequence: " + sequenceText);
  const marchTrip = page.locator("#marcha g[role=button]").filter({ hasText: String(sequence) }).first();
  const blockTrip = page.getByRole("button", { name: new RegExp("^Selecionar viagem " + sequence + " ") }).first();
  await marchTrip.waitFor({ state: "visible" });
  await blockTrip.waitFor({ state: "visible" });
  await row.focus();
  await page.keyboard.press("Enter");
  if (await row.getAttribute("aria-selected") !== "true") throw new Error("timetable keyboard selection did not activate");
  if (await marchTrip.getAttribute("aria-pressed") !== "true") throw new Error("March cross-selection did not activate");
  if (await blockTrip.getAttribute("aria-pressed") !== "true") throw new Error("vehicle-block cross-selection did not activate");
  await blockTrip.focus();
  await page.keyboard.press("Space");
  if (await row.getAttribute("aria-selected") !== "false") throw new Error("timetable selection did not clear from block keyboard toggle");
  if (await marchTrip.getAttribute("aria-pressed") !== "false") throw new Error("March selection did not clear from block keyboard toggle");
  if (await blockTrip.getAttribute("aria-pressed") !== "false") throw new Error("block selection did not clear");
  await marchTrip.focus();
  await page.keyboard.press("Enter");
  if (await row.getAttribute("aria-selected") !== "true" || await blockTrip.getAttribute("aria-pressed") !== "true") throw new Error("March keyboard selection did not propagate across workspace");
  console.log(JSON.stringify({ status: "PASS", sequence, checks: ["timetable-keyboard", "march-cross-selection", "block-cross-selection", "toggle-clear", "march-keyboard"] }));
} finally {
  await browser.close();
}
