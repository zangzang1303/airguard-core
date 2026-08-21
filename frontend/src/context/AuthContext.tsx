import React, { createContext, ReactNode, useContext, useEffect, useState } from "react";
import { UserGroup, UserRole } from "../types";
import { api } from "../api/client";
import { formatAuthError } from "../utils/authErrors";

export type ScreenType =
  | "dashboard"
  | "admin-users"
  | "admin-regions"
  | "admin-devices"
  | "admin-settings"
  | "station-detail"
  | "agent"
  | "alerts"
  | "approvals"
  | "audit"
  | "profile"
  | "login"
  | "register"
  | "verify-email"
  | "forgot-password"
  | "reset-password";

export interface AuthUser {
  userId: string;
  email: string;
  name: string;
  role: UserRole;
  userGroup: UserGroup;
  organization: string;
  emailVerified: boolean;
}

export interface RegisterResidentInput {
  name: string;
  email: string;
  password: string;
  userGroup: UserGroup;
}

interface AuthResult {
  success: boolean;
  message?: string;
}

interface AuthContextType {
  currentScreen: ScreenType;
  setCurrentScreen: (screen: ScreenType) => void;
  isAuthenticated: boolean;
  isLoading: boolean;
  authMessage: string | null;
  setAuthMessage: (msg: string | null) => void;
  clearAuthMessage: () => void;
  demoMode: boolean;
  googleAuthEnabled: boolean;
  login: (email: string, password: string) => Promise<AuthResult>;
  demoLogin: (persona: "resident" | "manager" | "admin") => Promise<AuthResult>;
  logout: () => Promise<void>;
  registerResident: (input: RegisterResidentInput) => Promise<AuthResult>;
  verifyEmail: (token: string) => Promise<AuthResult>;
  resendVerification: (email: string) => Promise<AuthResult>;
  forgotPassword: (email: string) => Promise<AuthResult>;
  resetPassword: (token: string, newPassword: string) => Promise<AuthResult>;
  selectedStationId: string;
  setSelectedStationId: (id: string) => void;
  role: UserRole;
  userGroup: UserGroup;
  setUserGroup: (group: UserGroup) => void;
  userName: string;
  setUserName: (name: string) => void;
  userEmail: string;
  userId: string;
  organization: string;
  pendingApprovalsCount: number;
  setPendingApprovalsCount: React.Dispatch<React.SetStateAction<number>>;
  navigateTo: (screen: ScreenType, params?: { stationId?: string }) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [currentScreen, setCurrentScreen] = useState<ScreenType>("dashboard");
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [authMessage, setAuthMessage] = useState<string | null>(null);
  const [demoMode, setDemoMode] = useState(true);
  const [googleAuthEnabled, setGoogleAuthEnabled] = useState(false);
  const [selectedStationId, setSelectedStationId] = useState("S01");
  const [role, setRole] = useState<UserRole>("resident");
  const [userGroup, setUserGroup] = useState<UserGroup>("normal");
  const [userName, setUserName] = useState("Cư dân AirGuard");
  const [userEmail, setUserEmail] = useState("");
  const [userId, setUserId] = useState("");
  const [organization, setOrganization] = useState("Vinhomes Ocean Park 1");
  const [pendingApprovalsCount, setPendingApprovalsCount] = useState(0);

  // Auto-dismiss auth message after 4s
  useEffect(() => {
    if (!authMessage) return;
    const timer = setTimeout(() => {
      setAuthMessage(null);
    }, 4000);
    return () => clearTimeout(timer);
  }, [authMessage]);

  const applyUser = (user: any) => {
    setRole(user.role as UserRole);
    setUserGroup((user.sensitivity_group as UserGroup) || "normal");
    setUserName(user.full_name || user.name || "Cư dân");
    setUserEmail(user.email);
    setUserId(user.user_id || user.userId);
    setOrganization(
      user.role === "admin"
        ? "AirGuard Operations"
        : user.role === "manager"
        ? "Ban Quản lý Khu đô thị"
        : "Vinhomes Ocean Park 1"
    );
    setIsAuthenticated(true);
  };

  // Check existing session & load config on mount
  useEffect(() => {
    let mounted = true;
    const checkSessionAndConfig = async () => {
      try {
        const config = await api.getAuthConfig().catch(() => ({ demo_mode: true, google_auth_enabled: false }));
        if (mounted) {
          setDemoMode(config.demo_mode);
          setGoogleAuthEnabled(config.google_auth_enabled);
        }

        // Check Google OAuth URL parameters
        const urlParams = new URLSearchParams(window.location.search);
        const authStatus = urlParams.get("auth");
        if (authStatus === "google_success") {
          window.history.replaceState({}, document.title, window.location.pathname);
          const data = await api.getMe();
          if (mounted && data.user) {
            applyUser(data.user);
            setAuthMessage("Đăng nhập bằng tài khoản Google thành công!");
          }
          return;
        } else if (authStatus === "google_error") {
          const errorReason = urlParams.get("error");
          window.history.replaceState({}, document.title, window.location.pathname);
          if (mounted) {
            if (errorReason === "not_configured") {
              setAuthMessage("Đăng nhập Google hiện chưa khả dụng.");
            } else {
              setAuthMessage("Đăng nhập bằng Google không thành công hoặc đã bị hủy.");
            }
          }
        }

        const data = await api.getMe();
        if (mounted && data.user) {
          applyUser(data.user);
        }
      } catch {
        if (mounted) {
          setIsAuthenticated(false);
        }
      } finally {
        if (mounted) {
          setIsLoading(false);
        }
      }
    };
    checkSessionAndConfig();
    return () => {
      mounted = false;
    };
  }, []);

