import React from "react";

interface AuthLayoutProps {
  children: React.ReactNode;
  title?: string;
  description?: string;
}

export const AuthLayout: React.FC<AuthLayoutProps> = ({ children }) => (
  <main className="auth-layout" aria-label="Màn hình xác thực AirGuard AI">
    <div className="auth-centered-container">
      {children}
    </div>
  </main>
);


