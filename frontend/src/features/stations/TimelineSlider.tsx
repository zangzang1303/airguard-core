import React from "react";
import { Clock, RefreshCw } from "lucide-react";

export interface HorizonStepOption {
  hours: number;
  label: string;
}

/** The product timeline has five discrete positions, not five linear hours. */
export const ALL_HORIZON_STEPS: HorizonStepOption[] = [
  { hours: 0, label: "Hiện tại" },
  { hours: 1, label: "+1h" },
  { hours: 3, label: "+3h" },
  { hours: 6, label: "+6h" },
  { hours: 24, label: "+24h" },
];

export interface TimelineSliderProps {
  value: number;
  onChange: (hours: number) => void;
  loading?: boolean;
  disabled?: boolean;
  className?: string;
  label?: string;
}

function getStepIndex(hours: number): number {
  const exactIndex = ALL_HORIZON_STEPS.findIndex((step) => step.hours === hours);
  if (exactIndex >= 0) return exactIndex;

  // Keep the control usable if an older caller still holds the removed +2h value.
  return ALL_HORIZON_STEPS.reduce((closestIndex, step, index) => {
    const closestDistance = Math.abs(ALL_HORIZON_STEPS[closestIndex].hours - hours);
    const distance = Math.abs(step.hours - hours);
    return distance < closestDistance ? index : closestIndex;
  }, 0);
}

export const TimelineSlider: React.FC<TimelineSliderProps> = ({
  value,
  onChange,
  loading = false,
  disabled = false,
  className = "",
  label = "Thời gian dự báo",
}) => {
  const stepIndex = getStepIndex(value);
  const currentStep = ALL_HORIZON_STEPS[stepIndex];
  const isDisabled = disabled || loading;

  return (
    <div className={`timeline-slider-card ${className}`} role="group" aria-label="Thanh trượt mốc thời gian dự báo">
      <div className="timeline-slider-header">
        <div className="timeline-slider-title">
          <Clock size={15} aria-hidden="true" />
          <span>{label}</span>
        </div>
        <div className="timeline-slider-current-value">
          {loading && <RefreshCw size={13} className="spin-icon" aria-label="Đang tải" />}
          <span>{currentStep.hours === 0 ? "Hiện tại (0h)" : `Dự báo ${currentStep.label}`}</span>
        </div>
      </div>

      <div className="timeline-slider-control">
        <div className="timeline-slider-track-wrap">
          <div className="timeline-slider-ticks" aria-hidden="true">
            {ALL_HORIZON_STEPS.map((step, index) => (
              <span
                key={step.hours}
                style={{ left: `${(index / (ALL_HORIZON_STEPS.length - 1)) * 100}%` }}
              />
            ))}
          </div>
          <input
            className="timeline-slider-input"
            type="range"
            min={0}
            max={ALL_HORIZON_STEPS.length - 1}
            step={1}
            value={stepIndex}
            disabled={isDisabled}
            aria-label={label}
            aria-valuetext={currentStep.hours === 0 ? "Dữ liệu hiện tại" : `Dự báo ${currentStep.label}`}
            onChange={(event) => {
              const nextStep = ALL_HORIZON_STEPS[Number(event.target.value)];
              if (nextStep) onChange(nextStep.hours);
            }}
          />
        </div>
        <div className="timeline-slider-labels">
          {ALL_HORIZON_STEPS.map((step, index) => (
            <button
              type="button"
              key={step.hours}
              className={`timeline-slider-mark${index === stepIndex ? " is-active" : ""}`}
              disabled={isDisabled}
              onClick={() => onChange(step.hours)}
              title={`Chuyển sang mốc ${step.label}`}
              aria-pressed={index === stepIndex}
              style={{ left: `${(index / (ALL_HORIZON_STEPS.length - 1)) * 100}%` }}
            >
              <span>{step.label}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};
