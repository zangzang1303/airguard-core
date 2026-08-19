import React, { useMemo } from "react";
import { AlertTriangle, Clock3, Radio, ShieldAlert, Wifi, WifiOff } from "lucide-react";

import { Alert, Station } from "../../types";

interface ManagerStationStatusBarProps {
  stations: Station[];
  alerts: Alert[];
}

export const ManagerStationStatusBar: React.FC<ManagerStationStatusBarProps> = ({ stations, alerts }) => {
  const counts = useMemo(() => {
    const activeAlerts = alerts.filter((alert) => alert.status === "active");
    const warningStations = new Set(
      activeAlerts
        .filter((alert) => alert.severity === "warning" || alert.severity === "moderate")
        .map((alert) => alert.station_id),
    );
    const criticalStations = new Set(
      activeAlerts
        .filter((alert) => alert.severity === "critical")
        .map((alert) => alert.station_id),
    );

    return {
      online: stations.filter((station) => station.status === "online" && !station.is_stale).length,
      offline: stations.filter((station) => station.status === "offline").length,
      stale: stations.filter((station) => station.status === "stale" || station.is_stale).length,
      warning: warningStations.size,
      critical: criticalStations.size,
    };
  }, [alerts, stations]);

  return (
    <section className="manager-station-status-bar" aria-label="Tổng quan trạng thái trạm dành cho Ban Quản lý">
      <span className="manager-status-title"><Radio size={14} aria-hidden="true" /> Giám sát trạm</span>
      <span className="manager-status-item is-online"><Wifi size={14} aria-hidden="true" /><b>{counts.online}</b> Online</span>
      <span className="manager-status-item is-offline"><WifiOff size={14} aria-hidden="true" /><b>{counts.offline}</b> Offline</span>
      <span className="manager-status-item is-stale"><Clock3 size={14} aria-hidden="true" /><b>{counts.stale}</b> Stale</span>
      <span className="manager-status-item is-warning"><AlertTriangle size={14} aria-hidden="true" /><b>{counts.warning}</b> Warning</span>
      <span className="manager-status-item is-critical"><ShieldAlert size={14} aria-hidden="true" /><b>{counts.critical}</b> Critical</span>
    </section>
  );
};
