import React, { useEffect, useMemo, useState } from "react";
import { Activity, Clock3, Gauge, History, Leaf, ShieldCheck, Wind, X, Zap } from "lucide-react";
import { VentilationDevice } from "../../types";
import { useDraggableFloatingPanel } from "../floating";


interface DeviceDetailDrawerProps {
  device: VentilationDevice;
  loading?: boolean;
  error?: string | null;
  onClose: () => void;
  onRefresh: () => Promise<void>;
  onCreateProposal: (action: "eco_mode" | "standby", reason: string) => Promise<void>;
}

const dateTime = (value?: string | null) =>
  value
    ? new Date(value).toLocaleString("vi-VN", {
        hour: "2-digit",
        minute: "2-digit",
        day: "2-digit",
        month: "2-digit",
        year: "numeric",
      })
    : "—";

const formatCountdown = (seconds: number) => {
  const safe = Math.max(0, seconds);
  const minutes = Math.floor(safe / 60);
  const remainder = safe % 60;
  return `${minutes}:${String(remainder).padStart(2, "0")}`;
};

export const DeviceDetailDrawer: React.FC<DeviceDetailDrawerProps> = ({
  device,
  loading,
  error,
  onClose,
  onRefresh,
  onCreateProposal,
}) => {
  const { containerProps, handleProps } = useDraggableFloatingPanel({
    panelId: "device-detail",
    group: "drawer",
  });
  const [now, setNow] = useState(Date.now());
  const [pendingAction, setPendingAction] = useState<"eco_mode" | "standby" | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  useEffect(() => {
    const timer = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(timer);
  }, []);

  const remainingSeconds = useMemo(() => {
    if (!device.ends_at || !device.is_active) return 0;
    return Math.max(0, Math.ceil((new Date(device.ends_at).getTime() - now) / 1000));
  }, [device.ends_at, device.is_active, now]);
  const modeLabel =
    device.operating_mode === "RUNNING_BOOST"
      ? "Running Boost"
      : device.operating_mode === "AIR_PURIFIER_ON"
        ? "Air Purifier On"
        : device.operating_mode === "ECO_MODE"
          ? "Eco Mode"
          : "Standby";
  const effectiveness = device.effectiveness;

  const requestProposal = async (action: "eco_mode" | "standby") => {
    if (pendingAction) return;
    setPendingAction(action);
    setNotice(null);
    try {
      await onCreateProposal(
        action,
        action === "eco_mode"
          ? `Manager requests eco mode for ${device.device_id} after reviewing measured recovery.`
          : `Manager requests an audited safe stop for ${device.device_id}.`,
      );
      setNotice("Đã tạo proposal pending. Thiết bị chỉ đổi trạng thái sau khi BQL phê duyệt.");
    } catch (requestError: any) {
      setNotice(requestError?.message || "Không thể tạo proposal từ trạng thái hiện tại.");
    } finally {
      setPendingAction(null);
    }
  };

  return (
    <aside {...containerProps} className="contextual-drawer right-drawer device-detail-drawer">
      <div className="drawer-header-bar device-header">
        <div className="drawer-title-group" {...handleProps}>
          <span className="drawer-eyebrow-tag">THIẾT BỊ MÔ PHỎNG · HITL</span>
          <h2 className="drawer-main-title">{device.device_name}</h2>
          <p className="drawer-sub-meta">{device.device_id} · {device.station_id} — {device.station_name}</p>
        </div>
        <button className="no-drag drawer-close-btn" data-no-drag="true" onClick={onClose} aria-label="Đóng chi tiết thiết bị">
          <X size={18} />
        </button>
      </div>

      <div className="drawer-scroll-body ventilation-device-body">
        <section className={`device-mode-hero mode-${device.operating_mode.toLowerCase()}`}>
          <span className="device-mode-icon"><Wind size={26} /></span>
          <div>
            <small>Trạng thái đã ACK</small>
            <strong>{modeLabel}</strong>
            <span>{device.is_simulated ? "Device simulator" : "Nguồn thiết bị chưa xác định"}</span>
          </div>
        </section>

        <div className="device-kpi-grid">
          <article><Gauge size={18} /><span>Công suất</span><strong>{device.intensity_percent ?? 0}%</strong></article>
          <article><Clock3 size={18} /><span>Còn lại</span><strong>{formatCountdown(remainingSeconds)}</strong></article>
          <article><Zap size={18} /><span>Chu kỳ</span><strong>{device.duration_minutes ? `${device.duration_minutes} phút` : "—"}</strong></article>
          <article><Activity size={18} /><span>Nguồn</span><strong>Simulator</strong></article>
        </div>

        <section className="device-detail-section">
          <h3><Leaf size={16} /> Hiệu quả môi trường đo được</h3>
          {effectiveness ? (
            <div className="effectiveness-grid">
              <div><span>PM2.5</span><strong>{effectiveness.baseline_pm25 ?? "—"} → {effectiveness.current_pm25 ?? "—"} µg/m³</strong><em>{effectiveness.pm25_reduction_percent != null ? `Giảm ${effectiveness.pm25_reduction_percent}%` : "Chưa đủ dữ liệu"}</em></div>
              <div><span>CO₂</span><strong>{effectiveness.baseline_co2 ?? "—"} → {effectiveness.current_co2 ?? "—"} ppm</strong><em>{effectiveness.co2_reduction_percent != null ? `Giảm ${effectiveness.co2_reduction_percent}%` : "Chưa đủ dữ liệu"}</em></div>
            </div>
          ) : <p className="device-empty-copy">Chưa có đủ cặp số đo trước/sau ACK để đánh giá.</p>}
        </section>

        <section className="device-detail-section">
          <h3><History size={16} /> Lệnh gần nhất</h3>
          <dl className="device-command-history">
            <div><dt>Bắt đầu</dt><dd>{dateTime(device.started_at)}</dd></div>
            <div><dt>Kết thúc dự kiến</dt><dd>{dateTime(device.ends_at)}</dd></div>
            <div><dt>Người duyệt</dt><dd>{device.latest_command?.approved_by || "—"}</dd></div>
            <div><dt>Thời điểm duyệt</dt><dd>{dateTime(device.latest_command?.approved_at)}</dd></div>
            <div><dt>ACK</dt><dd>{device.latest_command?.ack_status || "—"}</dd></div>
          </dl>
        </section>

        {(error || notice) && <div className={`device-action-notice ${error ? "is-error" : ""}`} role="status">{error || notice}</div>}

        <section className="device-hitl-actions">
          <div><ShieldCheck size={17} /><span>Mọi nút dưới đây chỉ tạo proposal pending; không gửi lệnh trực tiếp.</span></div>
          <button type="button" disabled={Boolean(pendingAction) || loading} onClick={() => requestProposal("eco_mode")} className="device-action-button eco">
            <Leaf size={16} /> {pendingAction === "eco_mode" ? "Đang tạo…" : "Đề xuất chuyển Eco Mode"}
          </button>
          <button type="button" disabled={Boolean(pendingAction) || loading} onClick={() => requestProposal("standby")} className="device-action-button stop">
            <Zap size={16} /> {pendingAction === "standby" ? "Đang tạo…" : "Đề xuất dừng khẩn cấp"}
          </button>
          <button type="button" onClick={onRefresh} className="device-refresh-button">Cập nhật trạng thái</button>
        </section>
      </div>
    </aside>
  );
};
