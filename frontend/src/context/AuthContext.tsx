import React, { createContext, useContext, useState, ReactNode } from "react";
import { UserRole, UserGroup } from "../types";

export type ScreenType = 
  | "dashboard" 
  | "station-detail" 
  | "compare" 
  | "agent" 
  | "alerts" 
  | "approvals" 
  | "audit" 
  | "profile" 
  | "login";

interface AuthContextType {
  currentScreen: ScreenType;
  setCurrentScreen: (screen: ScreenType) => void;
  selectedStationId: string;
  setSelectedStationId: (id: string) => void;
  compareStationIds: [string, string];
  setCompareStationIds: (ids: [string, string]) => void;
  role: UserRole;
  setRole: (role: UserRole) => void;
  userGroup: UserGroup;
  setUserGroup: (group: UserGroup) => void;
  userName: string;
  setUserName: (name: string) => void;
  pendingApprovalsCount: number;
  setPendingApprovalsCount: React.Dispatch<React.SetStateAction<number>>;
  navigateTo: (screen: ScreenType, params?: { stationId?: string; compareIds?: [string, string] }) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [currentScreen, setCurrentScreen] = useState<ScreenType>("dashboard");
  const [selectedStationId, setSelectedStationId] = useState<string>("S01");
  const [compareStationIds, setCompareStationIds] = useState<[string, string]>(["S01", "S02"]);

  const [role, setRole] = useState<UserRole>("manager");
  const [userGroup, setUserGroup] = useState<UserGroup>("sensitive");
  const [userName, setUserName] = useState<string>("Nguyễn Văn A");
  const [pendingApprovalsCount, setPendingApprovalsCount] = useState<number>(1);

  const navigateTo = (screen: ScreenType, params?: { stationId?: string; compareIds?: [string, string] }) => {
    if (params?.stationId) {
      setSelectedStationId(params.stationId);
    }
    if (params?.compareIds) {
      setCompareStationIds(params.compareIds);
    }
    setCurrentScreen(screen);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  return (
    <AuthContext.Provider
      value={{
        currentScreen,
        setCurrentScreen,
        selectedStationId,
        setSelectedStationId,
        compareStationIds,
        setCompareStationIds,
        role,
        setRole,
        userGroup,
        setUserGroup,
        userName,
        setUserName,
        pendingApprovalsCount,
        setPendingApprovalsCount,
        navigateTo
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
