import React, { useEffect, useMemo, useRef, useState } from "react";
import { Pause, Play, RefreshCw } from "lucide-react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api } from "../../api/client";
import { ForecastData, GoldenWindowsData } from "../../types";
import { useDraggableFloatingPanel } from "../floating";
import { TimelineSlider } from "../stations/TimelineSlider";

interface DraggableTimelineDockProps {
  stationId: string | null;
  currentAqi: number | null;
  forecastHour: number;
  onForecastHourChange: (hours: number) => void;
}

const formatWindowTime = (value: string) =>
  new Intl.DateTimeFormat("vi-VN", {
    timeZone: "Asia/Bangkok",
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));

export const DraggableTimelineDock: React.FC<DraggableTimelineDockProps> = ({
  stationId,
  currentAqi,
  forecastHour,
  onForecastHourChange,
}) => {
  const { containerProps, handleProps } = useDraggableFloatingPanel({
    panelId: "timeline",
    group: "widget",
    baseTransform: "translateX(-50%)",
  });
  const [playing, setPlaying] = useState(false);
  const [forecast, setForecast] = useState<ForecastData | null>(null);
  const [goldenWindows, setGoldenWindows] = useState<GoldenWindowsData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const hourRef = useRef(forecastHour);

  useEffect(() => {
    hourRef.current = forecastHour;
    if (forecastHour >= 24) setPlaying(false);
  }, [forecastHour]);

  useEffect(() => {
    if (!playing) return;
    const intervalId = window.setInterval(() => {
      const nextHour = hourRef.current >= 24 ? 0 : hourRef.current + 1;
      hourRef.current = nextHour;
      onForecastHourChange(nextHour);
      if (nextHour >= 24) setPlaying(false);
    }, 800);
    return () => window.clearInterval(intervalId);
  }, [onForecastHourChange, playing]);

  useEffect(() => {
    if (!stationId) {
      setForecast(null);
      setGoldenWindows(null);
      return;
    }
    let cancelled = false;
    setLoading(true);
    setError(null);
    Promise.all([
      api.getStationForecast(stationId, "aqi", 24, "extended"),
      api.getGoldenWindows(stationId),
    ])
      .then(([nextForecast, nextWindows]) => {
        if (cancelled) return;
        setForecast(nextForecast);
        setGoldenWindows(nextWindows);
      })
      .catch((requestError) => {
        if (cancelled) return;
        setError(requestError instanceof Error ? requestError.message : "Không thể tải dự báo 24 giờ.");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [stationId]);

  const chartData = useMemo(() => {
    const current = {
      hour: 0,
      label: "0h",
      current: currentAqi,
      forecast: null,
      interval: currentAqi == null ? null : [currentAqi, currentAqi],
    };
    const future = (forecast?.forecasts ?? []).map((point) => ({
      hour: point.hour_offset ?? Number.parseInt(point.horizon, 10),
      label: `+${point.hour_offset ?? Number.parseInt(point.horizon, 10)}h`,
      current: null,
      forecast: point.value,
      interval: point.range,
    }));
    return [current, ...future];
  }, [currentAqi, forecast]);

  const togglePlayback = () => {
    if (!playing && forecastHour >= 24) {
      hourRef.current = 0;
      onForecastHourChange(0);
    }
    setPlaying((value) => !value);
  };

  return (
    <div {...containerProps} className="map-timeline-floating-dock">
      <div className="timeline-simulation-toolbar">
        <button type="button" className="timeline-play-button" onClick={togglePlayback} aria-pressed={playing}>
          {playing ? <Pause size={15} aria-hidden="true" /> : <Play size={15} aria-hidden="true" />}
          {playing ? "Tạm dừng" : "Play Simulation"}
        </button>
        <span>{stationId ? `Trạm ${stationId}` : "Chọn một trạm để xem khung giờ vàng"}</span>
      </div>

      <TimelineSlider
        value={forecastHour}
        onChange={(hour) => {
          setPlaying(false);
          onForecastHourChange(hour);
        }}
        loading={loading}
        label="Diễn biến AQI 24 giờ"
        titleProps={handleProps}
      />

      {stationId && (
        <div className="timeline-intelligence-panel" aria-live="polite">
          {loading && <p className="timeline-load-state"><RefreshCw size={13} className="spin-icon" /> Đang tải dự báo…</p>}
          {error && <p className="timeline-load-state is-error">{error}</p>}
          {!loading && !error && goldenWindows && (
            <div className="golden-window-grid">
              <div className="golden-window-card is-best">
                <strong>🌿 Khung giờ vàng</strong>
                {goldenWindows.best_window ? (
                  <span>
                    {formatWindowTime(goldenWindows.best_window.start_at)}–{formatWindowTime(goldenWindows.best_window.end_at)} · AQI TB {goldenWindows.best_window.average_aqi}
                  </span>
                ) : (
                  <span>Chưa có ≥2 giờ liên tục đạt AQI ≤50 và đủ gió.</span>
                )}
              </div>
              <div className="golden-window-card is-worst">
                <strong>⚠️ Đỉnh cần tránh</strong>
                <span>{formatWindowTime(goldenWindows.worst_window.forecast_at)} · AQI {goldenWindows.worst_window.aqi}</span>
              </div>
            </div>
          )}

          {!loading && !error && forecast && (
            <div className="timeline-mini-chart" role="img" aria-label="Biểu đồ AQI hiện tại, dự báo và khoảng tin cậy 24 giờ">
              <ResponsiveContainer width="100%" height={116}>
                <AreaChart data={chartData} margin={{ top: 6, right: 8, bottom: 0, left: -22 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="label" ticks={["0h", "+6h", "+12h", "+18h", "+24h"]} tick={{ fontSize: 9 }} />
                  <YAxis tick={{ fontSize: 9 }} domain={[0, "auto"]} />
                  <Tooltip />
                  <Area dataKey="interval" stroke="none" fill="#38bdf8" fillOpacity={0.16} connectNulls />
                  <Line dataKey="current" stroke="#0f172a" strokeWidth={2.5} dot={{ r: 3 }} connectNulls />
                  <Line dataKey="forecast" stroke="#0284c7" strokeWidth={2} strokeDasharray="6 4" dot={false} connectNulls />
                </AreaChart>
              </ResponsiveContainer>
              <small>{forecast.model_name} · {forecast.source} · độ tin cậy {forecast.confidence}</small>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
