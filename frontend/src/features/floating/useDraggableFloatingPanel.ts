import { useEffect, useRef, useState, useCallback, useMemo } from "react";
import { useFloatingPanelContext, StackingGroup, PanelPosition } from "./FloatingPanelContext";

export interface UseDraggableFloatingPanelOptions {
  panelId: string;
  group?: StackingGroup;
  disabled?: boolean;
  minMargin?: number;
  dragThreshold?: number;
  /** Base CSS transform string to preserve (e.g. "translateX(-50%)") */
  baseTransform?: string;
  /** Optional custom clamp bounds function */
  customClamp?: (proposed: PanelPosition, rect: DOMRect, boundary: DOMRect) => PanelPosition;
}

interface DragSession {
  pointerId: number;
  startX: number;
  startY: number;
  initialOffset: PanelPosition;
  isPointerDown: boolean;
  isDragging: boolean;
  handleEl: HTMLElement | null;
}

export function useDraggableFloatingPanel({
  panelId,
  group = "drawer",
  disabled = false,
  minMargin = 12,
  dragThreshold = 4,
  baseTransform,
  customClamp,
}: UseDraggableFloatingPanelOptions) {
  const {
    getPosition,
    updatePosition,
    resetPosition: ctxResetPosition,
    bringToFront,
    getZIndex,
    getBoundaryRect,
    acquireMapLock,
    releaseMapLock,
  } = useFloatingPanelContext();

  const containerRef = useRef<any>(null);
  const handleRef = useRef<any>(null);

  const [isDragging, setIsDragging] = useState(false);
  const dragSessionRef = useRef<DragSession | null>(null);

  const currentOffset = getPosition(panelId);
  const zIndex = getZIndex(panelId, group);

  // Clamp helper
  const clampOffset = useCallback(
    (proposed: PanelPosition): PanelPosition => {
      const container = containerRef.current;
      if (!container) return proposed;

      const boundary = getBoundaryRect();
      if (!boundary) return proposed;

      // Get natural un-transformed rect
      const rect = container.getBoundingClientRect();
      if (customClamp) {
        return customClamp(proposed, rect, boundary);
      }

      // Calculate where container would be with proposed offset relative to boundary
      const naturalLeft = rect.left - currentOffset.x;
      const naturalTop = rect.top - currentOffset.y;

      const targetLeft = naturalLeft + proposed.x;
      const targetTop = naturalTop + proposed.y;
      const targetRight = targetLeft + rect.width;
      const targetBottom = targetTop + rect.height;

      let clampedX = proposed.x;
      let clampedY = proposed.y;

      // Boundary limits
      const minLeft = boundary.left + minMargin;
      const maxRight = boundary.right - minMargin;
      const minTop = boundary.top + minMargin;
      const maxBottom = boundary.bottom - minMargin;

      // If panel is smaller than boundary, clamp strictly inside
      if (rect.width <= boundary.width - minMargin * 2) {
        if (targetLeft < minLeft) {
          clampedX = proposed.x + (minLeft - targetLeft);
        } else if (targetRight > maxRight) {
          clampedX = proposed.x - (targetRight - maxRight);
        }
      }

      if (rect.height <= boundary.height - minMargin * 2) {
        if (targetTop < minTop) {
          clampedY = proposed.y + (minTop - targetTop);
        } else if (targetBottom > maxBottom) {
          clampedY = proposed.y - (targetBottom - maxBottom);
        }
      } else {
        // For very tall panels, ensure at least the top header (first 50px) is visible
        if (targetTop < minTop) {
          clampedY = proposed.y + (minTop - targetTop);
        } else if (targetTop > boundary.bottom - 60) {
          clampedY = proposed.y - (targetTop - (boundary.bottom - 60));
        }
      }

      return { x: Math.round(clampedX), y: Math.round(clampedY) };
    },
    [getBoundaryRect, currentOffset, minMargin, customClamp]
  );

  // Cleanup on unmount if mid-drag
  useEffect(() => {
    return () => {
      if (dragSessionRef.current?.isDragging) {
        releaseMapLock();
      }
    };
  }, [releaseMapLock]);

  // ResizeObserver to re-clamp if screen or panel size changes
  useEffect(() => {
    if (disabled) return;
    const handleReclamp = () => {
      const pos = getPosition(panelId);
      if (pos.x !== 0 || pos.y !== 0) {
        const clamped = clampOffset(pos);
        if (clamped.x !== pos.x || clamped.y !== pos.y) {
          updatePosition(panelId, clamped);
        }
      }
    };

    window.addEventListener("resize", handleReclamp, { passive: true });
    window.addEventListener("orientationchange", handleReclamp, { passive: true });

    let observer: ResizeObserver | null = null;
    if (containerRef.current && typeof ResizeObserver !== "undefined") {
      observer = new ResizeObserver(() => handleReclamp());
      observer.observe(containerRef.current);
    }

    return () => {
      window.removeEventListener("resize", handleReclamp);
      window.removeEventListener("orientationchange", handleReclamp);
      if (observer) observer.disconnect();
    };
  }, [disabled, panelId, getPosition, clampOffset, updatePosition]);

  // Pointer Down handler on title
  const handlePointerDown = useCallback(
    (e: React.PointerEvent) => {
      if (disabled) return;

      // Bring panel to front on any handle pointerdown
      bringToFront(panelId, group);

      const target = e.target as HTMLElement | null;
      const handleEl = e.currentTarget as HTMLElement;

      // Check if target is non-draggable interactive element
      if (target) {
        if (
          target.closest("button") ||
          target.closest("input") ||
          target.closest("select") ||
          target.closest("textarea") ||
          target.closest("a") ||
          target.closest('[role="tab"]')
        ) {
          return;
        }

        const noDragEl = target.closest('[data-no-drag="true"], .no-drag');
        if (noDragEl && handleEl && handleEl.contains(noDragEl)) {
          return;
        }
      }

      // Stop propagation to native Leaflet map
      e.stopPropagation();

      const initialOffset = getPosition(panelId);

      dragSessionRef.current = {
        pointerId: e.pointerId,
        startX: e.clientX,
        startY: e.clientY,
        initialOffset,
        isPointerDown: true,
        isDragging: false,
        handleEl,
      };

      try {
        handleEl.setPointerCapture(e.pointerId);
      } catch {
        // setPointerCapture might throw on unsupported elements
      }
    },
    [disabled, panelId, group, bringToFront, getPosition]
  );

  const handlePointerMove = useCallback(
    (e: React.PointerEvent) => {
      const session = dragSessionRef.current;
      if (!session || !session.isPointerDown) return;
      if (session.pointerId !== e.pointerId) return;

      e.stopPropagation();
      e.preventDefault();

      const deltaX = e.clientX - session.startX;
      const deltaY = e.clientY - session.startY;

      // Check drag threshold
      if (!session.isDragging) {
        const distance = Math.hypot(deltaX, deltaY);
        if (distance < dragThreshold) {
          return;
        }
        session.isDragging = true;
        setIsDragging(true);
        acquireMapLock();
      }

      const rawProposed: PanelPosition = {
        x: session.initialOffset.x + deltaX,
        y: session.initialOffset.y + deltaY,
      };

      const clamped = clampOffset(rawProposed);
      updatePosition(panelId, clamped);
    },
    [dragThreshold, acquireMapLock, clampOffset, updatePosition, panelId]
  );

  const handlePointerUp = useCallback(
    (e: React.PointerEvent) => {
      const session = dragSessionRef.current;
      if (!session) return;
      if (session.pointerId !== e.pointerId) return;

      e.stopPropagation();

      if (session.isDragging) {
        releaseMapLock();
        setIsDragging(false);
      }

      try {
        session.handleEl?.releasePointerCapture(e.pointerId);
      } catch {
        // ignore
      }

      dragSessionRef.current = null;
    },
    [releaseMapLock]
  );

  const handlePointerCancel = useCallback(
    (e: React.PointerEvent) => {
      const session = dragSessionRef.current;
      if (!session) return;
      if (session.pointerId !== e.pointerId) return;

      e.stopPropagation();

      if (session.isDragging) {
        releaseMapLock();
        setIsDragging(false);
      }

      try {
        session.handleEl?.releasePointerCapture(e.pointerId);
      } catch {
        // ignore
      }

      dragSessionRef.current = null;
    },
    [releaseMapLock]
  );

  // Keyboard navigation on handle
  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (disabled) return;

      let dx = 0;
      let dy = 0;
      const step = e.shiftKey ? 50 : 10;

      if (e.key === "ArrowLeft") dx = -step;
      else if (e.key === "ArrowRight") dx = step;
      else if (e.key === "ArrowUp") dy = -step;
      else if (e.key === "ArrowDown") dy = step;
      else if (e.key === "Home") {
        e.preventDefault();
        e.stopPropagation();
        ctxResetPosition(panelId);
        return;
      } else {
        return;
      }

      e.preventDefault();
      e.stopPropagation();

      const current = getPosition(panelId);
      const proposed: PanelPosition = {
        x: current.x + dx,
        y: current.y + dy,
      };

      const clamped = clampOffset(proposed);
      updatePosition(panelId, clamped);
      bringToFront(panelId, group);
    },
    [disabled, panelId, group, getPosition, clampOffset, updatePosition, bringToFront, ctxResetPosition]
  );

  const resetPosition = useCallback(() => {
    ctxResetPosition(panelId);
  }, [ctxResetPosition, panelId]);

  // Click panel container to bring to front
  const handleContainerClick = useCallback(() => {
    bringToFront(panelId, group);
  }, [panelId, group, bringToFront]);

  const handleContainerPointerDown = useCallback(
    (event: React.PointerEvent) => {
      event.stopPropagation();
      bringToFront(panelId, group);
    },
    [panelId, group, bringToFront],
  );

  // Dynamic CSS style for panel container
  const panelStyle = useMemo((): React.CSSProperties => {
    const hasOffset = currentOffset.x !== 0 || currentOffset.y !== 0;
    const offsetStr = hasOffset ? `translate3d(${currentOffset.x}px, ${currentOffset.y}px, 0)` : "";
    let transformStr: string | undefined;

    if (baseTransform) {
      transformStr = offsetStr ? `${baseTransform} ${offsetStr}` : baseTransform;
    } else {
      transformStr = offsetStr || undefined;
    }

    return {
      transform: transformStr,
      zIndex,
      transition: isDragging ? "none" : "transform 0.15s ease-out, box-shadow 0.15s ease",
    };
  }, [baseTransform, currentOffset.x, currentOffset.y, zIndex, isDragging]);

  const handleProps = useMemo(() => {
    return {
      tabIndex: disabled ? -1 : 0,
      role: "region",
      "aria-label": `Kéo tiêu đề để di chuyển bảng điều khiển ${panelId} (Home: Đặt lại)`,
      "aria-roledescription": "Tiêu đề panel có thể di chuyển",
      "data-floating-handle": "true",
      style: {
        cursor: disabled ? "default" : isDragging ? "grabbing" : "grab",
        userSelect: "none" as const,
        touchAction: "none" as const,
      },
      onPointerDown: handlePointerDown,
      onPointerMove: handlePointerMove,
      onPointerUp: handlePointerUp,
      onPointerCancel: handlePointerCancel,
      onKeyDown: handleKeyDown,
    };
  }, [
    disabled,
    panelId,
    isDragging,
    handlePointerDown,
    handlePointerMove,
    handlePointerUp,
    handlePointerCancel,
    handleKeyDown,
  ]);

  return {
    containerRef,
    handleRef,
    position: currentOffset,
    isDragging,
    zIndex,
    panelStyle,
    handleProps,
    resetPosition,
    bringToFront: () => bringToFront(panelId, group),
    containerProps: {
      ref: containerRef,
      style: panelStyle,
      onPointerDown: handleContainerPointerDown,
      onMouseDown: handleContainerClick,
      onTouchStart: handleContainerClick,
    },
  };
}
