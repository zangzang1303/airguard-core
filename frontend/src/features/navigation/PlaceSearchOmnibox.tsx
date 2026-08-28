import React, { useState, useRef, useEffect, useMemo } from "react";
import {
  Search,
  X,
  MapPin,
  Sparkles,
  Navigation,
  ChevronRight,
  LocateFixed,
  Crosshair,
  Compass,
  Waves,
  Sun,
  ShoppingBag,
  GraduationCap,
  Building2,
  Trees,
  Flower2,
  Home,
  Radio,
  Clock,
  Trash2,
  ArrowUpRight,
  Flame,
} from "lucide-react";
import { OCEAN_PARK_POIS } from "../map/poiData";
import { Station } from "../../types";
import { PlacePOI } from "../../types/superApp";
import { parseCoordinateString } from "../../utils/geoUtils";
import { getAqiColorHex, getAqiLevel } from "../../constants/aqi";

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

interface RecentSearchItem {
  id: string;
  type: "station" | "poi" | "coord" | "ai";
  title: string;
  subtitle?: string;
  payload?: any;
  timestamp: number;
}

const RECENT_SEARCHES_STORAGE_KEY = "airguard_recent_searches_v1";

const AI_SUGGESTED_PROMPTS = [
  {
    id: "prompt-run",
    badge: "Chạy bộ",
    title: "Khu vực chạy bộ không khí sạch nhất hôm nay?",
    query: "Khu vực nào ở Vinhomes Ocean Park 1 đang có không khí trong lành nhất để chạy bộ hôm nay?",
  },
  {
    id: "prompt-kids",
    badge: "Trẻ em",
    title: "Chất lượng không khí có an toàn cho trẻ nhỏ ra ngoài?",
    query: "Chất lượng không khí hiện tại ở Ocean Park 1 có an toàn cho trẻ nhỏ và người già vui chơi ngoài trời không?",
  },
  {
    id: "prompt-window",
    badge: "Nhà ở",
    title: "Thời điểm này có nên mở cửa sổ thông gió không?",
    query: "Chỉ số bụi mịn PM2.5 và ô nhiễm hiện tại có thích hợp để mở cửa sổ thông gió trong căn hộ không?",
  },
];

