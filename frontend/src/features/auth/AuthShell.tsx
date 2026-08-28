import React from "react";

interface AuthShellProps {
  children: React.ReactNode;
  className?: string;
}

/**
 * Shared two-column authentication frame. Screen-specific content supplies the
 * main form and optional supporting panel, while this component owns the
 * background, card, border, shadow, and responsive column behavior.
 */
export const AuthShell: React.FC<AuthShellProps> = ({ children, className = "" }) => (
  <main className="auth-layout" aria-label="Màn hình xác thực AirGuard AI">
    <div className={`auth-unified-container ${className}`.trim()}>
      {children}
    </div>
  </main>
);
