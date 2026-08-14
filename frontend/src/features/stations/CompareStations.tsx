import React, { useEffect, useState } from "react";
import { Bot, Droplets, GitCompareArrows, Thermometer, TriangleAlert, Wind } from "lucide-react";
import { api } from "../../api/client";
import { Button } from "../../components/common/Button";
import { DataQualityBadge, getPm25Severity } from "../../components/common/DataQualityBadge";
import { PageHeader } from "../../components/common/PageHeader";
import { useAuth } from "../../context/AuthContext";
import { Station, StationDetailData } from "../../types";
import { formatVnTime } from "../../utils/datetime";

export const CompareStations: React.FC = () => {
  const { compareStationIds, setCompareStationIds, navigateTo } = useAuth();
  const [allStations, setAllStations] = useState<Station[]>([]);
  const [stationA, setStationA] = useState<StationDetailData | null>(null);
  const [stationB, setStationB] = useState<StationDetailData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [reloadToken, setReloadToken] = useState(0);

  useEffect(() => {
    const loadCompare = async () => {
      setLoading(true);
      setError(null);
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
        setError("Không thể tải dữ liệu so sánh. Vui lòng thử lại.");
      } finally {
        setLoading(false);
      }
    };
    loadCompare();
  }, [compareStationIds, reloadToken]);

  const handleAskAICompare = () => {
    navigateTo("agent", { stationId: `${compareStationIds[0]}, ${compareStationIds[1]}` });
  };

  if (loading) {
    return (
      <div className="compare-container">
        <PageHeader
          title="So sánh khu vực"
          description="Đối chiếu PM2.5 và độ mới dữ liệu giữa hai trạm."
        />
        <div className="skeleton-card skeleton-card--lg" role="status" aria-label="Đang tải dữ liệu so sánh" />
      </div>
    );
  }

  // Lỗi tải phải hiện thông báo kèm nút thử lại, không rơi vào skeleton vĩnh viễn.
  if (error || !stationA || !stationB) {
    return (
      <div className="compare-container">
        <PageHeader
          title="So sánh khu vực"
          description="Không thể hiển thị dữ liệu so sánh ở thời điểm này."
        />
        <div className="alert-box alert-error" role="alert">
          <TriangleAlert size={17} aria-hidden="true" />
          <span>{error ?? "Không tìm thấy dữ liệu cho một trong hai trạm được chọn."}</span>
          <Button variant="outline" size="sm" onClick={() => setReloadToken((token) => token + 1)}>
            Thử lại
          </Button>
        </div>
      </div>
    );
  }

  const sevA = getPm25Severity(stationA.pm25);
  const sevB = getPm25Severity(stationB.pm25);
  const canCompare = [stationA, stationB].every(
    (station) => station.status === "online" && !station.is_stale && station.pm25 !== null,
  );
  const difference = canCompare
    ? Math.abs(Number(stationA.pm25) - Number(stationB.pm25)).toFixed(1)
    : null;

  return (
    <div className="compare-container">
      <PageHeader
        title="So sánh khu vực"
        description="Đối chiếu PM2.5, thời tiết ngữ cảnh và độ mới dữ liệu giữa hai trạm."
        actions={(
          <Button variant="primary" onClick={handleAskAICompare}>
            <Bot size={17} aria-hidden="true" />
            Hỏi AI phân tích
          </Button>
        )}
      />

      {/* Selectors */}
      <div className="compare-selectors">
        <div className="select-box">
          <label htmlFor="compare-station-a">Trạm A:</label>
          <select
            id="compare-station-a"
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

        <span className="vs-badge" aria-hidden="true">VS</span>

        <div className="select-box">
          <label htmlFor="compare-station-b">Trạm B:</label>
          <select
            id="compare-station-b"
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
          <h2>{stationA.station_name} ({stationA.station_id})</h2>
          <div className="metric-value" style={{ color: sevA.color }}>
            {stationA.pm25 ?? "N/A"} <small>µg/m³</small>
          </div>
          <DataQualityBadge status={stationA.status} isStale={stationA.is_stale} pm25={stationA.pm25} aqi={stationA.aqi} />
          
          <div className="compare-details">
            <div><Thermometer size={16} aria-hidden="true" /> Nhiệt độ: <strong>{stationA.weather?.temperature ?? "Không khả dụng"}{stationA.weather ? " °C" : ""}</strong></div>
            <div><Droplets size={16} aria-hidden="true" /> Độ ẩm: <strong>{stationA.weather?.humidity ?? "Không khả dụng"}{stationA.weather ? " %" : ""}</strong></div>
            <div><Wind size={16} aria-hidden="true" /> Tốc độ gió: <strong>{stationA.weather?.wind_speed ?? "Không khả dụng"}{stationA.weather ? " m/s" : ""}</strong></div>
            <div>Cập nhật: {formatVnTime(stationA.updated_at)}</div>
          </div>
        </div>

        {/* Card B */}
        <div className="compare-card">
          <div className="card-badge">Trạm B</div>
          <h2>{stationB.station_name} ({stationB.station_id})</h2>
          <div className="metric-value" style={{ color: sevB.color }}>
            {stationB.pm25 ?? "N/A"} <small>µg/m³</small>
          </div>
          <DataQualityBadge status={stationB.status} isStale={stationB.is_stale} pm25={stationB.pm25} aqi={stationB.aqi} />

          <div className="compare-details">
            <div><Thermometer size={16} aria-hidden="true" /> Nhiệt độ: <strong>{stationB.weather?.temperature ?? "Không khả dụng"}{stationB.weather ? " °C" : ""}</strong></div>
            <div><Droplets size={16} aria-hidden="true" /> Độ ẩm: <strong>{stationB.weather?.humidity ?? "Không khả dụng"}{stationB.weather ? " %" : ""}</strong></div>
            <div><Wind size={16} aria-hidden="true" /> Tốc độ gió: <strong>{stationB.weather?.wind_speed ?? "Không khả dụng"}{stationB.weather ? " m/s" : ""}</strong></div>
            <div>Cập nhật: {formatVnTime(stationB.updated_at)}</div>
          </div>
        </div>
      </div>

      {/* Difference Analysis Box */}
      <div className="difference-box">
        <h2><GitCompareArrows size={18} aria-hidden="true" /> Kết quả so sánh</h2>
        {difference ? (
          <p>Chênh lệch PM2.5 giữa hai trạm là <strong>{difference} µg/m³</strong>. Hãy dùng AI Agent nếu cần phân tích nguyên nhân dựa trên dữ liệu backend.</p>
        ) : (
          <p>Không đủ dữ liệu hợp lệ để tính chênh lệch. Một trong hai trạm đang offline, stale, invalid hoặc không có giá trị PM2.5.</p>
        )}
      </div>
    </div>
  );
};