function getPoiIcon(iconName?: string) {
  switch (iconName) {
    case "Waves":
      return <Waves size={15} className="item-icon-poi-nature" />;
    case "Sun":
      return <Sun size={15} className="item-icon-poi-sun" />;
    case "ShoppingBag":
      return <ShoppingBag size={15} className="item-icon-poi-mall" />;
    case "GraduationCap":
      return <GraduationCap size={15} className="item-icon-poi-edu" />;
    case "Building":
    case "Building2":
      return <Building2 size={15} className="item-icon-poi-landmark" />;
    case "Trees":
      return <Trees size={15} className="item-icon-poi-nature" />;
    case "Flower2":
      return <Flower2 size={15} className="item-icon-poi-park" />;
    case "Home":
      return <Home size={15} className="item-icon-poi-home" />;
    default:
      return <MapPin size={15} className="item-icon-poi" />;
  }
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
  const [recentSearches, setRecentSearches] = useState<RecentSearchItem[]>([]);
  const wrapperRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Load recent searches from localStorage
  useEffect(() => {
    try {
      const raw = localStorage.getItem(RECENT_SEARCHES_STORAGE_KEY);
      if (raw) {
        const parsed = JSON.parse(raw);
        if (Array.isArray(parsed)) {
          setRecentSearches(parsed.slice(0, 5));
        }
      }
    } catch {
      // Ignore localStorage errors
    }
  }, []);

  const saveRecentSearch = (item: Omit<RecentSearchItem, "timestamp">) => {
    try {
      setRecentSearches((prev) => {
        const filtered = prev.filter((r) => r.id !== item.id);
        const updated = [{ ...item, timestamp: Date.now() }, ...filtered].slice(0, 5);
        localStorage.setItem(RECENT_SEARCHES_STORAGE_KEY, JSON.stringify(updated));
        return updated;
      });
    } catch {
      // Ignore
    }
  };

  const handleClearRecentSearches = (e: React.MouseEvent) => {
    e.stopPropagation();
    setRecentSearches([]);
    try {
      localStorage.removeItem(RECENT_SEARCHES_STORAGE_KEY);
    } catch {
      // Ignore
    }
  };

  const handleRemoveRecentSearchItem = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setRecentSearches((prev) => {
      const updated = prev.filter((item) => item.id !== id);
      try {
        localStorage.setItem(RECENT_SEARCHES_STORAGE_KEY, JSON.stringify(updated));
      } catch {
        // Ignore
      }
      return updated;
    });
  };

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
      normalizedQuery.includes("an toàn") ||
      normalizedQuery.includes("mở cửa"));

  const handleSelectPoiItem = (poi: PlacePOI, asUserLocation = false) => {
    setQuery(poi.name);
    setIsOpen(false);
    onSelectPoi(poi);
    onSelectCoordinates([poi.latitude, poi.longitude], poi.name);
    saveRecentSearch({
      id: `poi-${poi.id}`,
      type: "poi",
      title: poi.name,
      subtitle: poi.subdivision || "Địa điểm KĐT",
      payload: poi,
    });
    if (asUserLocation && onSetUserLocation) {
      onSetUserLocation([poi.latitude, poi.longitude], poi.name, "search");
    }
  };

  const handleSelectStationItem = (station: Station, asUserLocation = false) => {
    setQuery(station.station_name);
    setIsOpen(false);
    onSelectStation(station.station_id);
    onSelectCoordinates([station.latitude, station.longitude], station.station_name);
    saveRecentSearch({
      id: `station-${station.station_id}`,
      type: "station",
      title: station.station_name,
      subtitle: `Trạm ${station.station_id} • AQI ${station.aqi ?? "—"}`,
      payload: station,
    });
    if (asUserLocation && onSetUserLocation) {
      onSetUserLocation([station.latitude, station.longitude], station.station_name, "search");
    }
  };

  const handleSelectCustomCoordinates = (coords: [number, number]) => {
    const title = `Toạ độ (${coords[0].toFixed(4)}, ${coords[1].toFixed(4)})`;
    setIsOpen(false);
    onSelectCoordinates(coords, title);
    saveRecentSearch({
      id: `coord-${coords[0].toFixed(4)}-${coords[1].toFixed(4)}`,
      type: "coord",
      title: title,
      subtitle: "Toạ độ GPS thủ công",
      payload: coords,
    });
    if (onSetUserLocation) {
      onSetUserLocation(coords, title, "search");
    }
  };

  const handleTriggerAiSearch = (text: string) => {
    setIsOpen(false);
    saveRecentSearch({
      id: `ai-${text.slice(0, 30)}`,
      type: "ai",
      title: text,
      subtitle: "Câu hỏi AI Assistant",
      payload: text,
    });
    onAskAiWithQuery(text);
  };

  const handleSelectRecentItem = (item: RecentSearchItem) => {
    if (item.type === "poi" && item.payload) {
      handleSelectPoiItem(item.payload, false);
    } else if (item.type === "station" && item.payload) {
      handleSelectStationItem(item.payload, false);
    } else if (item.type === "coord" && item.payload) {
      handleSelectCustomCoordinates(item.payload);
    } else if (item.type === "ai") {
      handleTriggerAiSearch(item.payload || item.title);
    } else {
      setQuery(item.title);
    }
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

  // 6 top featured POIs for quick discovery
  const featuredPois = useMemo(() => {
    return OCEAN_PARK_POIS.slice(0, 6);
  }, []);

  return (
    <div className="search-omnibox-container" ref={wrapperRef}>
      <div className={`search-omnibox-bar ${isOpen ? "focused" : ""}`}>
        <Search className="search-icon-prefix" size={18} />
        <input
          ref={inputRef}
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
              } else if (matchedStations.length > 0) {
                handleSelectStationItem(matchedStations[0], true);
              } else if (query.trim().length > 0) {
                handleTriggerAiSearch(query.trim());
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
              inputRef.current?.focus();
            }}
            aria-label="Xóa tìm kiếm"
          >
            <X size={15} />
          </button>
        )}
      </div>

      {/* Instant Dropdown Suggestions & Discovery Hub */}
      {isOpen && (
        <div className="search-dropdown-menu">
          {/* ========================================================================= */}
          {/* MODE 1: DEFAULT DISCOVERY HUB (When query is empty)                       */}
          {/* ========================================================================= */}
          {normalizedQuery === "" && (
            <div className="search-discovery-hub">
              {/* Quick Actions Bar */}
              <section className="search-section search-quick-actions-section" aria-label="Thao tác vị trí nhanh">
                <div className="search-section-header">
                  <span className="search-section-title">Vị trí & Điều hướng</span>
                </div>
                <div className="search-quick-actions-bar">
                  <button
                    type="button"
                    className="search-quick-btn"
                    onClick={handleQuickGps}
                    disabled={!onLocateGps}
                    aria-label="Dùng vị trí hiện tại bằng GPS"
                  >
                    <LocateFixed size={16} className="btn-icon-gps" aria-hidden="true" />
                    <span>Dùng vị trí hiện tại</span>
                  </button>
                  <button
                    type="button"
                    className="search-quick-btn"
                    onClick={handleQuickPickOnMap}
                    disabled={!onStartPickOnMap}
                    aria-label="Chọn vị trí trên bản đồ"
                  >
                    <Crosshair size={16} className="btn-icon-pick" aria-hidden="true" />
                    <span>Chọn trên bản đồ</span>
                  </button>
                </div>
              </section>

              {/* Recent Searches (if available) */}
              {recentSearches.length > 0 && (
                <section className="search-section search-recent-section" aria-label="Tìm kiếm gần đây">
                  <div className="search-section-header">
                    <div className="search-section-title-wrapper">
                      <Clock size={13} className="section-icon text-muted" />
                      <span className="search-section-title">Tìm kiếm gần đây</span>
                    </div>
                    <button
                      type="button"
                      className="search-section-action-btn"
                      onClick={handleClearRecentSearches}
                      title="Xóa toàn bộ lịch sử tìm kiếm"
                    >
                      <Trash2 size={12} />
                      <span>Xóa lịch sử</span>
                    </button>
                  </div>
                  <div className="search-recent-list">
                    {recentSearches.map((item) => (
                      <div
                        key={item.id}
                        className="search-recent-item"
                        onClick={() => handleSelectRecentItem(item)}
                      >
                        <div className="recent-item-icon">
                          {item.type === "station" ? (
                            <Radio size={14} className="icon-station" />
                          ) : item.type === "poi" ? (
                            <MapPin size={14} className="icon-poi" />
                          ) : item.type === "ai" ? (
                            <Sparkles size={14} className="icon-ai" />
                          ) : (
                            <Compass size={14} className="icon-coord" />
                          )}
                        </div>
                        <div className="recent-item-info">
                          <div className="recent-item-title">{item.title}</div>
                          {item.subtitle && <div className="recent-item-sub">{item.subtitle}</div>}
                        </div>
                        <button
                          type="button"
                          className="recent-item-delete-btn"
                          onClick={(e) => handleRemoveRecentSearchItem(item.id, e)}
                          title="Xóa mục này"
                          aria-label="Xóa mục lịch sử"
                        >
                          <X size={12} />
                        </button>
                      </div>
                    ))}
                  </div>
                </section>
              )}

              {/* 5 Air Quality Stations (Real-time monitoring stations) */}
              <section className="search-section" aria-label="Trạm cảm biến quan trắc">
                <div className="search-section-header">
                  <div className="search-section-title-wrapper">
                    <Radio size={13} className="section-icon text-emerald" />
                    <span className="search-section-title">Trạm quan trắc không khí</span>
                  </div>
                  <span className="search-section-badge badge-live">5 trạm trực tiếp</span>
                </div>
                <div className="search-stations-list">
                  {stations.map((st) => {
                    const aqiColor = getAqiColorHex(st.aqi);
                    const aqiLevel = getAqiLevel(st.aqi);
                    const isOffline = st.status === "offline";

                    return (
                      <div
                        key={st.station_id}
                        className="search-station-card"
                        onClick={() => handleSelectStationItem(st, false)}
                      >
                        <div className="station-card-left">
                          <div
                            className="station-status-indicator"
                            style={{ backgroundColor: isOffline ? "#94a3b8" : aqiColor }}
                          />
                          <div className="station-card-info">
                            <div className="station-card-name">
                              {st.station_name}
                              <span className="station-id-tag">{st.station_id}</span>
                            </div>
                            <div className="station-card-metrics">
                              <span>PM2.5: <strong>{st.pm25 !== null && st.pm25 !== undefined ? `${st.pm25} µg/m³` : "—"}</strong></span>
                              {st.temperature !== undefined && st.temperature !== null && (
                                <span className="metric-sep">• {st.temperature}°C</span>
                              )}
                              <span className="metric-status">
                                • {isOffline ? "Ngoại tuyến" : "Trực tuyến"}
                              </span>
                            </div>
                          </div>
                        </div>

                        <div className="station-card-right">
                          <div
                            className="station-aqi-pill"
                            style={{
                              backgroundColor: `${aqiColor}18`,
                              borderColor: aqiColor,
                              color: isOffline ? "#64748b" : aqiColor,
                            }}
                          >
                            <span className="aqi-num">AQI {st.aqi ?? "—"}</span>
                            <span className="aqi-label">{isOffline ? "Offline" : (aqiLevel?.shortLabel || "—")}</span>
                          </div>
                          {onSetUserLocation && (
                            <button
                              type="button"
                              className="item-set-location-btn"
                              title="Đặt vị trí của bạn tại trạm này"
                              onClick={(e) => {
                                e.stopPropagation();
                                handleSelectStationItem(st, true);
                              }}
                            >
                              <MapPin size={11} />
                              <span>Đặt vị trí</span>
                            </button>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </section>

              {/* Popular POIs of Vinhomes Ocean Park 1 */}
              <section className="search-section" aria-label="Địa điểm nổi bật">
                <div className="search-section-header">
                  <div className="search-section-title-wrapper">
                    <Compass size={13} className="section-icon text-blue" />
                    <span className="search-section-title">Địa điểm nổi bật (Ocean Park 1)</span>
                  </div>
                  <span className="search-section-badge">Tiện ích KĐT</span>
                </div>
                <div className="search-poi-grid">
                  {featuredPois.map((poi) => (
                    <div
                      key={poi.id}
                      className="search-poi-card"
                      onClick={() => handleSelectPoiItem(poi, false)}
                    >
                      <div className="poi-card-icon-wrapper">
                        {getPoiIcon(poi.iconName)}
                      </div>
                      <div className="poi-card-details">
                        <div className="poi-card-name" title={poi.name}>{poi.name}</div>
                        <div className="poi-card-sub">{poi.subdivision || "Ocean Park 1"}</div>
                      </div>
                      <ChevronRight size={14} className="poi-card-arrow" />
                    </div>
                  ))}
                </div>
              </section>

              {/* Smart AI Prompt Suggestions */}
              <section className="search-section search-ai-prompts-section" aria-label="Gợi ý hỏi AI">
                <div className="search-section-header">
                  <div className="search-section-title-wrapper">
                    <Sparkles size={13} className="section-icon text-purple" />
                    <span className="search-section-title">Gợi ý hỏi Trợ lý AI</span>
                  </div>
                  <span className="search-section-badge badge-ai">AirGuard AI</span>
                </div>
                <div className="search-ai-prompts-list">
                  {AI_SUGGESTED_PROMPTS.map((prompt) => (
                    <button
                      key={prompt.id}
                      type="button"
                      className="search-ai-prompt-card"
                      onClick={() => handleTriggerAiSearch(prompt.query)}
                    >
                      <div className="ai-prompt-icon-wrap">
                        <Sparkles size={14} />
                      </div>
                      <div className="ai-prompt-content">
                        <div className="ai-prompt-header">
                          <span className="ai-prompt-badge">{prompt.badge}</span>
                          <span className="ai-prompt-title">{prompt.title}</span>
                        </div>
                        <div className="ai-prompt-preview">{prompt.query}</div>
                      </div>
                      <ArrowUpRight size={15} className="ai-prompt-arrow" />
                    </button>
                  ))}
                </div>
              </section>
            </div>
          )}

          {/* ========================================================================= */}
          {/* MODE 2: ACTIVE SEARCH RESULTS (When query is typed)                       */}
          {/* ========================================================================= */}
          {normalizedQuery !== "" && (
            <div className="search-results-container">
              {/* Coordinate input detected match */}
              {parsedCoords && (
                <button
                  type="button"
                  className="search-dropdown-coord-item"
                  onClick={() => handleSelectCustomCoordinates(parsedCoords)}
                  aria-label={`Đặt vị trí tại toạ độ ${parsedCoords[0].toFixed(5)}, ${parsedCoords[1].toFixed(5)}`}
                >
                  <Compass size={18} className="coord-icon" />
                  <div className="coord-text">
                    <strong>Đặt vị trí tại toạ độ: {parsedCoords[0].toFixed(5)}, {parsedCoords[1].toFixed(5)}</strong>
                    <span>Nhấn để ghim vị trí và di chuyển bản đồ đến điểm này</span>
                  </div>
                  <ChevronRight size={16} className="item-arrow" />
                </button>
              )}

              {/* Station Matches */}
              {matchedStations.length > 0 && (
                <div className="search-group">
                  <div className="search-group-title">
                    <span>Trạm cảm biến quan trắc ({matchedStations.length})</span>
                  </div>
                  {matchedStations.map((station) => {
                    const aqiColor = getAqiColorHex(station.aqi);
                    const aqiLevel = getAqiLevel(station.aqi);
                    const isOffline = station.status === "offline";

                    return (
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
                          <div className="item-sub">
                            PM2.5: {station.pm25 !== null && station.pm25 !== undefined ? `${station.pm25} µg/m³` : "—"} • {station.location_type || "Trạm đo"}
                          </div>
                        </div>
                        <span
                          className="item-aqi-chip"
                          style={{
                            backgroundColor: `${aqiColor}18`,
                            borderColor: aqiColor,
                            color: isOffline ? "#64748b" : aqiColor,
                            borderWidth: 1,
                            borderStyle: "solid",
                          }}
                        >
                          AQI {station.aqi ?? "—"} • {isOffline ? "Offline" : (aqiLevel?.shortLabel || "")}
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
                            <MapPin size={11} />
                            <span>Đặt vị trí</span>
                          </button>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}

              {/* POI Matches */}
              {matchedPois.length > 0 && (
                <div className="search-group">
                  <div className="search-group-title">
                    <span>Địa điểm Ocean Park 1 ({matchedPois.length})</span>
                  </div>
                  {matchedPois.slice(0, 8).map((poi) => (
                    <div
                      key={poi.id}
                      className="search-result-item"
                      onClick={() => handleSelectPoiItem(poi, false)}
                    >
                      <div className="poi-icon-small">
                        {getPoiIcon(poi.iconName)}
                      </div>
                      <div className="item-details">
                        <div className="item-name">{poi.name}</div>
                        <div className="item-sub">{poi.subdivision || poi.category}</div>
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
                          <MapPin size={11} />
                          <span>Đặt vị trí</span>
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              )}

              {/* AI Quick Query Card */}
              <button
                type="button"
                className="search-dropdown-ai-item"
                onClick={() => handleTriggerAiSearch(query)}
                aria-label={`Hỏi AirGuard AI: ${query}`}
              >
                <div className="ai-item-icon">
                  <Sparkles size={16} />
                </div>
                <div className="ai-item-text">
                  <strong>Hỏi AirGuard AI: &ldquo;{query}&rdquo;</strong>
                  <span>Phân tích không khí theo thời gian thực & tư vấn sức khoẻ</span>
                </div>
                <ChevronRight size={16} className="item-arrow" />
              </button>

              {/* Fallback Empty State */}
              {!parsedCoords && matchedPois.length === 0 && matchedStations.length === 0 && (
                <button
                  type="button"
                  className="search-empty-state"
                  onClick={() => handleTriggerAiSearch(query)}
                  aria-label={`Không tìm thấy kết quả. Hỏi AirGuard AI: ${query}`}
                >
                  <Sparkles size={22} className="empty-ai-icon" />
                  <div className="empty-state-title">Không tìm thấy địa điểm khớp chính xác</div>
                  <div className="empty-state-desc">
                    Nhấn vào đây để hỏi <strong>AirGuard AI</strong> tìm kiếm và phân tích thông minh cho &ldquo;{query}&rdquo;.
                  </div>
                </button>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
