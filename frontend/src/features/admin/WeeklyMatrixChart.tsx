import React, { useEffect, useMemo, useState } from "react";
import { WeeklyMatrixStatistics } from "../../types";

interface WeeklyMatrixChartProps {
  matrix?: WeeklyMatrixStatistics;
}

const FALLBACK_PALETTE = ["#e8f5e9", "#b9e4c9", "#f4e38b", "#f6b26b", "#e06666", "#8e3b63"];

function cellColor(value: number, stops: number[], palette: string[]): string {
  const index = stops.findIndex((stop) => value <= stop);
  return palette[index < 0 ? palette.length - 1 : Math.min(index, palette.length - 1)];
}

function percent(value: number): string {
  return new Intl.NumberFormat("vi-VN", {
    style: "percent",
    maximumFractionDigits: 1,
  }).format(value);
}

export const WeeklyMatrixChart: React.FC<WeeklyMatrixChartProps> = ({ matrix }) => {
  const [selector, setSelector] = useState("all_stations");

  useEffect(() => {
    const options = matrix?.station_options ?? [];
    if (!options.includes(selector)) setSelector(options[0] ?? "all_stations");
  }, [matrix, selector]);

  const view = useMemo(
    () => matrix?.views.find((item) => item.station_selector === selector) ?? matrix?.views[0],
    [matrix, selector],
  );

  if (!matrix || matrix.status === "legacy_unavailable") {
    return <div className="matrix-empty-state">Báo cáo legacy không có ma trận theo giờ.</div>;
  }
  if (matrix.status !== "available") {
    return <div className="matrix-empty-state">Ma trận chỉ áp dụng cho báo cáo hàng tuần.</div>;
  }
  if (!view) {
    return <div className="matrix-empty-state">Backend chưa cung cấp view ma trận.</div>;
  }
  if (view.cells.length !== 168) {
    return (
      <div className="matrix-error-state" role="alert">
        Ma trận persisted không hợp lệ: cần đúng 168 ô.
      </div>
    );
  }

  const palette = matrix.color_scale.palette?.length === 6
    ? matrix.color_scale.palette
    : FALLBACK_PALETTE;
  const days = Array.from(new Set(view.cells.map((cell) => cell.local_date)));

  return (
    <div className="weekly-matrix-chart">
      <div className="matrix-toolbar">
        <label htmlFor="weekly-matrix-station">Phạm vi trạm</label>
        <select
          id="weekly-matrix-station"
          value={view.station_selector}
          onChange={(event) => setSelector(event.target.value)}
        >
          {matrix.station_options.map((option) => (
            <option key={option} value={option}>
              {option === "all_stations" ? "Tất cả trạm (mean không trọng số)" : option}
            </option>
          ))}
        </select>
        <span>Thang cố định: {matrix.color_scale.version}</span>
      </div>

      <div className="matrix-scroll" role="region" aria-label="Ma trận PM2.5 bảy ngày theo hai mươi bốn giờ">
        <div className="matrix-grid" role="grid">
          <div className="matrix-corner" aria-hidden="true">Ngày</div>
          {Array.from({ length: 24 }, (_, hour) => (
            <div key={`hour-${hour}`} className="matrix-hour" role="columnheader">{hour}</div>
          ))}
          {days.map((day, dayIndex) => (
            <React.Fragment key={day}>
              <div className="matrix-day" role="rowheader">{day.slice(5)}</div>
              {view.cells.slice(dayIndex * 24, dayIndex * 24 + 24).map((cell) => {
                const eligible = cell.status === "eligible" && cell.value != null;
                const title = eligible
                  ? `${cell.local_date} ${cell.local_hour}:00 · PM2.5 ${cell.value} µg/m³ · mẫu ${cell.valid_sample_count}/${cell.expected_sample_count} · coverage ${percent(cell.coverage_ratio)} · trạm ${cell.eligible_station_count}/${cell.active_station_count}`
                  : `${cell.local_date} ${cell.local_hour}:00 · N/A · mẫu ${cell.valid_sample_count}/${cell.expected_sample_count} · coverage ${percent(cell.coverage_ratio)} · trạm ${cell.eligible_station_count}/${cell.active_station_count}`;
                return (
                  <div
                    key={`${cell.local_date}-${cell.local_hour}`}
                    role="gridcell"
                    className={`matrix-cell ${eligible ? "is-eligible" : "is-na"}`}
                    style={eligible ? { backgroundColor: cellColor(cell.value!, matrix.color_scale.stops, palette) } : undefined}
                    title={title}
                    aria-label={title}
                  >
                    {eligible ? cell.value!.toFixed(0) : "N/A"}
                  </div>
                );
              })}
            </React.Fragment>
          ))}
        </div>
      </div>

      <div className="matrix-legend" aria-label="Chú giải màu PM2.5">
        {matrix.color_scale.stops.map((stop, index) => (
          <span key={stop}>
            <i style={{ backgroundColor: palette[index] }} />
            {stop}
          </span>
        ))}
        <span><i className="matrix-na-swatch" />N/A</span>
      </div>
      <p className="matrix-caption">
        Màu chỉ là thang trực quan cố định; không phải phân loại AQI hay kết luận QCVN/WHO.
        Ô N/A không được diễn giải là chất lượng không khí tốt.
      </p>
    </div>
  );
};
