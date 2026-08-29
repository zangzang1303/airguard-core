/**
 * Regression Test Suite for AirGuard Unified Map Legend Architecture.
 *
 * Verifies:
 * 1. Single Context-Aware Legend (UnifiedMapLegend / AqiLegend) supports variants "stations" & "dispersion".
 * 2. MetricColorScale is rendered strictly ONCE inside the unified legend.
 * 3. HeatmapLayer focuses purely on Leaflet raster rendering without duplicate metadata card UI.
 * 4. showDispersionInfo is completely purged from types, default state, and MapLayersPopover.
 * 5. IDW methodology details are neatly nested inside an accordion inside the unified panel.
 * 6. SuperMap dynamically switches legend variant based on viewMode.
 */

import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const FRONTEND_SRC = path.resolve(__dirname, "../src");

const TYPES_FILE = path.join(FRONTEND_SRC, "types/superApp.ts");
const POPOVER_FILE = path.join(FRONTEND_SRC, "features/navigation/MapLayersPopover.tsx");
const APP_FILE = path.join(FRONTEND_SRC, "App.tsx");
const HEATMAP_LAYER_FILE = path.join(FRONTEND_SRC, "features/stations/HeatmapLayer.tsx");
const AQI_LEGEND_FILE = path.join(FRONTEND_SRC, "features/map/AqiLegend.tsx");
const SUPER_MAP_FILE = path.join(FRONTEND_SRC, "features/map/SuperMap.tsx");
const STYLES_FILE = path.join(FRONTEND_SRC, "styles.css");

let passed = 0;
let failed = 0;

function assert(condition, message) {
  if (condition) {
    console.log(`  ✓ ${message}`);
    passed++;
  } else {
    console.error(`  ✗ FAIL: ${message}`);
    failed++;
  }
}

console.log("\n🧪 Running AirGuard Unified Map Legend Regression Suite...\n");

// 1. Types Contract
console.log("1. Checking superApp.ts types contract...");
const typesContent = fs.readFileSync(TYPES_FILE, "utf-8");
assert(!typesContent.includes("showDispersionInfo"), "showDispersionInfo is purged from types/superApp.ts");
assert(typesContent.includes('"showMapLegend"'), "showMapLegend is present in MapLayerVisibilityKey");
assert(typesContent.includes("showMapLegend?: boolean;"), "showMapLegend is in MapLayerConfig");

// 2. MapLayersPopover Contract
console.log("\n2. Checking MapLayersPopover.tsx toggle contract...");
const popoverContent = fs.readFileSync(POPOVER_FILE, "utf-8");
assert(!popoverContent.includes("showDispersionInfo"), "MapLayersPopover no longer references showDispersionInfo");
assert(!popoverContent.includes("toggle-dispersion"), "toggle-dispersion checkbox row is removed");
assert(popoverContent.includes("toggle-map-legend"), "toggle-map-legend checkbox row is preserved as sole legend toggle");

// 3. App.tsx Initial State
console.log("\n3. Checking App.tsx state...");
const appContent = fs.readFileSync(APP_FILE, "utf-8");
assert(!appContent.includes("showDispersionInfo"), "App.tsx initial layerConfig does not contain showDispersionInfo");

// 4. HeatmapLayer Cleanliness
console.log("\n4. Checking HeatmapLayer.tsx rendering...");
const heatmapContent = fs.readFileSync(HEATMAP_LAYER_FILE, "utf-8");
assert(!heatmapContent.includes("spatial-heatmap-metadata-card"), "HeatmapLayer does NOT own spatial-heatmap-metadata-card");
assert(!heatmapContent.includes("unified-aqi-panel"), "HeatmapLayer does NOT own unified-aqi-panel");
assert(!heatmapContent.includes("<MetricColorScale"), "HeatmapLayer does NOT render MetricColorScale (avoids duplication)");
assert(heatmapContent.includes("onDataChange"), "HeatmapLayer exposes onDataChange callback for unified metadata");
assert(heatmapContent.includes("<ImageOverlay"), "HeatmapLayer renders ImageOverlay in Pane");

// 5. Unified AqiLegend Component
console.log("\n5. Checking AqiLegend.tsx (UnifiedMapLegend)...");
const aqiLegendContent = fs.readFileSync(AQI_LEGEND_FILE, "utf-8");
assert(aqiLegendContent.includes("export type MapLegendVariant ="), "MapLegendVariant type is defined");
assert(aqiLegendContent.includes("export const UnifiedMapLegend = AqiLegend;"), "UnifiedMapLegend is exported");
assert(aqiLegendContent.includes("export const MetricColorScale:"), "MetricColorScale is exported");
assert(aqiLegendContent.includes("export const StationStatusLegend:"), "StationStatusLegend is exported");
assert(aqiLegendContent.includes("export const DispersionMetadata:"), "DispersionMetadata is exported");
assert(aqiLegendContent.includes("dispersion-detail-trigger"), "IDW details are rendered in accordion trigger");
assert(aqiLegendContent.includes("dispersion-detail-box"), "IDW accordion detail box is present");
assert(aqiLegendContent.includes("panel-collapse-btn"), "Panel collapse button is present");
assert(aqiLegendContent.includes("legend-close-btn"), "Legend close button is present");

// 6. SuperMap Integration & Context-Aware Switching
console.log("\n6. Checking SuperMap.tsx variant switching...");
const superMapContent = fs.readFileSync(SUPER_MAP_FILE, "utf-8");
assert(superMapContent.includes('variant={viewMode === "heatmap" ? "dispersion" : "stations"}'), "SuperMap dynamically sets variant based on viewMode");
assert(superMapContent.includes("handleHeatmapDataChange"), "SuperMap connects heatmap data changes to unified legend");
assert(!superMapContent.includes("showDispersionInfo"), "SuperMap does not use showDispersionInfo");

// 7. Styles CSS
console.log("\n7. Checking styles.css...");
const stylesContent = fs.readFileSync(STYLES_FILE, "utf-8");
assert(stylesContent.includes(".unified-map-legend"), "styles.css has .unified-map-legend styles");
assert(stylesContent.includes(".dispersion-metadata-block"), "styles.css has .dispersion-metadata-block styles");
assert(stylesContent.includes(".dispersion-toggle-btn"), "styles.css has .dispersion-toggle-btn accordion styles");
assert(stylesContent.includes(".dispersion-detail-box"), "styles.css has .dispersion-detail-box styles");

console.log(`\n========================================`);
console.log(`Summary: ${passed} passed, ${failed} failed`);
console.log(`========================================\n`);

if (failed > 0) {
  process.exit(1);
}