  const login = async (email: string, password: string): Promise<AuthResult> => {
    try {
      await api.login({ email, password });
      const meData = await api.getMe();
      if (meData.user) {
        applyUser(meData.user);
        setAuthMessage(null);
        setCurrentScreen("dashboard");
        window.scrollTo({ top: 0, left: 0, behavior: "auto" });
        return { success: true, message: `Đăng nhập thành công.` };
      }
      return { success: false, message: "Đăng nhập không thành công." };
    } catch (err: any) {
      return {
        success: false,
        message: formatAuthError(err),
      };
    }
  };

  const demoLogin = async (persona: "resident" | "manager" | "admin"): Promise<AuthResult> => {
    try {
      await api.demoLogin(persona);
      const meData = await api.getMe();
      if (meData.user) {
        applyUser(meData.user);
        setAuthMessage(null);
        setCurrentScreen("dashboard");
        window.scrollTo({ top: 0, left: 0, behavior: "auto" });
        return { success: true, message: `Đăng nhập thành công với vai trò ${meData.user.role}.` };
      }
      return { success: false, message: "Đăng nhập demo không thành công." };
    } catch (err: any) {
      return {
        success: false,
        message: formatAuthError(err),
      };
    }
  };

  const logout = async () => {
    try {
      await api.logout();
    } catch (err) {
      console.warn("Logout error:", err);
    }
    setIsAuthenticated(false);
    setRole("resident");
    setUserGroup("normal");
    setUserName("Cư dân AirGuard");
    setUserEmail("");
    setUserId("");
    setAuthMessage("Bạn đã đăng xuất.");
    setCurrentScreen("login");
    window.scrollTo({ top: 0, left: 0, behavior: "auto" });
  };

  const registerResident = async (input: RegisterResidentInput): Promise<AuthResult> => {
    try {
      const data = await api.register({
        email: input.email,
        password: input.password,
        full_name: input.name,
        sensitivity_group: input.userGroup,
      });
      setAuthMessage(data.message || "Đăng ký thành công! Vui lòng kiểm tra email để kích hoạt tài khoản.");
      setCurrentScreen("login");
      window.scrollTo({ top: 0, left: 0, behavior: "auto" });
      return { success: true, message: data.message };
    } catch (err: any) {
      return {
        success: false,
        message: formatAuthError(err),
      };
    }
  };

  const verifyEmail = async (token: string): Promise<AuthResult> => {
    try {
      const data = await api.verifyEmail(token);
      return { success: true, message: data.message };
    } catch (err: any) {
      return { success: false, message: err?.message || "Xác minh email không thành công." };
    }
  };

  const resendVerification = async (email: string): Promise<AuthResult> => {
    try {
      const data = await api.resendVerification(email);
      return { success: true, message: data.message };
    } catch (err: any) {
      return { success: false, message: err?.message || "Gửi lại email xác minh không thành công." };
    }
  };

  const forgotPassword = async (email: string): Promise<AuthResult> => {
    try {
      const data = await api.forgotPassword(email);
      return { success: true, message: data.message };
    } catch (err: any) {
      return { success: false, message: err?.message || "Yêu cầu đặt lại mật khẩu thất bại." };
    }
  };

  const resetPassword = async (token: string, newPassword: string): Promise<AuthResult> => {
    try {
      const data = await api.resetPassword(token, newPassword);
      return { success: true, message: data.message };
    } catch (err: any) {
      return { success: false, message: err?.message || "Đặt lại mật khẩu không thành công." };
    }
  };

  const navigateTo = (screen: ScreenType, params?: { stationId?: string }) => {
    const publicScreens: ScreenType[] = ["login", "register", "verify-email", "forgot-password", "reset-password", "dashboard", "station-detail", "alerts"];
    if (!isAuthenticated && !publicScreens.includes(screen)) {
      setCurrentScreen("login");
      return;
    }
    if (params?.stationId) setSelectedStationId(params.stationId);
    setCurrentScreen(screen);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  return (
    <AuthContext.Provider
      value={{
        currentScreen,
        setCurrentScreen,
        isAuthenticated,
        isLoading,
        authMessage,
        setAuthMessage,
        clearAuthMessage: () => setAuthMessage(null),
        demoMode,
        googleAuthEnabled,
        login,
        demoLogin,
        logout,
        registerResident,
        verifyEmail,
        resendVerification,
        forgotPassword,
        resetPassword,
        selectedStationId,
        setSelectedStationId,
        role,
        userGroup,
        setUserGroup,
        userName,
        setUserName,
        userEmail,
        userId,
        organization,
        pendingApprovalsCount,
        setPendingApprovalsCount,
        navigateTo,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used within an AuthProvider");
  return context;
};
