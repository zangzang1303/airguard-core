import assert from "node:assert/strict";
import { existsSync } from "node:fs";
import { spawnSync } from "node:child_process";
import { chromium } from "playwright-core";

const python = process.env.AIRGUARD_PYTHON || (process.platform === "win32" ? "python.exe" : "python3");
const chromeCandidates = [
  process.env.CHROME_PATH,
  "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
  "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
].filter(Boolean);
const executablePath = chromeCandidates.find((candidate) => existsSync(candidate));
assert.ok(executablePath, "Chrome or Edge is required for email snapshot layout tests");

const renderScript = String.raw`
import json
from backend.app.services.predictive_warning_email import render_predictive_warning_email

episode = {
    "episode_id": "4c40af7b-3088-4aed-b2c2-f989a7dffac7",
    "station_id": "S01",
    "severity": "warning",
    "predicted_min": 55.25,
    "predicted_max": 72.5,
    "confidence": 0.8,
    "forecast_target_at": "2026-08-29T11:00:00+07:00",
    "model_version": "damped_linear_trend_v1",
    "policy_version": "predictive-warning-policy-v1",
    "source": "simulator_history_damped_linear_v1",
}
print(json.dumps(render_predictive_warning_email(episode, frontend_url="http://localhost:5173")))
`;
const rendered = spawnSync(python, ["-c", renderScript], {
  cwd: new URL("../../", import.meta.url),
  encoding: "utf8",
  env: process.env,
});
let rendererResult = rendered;
const hostRuntimeUnavailable =
  rendererResult.status === null ||
  (rendererResult.status !== 0 && /No Python at|No module named ['"]psycopg2['"]/.test(rendererResult.stderr || ""));
if (hostRuntimeUnavailable) {
  const localDocker = process.env.LOCALAPPDATA
    ? `${process.env.LOCALAPPDATA}\\Programs\\DockerDesktop\\resources\\bin\\docker.exe`
    : null;
  const dockerCandidates = [
    process.env.AIRGUARD_DOCKER,
    localDocker,
    process.platform === "win32" ? "docker.exe" : "docker",
  ].filter(Boolean);
  const docker = dockerCandidates.find((candidate) => candidate === "docker" || candidate === "docker.exe" || existsSync(candidate));
  assert.ok(docker, "Python is unavailable and Docker CLI could not be located");
  rendererResult = spawnSync(
    docker,
    [
      "exec",
      "-i",
      process.env.AIRGUARD_PYTHON_CONTAINER || "airguard-agent",
      "python",
      "-c",
      renderScript,
    ],
    {
      cwd: new URL("../../", import.meta.url),
      encoding: "utf8",
      env: process.env,
    },
  );
}
assert.equal(rendererResult.status, 0, rendererResult.stderr || "backend email renderer failed");
const email = JSON.parse(rendererResult.stdout);

const browser = await chromium.launch({ executablePath, headless: true });
try {
  for (const viewport of [
    { width: 375, height: 812 },
    { width: 1280, height: 900 },
  ]) {
    const page = await browser.newPage({ viewport });
    await page.setContent(email.html, { waitUntil: "load" });
    const layout = await page.evaluate(() => {
      const button = document.querySelector(".button");
      const rect = button?.getBoundingClientRect();
      return {
        scrollWidth: document.documentElement.scrollWidth,
        buttonVisible: Boolean(rect && rect.width > 0 && rect.height > 0),
        buttonWithinViewport: Boolean(rect && rect.left >= 0 && rect.right <= window.innerWidth),
      };
    });
    assert.ok(layout.scrollWidth <= viewport.width, `horizontal overflow at ${viewport.width}px`);
    assert.ok(layout.buttonVisible, `CTA hidden at ${viewport.width}px`);
    assert.ok(layout.buttonWithinViewport, `CTA clipped at ${viewport.width}px`);
    const screenshot = await page.screenshot({ fullPage: true, type: "png" });
    assert.ok(screenshot.byteLength > 1000, `empty screenshot at ${viewport.width}px`);
    await page.close();
  }
} finally {
  await browser.close();
}

console.log("predictive warning email snapshots 375/1280: PASS");
