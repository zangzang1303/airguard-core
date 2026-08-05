import React from "react";
import { RotateCcw, Search } from "lucide-react";
import { Button } from "./Button";

interface AlertFiltersProps {
  search: string;
  status: string;
  severity: string;
  onSearchChange: (value: string) => void;
  onStatusChange: (value: string) => void;
  onSeverityChange: (value: string) => void;
  onReset: () => void;
}

export const AlertFilters: React.FC<AlertFiltersProps> = ({
  search,
  status,
  severity,
  onSearchChange,
  onStatusChange,
  onSeverityChange,
  onReset,
}) => (
  <section className="filter-toolbar" aria-label="Bộ lọc cảnh báo">
    <div className="filter-group filter-group--search">
      <label htmlFor="alert-station-search">Tìm trạm</label>
      <div className="input-with-icon">
        <Search size={17} aria-hidden="true" />
        <input
          id="alert-station-search"
          type="search"
          value={search}
          onChange={(event) => onSearchChange(event.target.value)}
          placeholder="Tên hoặc mã trạm..."
          className="search-input"
        />
      </div>
    </div>
    <div className="filter-group">
      <label htmlFor="alert-status">Trạng thái</label>
      <select id="alert-status" value={status} onChange={(event) => onStatusChange(event.target.value)} className="role-select">
        <option value="all">Tất cả trạng thái</option>
        <option value="active">Đang kích hoạt</option>
        <option value="resolved">Đã xử lý</option>
      </select>
    </div>
    <div className="filter-group">
      <label htmlFor="alert-severity">Mức độ nghiêm trọng</label>
      <select id="alert-severity" value={severity} onChange={(event) => onSeverityChange(event.target.value)} className="role-select">
        <option value="all">Tất cả mức độ</option>
        <option value="moderate">Trung bình</option>
        <option value="warning">Cảnh báo</option>
        <option value="critical">Nghiêm trọng</option>
      </select>
    </div>
    <Button variant="ghost" size="sm" onClick={onReset}>
      <RotateCcw size={16} aria-hidden="true" />
      Đặt lại
    </Button>
  </section>
);

