import { useEffect, useState } from "react";
import { mapActionController } from "./MapActionController";

/**
 * Custom React hook that subscribes to MapActionController's AI overlay state.
 * Returns true when there are active AI route, marker, or area layers on the map.
 */
export function useAiOverlayActive(): boolean {
  const [hasOverlay, setHasOverlay] = useState<boolean>(() => mapActionController.hasAIOverlay());

  useEffect(() => {
    const unsubscribe = mapActionController.subscribe((active) => {
      setHasOverlay(active);
    });
    return unsubscribe;
  }, []);

  return hasOverlay;
}
