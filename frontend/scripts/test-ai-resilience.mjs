/**
 * test-ai-resilience.mjs — AI-24 fault injection contract regression gate
 *
 * Requirements:
 *   - Clean Node.js built-ins only.
 *   - Directly imports production formatAgentRequestError and extractAgentReply from src/api/agentResponseHelper.js.
 *   - Directly imports resolveApiBaseUrl from src/api/apiBaseUrl.js.
 *   - Pass mode proxies live requests to backend at 127.0.0.1:8000 (real grounded data).
 *   - Proper socket and timer cleanup; exits naturally with code 0 without forced process.exit().
 *   - Strict fail-closed verification.
 */

import assert from "node:assert/strict";
import http from "node:http";
import { resolveApiBaseUrl } from "../src/api/apiBaseUrl.js";
import { formatAgentRequestError, extractAgentReply } from "../src/api/agentResponseHelper.js";

const SESSION_ID = "3f-" + Date.now();
const HARNESS_PORT = 19337;
const HARNESS_HOST = "127.0.0.1";
const HARNESS_BASE = `http://${HARNESS_HOST}:${HARNESS_PORT}`;
const REAL_BACKEND_BASE = "http://127.0.0.1:8000";
const CLIENT_TIMEOUT_MS = 10_000;

// Fixture log
const fixtureLog = [];
function fixtureRecord(scenario, marker, detail) {
  const entry = { scenario, marker, detail, ts: new Date().toISOString() };
  fixtureLog.push(entry);
  console.log(`  [fixture] ${scenario} | ${marker} | ${detail}`);
}

// PASS / FAIL counter
let passed = 0;
let failed = 0;
function ok(name) {
  passed++;
  console.log(`  PASS: ${name}`);
}
function fail(name, err) {
  failed++;
  console.error(`  FAIL: ${name}: ${err?.message ?? err}`);
}

// -----------------------------------------------------------------
// Section 1 — Production Error Formatter Logic (imported directly)
// -----------------------------------------------------------------
console.log("\n[Section 1] Production Error Formatter (formatAgentRequestError)");

try {
  const msg503 = formatAgentRequestError({ status: 503 });
  assert.ok(msg503.includes("gián đoạn"), "503 message must mention 'gián đoạn'");
  ok("formatAgentRequestError: 503 -> gián đoạn message");
} catch (e) { fail("formatAgentRequestError: 503", e); }

try {
  const msg502 = formatAgentRequestError({ status: 502 });
  assert.ok(msg502.includes("gián đoạn"), "502 message must mention 'gián đoạn'");
  ok("formatAgentRequestError: 502 -> gián đoạn message");
} catch (e) { fail("formatAgentRequestError: 502", e); }

try {
  const msg504 = formatAgentRequestError({ status: 504 });
  assert.ok(msg504.includes("gián đoạn"), "504 message must mention 'gián đoạn'");
  ok("formatAgentRequestError: 504 -> gián đoạn message");
} catch (e) { fail("formatAgentRequestError: 504", e); }

try {
  const msg422 = formatAgentRequestError({ status: 422 });
  assert.ok(msg422.includes("chưa hợp lệ"), "422 message must mention 'chưa hợp lệ'");
  ok("formatAgentRequestError: 422 -> validation message");
} catch (e) { fail("formatAgentRequestError: 422", e); }

try {
  const msgNetwork = formatAgentRequestError({ name: "AbortError" });
  assert.ok(msgNetwork.includes("lỗi mạng") || msgNetwork.includes("kết nối"), "network error message");
  ok("formatAgentRequestError: network/abort -> lỗi mạng message");
} catch (e) { fail("formatAgentRequestError: network/abort", e); }

