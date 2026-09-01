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
  onManualControl: (action: "ventilation_boost" | "standby") => Promise<void>;
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

const modeLabels: Record<VentilationDevice["operating_mode"], string> = {
  RUNNING_BOOST: "Đang lọc không khí tăng cường",
  AIR_PURIFIER_ON: "Đang lọc không khí",
  ECO_MODE: "Chế độ tiết kiệm",
  STANDBY: "Chế độ chờ",
};

const acknowledgementLabel = (status?: string | null) => {
  switch (status) {
    case "succeeded": return "Đã được thiết bị xác nhận";
    case "failed": return "Thiết bị không xác nhận lệnh";
    case "rejected": return "Thiết bị từ chối lệnh";
    case "duplicate": return "Lệnh đã được thiết bị xử lý";
    default: return "Chưa có phản hồi từ thiết bị";
  }
};

export const DeviceDetailDrawer: React.FC<DeviceDetailDrawerProps> = ({
  device,
  loading,
  error,
  onClose,
  onRefresh,
  onManualControl,
}) => {
  const { containerProps, handleProps } = useDraggableFloatingPanel({
    panelId: "device-detail",
    group: "drawer",
  });
  const [now, setNow] = useState(Date.now());
  const [pendingAction, setPendingAction] = useState<"ventilation_boost" | "standby" | null>(null);
  const [awaitingAction, setAwaitingAction] = useState<"ventilation_boost" | "standby" | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  useEffect(() => {
    const timer = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(timer);
  }, []);

  // Tự động kiểm tra trạng thái phản hồi ACK từ thiết bị mô phỏng (chu kỳ 800ms)
  useEffect(() => {
    if (!awaitingAction) return;

    const isTargetReached =
      awaitingAction === "ventilation_boost"
        ? Boolean(device.is_active || device.operating_mode === "RUNNING_BOOST" || device.operating_mode === "AIR_PURIFIER_ON")
        : Boolean(!device.is_active && device.operating_mode === "STANDBY");

    if (isTargetReached) {
      setNotice(
        awaitingAction === "ventilation_boost"
          ? "Thiết bị đã xác nhận lệnh: Đang lọc không khí tăng cường."
          : "Thiết bị đã xác nhận lệnh: Đã chuyển về chế độ chờ."
      );
      setAwaitingAction(null);
      const dismissTimer = window.setTimeout(() => setNotice(null), 4000);
      return () => window.clearTimeout(dismissTimer);
    }

    const pollTimer = window.setInterval(() => {
      void onRefresh();
    }, 800);

    const timeoutTimer = window.setTimeout(() => {
      setAwaitingAction(null);
    }, 10_000);

    return () => {
      window.clearInterval(pollTimer);
      window.clearTimeout(timeoutTimer);
    };
  }, [awaitingAction, device.is_active, device.operating_mode, onRefresh]);

  const remainingSeconds = useMemo(() => {
    if (!device.ends_at || !device.is_active) return 0;
    return Math.max(0, Math.ceil((new Date(device.ends_at).getTime() - now) / 1000));
  }, [device.ends_at, device.is_active, now]);
  const modeLabel = modeLabels[device.operating_mode];
  const effectiveness = device.effectiveness;

  const controlDevice = async (action: "ventilation_boost" | "standby") => {
    if (pendingAction) return;
    setPendingAction(action);
    setNotice(null);
    try {
      await onManualControl(action);
      setAwaitingAction(action);
      setNotice(action === "ventilation_boost" ? "BQL đã gửi lệnh bật máy lọc. Đang chờ thiết bị phản hồi…" : "BQL đã gửi lệnh tắt máy lọc. Đang chờ thiết bị phản hồi…");
      // Thực hiện refresh ngay lần đầu
      void onRefresh();
    } catch (requestError: any) {
      setNotice(requestError?.message || "Không thể gửi lệnh từ trạng thái hiện tại.");
      setAwaitingAction(null);
    } finally {
      setPendingAction(null);
    }
  };

  return (
    <aside {...containerProps} className="contextual-drawer right-drawer device-detail-drawer">
      <div className="drawer-header-bar device-header">
        <div className="drawer-title-group" {...handleProps}>
          <span className="drawer-eyebrow-tag">THIẾT BỊ MÔ PHỎNG · BQL ĐIỀU KHIỂN</span>
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
            <small>Trạng thái thiết bị</small>
            <strong>{modeLabel}</strong>
            <span>{device.is_simulated ? "Dữ liệu mô phỏng cho MVP" : "Nguồn thiết bị chưa xác định"}</span>
          </div>
        </section>

        <div className="device-kpi-grid">
          <article><Gauge size={18} /><span>Công suất</span><strong>{device.intensity_percent ?? 0}%</strong></article>
          <article><Clock3 size={18} /><span>Còn lại</span><strong>{formatCountdown(remainingSeconds)}</strong></article>
          <article><Zap size={18} /><span>Chu kỳ</span><strong>{device.duration_minutes ? `${device.duration_minutes} phút` : "—"}</strong></article>
          <article><Activity size={18} /><span>Nguồn</span><strong>Dữ liệu mô phỏng</strong></article>
        </div>

        <section className="device-detail-section">
          <h3><Leaf size={16} /> Mức cải thiện không khí ghi nhận</h3>
          {effectiveness ? (
            <div className="effectiveness-grid">
              <div><span>PM2.5</span><strong>{effectiveness.baseline_pm25 ?? "—"} → {effectiveness.current_pm25 ?? "—"} µg/m³</strong><em>{effectiveness.pm25_reduction_percent != null ? `Giảm ${effectiveness.pm25_reduction_percent}%` : "Chưa đủ dữ liệu"}</em></div>
              <div><span>CO₂</span><strong>{effectiveness.baseline_co2 ?? "—"} → {effectiveness.current_co2 ?? "—"} ppm</strong><em>{effectiveness.co2_reduction_percent != null ? `Giảm ${effectiveness.co2_reduction_percent}%` : "Chưa đủ dữ liệu"}</em></div>
            </div>
          ) : <p className="device-empty-copy">Chưa có đủ cặp số đo trước/sau ACK để đánh giá.</p>}
        </section>

        <section className="device-detail-section">
          <h3><History size={16} /> Lần vận hành gần nhất</h3>
          <dl className="device-command-history">
            <div><dt>Bắt đầu vận hành</dt><dd>{dateTime(device.started_at)}</dd></div>
            <div><dt>Kết thúc dự kiến</dt><dd>{dateTime(device.ends_at)}</dd></div>
            <div><dt>Người phê duyệt</dt><dd>{device.latest_command?.approved_by_name || (device.latest_command?.approved_by ? "Tài khoản Ban quản lý" : "—")}</dd></div>
            <div><dt>Thời điểm duyệt</dt><dd>{dateTime(device.latest_command?.approved_at)}</dd></div>
            <div><dt>Xác nhận từ thiết bị</dt><dd>{device.latest_command ? acknowledgementLabel(device.latest_command.ack_status) : "Chưa có lệnh"}</dd></div>
          </dl>
        </section>

        {(error || notice) && <div className={`device-action-notice ${error ? "is-error" : ""}`} role="status">{error || notice}</div>}

        <section className="device-hitl-actions">
          <div><ShieldCheck size={17} /><span>Thao tác thủ công của BQL được ghi nhật ký và gửi lệnh ngay cho thiết bị mô phỏng.</span></div>
          {!device.is_active ? <button type="button" disabled={Boolean(pendingAction) || loading} onClick={() => controlDevice("ventilation_boost")} className="device-action-button eco">
            <Wind size={16} /> {pendingAction === "ventilation_boost" ? "Đang bật…" : "Bật máy lọc"}
          </button> : <button type="button" disabled={Boolean(pendingAction) || loading} onClick={() => controlDevice("standby")} className="device-action-button stop">
            <Zap size={16} /> {pendingAction === "standby" ? "Đang tắt…" : "Tắt máy lọc"}
          </button>}
          <button type="button" onClick={onRefresh} className="device-refresh-button">Cập nhật trạng thái</button>
        </section>
      </div>
    </aside>
  );
};
