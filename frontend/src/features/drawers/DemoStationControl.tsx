import React, { useEffect, useState } from "react";
import { FlaskConical, RotateCcw } from "lucide-react";
import { api } from "../../api/client";
import { useAuth } from "../../context/AuthContext";

const DEFAULT_VALUES = { pm25: 120, co2: 1600, noise_db: 88, temperature: 39 };

export const DemoStationControl: React.FC = () => {
  const { role, selectedStationId } = useAuth();
  const [open, setOpen] = useState(false);
  const [stationId, setStationId] = useState(selectedStationId || "S03");
  const [values, setValues] = useState(DEFAULT_VALUES);
  const [active, setActive] = useState<Record<string, unknown>>({});
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const allowed = role === "manager" || role === "admin";

  const refresh = async () => {
    try {
      setActive((await api.getDemoStationOverrides()).overrides || {});
    } catch {
      setMessage("Không tải được trạng thái điều khiển demo.");
    }
  };
  useEffect(() => { refresh(); }, []);
  useEffect(() => { if (selectedStationId) setStationId(selectedStationId); }, [selectedStationId]);
  const setValue = (key: keyof typeof values, value: string) => setValues((old) => ({ ...old, [key]: Number(value) }));
  const apply = async () => {
    setBusy(true); setMessage("");
    try { await api.setDemoStationOverride(stationId, values); await refresh(); setMessage(`Đã áp dụng dữ liệu demo cho ${stationId}.`); }
    catch { setMessage("Không thể áp dụng override. Hãy đăng nhập Manager/Admin rồi thử lại."); }
    finally { setBusy(false); }
  };
  const reset = async () => {
    setBusy(true); setMessage("");
    try { await api.clearDemoStationOverride(stationId); await refresh(); setMessage(`${stationId} đã quay về mô phỏng tự động.`); }
    catch { setMessage("Không thể gỡ override."); }
    finally { setBusy(false); }
  };

  return <section style={{ margin: "0 16px 8px", border: "1px solid #fed7aa", borderRadius: 12, background: "#fff7ed", padding: 10 }}>
    <button type="button" onClick={() => setOpen(!open)} style={{ border: 0, background: "transparent", width: "100%", display: "flex", justifyContent: "space-between", cursor: "pointer", color: "#9a3412", fontWeight: 800 }}>
      <span><FlaskConical size={15} style={{ verticalAlign: "-3px", marginRight: 6 }} />Điều khiển dữ liệu demo</span><span>{open ? "Ẩn" : "Mở"}</span>
    </button>
    {open && <div style={{ marginTop: 10, fontSize: 12, color: "#431407" }}>
      <p style={{ margin: "0 0 8px" }}>Chỉ dùng khi demo. Giá trị sẽ được gắn nhãn override; chọn “Tự động” để trả về simulator.{!allowed && " Cần đăng nhập Manager/Admin để áp dụng."}</p>
      <select value={stationId} onChange={(e) => setStationId(e.target.value)} style={{ width: "100%", padding: 7, borderRadius: 7, border: "1px solid #fdba74" }}>
        {["S01", "S02", "S03", "S04", "S05"].map((id) => <option key={id}>{id}</option>)}
      </select>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 6, marginTop: 7 }}>
        {([ ["pm25", "PM2.5"], ["co2", "CO₂"], ["noise_db", "dB"], ["temperature", "°C"] ] as const).map(([key, label]) => <label key={key}>{label}<input type="number" value={values[key]} onChange={(e) => setValue(key, e.target.value)} style={{ width: "100%", boxSizing: "border-box", padding: 6, marginTop: 2, border: "1px solid #fdba74", borderRadius: 6 }} /></label>)}
      </div>
      <div style={{ display: "flex", gap: 6, marginTop: 8 }}><button disabled={busy || !allowed} onClick={apply} style={{ flex: 1, padding: 7, border: 0, borderRadius: 7, background: "#ea580c", color: "white", fontWeight: 700 }}>Áp dụng</button><button disabled={busy || !allowed || !active[stationId]} onClick={reset} style={{ flex: 1, padding: 7, border: "1px solid #fb923c", borderRadius: 7, background: "white", color: "#9a3412", fontWeight: 700 }}><RotateCcw size={13} /> Tự động</button></div>
      {active[stationId] && <div style={{ marginTop: 7, color: "#c2410c", fontWeight: 700 }}>● Override đang bật tại {stationId}</div>}
      {message && <div style={{ marginTop: 7 }}>{message}</div>}
    </div>}
  </section>;
};
