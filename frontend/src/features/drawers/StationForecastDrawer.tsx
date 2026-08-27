import React, { useEffect, useMemo, useState } from "react";
import { ArrowLeft, Clock3, Database, Sparkles, TriangleAlert, X } from "lucide-react";

import { api } from "../../api/client";
import { DataQualityBadge } from "../../components/common/DataQualityBadge";
import { ForecastData, ForecastHorizon, Station } from "../../types";
import { TimelineSlider } from "../stations/TimelineSlider";
import { useDraggableFloatingPanel } from "../floating";

type MetricKey = ForecastData["metric"];

const METRICS: Record<MetricKey, { label: string; unit: string }> = {
  aqi: { label: "AQI", unit: "" },
  pm25: { label: "PM2.5", unit: "µg/m³" },
  co2: { label: "CO₂", unit: "ppm" },
  noise_db: { label: "Tiếng ồn", unit: "dB" },
  temperature: { label: "Nhiệt độ", unit: "°C" },
};

interface StationForecastDrawerProps {
  station: Station;
  onBack: () => void;
  onClose: () => void;
}

function getHorizonHour(item: ForecastHorizon, index: number): number | null {
  const parsed = Number.parseInt(item.horizon, 10);
  if (Number.isFinite(parsed) && parsed > 0) return parsed;
  const fallback = index + 1;
  return fallback <= 3 ? fallback : null;
}

function getCurrentValue(station: Station, metric: MetricKey): number | null {
  if (station.status !== "online" || station.is_stale) return null;
  if (metric === "aqi") return station.aqi ?? null;
  if (metric === "pm25") return station.pm25 ?? null;
  if (metric === "co2") return station.co2 ?? null;
  if (metric === "noise_db") return station.noise_db ?? null;
  if (metric === "temperature") return station.temperature ?? null;
  return null;
}

function formatConfidence(value: number | string | undefined): string {
  if (typeof value === "number" && Number.isFinite(value)) {
    return `${Math.round((value <= 1 ? value * 100 : value))}%`;
  }
  return value !== undefined && value !== "" ? String(value) : "Không khả dụng";
}