try {
  const msgMalformed = formatAgentRequestError({ status: 200, code: "agent_malformed_success" });
  assert.ok(msgMalformed.includes("định dạng"), "malformed-success must mention 'định dạng'");
  assert.ok(!msgMalformed.includes("Agent đã xử lý"), "must not contain legacy success fallback");
  ok("formatAgentRequestError: agent_malformed_success -> định dạng message (no fake fallback)");
} catch (e) { fail("formatAgentRequestError: agent_malformed_success", e); }

// -----------------------------------------------------------------
// Section 2 — Production Fail-Closed Parser (extractAgentReply)
// -----------------------------------------------------------------
console.log("\n[Section 2] Production Fail-Closed Parser (extractAgentReply)");

try {
  assert.throws(
    () => extractAgentReply({ request_id: "test-rid-1", extra_field: "ignored" }),
    (err) => err.code === "agent_malformed_success" && err.status === 200,
    "Should throw agent_malformed_success on empty payload",
  );
  ok("extractAgentReply: empty body -> throws agent_malformed_success (fail-closed)");
} catch (e) { fail("extractAgentReply: empty body", e); }

try {
  assert.throws(
    () => extractAgentReply({ answer: {}, request_id: "test-rid-2" }),
    (err) => err.code === "agent_malformed_success" && err.status === 200,
    "Should throw agent_malformed_success when answer is empty object",
  );
  ok("extractAgentReply: answer={} -> throws agent_malformed_success (fail-closed)");
} catch (e) { fail("extractAgentReply: answer={}", e); }

try {
  assert.throws(
    () => extractAgentReply(null),
    (err) => err.code === "agent_malformed_success" && err.status === 200,
  );
  ok("extractAgentReply: null body -> throws agent_malformed_success (fail-closed)");
} catch (e) { fail("extractAgentReply: null body", e); }

try {
  const result = extractAgentReply({ response: "AQI tại trạm S03 là 85 — Tốt.", request_id: "valid-rid" });
  assert.equal(result.reply, "AQI tại trạm S03 là 85 — Tốt.");
  assert.ok(!result.reply.includes("Agent đã xử lý yêu cầu"), "No fake fallback phrase");
  ok("extractAgentReply: valid response string -> extracts reply cleanly");
} catch (e) { fail("extractAgentReply: valid response string", e); }

try {
  const result = extractAgentReply({
    answer: { summary: "AQI S03: 85 (Tốt)", details: "Khuyến nghị hoạt động ngoài trời bình thường." },
    request_id: "valid-rid-2",
  });
  assert.ok(result.reply.includes("AQI S03: 85"), "Summary is in reply");
  assert.ok(result.reply.includes("Khuyến nghị"), "Details are in reply");
  ok("extractAgentReply: valid answer object -> combines summary and details");
} catch (e) { fail("extractAgentReply: valid answer object", e); }

// -----------------------------------------------------------------
// Section 3 — Base URL Host-Alignment Regression
// -----------------------------------------------------------------
console.log("\n[Section 3] Base URL Alignment (resolveApiBaseUrl)");

try {
  assert.equal(
    resolveApiBaseUrl({ hostname: "localhost", configuredBaseUrl: "http://127.0.0.1:8000" }),
    "http://localhost:8000",
  );
  ok("resolveApiBaseUrl: localhost -> resolves to http://localhost:8000");
} catch (e) { fail("resolveApiBaseUrl: localhost", e); }

try {
  assert.equal(
    resolveApiBaseUrl({ hostname: "127.0.0.1", configuredBaseUrl: "http://localhost:8000" }),
    "http://127.0.0.1:8000",
  );
  ok("resolveApiBaseUrl: 127.0.0.1 -> resolves to http://127.0.0.1:8000");
} catch (e) { fail("resolveApiBaseUrl: 127.0.0.1", e); }

try {
  assert.equal(
    resolveApiBaseUrl({ hostname: "airguard.example", configuredBaseUrl: "https://api.example" }),
    "https://api.example",
  );
  ok("resolveApiBaseUrl: external hostname -> uses configuredBaseUrl");
} catch (e) { fail("resolveApiBaseUrl: external", e); }

