import React, { useMemo } from "react";
import L from "leaflet";
import { Marker, Tooltip } from "react-leaflet";
import { VentilationDevice } from "../../types";


interface VentilationDeviceMarkersProps {
  devices: VentilationDevice[];
  visible: boolean;
  onSelectDevice: (device: VentilationDevice) => void;
}

const modeClass = (mode: VentilationDevice["operating_mode"]) => {
  if (mode === "RUNNING_BOOST" || mode === "AIR_PURIFIER_ON") return "boost";
  if (mode === "ECO_MODE") return "eco";
  return "standby";
};

export const VentilationDeviceMarkers: React.FC<VentilationDeviceMarkersProps> = ({
  devices,
  visible,
  onSelectDevice,
}) => {
  const markers = useMemo(
    () =>
      devices
        .filter((device) => device.latitude != null && device.longitude != null)
        .map((device) => ({
          device,
          icon: L.divIcon({
            className: "ventilation-marker-host",
            html: `<span class="ventilation-marker ventilation-marker--${modeClass(device.operating_mode)}" aria-hidden="true"><span class="ventilation-marker__pulse"></span><span class="ventilation-marker__fan">✣</span></span>`,
            iconSize: [42, 42],
            iconAnchor: [21, 21],
          }),
        })),
    [devices],
  );

  if (!visible) return null;

  return (
    <>
      {markers.map(({ device, icon }) => (
        <Marker
          key={device.device_id}
          position={[Number(device.latitude), Number(device.longitude)]}
          icon={icon}
          eventHandlers={{ click: () => onSelectDevice(device) }}
          zIndexOffset={650}
        >
          <Tooltip direction="top" offset={[0, -18]} opacity={0.96}>
            <strong>{device.device_id}</strong>
            <br />
            {device.operating_mode === "RUNNING_BOOST"
              ? `Boost · ${device.intensity_percent ?? 80}%`
              : device.operating_mode === "ECO_MODE"
                ? "Eco Mode"
                : "Standby"}
          </Tooltip>
        </Marker>
      ))}
    </>
  );
};
