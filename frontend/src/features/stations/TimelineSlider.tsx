import React from "react";
import { Clock, RefreshCw } from "lucide-react";

export interface HorizonStepOption {
  hours: number;
  label: string;
}

/** Labels stay sparse while the range exposes every hourly forecast step. */
export const ALL_HORIZON_STEPS: HorizonStepOption[] = [
  { hours: 0, label: "Hiện tại" },
  { hours: 6, label: "+6h" },
  { hours: 12, label: "+12h" },
  { hours: 18, label: "+18h" },
  { hours: 24, label: "+24h" },
];

export interface TimelineSliderProps {
  value: number;
  onChange: (hours: number) => void;
  loading?: boolean;
  disabled?: boolean;
  className?: string;
  label?: string;
  titleProps?: any;
}

export const TimelineSlider: React.FC<TimelineSliderProps> = ({
  value,
  onChange,
  loading = false,
  disabled = false,
  className = "",
  label = "Thời gian dự báo",
  titleProps,
}) => {
  const currentHour = Math.max(0, Math.min(24, Math.round(value)));
  const isDisabled = disabled || loading;

  return (
    <div className={`timeline-slider-card ${className}`} role="group" aria-label="Thanh trượt mốc thời gian dự báo">
      <div className="timeline-slider-header">
        <div className="timeline-slider-title" {...titleProps}>
          <Clock size={15} aria-hidden="true" />
          <span>{label}</span>
        </div>
        <div className="timeline-slider-current-value">
          {loading && <RefreshCw size={13} className="spin-icon" aria-label="Đang tải" />}
          <span>{currentHour === 0 ? "Hiện tại (0h)" : `Dự báo +${currentHour}h`}</span>
        </div>
      </div>

      <div className="timeline-slider-control">
        <div className="timeline-slider-track-wrap">
          <div className="timeline-slider-ticks" aria-hidden="true">
            {ALL_HORIZON_STEPS.map((step) => (
              <span
                key={step.hours}
                style={{ left: `${(step.hours / 24) * 100}%` }}
              />
            ))}
          </div>
          <input
            className="timeline-slider-input"
            type="range"
            min={0}
            max={24}
            step={1}
            value={currentHour}
            disabled={isDisabled}
            aria-label={label}
            aria-valuetext={currentHour === 0 ? "Dữ liệu hiện tại" : `Dự báo +${currentHour}h`}
            onChange={(event) => onChange(Number(event.target.value))}
          />
        </div>
        <div className="timeline-slider-labels">
          {ALL_HORIZON_STEPS.map((step) => (
            <button
              type="button"
              key={step.hours}
              className={`timeline-slider-mark${step.hours === currentHour ? " is-active" : ""}`}
              disabled={isDisabled}
              onClick={() => onChange(step.hours)}
              title={`Chuyển sang mốc ${step.label}`}
              aria-pressed={step.hours === currentHour}
              style={{ left: `${(step.hours / 24) * 100}%` }}
            >
              <span>{step.label}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};
