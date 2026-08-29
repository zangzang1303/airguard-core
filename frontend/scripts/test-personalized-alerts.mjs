import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const read = (path) => readFileSync(new URL(`../${path}`, import.meta.url), "utf8");

const client = read("src/api/client.ts");
const profile = read("src/features/profile/Profile.tsx");
const alerts = read("src/features/alerts/AlertList.tsx");
const app = read("src/App.tsx");
const assistant = read("src/features/drawers/AiAssistantDrawer.tsx");
const map = read("src/features/map/MapActionController.ts");

assert.match(client, /getNotificationPreferences/);
assert.match(client, /updateNotificationPreferences/);
assert.match(client, /updatePredictiveWarningChecklist/);
assert.match(profile, /environmental_email_enabled/);
assert.match(profile, /predictive_email_enabled/);
assert.doesNotMatch(profile, /Chưa cấu hình trong MVP/);

assert.match(alerts, /predictive_warning_id/);
assert.match(alerts, /close_windows/);
assert.match(alerts, /reduce_outdoor_activity/);
assert.match(alerts, /role !== "resident"/);
assert.match(app, /params\.get\("panel"\) !== "alerts"/);
assert.match(app, /setFlyToTarget\(\[station\.latitude, station\.longitude\]\)/);

assert.match(assistant, /estimated_inhaled_mass_ug/);
assert.match(assistant, /duration_minutes/);
assert.match(assistant, /exposure_reduction_pct/);
assert.doesNotMatch(assistant, /Math\.round\(routeAction\.distance_km \* 6\.5\)/);
assert.match(map, /segment\.estimated_inhaled_mass_ug/);

console.log("personalized alerts frontend contract: PASS");
