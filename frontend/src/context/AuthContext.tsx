import React, { createContext, ReactNode, useContext, useState } from "react";
import { UserGroup, UserRole } from "../types";

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
  | "register";

export interface DemoAccount {
  userId: string;
  email: string;
  name: string;
  role: UserRole;
  userGroup: UserGroup;
  organization: string;
}

interface StoredAccount extends DemoAccount {
  password: string;
}

export interface RegisterResidentInput {
  name: string;
  email: string;
  password: string;
  userGroup: UserGroup;
}

export const DEMO_PASSWORD = "AirGuard@2026";

const DEMO_ACCOUNT_RECORDS: StoredAccount[] = [
  {
    userId: "00000000-0000-0000-0000-000000000101",
    email: "resident@vinuni.edu.vn",
    password: DEMO_PASSWORD,
    name: "Trần Minh Anh",
    role: "resident",
    userGroup: "normal",
    organization: "Vinhomes Ocean Park",
  },
  {
    userId: "00000000-0000-0000-0000-000000000102",
    email: "manager@vinuni.edu.vn",
    password: DEMO_PASSWORD,
    name: "Nguyễn Văn A",
    role: "manager",
    userGroup: "sensitive",
    organization: "VinUniversity",
  },
  {
    userId: "00000000-0000-0000-0000-000000000103",
    email: "admin@vinuni.edu.vn",
    password: DEMO_PASSWORD,
    name: "Lê Thị D",
    role: "admin",
    userGroup: "normal",
    organization: "AirGuard Operations",
  },
];

export const DEMO_ACCOUNTS: DemoAccount[] = DEMO_ACCOUNT_RECORDS.map(({ password: _password, ...account }) => account);

interface AuthResult {
  success: boolean;
  message?: string;
}

interface AuthContextType {
  currentScreen: ScreenType;
  setCurrentScreen: (screen: ScreenType) => void;
  isAuthenticated: boolean;
  authMessage: string | null;
  clearAuthMessage: () => void;
  login: (email: string, password: string) => AuthResult;
  loginAsDemo: (role: UserRole) => void;
  logout: () => void;
  registerResident: (input: RegisterResidentInput) => AuthResult;
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
  const [currentScreen, setCurrentScreen] = useState<ScreenType>("login");
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [authMessage, setAuthMessage] = useState<string | null>(null);
  const [registeredAccounts, setRegisteredAccounts] = useState<StoredAccount[]>([]);
  const [selectedStationId, setSelectedStationId] = useState("S01");
  const [role, setRole] = useState<UserRole>("resident");
  const [userGroup, setUserGroup] = useState<UserGroup>("normal");
  const [userName, setUserName] = useState("Trần Minh Anh");
  const [userEmail, setUserEmail] = useState("resident@vinuni.edu.vn");
  const [userId, setUserId] = useState("00000000-0000-0000-0000-000000000101");
  const [organization, setOrganization] = useState("Vinhomes Ocean Park");
  const [pendingApprovalsCount, setPendingApprovalsCount] = useState(1);

  const applyAccount = (account: DemoAccount) => {
    window.scrollTo({ top: 0, left: 0, behavior: "auto" });
    setRole(account.role);
    setUserGroup(account.userGroup);
    setUserName(account.name);
    setUserEmail(account.email);
    setUserId(account.userId);
    setOrganization(account.organization);
    setIsAuthenticated(true);
    setAuthMessage(null);
    setCurrentScreen("dashboard");
  };

  const login = (email: string, password: string): AuthResult => {
    const normalizedEmail = email.trim().toLowerCase();
    const account = [...DEMO_ACCOUNT_RECORDS, ...registeredAccounts].find(
      (candidate) => candidate.email.toLowerCase() === normalizedEmail && candidate.password === password,
    );

    if (!account) return { success: false, message: "Email hoặc mật khẩu không chính xác." };
    applyAccount(account);
    return { success: true };
  };

  const loginAsDemo = (targetRole: UserRole) => {
    const account = DEMO_ACCOUNT_RECORDS.find((candidate) => candidate.role === targetRole);
    if (account) applyAccount(account);
  };

  const logout = () => {
    window.scrollTo({ top: 0, left: 0, behavior: "auto" });
    setIsAuthenticated(false);
    setAuthMessage("Bạn đã đăng xuất an toàn khỏi phiên demo.");
    setCurrentScreen("login");
  };

  const registerResident = (input: RegisterResidentInput): AuthResult => {
    const normalizedEmail = input.email.trim().toLowerCase();
    const emailExists = [...DEMO_ACCOUNT_RECORDS, ...registeredAccounts].some(
      (account) => account.email.toLowerCase() === normalizedEmail,
    );

    if (emailExists) return { success: false, message: "Email này đã được sử dụng." };

    setRegisteredAccounts((accounts) => [...accounts, {
      userId: crypto.randomUUID(),
      email: normalizedEmail,
      password: input.password,
      name: input.name.trim(),
      role: "resident",
      userGroup: input.userGroup,
      organization: "Cư dân Ocean Park",
    }]);
    setAuthMessage("Tạo tài khoản Cư dân thành công trong phiên demo. Bạn có thể đăng nhập ngay.");
    window.scrollTo({ top: 0, left: 0, behavior: "auto" });
    setCurrentScreen("login");
    return { success: true };
  };

  const navigateTo = (screen: ScreenType, params?: { stationId?: string }) => {
    if (!isAuthenticated && screen !== "login" && screen !== "register") {
      setCurrentScreen("login");
      return;
    }
    if (params?.stationId) setSelectedStationId(params.stationId);
    setCurrentScreen(screen);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  return (
    <AuthContext.Provider value={{
      currentScreen,
      setCurrentScreen,
      isAuthenticated,
      authMessage,
      clearAuthMessage: () => setAuthMessage(null),
      login,
      loginAsDemo,
      logout,
      registerResident,
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
    }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used within an AuthProvider");
  return context;
};
