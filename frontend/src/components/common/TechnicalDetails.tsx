import React, { useState } from "react";
import { ChevronDown, Wrench } from "lucide-react";

interface TechnicalDetailsProps {
  tools: string[];
}

export const TechnicalDetails: React.FC<TechnicalDetailsProps> = ({ tools }) => {
  const [open, setOpen] = useState(false);

  if (tools.length === 0) return null;

  return (
    <div className={`technical-details ${open ? "is-open" : ""}`}>
      <button
        type="button"
        className="technical-details__trigger"
        aria-expanded={open}
        onClick={() => setOpen((value) => !value)}
      >
        <Wrench size={14} aria-hidden="true" />
        <span>Xem chi tiết tiến trình AI</span>
        <ChevronDown className="technical-details__chevron" size={14} aria-hidden="true" />
      </button>
      {open && (
        <div className="technical-details__content">
          {tools.map((tool) => <code key={tool}>{tool}</code>)}
        </div>
      )}
    </div>
  );
};

