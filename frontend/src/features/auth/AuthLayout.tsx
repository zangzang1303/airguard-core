import React from "react";
import { Activity, Bot, ShieldCheck } from "lucide-react";

interface AuthLayoutProps {
  children: React.ReactNode;
  title: string;
  description: string;
}

export const AuthLayout: React.FC<AuthLayoutProps> = ({ children, title, description }) => (
  <main className="auth-layout">
    <section className="auth-visual" aria-label="Giới thiệu AirGuard AI">
      <div className="auth-visual__orb auth-visual__orb--one" aria-hidden="true" />
      <div className="auth-visual__orb auth-visual__orb--two" aria-hidden="true" />
      <div className="auth-brand">
        <span className="auth-brand__mark"><ShieldCheck size={28} strokeWidth={2.2} aria-hidden="true" /></span>
        <span>
          <strong>AirGuard AI</strong>
          <small>PM2.5 Monitoring Platform</small>
        </span>
      </div>

      <div className="auth-visual__content">
        <span className="auth-visual__eyebrow">Enterprise Environmental Intelligence</span>
        <h1>{title}</h1>
        <p>{description}</p>
        <div className="auth-feature-list">
          <div><Activity size={19} aria-hidden="true" /><span><strong>Quan sát tập trung</strong><small>5 trạm PM2.5 quanh VinUni và Ocean Park</small></span></div>
          <div><Bot size={19} aria-hidden="true" /><span><strong>AI có căn cứ</strong><small>Phân tích từ backend tools, không tự tạo dữ liệu</small></span></div>
          <div><ShieldCheck size={19} aria-hidden="true" /><span><strong>Human-in-the-Loop</strong><small>Phê duyệt và audit minh bạch theo vai trò</small></span></div>
        </div>
      </div>

      <p className="auth-visual__disclaimer">Dữ liệu mô phỏng cho MVP · Không phải quan trắc chính thức</p>
    </section>
    <section className="auth-panel">{children}</section>
  </main>
);

