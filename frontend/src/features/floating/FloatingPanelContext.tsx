import React, { createContext, useContext, useEffect, useState, useCallback, useRef } from "react";

export type StackingGroup = "widget" | "popover" | "drawer" | "sheet" | "modal";
export type BreakpointType = "mobile" | "tablet" | "desktop";

export interface PanelPosition {
  x: number;
  y: number;
}

export type LayoutStorageMap = Record<BreakpointType, Record<string, PanelPosition>>;

interface MapHandlersSnapshot {
  dragging: boolean;
  touchZoom: boolean;
  scrollWheelZoom: boolean;
  doubleClickZoom: boolean;
  boxZoom: boolean;
  keyboard: boolean;
}

interface FloatingPanelContextValue {
  rootRef: React.RefObject<HTMLDivElement>;
  positions: Record<string, PanelPosition>;
  currentBreakpoint: BreakpointType;
  getPosition: (panelId: string) => PanelPosition;
  updatePosition: (panelId: string, pos: PanelPosition) => void;
  resetPosition: (panelId: string) => void;
  resetAllPositions: () => void;
  bringToFront: (panelId: string, group: StackingGroup) => void;
  getZIndex: (panelId: string, group: StackingGroup) => number;
  getBoundaryRect: () => DOMRect | null;
  getTopBarBottom: () => number;
  getBottomDockTop: () => number;
  registerMap: (map: any) => void;
  acquireMapLock: () => void;
  releaseMapLock: () => void;
}

const STORAGE_KEY = "airguard.ui.floating-panel-layout.v1";

const BASE_Z_INDEX: Record<StackingGroup, { min: number; max: number }> = {
  widget: { min: 1000, max: 1015 },
  popover: { min: 1020, max: 1040 },
  drawer: { min: 1040, max: 1080 },
  sheet: { min: 1040, max: 1080 },
  modal: { min: 2000, max: 2500 },
};

function getBreakpoint(width: number): BreakpointType {
  if (width < 640) return "mobile";
  if (width < 1024) return "tablet";
  return "desktop";
}

function loadSavedLayouts(): LayoutStorageMap {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return { mobile: {}, tablet: {}, desktop: {} };
    const parsed = JSON.parse(raw);
    return {
      mobile: typeof parsed.mobile === "object" && parsed.mobile !== null ? parsed.mobile : {},
      tablet: typeof parsed.tablet === "object" && parsed.tablet !== null ? parsed.tablet : {},
      desktop: typeof parsed.desktop === "object" && parsed.desktop !== null ? parsed.desktop : {},
    };
  } catch {
    return { mobile: {}, tablet: {}, desktop: {} };
  }
}

function saveLayouts(data: LayoutStorageMap) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
  } catch {
    // Ignore storage quota errors
  }
}

const FloatingPanelContext = createContext<FloatingPanelContextValue | null>(null);

