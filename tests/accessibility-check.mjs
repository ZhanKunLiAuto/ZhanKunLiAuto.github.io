import AxeBuilder from "@axe-core/playwright";
import { chromium } from "playwright";

const pages = ["/", "/about/", "/blog/", "/projects/", "/publications/", "/cv/"];
const baseUrl = process.env.ACCESSIBILITY_BASE_URL || "http://127.0.0.1:8080";

let hasViolations = false;
const browser = await chromium.launch();
const context = await browser.newContext();

try {
  const page = await context.newPage();

  for (const path of pages) {
    const url = new URL(path, baseUrl).toString();
    const response = await page.goto(url, { waitUntil: "networkidle" });

    if (!response || !response.ok()) {
      console.error(`Failed to load ${url}: ${response ? response.status() : "no response"}`);
      hasViolations = true;
      continue;
    }

    const results = await new AxeBuilder({ page }).analyze();

    if (results.violations.length === 0) {
      console.log(`PASS ${path}`);
      continue;
    }

    hasViolations = true;
    console.error(`FAIL ${path}`);

    for (const violation of results.violations) {
      console.error(`- ${violation.id}: ${violation.help}`);
      for (const node of violation.nodes) {
        console.error(`  ${node.target.join(", ")}`);
      }
    }
  }
} finally {
  await context.close();
  await browser.close();
}

if (hasViolations) {
  process.exit(1);
}
