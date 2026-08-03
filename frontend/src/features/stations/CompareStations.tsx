import React, { useEffect, useState } from "react";
import { api } from "../../api/client";
import { DataQualityBadge, getPm25Severity } from "../../components/common/DataQualityBadge";
import { useAuth } from "../../context/AuthContext";
import { Station, StationDetailData } from "../../types";

export const CompareStations: React.FC = () => {
  const { compareStationIds, setCompareStationIds, navigateTo } = useAuth();
  const [allStations, setAllStations] = useState<Station[]>([]);
  const [stationA, setStationA] = useState<StationDetailData | null>(null);
  const [stationB, setStationB] = useState<StationDetailData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    const loadCompare = async () => {
      setLoading(true);
      try {
        const [list, dataA, dataB] = await Promise.all([
          api.getStations(),
          api.getStationCurrent(compareStationIds[0]),
          api.getStationCurrent(compareStationIds[1])
        ]);
        setAllStations(list);
        setStationA(dataA);
        setStationB(dataB);
      } catch (err) {
        console.error("Error loading comparison data:", err);
      } finally {
        setLoading(false);
      }
    };
    loadCompare();
  }, [compareStationIds]);

  const handleAskAICompare = () => {
    navigateTo("agent", { stationId: `${compareStationIds[0]}, ${compareStationIds[1]}` });
  };

  if (loading || !stationA || !stationB) {
    return (
      <div className="compare-container">
        <div className="skeleton-card" style={{ height: 400 }}></div>
      </div>
    );
  }

  const sevA = getPm25Severity(stationA.pm25);
  const sevB = getPm25Severity(stationB.pm25);

  return (
    <div className="compare-container">
      <div className="compare-header">
        <h2>⚖️ So sánh Chất lượng Không khí giữa 2 Trạm</h2>
        <button className="btn-primary" onClick={handleAskAICompare}>
          🤖 Hỏi AI Phân tích sự Khác biệt
        </button>
      </div>

      {/* Selectors */}
      <div className="compare-selectors">
        <div className="select-box">
          <label>Trạm A:</label>
          <select
            value={compareStationIds[0]}
            onChange={(e) => setCompareStationIds([e.target.value, compareStationIds[1]])}
            className="role-select"
          >
            {allStations.map((s) => (
              <option key={s.station_id} value={s.station_id} disabled={s.station_id === compareStationIds[1]}>
                {s.station_id} - {s.station_name}
              </option>
            ))}
          </select>
        </div>

        <span className="vs-badge">VS</span>

        <div className="select-box">
          <label>Trạm B:</label>
          <select
            value={compareStationIds[1]}
            onChange={(e) => setCompareStationIds([compareStationIds[0], e.target.value])}
            className="role-select"
          >
            {allStations.map((s) => (
              <option key={s.station_id} value={s.station_id} disabled={s.station_id === compareStationIds[0]}>
                {s.station_id} - {s.station_name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Comparison Side-by-Side Cards */}
      <div className="compare-grid">
        {/* Card A */}
        <div className="compare-card">
          <div className="card-badge">Trạm A</div>
          <h3>{stationA.station_name} ({stationA.station_id})</h3>
          <div className="metric-value" style={{ color: sevA.color }}>
            {stationA.pm25 ?? "N/A"} <small>µg/m³</small>
          </div>
          <DataQualityBadge status={stationA.status} isStale={stationA.is_stale} pm25={stationA.pm25} />
          
          <div className="compare-details">
            <div>🌡️ Nhiệt độ: <strong>{stationA.weather?.temperature ?? 29} °C</strong></div>
            <div>💧 Độ ẩm: <strong>{stationA.weather?.humidity ?? 75} %</strong></div>
            <div>💨 Tốc độ gió: <strong>{stationA.weather?.wind_speed ?? 2.1} m/s</strong></div>
            <div>Cập nhật: {new Date(stationA.updated_at).toLocaleTimeString("vi-VN")}</div>
          </div>
        </div>

        {/* Card B */}
        <div className="compare-card">
          <div className="card-badge">Trạm B</div>
          <h3>{stationB.station_name} ({stationB.station_id})</h3>
          <div className="metric-value" style={{ color: sevB.color }}>
            {stationB.pm25 ?? "N/A"} <small>µg/m³</small>
          </div>
          <DataQualityBadge status={stationB.status} isStale={stationB.is_stale} pm25={stationB.pm25} />

          <div className="compare-details">
            <div>🌡️ Nhiệt độ: <strong>{stationB.weather?.temperature ?? 29} °C</strong></div>
            <div>💧 Độ ẩm: <strong>{stationB.weather?.humidity ?? 75} %</strong></div>
            <div>💨 Tốc độ gió: <strong>{stationB.weather?.wind_speed ?? 2.1} m/s</strong></div>
            <div>Cập nhật: {new Date(stationB.updated_at).toLocaleTimeString("vi-VN")}</div>
          </div>
        </div>
      </div>

      {/* Difference Analysis Box */}
      <div className="difference-box">
        <h4>📌 Kết luận So sánh Nhanh:</h4>
        <p>
          Chênh lệch PM2.5 giữa 2 khu vực là <strong>{Math.abs(Number(stationA.pm25 || 0) - Number(stationB.pm25 || 0)).toFixed(1)} µg/m³</strong>.
          {Number(stationA.pm25) > Number(stationB.pm25)
            ? ` Khu vực ${stationA.station_name} có chất lượng không khí kém hơn.`
            : ` Khu vực ${stationB.station_name} có chất lượng không khí kém hơn.`}
        </p>
      </div>
    </div>
  );
};
