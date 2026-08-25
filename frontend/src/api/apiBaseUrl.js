/**
 * Keep browser-to-local API requests on the same loopback hostname as the UI.
 * `localhost` and `127.0.0.1` are different cookie sites, even though they
 * resolve to the same local machine.
 * Respect explicit custom ports for isolated E2E test harnesses.
 */
export function resolveApiBaseUrl({ hostname, configuredBaseUrl }) {
  const isLocalLoopback = hostname === "localhost" || hostname === "127.0.0.1";

  if (configuredBaseUrl) {
    try {
      const parsed = new URL(configuredBaseUrl);
      const isConfiguredLoopback = parsed.hostname === "localhost" || parsed.hostname === "127.0.0.1";
      const hasCustomPort = parsed.port && parsed.port !== "8000" && parsed.port !== "80" && parsed.port !== "443";

      if (hasCustomPort) {
        if (isLocalLoopback || isConfiguredLoopback) {
          const targetHost = isLocalLoopback ? hostname : parsed.hostname;
          return `${parsed.protocol}//${targetHost}:${parsed.port}`;
        }
        return configuredBaseUrl.replace(/\/+$/, "");
      }
    } catch (_) {
      // If parsing fails, fall through to default logic
    }
  }

  if (isLocalLoopback) {
    return `http://${hostname}:8000`;
  }
  return configuredBaseUrl || "https://airguard-core.onrender.com";
}

