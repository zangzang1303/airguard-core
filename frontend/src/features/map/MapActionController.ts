import L from "leaflet";

export interface MapAction {
  type:
    | "clear_ai_layer"
    | "fly_to"
    | "fit_bounds"
    | "highlight_area"
    | "highlight_route"
    | "highlight_sensor"
    | "highlight_point"
    | "add_annotation"
    | "remove_annotation"
    | "show_radius"
    | "dim_other_markers"
    | "set_environment_layer"
    | "show_heatmap";
  [key: string]: any;
}

export type OverlayChangeListener = (hasOverlay: boolean) => void;

export class MapActionController {
  private map: L.Map | null = null;
  private aiOverlayLayer: L.FeatureGroup | null = null;
  private listeners: Set<OverlayChangeListener> = new Set();

  constructor() {
    this.aiOverlayLayer = L.featureGroup();
  }

  public subscribe(listener: OverlayChangeListener): () => void {
    this.listeners.add(listener);
    try {
      listener(this.hasAIOverlay());
    } catch (err) {
      console.error("[MapActionController] Error calling initial listener:", err);
    }
    return () => {
      this.listeners.delete(listener);
    };
  }

  public hasAIOverlay(): boolean {
    if (!this.aiOverlayLayer) return false;
    return this.aiOverlayLayer.getLayers().length > 0;
  }

  private notify() {
    const active = this.hasAIOverlay();
    this.listeners.forEach((listener) => {
      try {
        listener(active);
      } catch (err) {
        console.error("[MapActionController] Error in listener:", err);
      }
    });
  }

  public setMap(map: L.Map | null) {
    if (this.map && this.aiOverlayLayer && this.map.hasLayer(this.aiOverlayLayer)) {
      this.map.removeLayer(this.aiOverlayLayer);
    }
    this.map = map;
    if (this.map && this.aiOverlayLayer) {
      this.aiOverlayLayer.addTo(this.map);
    }
    this.notify();
  }

  public getOverlayLayer(): L.FeatureGroup | null {
    return this.aiOverlayLayer;
  }

  public clearAIOverlay() {
    if (this.aiOverlayLayer) {
      this.aiOverlayLayer.clearLayers();
    }
    this.notify();
  }

  public executeAll(actions: MapAction[] | undefined | null) {
    if (!actions || !Array.isArray(actions) || actions.length === 0) return;
    if (!this.map || !this.aiOverlayLayer) return;

    for (const action of actions) {
      try {
        this.executeInternal(action);
      } catch (err) {
        console.warn("[MapActionController] Error executing action:", action, err);
      }
    }
    this.notify();
  }

  public execute(action: MapAction) {
    this.executeInternal(action);
    this.notify();
  }