// -----------------------------------------------------------------
// Section 4 — Isolated Fault Injection Harness (Loopback 127.0.0.1:19337)
// -----------------------------------------------------------------
console.log("\n[Section 4] Fault Injection Harness (127.0.0.1:19337)");

let requestCount = 0;
const openSockets = new Set();
const activeTimers = new Set();

function registerTimer(fn, delayMs) {
  const timer = setTimeout(() => {
    activeTimers.delete(timer);
    fn();
  }, delayMs);
  activeTimers.add(timer);
  return timer;
}

function clearAllTimers() {
  for (const timer of activeTimers) {
    clearTimeout(timer);
  }
  activeTimers.clear();
}

const harnessServer = http.createServer((req, res) => {
  if (req.method !== "POST" || req.url !== "/api/v1/agent/chat") {
    res.writeHead(200, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ status: "ok" }));
    return;
  }

  requestCount++;
  const mode = req.headers["x-fault-mode"] || "pass";
  const scenarioId = req.headers["x-scenario-id"] || "unknown";
  const requestId = req.headers["x-request-id"] || (`harness-${Date.now()}`);

  fixtureRecord(mode, scenarioId, `request #${requestCount}, request_id=${requestId}`);

  if (mode === "structured_503") {
    res.writeHead(503, {
      "Content-Type": "application/json",
      "X-Request-ID": requestId,
    });
    res.end(JSON.stringify({
      code: "agent_unavailable",
      message: "Dịch vụ AI Agent đang tạm thời gián đoạn",
      request_id: requestId,
      details: {},
    }));
    return;
  }

  if (mode === "timeout") {
    fixtureRecord("timeout", scenarioId, `holding connection for ${CLIENT_TIMEOUT_MS + 2000}ms`);
    const timer = registerTimer(() => {
      if (!res.destroyed && !res.writableEnded) {
        res.writeHead(200, { "Content-Type": "application/json" });
        res.end(JSON.stringify({ response: "late_response" }));
      }
    }, CLIENT_TIMEOUT_MS + 2000);

    req.on("close", () => {
      clearTimeout(timer);
      activeTimers.delete(timer);
    });
    return;
  }

  if (mode === "network_failure") {
    fixtureRecord("network_failure", scenarioId, "destroying socket immediately");
    req.socket.destroy();
    return;
  }

  // Pass mode: Proxy to the real live backend at 127.0.0.1:8000
  let bodyBuffer = "";
  req.on("data", (chunk) => { bodyBuffer += chunk; });
  req.on("end", () => {
    const proxyReq = http.request(
      `${REAL_BACKEND_BASE}/api/v1/agent/chat`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Request-ID": requestId,
        },
      },
      (proxyRes) => {
        let proxyBody = "";
        proxyRes.on("data", (c) => { proxyBody += c; });
        proxyRes.on("end", () => {
          res.writeHead(proxyRes.statusCode || 200, {
            "Content-Type": proxyRes.headers["content-type"] || "application/json",
            "X-Request-ID": proxyRes.headers["x-request-id"] || requestId,
          });
          res.end(proxyBody);
        });
      },
    );

    proxyReq.on("error", (proxyErr) => {
      res.writeHead(503, { "Content-Type": "application/json", "X-Request-ID": requestId });
      res.end(JSON.stringify({
        code: "agent_unavailable",
        message: proxyErr.message,
        request_id: requestId,
        details: {},
      }));
    });

    proxyReq.write(bodyBuffer);
    proxyReq.end();
  });
});

harnessServer.on("connection", (socket) => {
  openSockets.add(socket);
  socket.on("close", () => {
    openSockets.delete(socket);
  });
});

function fetchWithTimeout(url, options, timeoutMs) {
  const controller = new AbortController();
  const tid = setTimeout(() => controller.abort(new Error("client_timeout")), timeoutMs);
  return fetch(url, { ...options, signal: controller.signal }).finally(() => clearTimeout(tid));
}

