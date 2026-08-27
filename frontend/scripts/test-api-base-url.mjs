import assert from "node:assert/strict";
import { resolveApiBaseUrl } from "../src/api/apiBaseUrl.js";

// Session 3A: Loopback hostname alignment for default port 8000
assert.equal(
  resolveApiBaseUrl({ hostname: "localhost", configuredBaseUrl: "http://127.0.0.1:8000" }),
  "http://localhost:8000",
);
assert.equal(
  resolveApiBaseUrl({ hostname: "127.0.0.1", configuredBaseUrl: "http://localhost:8000" }),
  "http://127.0.0.1:8000",
);
assert.equal(
  resolveApiBaseUrl({ hostname: "localhost", configuredBaseUrl: "" }),
  "http://localhost:8000",
);

// Explicit isolated E2E custom ports (e.g. 19338, 19337)
assert.equal(
  resolveApiBaseUrl({ hostname: "127.0.0.1", configuredBaseUrl: "http://127.0.0.1:19338" }),
  "http://127.0.0.1:19338",
);
assert.equal(
  resolveApiBaseUrl({ hostname: "localhost", configuredBaseUrl: "http://127.0.0.1:19338" }),
  "http://localhost:19338",
);
assert.equal(
  resolveApiBaseUrl({ hostname: "127.0.0.1", configuredBaseUrl: "http://localhost:19337" }),
  "http://127.0.0.1:19337",
);

// Production external hostname
assert.equal(
  resolveApiBaseUrl({ hostname: "airguard.example", configuredBaseUrl: "https://api.example" }),
  "https://api.example",
);

console.log("api base URL host-alignment regression checks passed");