  private executeInternal(action: MapAction) {
    if (!this.map || !this.aiOverlayLayer) return;

    switch (action.type) {
      case "clear_ai_layer":
        this.clearAIOverlay();
        break;

      case "fly_to": {
        const lat = Number(action.lat);
        const lng = Number(action.lng);
        const zoom = action.zoom ? Number(action.zoom) : 16;
        if (!isNaN(lat) && !isNaN(lng)) {
          this.map.flyTo([lat, lng], zoom, { duration: 1.2 });
        }
        break;
      }

      case "fit_bounds": {
        if (Array.isArray(action.bounds) && action.bounds.length === 2) {
          this.map.fitBounds(action.bounds as L.LatLngBoundsExpression, {
            padding: action.padding || [50, 50],
            maxZoom: 16,
            animate: true,
          });
        }
        break;
      }

      case "highlight_area": {
        const lat = Number(action.lat);
        const lng = Number(action.lng);
        const radius = Number(action.radius_m || 220);
        const style = action.style || "recommended";

        if (isNaN(lat) || isNaN(lng)) break;

        const colorMap: Record<string, { stroke: string; fill: string }> = {
          recommended: { stroke: "#10b981", fill: "#10b981" },
          alternative: { stroke: "#06b6d4", fill: "#06b6d4" },
          caution: { stroke: "#f59e0b", fill: "#f59e0b" },
          avoid: { stroke: "#ef4444", fill: "#ef4444" },
          danger: { stroke: "#dc2626", fill: "#dc2626" },
        };

        const theme = colorMap[style] || colorMap.recommended;

        // Outer pulsing ring
        const outerCircle = L.circle([lat, lng], {
          radius: radius,
          color: theme.stroke,
          weight: 2.5,
          opacity: 0.85,
          dashArray: style === "alternative" ? "6, 6" : undefined,
          fillColor: theme.fill,
          fillOpacity: 0.18,
        });

        // Inner glowing core
        const coreMarker = L.circleMarker([lat, lng], {
          radius: 8,
          color: "#ffffff",
          weight: 2,
          fillColor: theme.stroke,
          fillOpacity: 1.0,
        });

        this.aiOverlayLayer.addLayer(outerCircle);
        this.aiOverlayLayer.addLayer(coreMarker);
        break;
      }

      case "highlight_route": {
        const coords = action.coordinates as Array<[number, number]>;
        if (!coords || !Array.isArray(coords) || coords.length < 2) break;
        const segments = Array.isArray(action.segments) ? action.segments : [];

        const style = action.style || "recommended";
        const colorMap: Record<string, { stroke: string; halo: string }> = {
          recommended: { stroke: "#10b981", halo: "rgba(16, 185, 129, 0.45)" },
          alternative: { stroke: "#06b6d4", halo: "rgba(6, 182, 212, 0.45)" },
          caution: { stroke: "#f59e0b", halo: "rgba(245, 158, 11, 0.45)" },
          avoid: { stroke: "#ef4444", halo: "rgba(239, 68, 68, 0.45)" },
        };
        const theme = colorMap[style] || colorMap.recommended;

        // 1. Outer Glowing Halo Polyline
        const glowPolyline = L.polyline(coords, {
          color: theme.stroke,
          weight: 14,
          opacity: 0.38,
          className: "ai-route-halo-path",
          lineCap: "round",
          lineJoin: "round",
        });

        // 2. Draw the core by environmental segment when the backend supplies
        // grounded per-section exposure. This keeps the selected route visible
        // while showing local air-quality changes along it.
        const segmentColorMap: Record<string, string> = {
          good: "#10b981",
          moderate: "#f59e0b",
          unhealthy_sensitive: "#f97316",
          unhealthy: "#ef4444",
        };
        const segmentPolylines: L.Polyline[] = [];
        if (segments.length > 0) {
          segments.forEach((segment: any) => {
            const segmentCoords = segment?.coordinates as Array<[number, number]>;
            if (!Array.isArray(segmentCoords) || segmentCoords.length < 2) return;
            const segmentColor = segmentColorMap[String(segment.level)] || theme.stroke;
            const segmentPolyline = L.polyline(segmentCoords, {
              color: segmentColor,
              weight: 7,
              opacity: 0.98,
              lineCap: "round",
              lineJoin: "round",
            });
            const observedAt = segment.observed_at
              ? new Date(segment.observed_at).toLocaleString("vi-VN")
              : "Không có thời điểm";
            segmentPolyline.bindTooltip(
              `PM2.5 ${segment.pm25} µg/m³ · khối lượng hít vào ước tính ${segment.estimated_inhaled_mass_ug} µg · ${observedAt}`,
              { sticky: true, direction: "top" },
            );
            segmentPolylines.push(segmentPolyline);
          });
        }

        const corePolyline = segments.length === 0
          ? L.polyline(coords, {
              color: theme.stroke,
              weight: 5.5,
              opacity: 0.95,
              lineCap: "round",
              lineJoin: "round",
            })
          : null;

        // 3. Neon Flowing Dash Animation Overlay (Runner Track Effect)
        const flowingDash = L.polyline(coords, {
          color: "#ffffff",
          weight: 3,
          opacity: 0.95,
          className: "ai-route-flowing-dash",
          lineCap: "round",
          lineJoin: "round",
        });

        // 4. Start Point Pin with Animated Sonar Pulse
        const startHtml = `
          <div class="ai-runner-pin-wrapper">
            <div class="ai-runner-pin-pulse"></div>
            <div class="ai-runner-pin-circle" title="Xuất phát: ${action.name || ''}">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z"></path>
                <line x1="4" y1="22" x2="4" y2="15"></line>
              </svg>
            </div>
          </div>
        `;
        const startIcon = L.divIcon({
          html: startHtml,
          className: "ai-runner-custom-marker",
          iconSize: [36, 36],
          iconAnchor: [18, 18],
        });
        const startMarker = L.marker(coords[0], { icon: startIcon });

        // 5. Finish Point Marker
        const endCoord = coords[coords.length - 1];
        const endHtml = `
          <div style="width: 22px; height: 22px; border-radius: 50%; background: #ffffff; border: 2.5px solid ${theme.stroke}; display: flex; align-items: center; justify-content: center; box-shadow: 0 4px 10px rgba(0,0,0,0.3); font-size: 11px;">
            🏁
          </div>
        `;
        const endIcon = L.divIcon({
          html: endHtml,
          className: "ai-end-marker",
          iconSize: [22, 22],
          iconAnchor: [11, 11],
        });
        const endMarker = L.marker(endCoord, { icon: endIcon });

        this.aiOverlayLayer.addLayer(glowPolyline);
        if (corePolyline) this.aiOverlayLayer.addLayer(corePolyline);
        segmentPolylines.forEach((polyline) => this.aiOverlayLayer?.addLayer(polyline));
        this.aiOverlayLayer.addLayer(flowingDash);
        this.aiOverlayLayer.addLayer(startMarker);
        this.aiOverlayLayer.addLayer(endMarker);
        break;
      }

      case "highlight_sensor": {
        const lat = Number(action.lat);
        const lng = Number(action.lng);
        const severity = action.severity || "normal";
        if (isNaN(lat) || isNaN(lng)) break;

        const color = severity === "danger" ? "#ef4444" : "#10b981";

        const sensorHalo = L.circleMarker([lat, lng], {
          radius: 24,
          color: color,
          weight: 3,
          dashArray: "4, 4",
          fillColor: color,
          fillOpacity: 0.28,
        });

        this.aiOverlayLayer.addLayer(sensorHalo);
        break;
      }

      case "highlight_point": {
        const lat = Number(action.lat);
        const lng = Number(action.lng);
        if (isNaN(lat) || isNaN(lng)) break;

        const pin = L.circleMarker([lat, lng], {
          radius: 12,
          color: "#ffffff",
          weight: 3,
          fillColor: "#3b82f6",
          fillOpacity: 0.9,
        });

        this.aiOverlayLayer.addLayer(pin);
        break;
      }

      case "add_annotation": {
        const lat = Number(action.lat);
        const lng = Number(action.lng);
        if (isNaN(lat) || isNaN(lng)) break;

        const title = action.title || "Gợi ý AI";
        const badge = action.badge || "";
        const style = action.style || "recommended";

        const badgeBg =
          style === "recommended"
            ? "#10b981"
            : style === "danger"
            ? "#ef4444"
            : style === "caution"
            ? "#f59e0b"
            : "#06b6d4";

        const htmlContent = `
          <div class="ai-compact-leader-chip-wrapper">
            <div class="ai-compact-leader-chip" title="${action.subtitle || title}">
              <span>${title}</span>
              ${badge ? `<span class="ai-chip-badge" style="background: ${badgeBg};">${badge}</span>` : ""}
            </div>
            <div class="ai-chip-stem"></div>
          </div>
        `;

        const customIcon = L.divIcon({
          html: htmlContent,
          className: "ai-annotation-marker",
          iconSize: [0, 0],
          iconAnchor: [0, 0],
        });

        const marker = L.marker([lat, lng], { icon: customIcon });
        this.aiOverlayLayer.addLayer(marker);
        break;
      }

      case "show_radius": {
        const lat = Number(action.lat);
        const lng = Number(action.lng);
        const radius = Number(action.radius_m || 1000);
        if (isNaN(lat) || isNaN(lng)) break;

        const circle = L.circle([lat, lng], {
          radius: radius,
          color: "#3b82f6",
          weight: 1.5,
          dashArray: "6, 6",
          fillColor: "#3b82f6",
          fillOpacity: 0.05,
        });

        this.aiOverlayLayer.addLayer(circle);
        break;
      }

      default:
        console.info("[MapActionController] Unhandled action type:", action.type);
    }
  }
}

// Global Singleton for easy integration
export const mapActionController = new MapActionController();
