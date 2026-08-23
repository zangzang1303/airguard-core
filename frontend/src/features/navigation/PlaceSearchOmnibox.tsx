import React, { useState, useRef, useEffect, useMemo } from "react";
import { Search, X, MapPin, Sparkles, Navigation, ChevronRight, LocateFixed, Crosshair, Compass } from "lucide-react";
import { OCEAN_PARK_POIS } from "../map/poiData";
import { Station } from "../../types";
import { PlacePOI } from "../../types/superApp";
import { parseCoordinateString } from "../../utils/geoUtils";

interface PlaceSearchOmniboxProps {
  stations: Station[];
  onSelectCoordinates: (coords: [number, number], title: string) => void;
  onSelectStation: (stationId: string) => void;
  onSelectPoi: (poi: PlacePOI) => void;
  onAskAiWithQuery: (query: string) => void;
  onSetUserLocation?: (
    coords: [number, number],
    name: string,
    source: "search" | "manual_click" | "gps"
  ) => void;
  onLocateGps?: () => void;
  onStartPickOnMap?: () => void;
}

export const PlaceSearchOmnibox: React.FC<PlaceSearchOmniboxProps> = ({
  stations,
  onSelectCoordinates,
  onSelectStation,
  onSelectPoi,
  onAskAiWithQuery,
  onSetUserLocation,
  onLocateGps,
  onStartPickOnMap,
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

  // Check if input is a direct lat, lng coordinate
  const parsedCoords = useMemo(() => parseCoordinateString(query), [query]);

  // Filter matching POIs
  const matchedPois = useMemo(() => {
    if (!normalizedQuery) return [];
    return OCEAN_PARK_POIS.filter(
      (p) =>
        p.name.toLowerCase().includes(normalizedQuery) ||
        (p.subdivision && p.subdivision.toLowerCase().includes(normalizedQuery)) ||
        p.category.toLowerCase().includes(normalizedQuery)
    );
  }, [normalizedQuery]);

  // Filter matching Stations
  const matchedStations = useMemo(() => {
    if (!normalizedQuery) return [];
    return stations.filter(
      (s) =>
        s.station_name.toLowerCase().includes(normalizedQuery) ||
        s.station_id.toLowerCase().includes(normalizedQuery)
    );
  }, [normalizedQuery, stations]);

  const isAiQueryCandidate =
    normalizedQuery.length > 3 &&
    (normalizedQuery.includes("sạch") ||
      normalizedQuery.includes("chạy") ||
      normalizedQuery.includes("thế nào") ||
      normalizedQuery.includes("ở đâu") ||
      normalizedQuery.includes("tốt") ||
      normalizedQuery.includes("trẻ em") ||
      normalizedQuery.includes("an toàn"));

  const handleSelectPoiItem = (poi: PlacePOI, asUserLocation = false) => {
    setQuery(poi.name);
    setIsOpen(false);
    onSelectPoi(poi);
    onSelectCoordinates([poi.latitude, poi.longitude], poi.name);
    if (asUserLocation && onSetUserLocation) {
      onSetUserLocation([poi.latitude, poi.longitude], poi.name, "search");
    }
  };

  const handleSelectStationItem = (station: Station, asUserLocation = false) => {
    setQuery(station.station_name);
    setIsOpen(false);
    onSelectStation(station.station_id);
    onSelectCoordinates([station.latitude, station.longitude], station.station_name);
    if (asUserLocation && onSetUserLocation) {
      onSetUserLocation([station.latitude, station.longitude], station.station_name, "search");
    }
  };

  const handleSelectCustomCoordinates = (coords: [number, number]) => {
    const title = `Toạ độ (${coords[0].toFixed(4)}, ${coords[1].toFixed(4)})`;
    setIsOpen(false);
    onSelectCoordinates(coords, title);
    if (onSetUserLocation) {
      onSetUserLocation(coords, title, "search");
    }
  };

  const handleTriggerAiSearch = (text: string) => {
    setIsOpen(false);
    onAskAiWithQuery(text);
  };

  const handleQuickGps = () => {
    setIsOpen(false);
    if (onLocateGps) {
      onLocateGps();
    }
  };

  const handleQuickPickOnMap = () => {
    setIsOpen(false);
    if (onStartPickOnMap) {
      onStartPickOnMap();
    }
  };

  return (
    <div className="search-omnibox-container" ref={wrapperRef}>
      <div className={`search-omnibox-bar ${isOpen ? "focused" : ""}`}>
        <Search className="search-icon-prefix" size={18} />
        <input
          type="text"
          className="search-input"
          placeholder="Tìm địa điểm, nhập toạ độ (lat, lng), trạm đo hoặc hỏi AI..."
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            setIsOpen(true);
          }}
          onFocus={() => setIsOpen(true)}
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              if (parsedCoords) {
                handleSelectCustomCoordinates(parsedCoords);
              } else if (isAiQueryCandidate) {
                handleTriggerAiSearch(query);
              } else if (matchedPois.length > 0) {
                handleSelectPoiItem(matchedPois[0], true);
              }
            }
          }}
        />
        {query && (
          <button
            type="button"
            className="search-clear-btn"
            onClick={() => {
              setQuery("");
              setIsOpen(false);
            }}
            aria-label="Xóa tìm kiếm"
          >
            <X size={15} />
          </button>
        )}
      </div>

      {/* Instant Dropdown Suggestions */}
      {isOpen && (
        <div className="search-dropdown-menu">
          {/* Quick Location Action Buttons at the Top of Search Dropdown */}
          <div className="search-quick-actions-bar">
            {onLocateGps && (
              <button
                type="button"
                className="search-quick-btn"
                onClick={handleQuickGps}
              >
                <LocateFixed size={14} className="text-primary" />
                <span>Định vị GPS</span>
              </button>
            )}
            {onStartPickOnMap && (
              <button
                type="button"
                className="search-quick-btn"
                onClick={handleQuickPickOnMap}
              >
                <Crosshair size={14} className="text-emerald" />
                <span>Chọn trên bản đồ</span>
              </button>
            )}
          </div>

          {/* Coordinate input detected match */}
          {parsedCoords && (
            <div
              className="search-dropdown-coord-item"
              onClick={() => handleSelectCustomCoordinates(parsedCoords)}
            >
              <Compass size={18} className="coord-icon" />
              <div className="coord-text">
                <strong>Đặt vị trí tại toạ độ: {parsedCoords[0].toFixed(5)}, {parsedCoords[1].toFixed(5)}</strong>
                <span>Nhấn để ghim vị trí người dùng và di chuyển bản đồ đến điểm này</span>
              </div>
              <ChevronRight size={16} className="item-arrow" />
            </div>
          )}

          {/* AI Quick Prompt if applicable */}
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
              {matchedPois.slice(0, 6).map((poi) => (
                <div
                  key={poi.id}
                  className="search-result-item"
                  onClick={() => handleSelectPoiItem(poi, false)}
                >
                  <MapPin size={16} className="item-icon-poi" />
                  <div className="item-details">
                    <div className="item-name">{poi.name}</div>
                    <div className="item-sub">{poi.subdivision}</div>
                  </div>
                  {onSetUserLocation && (
                    <button
                      type="button"
                      className="item-set-location-btn"
                      title="Đặt địa điểm này làm vị trí của bạn"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleSelectPoiItem(poi, true);
                      }}
                    >
                      <MapPin size={12} />
                      <span>Đặt vị trí</span>
                    </button>
                  )}
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
                  onClick={() => handleSelectStationItem(station, false)}
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
                  {onSetUserLocation && (
                    <button
                      type="button"
                      className="item-set-location-btn"
                      title="Đặt trạm này làm vị trí của bạn"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleSelectStationItem(station, true);
                      }}
                    >
                      <MapPin size={12} />
                      <span>Đặt vị trí</span>
                    </button>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Fallback Empty State */}
          {!parsedCoords && matchedPois.length === 0 && matchedStations.length === 0 && query.trim().length > 0 && (
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
