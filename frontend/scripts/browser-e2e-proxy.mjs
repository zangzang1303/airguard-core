/**
 * browser-e2e-proxy.mjs — Isolated loopback proxy for browser E2E test.
 * Listens on 127.0.0.1:19338 and controls fault modes dynamically without touching shared services.
 */

import http from "node:http";

const PORT = 19338;
const HOST = "127.0.0.1";
const REAL_BACKEND = "http://127.0.0.1:8000";

let currentMode = "structured_503"; // 'structured_503' | 'timeout' | 'network_failure' | 'pass'
let requestLog = [];

const server = http.createServer((req, res) => {
  // CORS headers
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type, X-Request-ID, X-Fault-Mode, X-Scenario-ID");

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

  if (req.url === "/api/proxy-stats" && req.method === "GET") {
    res.writeHead(200, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ mode: currentMode, requests: requestLog }));
    return;
  }

  if (req.url === "/api/v1/agent/chat" && req.method === "POST") {
    const reqId = req.headers["x-request-id"] || `e2e-proxy-${Date.now()}`;
    const mode = req.headers["x-fault-mode"] || currentMode;
    requestLog.push({ mode, reqId, ts: new Date().toISOString() });
    console.log(`[E2E Proxy] Handling chat request: mode=${mode}, reqId=${reqId}`);

    if (mode === "structured_503") {
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
      // Hold connection
      const timer = setTimeout(() => {
        if (!res.destroyed && !res.writableEnded) {
          res.writeHead(503, { "Content-Type": "application/json" });
          res.end(JSON.stringify({ code: "agent_timeout", request_id: reqId }));
        }
      }, 15000);
      req.on("close", () => clearTimeout(timer));
      return;
    }

    if (mode === "network_failure") {
      req.socket.destroy();
      return;
    }

    // Pass mode: Proxy to real backend :8000
    let body = "";
    req.on("data", c => { body += c; });
    req.on("end", () => {
      const pReq = http.request(
        `${REAL_BACKEND}/api/v1/agent/chat`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-Request-ID": reqId,
          },
        },
        (pRes) => {
          let pBody = "";
          pRes.on("data", c => { pBody += c; });
          pRes.on("end", () => {
            res.writeHead(pRes.statusCode || 200, {
              "Content-Type": pRes.headers["content-type"] || "application/json",
              "X-Request-ID": pRes.headers["x-request-id"] || reqId,
            });
            res.end(pBody);
          });
        }
      );
      pReq.on("error", (err) => {
        res.writeHead(503, { "Content-Type": "application/json" });
        res.end(JSON.stringify({ code: "agent_unavailable", message: err.message, request_id: reqId }));
      });
      pReq.write(body);
      pReq.end();
    });
    return;
  }

  // Fallback: proxy other GET endpoints to backend :8000 (stations, alerts, etc.)
  const pReq = http.request(
    `${REAL_BACKEND}${req.url}`,
    {
      method: req.method,
      headers: req.headers,
    },
    (pRes) => {
      res.writeHead(pRes.statusCode || 200, pRes.headers);
      pRes.pipe(res);
    }
  );
  pReq.on("error", (e) => {
    res.writeHead(502, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ error: e.message }));
  });
  req.pipe(pReq);
});

server.listen(PORT, HOST, () => {
  console.log(`E2E Proxy running on http://${HOST}:${PORT}`);
});
