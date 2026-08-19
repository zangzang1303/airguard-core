import React from "react";
import { X, Clock, Play, Pause, ChevronRight } from "lucide-react";
import { ForecastTimeStep } from "../../types/superApp";

interface ForecastSliderBarProps {
  activeStepIndex: number;
  onSelectStepIndex: (idx: number) => void;
  onClose: () => void;
}

export const FORECAST_STEPS: ForecastTimeStep[] = [
  {
    label: "Hiện tại (Now)",
    hourOffset: 0,
    timeString: "17:30",
    heatMultiplier: 1.0,
    aqiMap: { S01: 118, S02: 149, S03: 158, S04: 78, S05: 99 },
  },
  {
    label: "+1 Giờ",
    hourOffset: 1,
    timeString: "18:30 (Cao điểm)",
    heatMultiplier: 1.25,
    aqiMap: { S01: 135, S02: 165, S03: 178, S04: 85, S05: 110 },
  },
  {
    label: "+3 Giờ",
    hourOffset: 3,
    timeString: "20:30 (Hạ nhiệt)",
    heatMultiplier: 0.75,
    aqiMap: { S01: 85, S02: 95, S03: 105, S04: 45, S05: 68 },
  },
  {
    label: "+6 Giờ",
    hourOffset: 6,
    timeString: "23:30 (Đêm)",
    heatMultiplier: 0.5,
    aqiMap: { S01: 42, S02: 48, S03: 52, S04: 28, S05: 38 },
  },
  {
    label: "Sáng mai",
    hourOffset: 12,
    timeString: "06:30 (Bình minh)",
    heatMultiplier: 0.45,
    aqiMap: { S01: 35, S02: 38, S03: 40, S04: 25, S05: 32 },
  },
];

export const ForecastSliderBar: React.FC<ForecastSliderBarProps> = ({
  activeStepIndex,
  onSelectStepIndex,
  onClose,
}) => {
  const currentStep = FORECAST_STEPS[activeStepIndex] || FORECAST_STEPS[0];

  return (
    <div className="forecast-timeline-floating-card">
      <div className="forecast-card-top-row">
        <div className="forecast-title-group">
          <Clock size={16} className="title-icon" />
          <span className="forecast-main-label">Dự báo mô phỏng lan truyền không gian</span>
          <span className="forecast-current-time-pill">{currentStep.timeString}</span>
        </div>
        <button className="forecast-close-btn" onClick={onClose} aria-label="Đóng thanh dự báo">
          <X size={16} />
        </button>
      </div>

      {/* Interactive Time Slider Nodes */}
      <div className="forecast-slider-track-wrap">
        <div className="forecast-nodes-row">
          {FORECAST_STEPS.map((step, idx) => {
            const isActive = idx === activeStepIndex;
            return (
              <button
                key={idx}
                className={`forecast-node-item ${isActive ? "active" : ""}`}
                onClick={() => onSelectStepIndex(idx)}
              >
                <div className="node-marker-dot"></div>
                <span className="node-label">{step.label}</span>
                <span className="node-time">{step.timeString.split(" ")[0]}</span>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
};