export const StationForecastDrawer: React.FC<StationForecastDrawerProps> = ({
  station,
  onBack,
  onClose,
}) => {
  const { containerProps, handleProps } = useDraggableFloatingPanel({
    panelId: "station-forecast",
    group: "drawer",
  });

  const [metric, setMetric] = useState<MetricKey>("aqi");
  const [forecastHour, setForecastHour] = useState(0);
  const [forecast, setForecast] = useState<ForecastData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reloadToken, setReloadToken] = useState(0);

  const hasUsableCurrentData = station.status === "online" && !station.is_stale;

  useEffect(() => {
    let active = true;

    if (!hasUsableCurrentData) {
      setForecast(null);
      setError("Trạm đang offline hoặc dữ liệu cũ. Không thể tính dự báo grounded.");
      return () => {
        active = false;
      };
    }

    setLoading(true);
    setError(null);

    api
      .getStationForecast(station.station_id, metric, 3)
      .then((data) => {
        if (!active) return;
        setForecast(data);
      })
      .catch((err) => {
        if (!active) return;
        setForecast(null);
        setError(err instanceof Error ? err.message : "Không thể tải dự báo ngắn hạn.");
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, [hasUsableCurrentData, metric, reloadToken, station.station_id]);

  const targetForecast = useMemo(
    () => forecast?.forecasts.find((item, index) => getHorizonHour(item, index) === forecastHour) ?? null,
    [forecast, forecastHour],
  );

  const currentValue = getCurrentValue(station, metric);
  const forecastValue = targetForecast?.value ?? targetForecast?.pm25_predicted ?? null;
  const rangeMin = targetForecast?.value_min ?? targetForecast?.range?.[0] ?? null;
  const rangeMax = targetForecast?.value_max ?? targetForecast?.range?.[1] ?? null;
  const displayedValue = forecastHour === 0 ? currentValue : forecastValue;

  return (
    <aside {...containerProps} className="contextual-drawer right-drawer station-forecast-drawer" aria-label={`Dự báo trạm ${station.station_name}`}>
      <div className="drawer-header-bar">
        <div className="drawer-title-group" {...handleProps}>
          <span className="badge-tag">Dự báo ngắn hạn</span>
          <h2 className="drawer-main-title">{station.station_name}</h2>
          <div className="drawer-sub-meta">
            <Clock3 size={13} aria-hidden="true" />
            <span>{station.station_id} · dữ liệu backend</span>
          </div>
        </div>
        <button className="no-drag drawer-close-btn" data-no-drag="true" onClick={onClose} aria-label="Đóng dự báo trạm">
          <X size={18} />
        </button>
      </div>

      <div className="drawer-scroll-body">
        <div className="forecast-drawer-quality-row">
          <span>Chất lượng dữ liệu hiện tại</span>
          <DataQualityBadge status={station.status} isStale={station.is_stale} pm25={station.pm25} aqi={station.aqi} />
        </div>

        <div className="forecast-drawer-metric-tabs" role="group" aria-label="Chọn chỉ số dự báo">
          {(Object.keys(METRICS) as MetricKey[]).map((item) => (
            <button
              type="button"
              key={item}
              className={metric === item ? "is-active" : ""}
              aria-pressed={metric === item}
              onClick={() => setMetric(item)}
            >
              {METRICS[item].label}
            </button>
          ))}
        </div>

        <TimelineSlider
          value={forecastHour}
          onChange={setForecastHour}
          loading={loading}
          disabled={loading || !hasUsableCurrentData}
          label={`Dự báo ${METRICS[metric].label}`}
        />

        {error && (
          <div className="forecast-drawer-state is-error" role="alert">
            <TriangleAlert size={19} aria-hidden="true" />
            <div>
              <strong>Không thể hiển thị dự báo</strong>
              <p>{error}</p>
            </div>
            {hasUsableCurrentData && (
              <button type="button" onClick={() => setReloadToken((value) => value + 1)}>Thử lại</button>
            )}
          </div>
        )}

        {!loading && !error && forecastHour > 0 && !targetForecast && (
          <div className="forecast-drawer-state is-info" role="status">
            <Clock3 size={19} aria-hidden="true" />
            <div>
              <strong>Chưa có dữ liệu cho mốc này</strong>
              <p>Backend chưa trả giá trị dự báo +{forecastHour}h. Không suy diễn hoặc lặp lại giá trị hiện tại.</p>
            </div>
          </div>
        )}

        {!loading && !error && (forecastHour === 0 || targetForecast) && (
          <section className="forecast-drawer-result" aria-live="polite">
            <div className="forecast-drawer-result__heading">
              <div>
                <span>{forecastHour === 0 ? "Giá trị hiện tại" : `Dự báo +${forecastHour} giờ`}</span>
                <strong>
                  {displayedValue ?? "—"}
                  {displayedValue != null && METRICS[metric].unit ? <small> {METRICS[metric].unit}</small> : null}
                </strong>
              </div>
              <Sparkles size={24} aria-hidden="true" />
            </div>

            {forecastHour > 0 && targetForecast && forecast && (
              <>
                <dl className="forecast-drawer-facts">
                  <div>
                    <dt>Khoảng dự báo</dt>
                    <dd>{rangeMin ?? "—"} – {rangeMax ?? "—"} {METRICS[metric].unit}</dd>
                  </div>
                  <div>
                    <dt>Độ tin cậy</dt>
                    <dd>{formatConfidence(targetForecast.confidence ?? forecast.confidence)}</dd>
                  </div>
                  <div>
                    <dt>Mô hình</dt>
                    <dd>{forecast.model_name || "Không khả dụng"}</dd>
                  </div>
                  <div>
                    <dt>Nguồn</dt>
                    <dd><Database size={13} aria-hidden="true" /> {forecast.source || "Không khả dụng"}</dd>
                  </div>
                </dl>
                {forecast.limitations?.length ? (
                  <div className="forecast-drawer-limitations">
                    <strong>Giới hạn mô hình</strong>
                    <p>{forecast.limitations.join(" · ")}</p>
                  </div>
                ) : null}
              </>
            )}

            {forecastHour === 0 && (
              <p className="forecast-drawer-current-note">
                Đây là phép đo hiện tại từ nguồn {station.source || "không khả dụng"}, không phải giá trị dự báo.
              </p>
            )}
          </section>
        )}
      </div>

      <div className="drawer-footer-actions">
        <button type="button" className="action-pill-btn secondary" onClick={onBack}>
          <ArrowLeft size={15} aria-hidden="true" />
          <span>Chi tiết trạm</span>
        </button>
      </div>
    </aside>
  );
};
