import React, { useState } from "react";
import { X, Send, MapPin, AlertCircle, Camera, CheckCircle2 } from "lucide-react";
import { CommunityReport } from "../../types/superApp";

interface CommunityReportModalProps {
  onClose: () => void;
  onSubmitReport: (report: Partial<CommunityReport>) => void;
}

export const CommunityReportModal: React.FC<CommunityReportModalProps> = ({
  onClose,
  onSubmitReport,
}) => {
  const [category, setCategory] = useState<CommunityReport["category"]>("dust");
  const [description, setDescription] = useState("");
  const [address, setAddress] = useState("Gần cụm Sapphire 2, Vinhomes Ocean Park 1");
  const [isSubmitted, setIsSubmitted] = useState(false);

  const CATEGORIES = [
    { id: "dust", label: "Bụi mịn / Công trình", emoji: "💨" },
    { id: "smoke", label: "Khói đốt / Rác thải", emoji: "🔥" },
    { id: "bad_smell", label: "Mùi khó chịu / Cống", emoji: "🦨" },
    { id: "noise", label: "Tiếng ồn bất thường", emoji: "🔊" },
    { id: "other", label: "Vấn đề môi trường khác", emoji: "⚠️" },
  ];

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!description.trim()) return;

    onSubmitReport({
      category,
      description,
      address,
      latitude: 20.9975,
      longitude: 105.9430,
      createdAt: new Date().toISOString(),
      status: "pending",
    });

    setIsSubmitted(true);
    setTimeout(() => {
      onClose();
    }, 1200);
  };

  return (
    <div className="modal-backdrop-overlay" onClick={onClose}>
      <div className="modal-card-dialog report-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header-row">
          <div className="modal-title-wrap">
            <AlertCircle size={18} className="modal-alert-icon" />
            <h3 className="modal-title">Phản ánh vấn đề Môi trường</h3>
          </div>
          <button className="modal-close-btn" onClick={onClose} aria-label="Đóng">
            <X size={18} />
          </button>
        </div>

        {isSubmitted ? (
          <div className="report-success-view">
            <CheckCircle2 size={42} className="success-icon" />
            <h4>Cảm ơn bạn đã phản ánh!</h4>
            <p>Ban Quản Lý Ocean Park 1 và hệ thống quan trắc AI đã ghi nhận tọa độ và sẽ kiểm tra trong 15 phút tới.</p>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="report-form-body">
            <div className="form-group">
              <label className="form-label">Loại sự cố môi trường:</label>
              <div className="category-chips-grid">
                {CATEGORIES.map((cat) => (
                  <button
                    key={cat.id}
                    type="button"
                    className={`cat-chip-btn ${category === cat.id ? "active" : ""}`}
                    onClick={() => setCategory(cat.id as CommunityReport["category"])}
                  >
                    <span>{cat.emoji}</span>
                    <span>{cat.label}</span>
                  </button>
                ))}
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">Vị trí ghi nhận:</label>
              <div className="location-picker-input-wrap">
                <MapPin size={16} className="loc-icon" />
                <input
                  type="text"
                  className="form-text-input"
                  value={address}
                  onChange={(e) => setAddress(e.target.value)}
                  placeholder="Nhập địa chỉ hoặc vị trí..."
                />
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">Mô tả chi tiết:</label>
              <textarea
                className="form-textarea"
                rows={3}
                placeholder="Mô tả mức độ khói bụi, tiếng ồn hoặc mùi lạ bạn đang cảm nhận..."
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                required
              />
            </div>

            <div className="modal-footer-actions">
              <button type="button" className="action-pill-btn secondary" onClick={onClose}>
                Hủy bỏ
              </button>
              <button type="submit" className="action-pill-btn primary" disabled={!description.trim()}>
                <Send size={15} />
                <span>Gửi phản ánh</span>
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};
