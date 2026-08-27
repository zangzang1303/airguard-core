/**
 * test-ai-browser-e2e.mjs — Rigorous Isolated Browser E2E Automation for AI-24.
 * Uses real Chromium via playwright-core, isolated proxy on 127.0.0.1:19338, and isolated preview on 127.0.0.1:5188.
 *
 * Implements:
 * 1. Strict transport failure (socket destroy) for network_failure mode.
 * 2. Independent DOM assertions on newly generated AI bubble (no reliance on user prompt keywords).
 * 3. Verified UX state: no duplicate user bubble on retry, error state removed/replaced on success.
 * 4. Full 7-record cumulative evidence logging saved directly into docs/evidence/session-3f/.
 */

import http from "node:http";
import path from "node:path";
import fs from "node:fs";
import { spawn, execSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright-core";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const FRONTEND_DIR = path.resolve(__dirname, "..");
const REPO_ROOT = path.resolve(__dirname, "..", "..");
const EVIDENCE_DIR = path.join(REPO_ROOT, "docs", "evidence", "session-3f");

// Ensure evidence directory exists inside the repo
if (!fs.existsSync(EVIDENCE_DIR)) {
  fs.mkdirSync(EVIDENCE_DIR, { recursive: true });
}

const PROXY_PORT = 19338;
const PROXY_HOST = "127.0.0.1";
const PROXY_URL = `http://${PROXY_HOST}:${PROXY_PORT}`;
const REAL_BACKEND = "http://127.0.0.1:8000";
const PREVIEW_URL = "http://127.0.0.1:5188";
const CHROME_PATH = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";

let currentMode = "structured_503";
const cumulativeRecords = [];
const ALLOWED_RECORD_HEADERS = [
  "content-type",
  "origin",
  "accept",
  "x-request-id",
  "x-fault-mode",
  "x-scenario-id",
  "user-agent",
];

function sanitizeRecordHeaders(headers) {
  const safe = {};
  for (const key of ALLOWED_RECORD_HEADERS) {
    if (headers[key]) {
      safe[key] = headers[key];
    }
  }
  return safe;
}

// Create Isolated Proxy Server
function createProxyServer() {
  return http.createServer((req, res) => {
    const origin = req.headers.origin || "http://127.0.0.1:5188";
    res.setHeader("Access-Control-Allow-Origin", origin);
    res.setHeader("Access-Control-Allow-Credentials", "true");
    res.setHeader("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS");
    res.setHeader("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Request-ID, X-Fault-Mode, X-Scenario-ID, X-CSRF-Token, Cache-Control");

    if (req.method === "OPTIONS") {
      res.writeHead(204);
      res.end();
      return;
    }

    if (req.url === "/api/set-fault-mode" && req.method === "POST") {
      let body = "";
      req.on("data", c => { body += c; });
      req.on("end", () => {
        try {
          const parsed = JSON.parse(body);
          currentMode = parsed.mode || currentMode;
          res.writeHead(200, { "Content-Type": "application/json" });
          res.end(JSON.stringify({ mode: currentMode, status: "updated" }));
        } catch (e) {
          res.writeHead(400, { "Content-Type": "application/json" });
          res.end(JSON.stringify({ error: e.message }));
        }
      });
      return;
    }

    if (req.url === "/api/v1/agent/chat" && req.method === "POST") {
      const reqId = req.headers["x-request-id"] || `e2e-req-${Date.now()}-${cumulativeRecords.length + 1}`;
      const mode = currentMode;
      const record = {
        ordinal: cumulativeRecords.length + 1,
        mode,
        reqId,
        url: req.url,
        timestamp: new Date().toISOString(),
        requestHeaders: sanitizeRecordHeaders(req.headers),
        outcome: null,
      };
      cumulativeRecords.push(record);
      console.log(`  [Proxy] Inbound /api/v1/agent/chat: ordinal=${record.ordinal}, mode=${mode}, reqId=${reqId}`);

      if (mode === "structured_503") {
        record.outcome = { status: 503, code: "agent_unavailable" };
        res.writeHead(503, {
          "Content-Type": "application/json",
          "X-Request-ID": reqId,
        });
        res.end(JSON.stringify({
          code: "agent_unavailable",
          message: "Dịch vụ AI Agent đang tạm thời gián đoạn",
          request_id: reqId,
          details: {},
        }));
        return;
      }

      if (mode === "timeout") {
        record.outcome = { status: "held_for_client_timeout", delay_ms: 15000 };
        // Hold connection past client 10s deadline
        const timer = setTimeout(() => {
          if (!res.destroyed && !res.writableEnded) {
            res.writeHead(504, { "Content-Type": "application/json", "X-Request-ID": reqId });
            res.end(JSON.stringify({ code: "agent_timeout", request_id: reqId }));
          }
        }, 15000);
        req.on("close", () => clearTimeout(timer));
        return;
      }

      if (mode === "network_failure") {
        record.outcome = { status: "socket_destroyed_transport_failure" };
        // Real transport layer failure: destroy socket before response headers
        req.socket.destroy();
        return;
      }

      // Pass Mode: Proxy to real backend :8000
      let body = "";
      req.on("data", (c) => { body += c; });
      req.on("end", () => {
        record.requestBody = body;
        const forwardHeaders = {
          ...req.headers,
          host: "127.0.0.1:8000",
          "X-Request-ID": reqId,
        };
        const pReq = http.request(
          `${REAL_BACKEND}/api/v1/agent/chat`,
          {
            method: "POST",
            headers: forwardHeaders,
          },
          (pRes) => {
            let pBody = "";
            pRes.on("data", (c) => { pBody += c; });
            pRes.on("end", () => {
              record.outcome = { status: pRes.statusCode, response_id: pRes.headers["x-request-id"] || reqId };
              res.writeHead(pRes.statusCode || 200, {
                ...pRes.headers,
                "access-control-allow-origin": origin,
                "access-control-allow-credentials": "true",
              });
              res.end(pBody);
            });
          }
        );
        pReq.on("error", (err) => {
          record.outcome = { status: 502, error: err.message };
          res.writeHead(502, { "Content-Type": "application/json" });
          res.end(JSON.stringify({ error: err.message }));
        });
        pReq.write(body);
        pReq.end();
      });
      return;
    }

    // Transparent Proxy for all other endpoints (auth, stations, measurements, etc.)
    const forwardReq = http.request(
      `${REAL_BACKEND}${req.url}`,
      {
        method: req.method,
        headers: {
          ...req.headers,
          host: "127.0.0.1:8000",
        },
      },
      (pRes) => {
        res.writeHead(pRes.statusCode || 200, {
          ...pRes.headers,
          "access-control-allow-origin": origin,
          "access-control-allow-credentials": "true",
        });
        pRes.pipe(res);
      }
    );
    forwardReq.on("error", (err) => {
      res.writeHead(502, { "Content-Type": "application/json" });
      res.end(JSON.stringify({ error: err.message }));
    });
    req.pipe(forwardReq);
  });
}

// Main test execution
async function run() {
  console.log("\n=======================================================");
  console.log("  AI Assistant Browser E2E Resilience & Recovery Suite  ");
  console.log("=======================================================\n");

  const server = createProxyServer();
  await new Promise((resolve) => server.listen(PROXY_PORT, PROXY_HOST, resolve));
  console.log(`[Setup] Isolated Proxy listening on http://${PROXY_HOST}:${PROXY_PORT}`);

  const results = {
    structured_503: false,
    recovery_503: false,
    timeout: false,
    recovery_timeout: false,
    network_failure: false,
    recovery_network: false,
  };

  const screenshots = [];
  let transportAttempts = 0;

  let browser = null;
  let previewChild = null;
  try {
    console.log(`[Setup] Building isolated test bundle for preview on ${PROXY_URL}...`);
    execSync("npx vite build", {
      cwd: FRONTEND_DIR,
      env: { ...process.env, VITE_API_BASE_URL: PROXY_URL },
      stdio: "inherit",
      shell: true,
    });

    console.log(`[Setup] Launching Chromium from ${CHROME_PATH}...`);
    // Auto-manage preview server if not already running
    async function isPreviewRunning() {
      try {
        await fetch(PREVIEW_URL);
        return true;
      } catch {
        return false;
      }
    }

    if (!(await isPreviewRunning())) {
      console.log(`[Setup] Starting Vite preview server on ${PREVIEW_URL}...`);
      previewChild = spawn("npx", ["vite", "preview", "--port", "5188", "--host", "127.0.0.1"], {
        cwd: FRONTEND_DIR,
        shell: true,
        stdio: "ignore",
      });

      // Poll until preview server is responsive
      for (let i = 0; i < 30; i++) {
        await new Promise((r) => setTimeout(r, 500));
        if (await isPreviewRunning()) break;
      }
    }

    browser = await chromium.launch({
      executablePath: CHROME_PATH,
      headless: true,
      args: ["--no-sandbox", "--disable-setuid-sandbox", "--disable-gpu"],
    });

    const context = await browser.newContext({
      viewport: { width: 1440, height: 900 },
      ignoreHTTPSErrors: true,
    });

    const page = await context.newPage();

    console.log(`[Setup] Navigating to ${PREVIEW_URL}...`);
    await page.goto(PREVIEW_URL, { waitUntil: "networkidle", timeout: 30000 });
    console.log(`[Setup] Page loaded. Title: "${await page.title()}"`);

    // Helper: Ensure we are in dashboard (login if currently on auth screen)
    async function ensureInDashboard() {
      const demoBtn = await page.$('button[aria-label="Dùng thử vai trò Cư dân"], button.demo-try-action-btn');
      if (demoBtn) {
        console.log("  [Auth] On login screen. Clicking demo Resident login button...");
        await demoBtn.click();
        await page.waitForSelector('button.ai-highlight-btn, button[aria-label="Hỏi Trợ lý AirGuard AI"]', { timeout: 20000 });
        console.log("  [Auth] Successfully logged into dashboard!");
      }
    }

    // Helper to open AI drawer if not already open
    async function ensureAiDrawerOpen() {
      await ensureInDashboard();
      const drawerInput = await page.$('[data-testid="ai-chat-input"]');
      if (!drawerInput) {
        console.log("  Opening AI Assistant drawer via button.ai-highlight-btn...");
        await page.waitForSelector('button.ai-highlight-btn, button[aria-label="Hỏi Trợ lý AirGuard AI"]', { timeout: 15000 });
        await page.click('button.ai-highlight-btn, button[aria-label="Hỏi Trợ lý AirGuard AI"]');
        await page.waitForSelector('[data-testid="ai-chat-input"]', { timeout: 15000 });
        console.log("  AI Assistant drawer opened successfully!");
      }
    }

    // Helper to save screenshot into docs/evidence/session-3f/
    async function takeScreenshot(name) {
      const filePath = path.join(EVIDENCE_DIR, `${name}.png`);
      await page.screenshot({ path: filePath, fullPage: false });
      screenshots.push({ name, path: filePath });
      console.log(`  [Screenshot] Saved: ${filePath}`);
    }

    // Helper to query chat bubble counts
    async function getBubbleMetrics() {
      return await page.evaluate(() => {
        const userBubbles = document.querySelectorAll('.chat-bubble-wrap.user');
        const errorAlerts = document.querySelectorAll('.chat-bubble-wrap.error, [data-testid="ai-error-message"]');
        const retryButtons = document.querySelectorAll('[data-testid="ai-retry-button"]');
        const aiSuccessBubbles = document.querySelectorAll('.chat-bubble-wrap.ai:not(.error):not(.typing)');
        const typingIndicator = document.querySelector('.chat-bubble-wrap.ai.typing');
        return {
          userCount: userBubbles.length,
          errorCount: errorAlerts.length,
          retryCount: retryButtons.length,
          aiSuccessCount: aiSuccessBubbles.length,
          isTyping: !!typingIndicator,
        };
      });
    }

    // -----------------------------------------------------------------
    // TEST 1: Structured 503 (agent_unavailable) & Pass-Through Recovery
    // -----------------------------------------------------------------
    console.log("\n--- [Test 1] Scenario: Structured 503 Fault Injection ---");
    currentMode = "structured_503";

    await ensureAiDrawerOpen();

    const m0 = await getBubbleMetrics();
    const recordsCountBefore1 = cumulativeRecords.length;

    const testPrompt1 = "Chất lượng không khí ở trạm S03 hôm nay thế nào?";
    console.log(`  Entering prompt: "${testPrompt1}"`);
    await page.fill('[data-testid="ai-chat-input"]', testPrompt1);
    await page.click('[data-testid="ai-send-button"]');

    // Wait for error bubble
    console.log("  Waiting for error alert in DOM...");
    await page.waitForSelector('[data-testid="ai-error-message"], [role="alert"]', { timeout: 10000 });

    const recordsCountAfter1 = cumulativeRecords.length;
    console.log(`  Outbound chat requests sent: ${recordsCountAfter1 - recordsCountBefore1} (Expected: exactly 1)`);

    const m1 = await getBubbleMetrics();
    console.log(`  Bubble counts: user=${m1.userCount}, error=${m1.errorCount}, retryBtn=${m1.retryCount}, aiSuccess=${m1.aiSuccessCount}`);

    const errorBubble1 = await page.$('[data-testid="ai-error-message"]');
    const errorText1 = errorBubble1 ? await errorBubble1.innerText() : "";
    console.log(`  Error bubble text: "${errorText1.trim().replace(/\n/g, ' ')}"`);

    const inputEnabled1 = await page.isEnabled('[data-testid="ai-chat-input"]');
    const pageContent1 = await page.content();
    const hasFakeFallback1 = pageContent1.includes("Agent đã xử lý yêu cầu.");

    if (
      m1.userCount === m0.userCount + 1 &&
      m1.errorCount === 1 &&
      m1.retryCount === 1 &&
      errorText1.includes("gián đoạn") &&
      inputEnabled1 &&
      !hasFakeFallback1 &&
      recordsCountAfter1 - recordsCountBefore1 === 1
    ) {
      results.structured_503 = true;
      console.log("  >>> PASS: Structured 503 assertions verified!");
    } else {
      console.error("  >>> FAIL: Structured 503 assertions failed!");
    }

    await takeScreenshot("screenshot_structured_503");

    // Recovery 1: Switch to Pass Mode and Click Retry
    console.log("\n--- [Test 1.b] Recovery: Switch to Pass Mode and Click Retry ---");
    currentMode = "pass";

    const preRetryMetrics1 = await getBubbleMetrics();
    const preRetryReqCount1 = cumulativeRecords.length;

    console.log(`  Pre-retry metrics: userCount=${preRetryMetrics1.userCount}, aiSuccessCount=${preRetryMetrics1.aiSuccessCount}`);
    const retryBtn1 = await page.$('[data-testid="ai-retry-button"]');
    await retryBtn1.click();
    console.log("  Clicked Retry button. Waiting for request dispatch and grounded response...");

    // Wait for new AI success bubble to appear
    await page.waitForFunction(
      (expectedSuccessCount) => {
        const aiSuccess = document.querySelectorAll('.chat-bubble-wrap.ai:not(.error):not(.typing)');
        return aiSuccess.length === expectedSuccessCount;
      },
      preRetryMetrics1.aiSuccessCount + 1,
      { timeout: 25000 }
    );

    // Wait for typing indicator to completely disappear
    await page.waitForFunction(() => !document.querySelector('.chat-bubble-wrap.ai.typing'), { timeout: 10000 });

    const postRetryMetrics1 = await getBubbleMetrics();
    const postRetryReqCount1 = cumulativeRecords.length;
    console.log(`  Post-retry metrics: userCount=${postRetryMetrics1.userCount}, errorCount=${postRetryMetrics1.errorCount}, retryBtn=${postRetryMetrics1.retryCount}, aiSuccessCount=${postRetryMetrics1.aiSuccessCount}`);
    console.log(`  Retry requests dispatched: ${postRetryReqCount1 - preRetryReqCount1} (Expected: exactly 1)`);

    // Extract text from the NEW AI bubble specifically
    const aiBubbles1 = await page.$$('.chat-bubble-wrap.ai:not(.error):not(.typing)');
    const latestAiBubble1 = aiBubbles1[aiBubbles1.length - 1];
    const newAiText1 = latestAiBubble1 ? await latestAiBubble1.innerText() : "";
    console.log(`  New AI Bubble text preview:\n"${newAiText1.substring(0, 150)}..."`);

    // Assertions for S03 grounding in NEW bubble text
    const lowerText1 = newAiText1.toLowerCase();
    const hasS03InNewBubble = newAiText1.includes("S03") || lowerText1.includes("ngọc trai");
    const hasProvenanceInNewBubble =
      lowerText1.includes("aqi") ||
      lowerText1.includes("pm2.5") ||
      lowerText1.includes("mô phỏng") ||
      lowerText1.includes("simulator") ||
      lowerText1.includes("thời gian thực") ||
      lowerText1.includes("tốt") ||
      lowerText1.includes("trung bình");
    const userCountUnchanged1 = postRetryMetrics1.userCount === preRetryMetrics1.userCount;
    const errorBubbleReplaced1 = postRetryMetrics1.errorCount === 0;

    console.log(`  Grounded assertions: S03=${hasS03InNewBubble}, metricProvenance=${hasProvenanceInNewBubble}, userCountUnchanged=${userCountUnchanged1}, errorCleared=${errorBubbleReplaced1}`);

    if (hasS03InNewBubble && hasProvenanceInNewBubble && userCountUnchanged1 && errorBubbleReplaced1 && (postRetryReqCount1 - preRetryReqCount1 === 1)) {
      results.recovery_503 = true;
      console.log("  >>> PASS: Recovery after 503 successfully verified (no duplicate user message, S03 grounded in new bubble, error replaced)!");
    } else {
      console.error("  >>> FAIL: Recovery after 503 assertions failed!");
    }

    await takeScreenshot("screenshot_recovery_503");

    // -----------------------------------------------------------------
    // TEST 2: Timeout Fault Injection & Recovery
    // -----------------------------------------------------------------
    console.log("\n--- [Test 2] Scenario: Timeout Fault Injection ---");
    currentMode = "timeout";

    const m2_before = await getBubbleMetrics();
    const recordsCountBefore2 = cumulativeRecords.length;

    const testPrompt2 = "Dự báo chất lượng không khí 1 giờ tới tại Ocean Park?";
    console.log(`  Entering prompt: "${testPrompt2}"`);
    await page.fill('[data-testid="ai-chat-input"]', testPrompt2);
    await page.click('[data-testid="ai-send-button"]');

    console.log("  Waiting for client timeout deadline (10s)...");
    await page.waitForTimeout(11000);

    const recordsCountAfter2 = cumulativeRecords.length;
    console.log(`  Outbound chat requests sent: ${recordsCountAfter2 - recordsCountBefore2} (Expected: exactly 1)`);

    const m2_after = await getBubbleMetrics();
    console.log(`  Bubble counts: user=${m2_after.userCount}, error=${m2_after.errorCount}, retryBtn=${m2_after.retryCount}, aiSuccess=${m2_after.aiSuccessCount}`);

    const errorBubble2 = await page.$('[data-testid="ai-error-message"]');
    const errorText2 = errorBubble2 ? await errorBubble2.innerText() : "";
    console.log(`  Error bubble text: "${errorText2.trim().replace(/\n/g, ' ')}"`);

    const inputEnabled2 = await page.isEnabled('[data-testid="ai-chat-input"]');

    if (
      m2_after.userCount === m2_before.userCount + 1 &&
      m2_after.errorCount === 1 &&
      m2_after.retryCount === 1 &&
      errorText2.includes("lỗi mạng") &&
      inputEnabled2 &&
      recordsCountAfter2 - recordsCountBefore2 === 1
    ) {
      results.timeout = true;
      console.log("  >>> PASS: Timeout assertions verified!");
    } else {
      console.error("  >>> FAIL: Timeout assertions failed!");
    }

    await takeScreenshot("screenshot_timeout");

    // Recovery 2: Switch to Pass Mode and Click Retry
    console.log("\n--- [Test 2.b] Recovery: Switch to Pass Mode and Click Retry ---");
    currentMode = "pass";

    const preRetryMetrics2 = await getBubbleMetrics();
    const preRetryReqCount2 = cumulativeRecords.length;

    const retryBtn2 = await page.$('[data-testid="ai-retry-button"]');
    await retryBtn2.click();
    console.log("  Clicked Retry button after timeout. Waiting for forecast response...");

    await page.waitForFunction(
      (expectedSuccessCount) => {
        const aiSuccess = document.querySelectorAll('.chat-bubble-wrap.ai:not(.error):not(.typing)');
        return aiSuccess.length === expectedSuccessCount;
      },
      preRetryMetrics2.aiSuccessCount + 1,
      { timeout: 25000 }
    );

    await page.waitForFunction(() => !document.querySelector('.chat-bubble-wrap.ai.typing'), { timeout: 10000 });

    const postRetryMetrics2 = await getBubbleMetrics();
    const postRetryReqCount2 = cumulativeRecords.length;

    const aiBubbles2 = await page.$$('.chat-bubble-wrap.ai:not(.error):not(.typing)');
    const latestAiBubble2 = aiBubbles2[aiBubbles2.length - 1];
    const newAiText2 = latestAiBubble2 ? await latestAiBubble2.innerText() : "";
    console.log(`  New Forecast AI Bubble text preview:\n"${newAiText2.substring(0, 150)}..."`);

    const lowerText2 = newAiText2.toLowerCase();
    const hasForecastGrounding =
      lowerText2.includes("1 giờ") ||
      lowerText2.includes("1h") ||
      lowerText2.includes("dự báo") ||
      lowerText2.includes("forecast") ||
      lowerText2.includes("baseline") ||
      lowerText2.includes("aqi") ||
      lowerText2.includes("pm2.5") ||
      lowerText2.includes("pm25") ||
      lowerText2.includes("simulator") ||
      lowerText2.includes("mô phỏng");
    const userCountUnchanged2 = postRetryMetrics2.userCount === preRetryMetrics2.userCount;
    const errorBubbleReplaced2 = postRetryMetrics2.errorCount === 0;

    console.log(`  Forecast assertions: forecastContent=${hasForecastGrounding}, userCountUnchanged=${userCountUnchanged2}, errorCleared=${errorBubbleReplaced2}`);

    if (hasForecastGrounding && userCountUnchanged2 && errorBubbleReplaced2 && (postRetryReqCount2 - preRetryReqCount2 === 1)) {
      results.recovery_timeout = true;
      console.log("  >>> PASS: Recovery after timeout verified (forecast rendered, no duplicate user message)!");
    } else {
      console.error("  >>> FAIL: Recovery after timeout assertions failed!");
    }

    await takeScreenshot("screenshot_recovery_timeout");

    // -----------------------------------------------------------------
    // TEST 3: Network Failure (Transport Destroyed) & Recovery
    // -----------------------------------------------------------------
    console.log("\n--- [Test 3] Scenario: Network Failure Fault Injection ---");
    currentMode = "network_failure";

    const m3_before = await getBubbleMetrics();
    const recordsCountBefore3 = cumulativeRecords.length;

    const testPrompt3 = "So sánh trạm S01 và S05 hiện tại";
    console.log(`  Entering prompt: "${testPrompt3}"`);
    await page.fill('[data-testid="ai-chat-input"]', testPrompt3);
    await page.click('[data-testid="ai-send-button"]');

    console.log("  Waiting for network error alert in DOM...");
    await page.waitForSelector('[data-testid="ai-error-message"], [role="alert"]', { timeout: 10000 });

    const recordsCountAfter3 = cumulativeRecords.length;
    transportAttempts = recordsCountAfter3 - recordsCountBefore3;
    console.log(`  Transport attempts observed: ${transportAttempts} (Expected: >= 1)`);

    const m3_after = await getBubbleMetrics();
    console.log(`  Bubble counts: user=${m3_after.userCount}, error=${m3_after.errorCount}, retryBtn=${m3_after.retryCount}, aiSuccess=${m3_after.aiSuccessCount}`);

    const errorBubble3 = await page.$('[data-testid="ai-error-message"]');
    const errorText3 = errorBubble3 ? await errorBubble3.innerText() : "";
    console.log(`  Error bubble text: "${errorText3.trim().replace(/\n/g, ' ')}"`);

    const inputEnabled3 = await page.isEnabled('[data-testid="ai-chat-input"]');

    if (
      m3_after.userCount === m3_before.userCount + 1 &&
      m3_after.errorCount === 1 &&
      m3_after.retryCount === 1 &&
      errorText3.includes("lỗi mạng") &&
      inputEnabled3 &&
      transportAttempts >= 1
    ) {
      results.network_failure = true;
      console.log("  >>> PASS: Network failure assertions verified (browser transport failure properly captured)!");
    } else {
      console.error("  >>> FAIL: Network failure assertions failed!");
    }

    await takeScreenshot("screenshot_network_failure");

    // Recovery 3: Switch to Pass Mode and Click Retry
    console.log("\n--- [Test 3.b] Recovery: Switch to Pass Mode and Click Retry ---");
    currentMode = "pass";

    const preRetryMetrics3 = await getBubbleMetrics();
    const preRetryReqCount3 = cumulativeRecords.length;

    const retryBtn3 = await page.$('[data-testid="ai-retry-button"]');
    await retryBtn3.click();
    console.log("  Clicked Retry button after network failure. Waiting for station comparison...");

    await page.waitForFunction(
      (expectedSuccessCount) => {
        const aiSuccess = document.querySelectorAll('.chat-bubble-wrap.ai:not(.error):not(.typing)');
        return aiSuccess.length === expectedSuccessCount;
      },
      preRetryMetrics3.aiSuccessCount + 1,
      { timeout: 25000 }
    );

    await page.waitForFunction(() => !document.querySelector('.chat-bubble-wrap.ai.typing'), { timeout: 10000 });

    const postRetryMetrics3 = await getBubbleMetrics();
    const postRetryReqCount3 = cumulativeRecords.length;

    const aiBubbles3 = await page.$$('.chat-bubble-wrap.ai:not(.error):not(.typing)');
    const latestAiBubble3 = aiBubbles3[aiBubbles3.length - 1];
    const newAiText3 = latestAiBubble3 ? await latestAiBubble3.innerText() : "";
    console.log(`  New Comparison AI Bubble text preview:\n"${newAiText3.substring(0, 150)}..."`);

    // Assert that the NEW AI bubble text contains both S01 and S05
    const hasS01InNew = newAiText3.includes("S01") || newAiText3.includes("Đa Tốn");
    const hasS05InNew = newAiText3.includes("S05") || newAiText3.includes("Hải Âu");
    const userCountUnchanged3 = postRetryMetrics3.userCount === preRetryMetrics3.userCount;
    const errorBubbleReplaced3 = postRetryMetrics3.errorCount === 0;

    console.log(`  Comparison assertions: S01=${hasS01InNew}, S05=${hasS05InNew}, userCountUnchanged=${userCountUnchanged3}, errorCleared=${errorBubbleReplaced3}`);

    if (hasS01InNew && hasS05InNew && userCountUnchanged3 && errorBubbleReplaced3 && (postRetryReqCount3 - preRetryReqCount3 === 1)) {
      results.recovery_network = true;
      console.log("  >>> PASS: Recovery after network failure verified (S01 and S05 comparison rendered in new bubble)!");
    } else {
      console.error("  >>> FAIL: Recovery after network failure assertions failed!");
    }

    await takeScreenshot("screenshot_recovery_network");

    // Write Full Cumulative Evidence JSON
    const evidenceReport = {
      test_suite: "AI Assistant Browser E2E Resilience & Recovery Suite",
      timestamp: new Date().toISOString(),
      results,
      all_passed: Object.values(results).every(v => v === true),
      transportAttempts,
      cumulative_proxy_records: cumulativeRecords,
      total_proxy_requests: cumulativeRecords.length,
      screenshots,
    };

    const evidenceFilePath = path.join(EVIDENCE_DIR, "browser_e2e_evidence.json");
    fs.writeFileSync(evidenceFilePath, JSON.stringify(evidenceReport, null, 2), "utf-8");
    console.log(`\n[Evidence] Saved full report to ${evidenceFilePath}`);

  } finally {
    if (browser) {
      await browser.close();
      console.log("[Teardown] Browser closed.");
    }
    if (previewChild) {
      previewChild.kill();
      console.log("[Teardown] Vite preview server closed.");
    }
    await new Promise((resolve) => server.close(resolve));
    console.log("[Teardown] Isolated Proxy server closed.");
  }

  console.log("\n=======================================================");
  console.log("  E2E Test Results Summary                              ");
  console.log("=======================================================");
  console.log(JSON.stringify(results, null, 2));

  const allPassed = Object.values(results).every(v => v === true);
  if (!allPassed) {
    console.error("\n✗ SOME BROWSER E2E TESTS FAILED!\n");
    process.exit(1);
  } else {
    console.log("\n✓ ALL BROWSER E2E TESTS PASSED (6/6)!\n");
    process.exit(0);
  }
}

run().catch((err) => {
  console.error("Fatal test runner error:", err);
  process.exit(1);
});