function agentChatRequest(mode, scenarioId, timeoutMs) {
  return fetchWithTimeout(
    `${HARNESS_BASE}/api/v1/agent/chat`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Fault-Mode": mode,
        "X-Scenario-ID": `${SESSION_ID}-${scenarioId}`,
        "X-Request-ID": `${SESSION_ID}-${scenarioId}`,
      },
      body: JSON.stringify({
        message: "Chất lượng không khí và AQI hiện tại ở trạm S03 VinUni thế nào?",
        user_id: "demo-user",
        station_id: "S03",
      }),
    },
    timeoutMs || CLIENT_TIMEOUT_MS,
  );
}

async function runHarnessTests() {
  await new Promise((resolve, reject) => {
    harnessServer.on("error", reject);
    harnessServer.listen(HARNESS_PORT, HARNESS_HOST, resolve);
  });
  console.log(`  Harness listening on ${HARNESS_HOST}:${HARNESS_PORT}`);

  // 4.1 Structured 503
  console.log("\n  [4.1] Structured 503 — agent_unavailable");
  try {
    const reqsBefore = requestCount;
    const res = await agentChatRequest("structured_503", "503-test");
    const reqsAfter = requestCount;

    assert.equal(reqsAfter - reqsBefore, 1, "POST chat must dispatch exactly one request (no auto-retry)");
    assert.equal(res.status, 503, "Status must be 503");
    const body = await res.json();

    assert.ok(typeof body.code === "string" && body.code.length > 0, "Error body must have 'code'");
    assert.ok(typeof body.message === "string" && body.message.length > 0, "Error body must have 'message'");
    assert.ok(typeof body.request_id === "string" && body.request_id.length > 0, "Error body must have 'request_id'");

    const headerRid = res.headers.get("x-request-id");
    assert.equal(headerRid, body.request_id, "X-Request-ID header must match request_id in body");

    const forbidden = ["answer", "response", "evidence", "sources", "used_tools", "map_actions", "proposal_id"];
    for (const field of forbidden) {
      assert.ok(!(field in body), `Error body must NOT contain '${field}' field`);
    }

    fixtureRecord("structured_503", `${SESSION_ID}-503-test`, `PASS — code=${body.code}, request_id=${body.request_id}`);
    ok("Structured 503: status=503, error envelope shape correct, no answer/evidence fields, single request");
  } catch (e) { fail("Structured 503", e); }

  // 4.2 Timeout
  console.log("\n  [4.2] Timeout — AbortController client deadline");
  try {
    const start = Date.now();
    let caughtError = null;
    try {
      // 1500ms timeout to verify client-side AbortController aborts before harness finishes
      await agentChatRequest("timeout", "timeout-test", 1500);
    } catch (err) {
      caughtError = err;
    }
    const elapsed = Date.now() - start;

    assert.ok(caughtError !== null, "Timeout must cause fetch to reject");
    const isAbort = caughtError.name === "AbortError" || (caughtError.message || "").includes("abort") || (caughtError.message || "").includes("client_timeout");
    const isNetwork = caughtError.name === "TypeError";
    assert.ok(isAbort || isNetwork, `Expected AbortError or network error, got: ${caughtError.name}: ${caughtError.message}`);
    assert.ok(elapsed < CLIENT_TIMEOUT_MS, `Test completed in ${elapsed}ms`);

    fixtureRecord("timeout", `${SESSION_ID}-timeout-test`, `PASS — error=${caughtError.name}, elapsed=${elapsed}ms`);
    ok(`Timeout: AbortController fires (${caughtError.name}), elapsed=${elapsed}ms, no success fallback`);
  } catch (e) { fail("Timeout: AbortController", e); }

  // 4.3 Network failure
  console.log("\n  [4.3] Network failure — socket destroyed");
  try {
    let caughtError = null;
    fixtureRecord("network_failure", `${SESSION_ID}-network-test`, "outbound request dispatched");
    try {
      await agentChatRequest("network_failure", "network-test");
    } catch (err) {
      caughtError = err;
    }

    assert.ok(caughtError !== null, "Network failure must cause an error to be thrown");
    const isNetworkErr = caughtError.name === "TypeError" || caughtError.name === "FetchError" || caughtError.code === "ECONNRESET";
    assert.ok(isNetworkErr, `Expected network error, got: ${caughtError.name}: ${caughtError.message}`);

    fixtureRecord("network_failure", `${SESSION_ID}-network-test`, `PASS — error=${caughtError.name}: ${caughtError.message}`);
    ok(`Network failure: socket destroyed, error thrown (${caughtError.name}), no fake success`);
  } catch (e) { fail("Network failure", e); }

  // 4.4 Real Pass-Through (Proxy to live backend at :8000)
  console.log("\n  [4.4] Real Pass-Through — live backend :8000 proxy");
  try {
    const reqsBefore = requestCount;
    const res = await agentChatRequest("pass", "real-backend-test");
    const reqsAfter = requestCount;

    assert.equal(reqsAfter - reqsBefore, 1, "Exactly one request must be dispatched");
    assert.equal(res.status, 200, "Live backend must return 200");
    const body = await res.json();

    // Verify grounded structure from real backend
    const parsed = extractAgentReply(body);
    assert.ok(parsed.reply.length > 0, "Reply must not be empty");
    assert.ok(typeof body.request_id === "string" && body.request_id.length > 0, "Must have request_id");
    assert.ok(!parsed.reply.includes("Agent đã xử lý yêu cầu"), "Must NOT contain fallback phrase");

    fixtureRecord("pass", `${SESSION_ID}-real-backend-test`, `PASS — real backend replied, request_id=${body.request_id}`);
    ok("Real pass-through: proxies to live backend :8000, returns real grounded response, no fake fallback");
  } catch (e) { fail("Real pass-through", e); }

  // 4.5 Error body fields exclusion
  console.log("\n  [4.5] Error body exclusion check");
  try {
    const res = await agentChatRequest("structured_503", "exclusion-check");
    const body = await res.json();
    const forbidden = ["answer", "response", "evidence", "sources", "used_tools", "map_actions", "proposal_id"];
    const present = forbidden.filter((f) => f in body);
    assert.equal(present.length, 0, `Error body MUST NOT contain: ${present.join(", ")}`);
    ok("Error body exclusion: none of [answer, response, evidence, sources, used_tools, map_actions, proposal_id] present in 503 body");
  } catch (e) { fail("Error body exclusion", e); }

  // Cleanup: Close sockets and server cleanly
  clearAllTimers();
  for (const socket of openSockets) {
    socket.destroy();
  }
  openSockets.clear();

  await new Promise((resolve) => {
    harnessServer.close(resolve);
  });
  console.log(`\n  Harness on ${HARNESS_HOST}:${HARNESS_PORT} closed — cleanup complete.`);
}

// Execute tests and summarize
runHarnessTests()
  .then(() => {
    console.log("\n-- Fixture Log --");
    for (const entry of fixtureLog) {
      console.log(`  [${entry.ts}] ${entry.scenario} | ${entry.marker} | ${entry.detail}`);
    }

    console.log("\n-- Test Results --");
    console.log(`  PASS: ${passed}`);
    console.log(`  FAIL: ${failed}`);

    if (failed > 0) {
      console.error("\n  ✗ test:ai-resilience FAILED — see errors above");
      process.exitCode = 1;
    } else {
      console.log("\n  ✓ test:ai-resilience ALL CHECKS PASSED");
      console.log("  AI-24 resilience contract gate: PASS");
      process.exitCode = 0;
    }
  })
  .catch((err) => {
    console.error("\nFatal harness error:", err);
    process.exitCode = 1;
  });
