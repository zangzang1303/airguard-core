import React, { useState, useRef, useEffect } from "react";
import { Search, X, MapPin, Sparkles, Navigation, ChevronRight } from "lucide-react";
import { OCEAN_PARK_POIS } from "../map/poiData";
import { Station } from "../../types";
import { PlacePOI } from "../../types/superApp";

interface PlaceSearchOmniboxProps {
  stations: Station[];
  onSelectCoordinates: (coords: [number, number], title: string) => void;
  onSelectStation: (stationId: string) => void;
  onSelectPoi: (poi: PlacePOI) => void;
  onAskAiWithQuery: (query: string) => void;
}

export const PlaceSearchOmnibox: React.FC<PlaceSearchOmniboxProps> = ({
  stations,
  onSelectCoordinates,
  onSelectStation,
  onSelectPoi,
  onAskAiWithQuery,
}) => {
  const [query, setQuery] = useState("");
  const [isOpen, setIsOpen] = useState(false);
  const wrapperRef = useRef<HTMLDivElement>(null);

  // Close dropdown on outside click
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const normalizedQuery = query.trim().toLowerCase();

  // Filter matching POIs
  const matchedPois = OCEAN_PARK_POIS.filter(
    (p) =>
      p.name.toLowerCase().includes(normalizedQuery) ||
      (p.subdivision && p.subdivision.toLowerCase().includes(normalizedQuery)) ||
      p.category.toLowerCase().includes(normalizedQuery)
  );

  // Filter matching Stations
  const matchedStations = stations.filter(
    (s) =>
      s.station_name.toLowerCase().includes(normalizedQuery) ||
      s.station_id.toLowerCase().includes(normalizedQuery)
  );

  const isAiQueryCandidate =
    normalizedQuery.length > 3 &&
    (normalizedQuery.includes("sạch") ||
      normalizedQuery.includes("chạy") ||
      normalizedQuery.includes("thế nào") ||
      normalizedQuery.includes("ở đâu") ||
      normalizedQuery.includes("tốt") ||
      normalizedQuery.includes("trẻ em") ||
      normalizedQuery.includes("an toàn"));

  const handleSelectPoiItem = (poi: PlacePOI) => {
    setQuery(poi.name);
    setIsOpen(false);
    onSelectPoi(poi);
    onSelectCoordinates([poi.latitude, poi.longitude], poi.name);
  };

  const handleSelectStationItem = (station: Station) => {
    setQuery(station.station_name);
    setIsOpen(false);
    onSelectStation(station.station_id);
    onSelectCoordinates([station.latitude, station.longitude], station.station_name);
  };

  const handleTriggerAiSearch = (text: string) => {
    setIsOpen(false);
    onAskAiWithQuery(text);
  };

  return (
    <div className="search-omnibox-container" ref={wrapperRef}>
      <div className={`search-omnibox-bar ${isOpen ? "focused" : ""}`}>
        <Search className="search-icon-prefix" size={18} />
        <input
          type="text"
          className="search-input"
          placeholder="Tìm địa điểm Ocean Park 1, trạm đo hoặc hỏi AI..."
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            setIsOpen(true);
          }}
          onFocus={() => setIsOpen(true)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && isAiQueryCandidate) {
              handleTriggerAiSearch(query);
            }
          }}
        />
        {query && (
          <button
            className="search-clear-btn"
            onClick={() => {
              setQuery("");
              setIsOpen(false);
            }}
          >
            <X size={15} />
          </button>
        )}
      </div>

      {/* Instant Dropdown Suggestions */}
      {isOpen && (
        <div className="search-dropdown-menu">
          {/* AI Quick Prompt Prompt if applicable */}
          {query.length > 2 && (
            <div
              className="search-dropdown-ai-item"
              onClick={() => handleTriggerAiSearch(query)}
            >
              <div className="ai-item-icon">
                <Sparkles size={16} />
              </div>
              <div className="ai-item-text">
                <strong>Hỏi AI: &ldquo;{query}&rdquo;</strong>
                <span>Phân tích chất lượng không khí & gợi ý vị trí tốt</span>
              </div>
              <ChevronRight size={16} className="item-arrow" />
            </div>
          )}

          {/* POI Results */}
          {matchedPois.length > 0 && (
            <div className="search-group">
              <div className="search-group-title">Địa điểm trong Ocean Park 1</div>
              {matchedPois.slice(0, 5).map((poi) => (
                <div
                  key={poi.id}
                  className="search-result-item"
                  onClick={() => handleSelectPoiItem(poi)}
                >
                  <MapPin size={16} className="item-icon-poi" />
                  <div className="item-details">
                    <div className="item-name">{poi.name}</div>
                    <div className="item-sub">{poi.subdivision}</div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Station Results */}
          {matchedStations.length > 0 && (
            <div className="search-group">
              <div className="search-group-title">Trạm cảm biến quan trắc</div>
              {matchedStations.map((station) => (
                <div
                  key={station.station_id}
                  className="search-result-item"
                  onClick={() => handleSelectStationItem(station)}
                >
                  <Navigation size={16} className="item-icon-sensor" />
                  <div className="item-details">
                    <div className="item-name">
                      {station.station_name} <span className="sensor-id-pill">{station.station_id}</span>
                    </div>
                    <div className="item-sub">PM2.5: {station.pm25 ?? "—"} µg/m³</div>
                  </div>
                  <span
                    className="item-aqi-chip"
                    style={{
                      backgroundColor:
                        (station.aqi ?? 0) <= 50
                          ? "#10b981"
                          : (station.aqi ?? 0) <= 100
                          ? "#eab308"
                          : "#ef4444",
                    }}
                  >
                    AQI {station.aqi ?? "—"}
                  </span>
                </div>
              ))}
            </div>
          )}

          {matchedPois.length === 0 && matchedStations.length === 0 && (
            <div className="search-empty-state" onClick={() => handleTriggerAiSearch(query)}>
              <Sparkles size={20} className="empty-ai-icon" />
              <div>Không tìm thấy địa danh trực tiếp. Nhấn để hỏi <strong>AirGuard AI</strong> tìm kiếm thông minh.</div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