export const FloatingPanelProvider: React.FC<{
  children: React.ReactNode;
  rootRef?: React.RefObject<HTMLDivElement>;
  boundarySelector?: string;
}> = ({ children, rootRef: externalRootRef, boundarySelector }) => {
  const internalRootRef = useRef<HTMLDivElement>(null);
  const rootRef = externalRootRef || internalRootRef;

  const [layouts, setLayouts] = useState<LayoutStorageMap>(loadSavedLayouts);
  const [breakpoint, setBreakpoint] = useState<BreakpointType>(() =>
    typeof window !== "undefined" ? getBreakpoint(window.innerWidth) : "desktop"
  );
  const [activeGroupOrders, setActiveGroupOrders] = useState<Record<StackingGroup, string[]>>({
    widget: [],
    popover: [],
    drawer: [],
    sheet: [],
    modal: [],
  });

  // Centralized Leaflet map registration & interaction lock
  const mapRef = useRef<any>(null);
  const lockCountRef = useRef(0);
  const mapSnapshotRef = useRef<MapHandlersSnapshot | null>(null);

  const registerMap = useCallback((map: any) => {
    mapRef.current = map;
    // If map was registered while lock is held, lock the new map
    if (map && lockCountRef.current > 0 && !mapSnapshotRef.current) {
      const snapshot: MapHandlersSnapshot = {
        dragging: Boolean(map.dragging?.enabled?.()),
        touchZoom: Boolean(map.touchZoom?.enabled?.()),
        scrollWheelZoom: Boolean(map.scrollWheelZoom?.enabled?.()),
        doubleClickZoom: Boolean(map.doubleClickZoom?.enabled?.()),
        boxZoom: Boolean(map.boxZoom?.enabled?.()),
        keyboard: Boolean(map.keyboard?.enabled?.()),
      };
      mapSnapshotRef.current = snapshot;
      if (snapshot.dragging) map.dragging?.disable?.();
      if (snapshot.touchZoom) map.touchZoom?.disable?.();
      if (snapshot.scrollWheelZoom) map.scrollWheelZoom?.disable?.();
      if (snapshot.doubleClickZoom) map.doubleClickZoom?.disable?.();
      if (snapshot.boxZoom) map.boxZoom?.disable?.();
      if (snapshot.keyboard) map.keyboard?.disable?.();
    }
  }, []);

  const acquireMapLock = useCallback(() => {
    lockCountRef.current += 1;
    if (lockCountRef.current === 1 && mapRef.current) {
      const map = mapRef.current;
      const snapshot: MapHandlersSnapshot = {
        dragging: Boolean(map.dragging?.enabled?.()),
        touchZoom: Boolean(map.touchZoom?.enabled?.()),
        scrollWheelZoom: Boolean(map.scrollWheelZoom?.enabled?.()),
        doubleClickZoom: Boolean(map.doubleClickZoom?.enabled?.()),
        boxZoom: Boolean(map.boxZoom?.enabled?.()),
        keyboard: Boolean(map.keyboard?.enabled?.()),
      };
      mapSnapshotRef.current = snapshot;
      if (snapshot.dragging) map.dragging?.disable?.();
      if (snapshot.touchZoom) map.touchZoom?.disable?.();
      if (snapshot.scrollWheelZoom) map.scrollWheelZoom?.disable?.();
      if (snapshot.doubleClickZoom) map.doubleClickZoom?.disable?.();
      if (snapshot.boxZoom) map.boxZoom?.disable?.();
      if (snapshot.keyboard) map.keyboard?.disable?.();
    }
  }, []);

  const releaseMapLock = useCallback(() => {
    lockCountRef.current = Math.max(0, lockCountRef.current - 1);
    if (lockCountRef.current === 0 && mapRef.current && mapSnapshotRef.current) {
      const map = mapRef.current;
      const snapshot = mapSnapshotRef.current;
      if (snapshot.dragging) map.dragging?.enable?.();
      if (snapshot.touchZoom) map.touchZoom?.enable?.();
      if (snapshot.scrollWheelZoom) map.scrollWheelZoom?.enable?.();
      if (snapshot.doubleClickZoom) map.doubleClickZoom?.enable?.();
      if (snapshot.boxZoom) map.boxZoom?.enable?.();
      if (snapshot.keyboard) map.keyboard?.enable?.();
      mapSnapshotRef.current = null;
    }
  }, []);

  // Listen to window resize for breakpoint updates
  useEffect(() => {
    const handleResize = () => {
      const bp = getBreakpoint(window.innerWidth);
      setBreakpoint(bp);
    };
    window.addEventListener("resize", handleResize, { passive: true });
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  const getPosition = useCallback(
    (panelId: string): PanelPosition => {
      const pos = layouts[breakpoint]?.[panelId];
      if (pos && typeof pos.x === "number" && typeof pos.y === "number" && !isNaN(pos.x) && !isNaN(pos.y)) {
        return pos;
      }
      return { x: 0, y: 0 };
    },
    [layouts, breakpoint]
  );

  const updatePosition = useCallback(
    (panelId: string, pos: PanelPosition) => {
      setLayouts((prev) => {
        const next: LayoutStorageMap = {
          ...prev,
          [breakpoint]: {
            ...prev[breakpoint],
            [panelId]: pos,
          },
        };
        saveLayouts(next);
        return next;
      });
    },
    [breakpoint]
  );

  const resetPosition = useCallback(
    (panelId: string) => {
      setLayouts((prev) => {
        const currentBpLayout = { ...prev[breakpoint] };
        delete currentBpLayout[panelId];
        const next = { ...prev, [breakpoint]: currentBpLayout };
        saveLayouts(next);
        return next;
      });
    },
    [breakpoint]
  );

  const resetAllPositions = useCallback(() => {
    const empty: LayoutStorageMap = { mobile: {}, tablet: {}, desktop: {} };
    setLayouts(empty);
    saveLayouts(empty);
  }, []);

  const bringToFront = useCallback((panelId: string, group: StackingGroup) => {
    setActiveGroupOrders((prev) => {
      const list = prev[group].filter((id) => id !== panelId);
      list.push(panelId);
      return {
        ...prev,
        [group]: list,
      };
    });
  }, []);

  const getZIndex = useCallback(
    (panelId: string, group: StackingGroup): number => {
      const conf = BASE_Z_INDEX[group] || BASE_Z_INDEX.widget;
      const order = activeGroupOrders[group] || [];
      const idx = order.indexOf(panelId);
      if (idx === -1) return conf.min;
      const range = conf.max - conf.min;
      const step = Math.min(range, idx + 1);
      return conf.min + step;
    },
    [activeGroupOrders]
  );

  const getBoundaryRect = useCallback((): DOMRect | null => {
    if (boundarySelector && typeof document !== "undefined") {
      const el = document.querySelector(boundarySelector);
      if (el) return el.getBoundingClientRect();
    }
    if (rootRef.current) {
      return rootRef.current.getBoundingClientRect();
    }
    if (typeof document !== "undefined") {
      const defaultEl = document.querySelector(".map-super-app-root");
      if (defaultEl) return defaultEl.getBoundingClientRect();
    }
    if (typeof window !== "undefined") {
      return new DOMRect(0, 0, window.innerWidth, window.innerHeight);
    }
    return null;
  }, [boundarySelector, rootRef]);

  const getTopBarBottom = useCallback((): number => {
    if (typeof document === "undefined") return 70;
    const topBar = document.querySelector(".top-floating-bar-header");
    if (topBar) {
      const rect = topBar.getBoundingClientRect();
      return rect.bottom;
    }
    return 70;
  }, []);

  const getBottomDockTop = useCallback((): number => {
    if (typeof document === "undefined") return 600;
    const bottomDock = document.querySelector(".bottom-action-dock-bar");
    if (bottomDock) {
      const rect = bottomDock.getBoundingClientRect();
      return rect.top;
    }
    return window.innerHeight - 80;
  }, []);

  return (
    <FloatingPanelContext.Provider
      value={{
        rootRef,
        positions: layouts[breakpoint] || {},
        currentBreakpoint: breakpoint,
        getPosition,
        updatePosition,
        resetPosition,
        resetAllPositions,
        bringToFront,
        getZIndex,
        getBoundaryRect,
        getTopBarBottom,
        getBottomDockTop,
        registerMap,
        acquireMapLock,
        releaseMapLock,
      }}
    >
      {children}
    </FloatingPanelContext.Provider>
  );
};

export function useFloatingPanelContext(): FloatingPanelContextValue {
  const ctx = useContext(FloatingPanelContext);
  if (!ctx) {
    throw new Error("useFloatingPanelContext must be used within a FloatingPanelProvider");
  }
  return ctx;
}
