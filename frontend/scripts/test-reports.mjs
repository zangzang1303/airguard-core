import fs from "node:fs";
import path from "node:path";
import process from "node:process";

const root = path.resolve(import.meta.dirname, "..");
const viewer = fs.readFileSync(path.join(root, "src/features/admin/ReportViewer.tsx"), "utf8");
const matrix = fs.readFileSync(path.join(root, "src/features/admin/WeeklyMatrixChart.tsx"), "utf8");
const types = fs.readFileSync(path.join(root, "src/types/index.ts"), "utf8");
const client = fs.readFileSync(path.join(root, "src/api/client.ts"), "utf8");
const app = fs.readFileSync(path.join(root, "src/App.tsx"), "utf8");
const auth = fs.readFileSync(path.join(root, "src/context/AuthContext.tsx"), "utf8");
const topBar = fs.readFileSync(path.join(root, "src/features/navigation/TopFloatingBar.tsx"), "utf8");

const assertions = [
  [viewer.includes("WeeklyMatrixChart"), "ReportViewer must render WeeklyMatrixChart"],
  [viewer.includes("Không đủ dữ liệu"), "ReportViewer must expose ESG insufficient-data state"],
  [viewer.includes("report-download-toolbar") && viewer.includes("Tải tệp"), "ReportViewer must expose a simple file download toolbar"],
  [!viewer.includes("Định dạng khác"), "ReportViewer must not hide export formats behind an extra menu"],
  [viewer.includes("Thông tin kỹ thuật và kiểm tra toàn vẹn"), "ReportViewer must keep technical metadata collapsed"],
  [viewer.includes("hasMultipleReports") && viewer.includes("Đang xem báo cáo:"), "ReportViewer must simplify the period control when only one report exists"],
  [!viewer.includes("Environmental performance brief"), "ReportViewer must not expose English report labels"],
  [viewer.includes("no_acknowledged_boost_cycles: \"Chưa có chu kỳ tăng cường thông gió được xác nhận."), "ReportViewer must translate ESG reason codes"],
  [viewer.includes('insufficient_data: "Chưa đủ dữ liệu"'), "ReportViewer must translate reference statuses"],
  [viewer.includes("Báo cáo legacy"), "ReportViewer must expose legacy compatibility state"],
  [viewer.includes("report-loading-state") && viewer.includes("report-empty-state") && viewer.includes("report-error-state"), "ReportViewer must retain loading, empty and error states"],
  [matrix.includes("view.cells.length !== 168"), "Matrix must fail closed unless a view has exactly 168 cells"],
  [matrix.includes("is-na") && matrix.includes("N/A"), "Matrix must distinguish N/A cells"],
  [matrix.includes("valid_sample_count") && matrix.includes("expected_sample_count") && matrix.includes("eligible_station_count"), "Matrix tooltip must include sample, expected and station counts"],
  [types.includes('"pm25-fixed-scale-v1"'), "Report types must freeze the matrix scale version"],
  [types.includes("content_checksum_sha256"), "Report types must include persisted checksum"],
  [client.includes("Content-Disposition") || client.includes("downloadApiFile"), "API client must preserve server download filenames"],
  [auth.includes('| "admin-reports"'), "Auth screen contract must include the reports route"],
  [auth.includes("authenticatedLandingScreen") && auth.includes('pathname.includes("reports")'), "Session restore must preserve the reports deep link"],
  [app.includes('navigateTo("admin-reports")') && app.includes('currentScreen === "admin-reports"'), "Manager navigation must route to ReportViewer"],
  [app.includes('pathname.includes("reports")') && app.includes('setCurrentScreen("admin-reports")'), "Reports must support a direct local QA route"],
  [topBar.includes("Mở Báo cáo môi trường định kỳ"), "Manager toolbar must expose a reports action"],
];

const failures = assertions.filter(([ok]) => !ok).map(([, message]) => message);
if (failures.length) {
  for (const failure of failures) console.error(`FAIL: ${failure}`);
  process.exit(1);
}

console.log(`Report UI contract checks passed (${assertions.length}).`);
