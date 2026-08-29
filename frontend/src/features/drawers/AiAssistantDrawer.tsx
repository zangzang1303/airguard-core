import React, { useState, useRef, useEffect } from "react";
import {
  X,
  Send,
  Sparkles,
  Bot,
  User,
  ShieldAlert,
  RotateCcw,
  MapPin,
  HelpCircle,
  ChevronDown,
  ChevronUp,
  Activity,
  Zap,
} from "lucide-react";
import { api } from "../../api/client";
import { formatAgentRequestError } from "../../api/agentResponseHelper.js";
import { useAuth } from "../../context/AuthContext";
import { Proposal, AgentResponse } from "../../types";
import { mapActionController, MapAction } from "../map/MapActionController";
import { useDraggableFloatingPanel } from "../floating";

interface AiAssistantDrawerProps {
  initialPrompt?: string;
  onClose: () => void;
  mapContext?: Record<string, any>;
}

interface ChatMessage {
  id: string;
  sender: "user" | "ai";
  text: string;
  timestamp: string;
  summary?: string;
  details?: string;
  intent?: string;
  time_context?: any;
  data_mode?: "live" | "forecast";
  evidence?: any;
  map_actions?: MapAction[];
  follow_up_actions?: string[];
  used_tools?: string[];
  proposal_created?: Proposal | null;
  isError?: boolean;
  retryQuery?: string;
  showEvidence?: boolean;
}

const renderInlineMarkdown = (text: string): React.ReactNode[] =>
  text
    .split(/(\*\*[^*\n]+\*\*)/g)
    .filter(Boolean)
    .map((part, index) =>
      part.startsWith("**") && part.endsWith("**") ? (
        <strong key={`bold-${index}`}>{part.slice(2, -2)}</strong>
      ) : (
        <React.Fragment key={`text-${index}`}>{part}</React.Fragment>
      )
    );

const DEFAULT_QUESTIONS = [
  "🏃‍♂️ Tìm đoạn đường chạy bộ phù hợp nhất tối nay",
  "⚠️ Khu nào đang ô nhiễm nhất?",
  "⚖️ So sánh Sapphire và Hồ Ngọc Trai",
  "🏫 VinUni không khí thế nào?",
  "🌿 Chất lượng không khí hiện tại ở Ocean Park 1?",
];

export const AiAssistantDrawer: React.FC<AiAssistantDrawerProps> = ({
  initialPrompt,
  onClose,
  mapContext,
}) => {
  const { role, userId, navigateTo, setPendingApprovalsCount } = useAuth();
  const { containerProps, handleProps } = useDraggableFloatingPanel({
    panelId: "ai-chat",
    group: "drawer",
  });
  const [conversationId, setConversationId] = useState<string>(() => `conv_${Date.now()}`);
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "msg-welcome",
      sender: "ai",
      text: "Xin chào! Tôi là AirGuard Geospatial AI Agent. Tôi phân tích dữ liệu môi trường và tự động vẽ lộ trình, khoanh vùng và định vị trực tiếp trên bản đồ.",
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    },
  ]);
  const [inputVal, setInputVal] = useState(initialPrompt || "");
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const initialPromptSentRef = useRef<string | null>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isTyping]);

  // Clean up AI overlay whenever the AI chat drawer is closed / unmounted
  useEffect(() => {
    return () => {
      mapActionController.clearAIOverlay();
    };
  }, []);

  // Listen for Escape key to close the drawer
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  useEffect(() => {
    if (initialPrompt && initialPromptSentRef.current !== initialPrompt) {
      initialPromptSentRef.current = initialPrompt;
      handleSend(initialPrompt);
    }
  }, [initialPrompt]);

  const handleResetConversation = () => {
    mapActionController.clearAIOverlay();
    setConversationId(`conv_${Date.now()}`);
    setMessages([
      {
        id: "msg-welcome",
        sender: "ai",
        text: "Xin chào! Tôi là AirGuard Geospatial AI Agent. Phiên hội thoại mới đã được thiết lập. Hãy hỏi tôi về không khí, đường chạy hoặc địa điểm tại Ocean Park 1.",
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      },
    ]);
  };

  const handleSend = async (textToSend?: string) => {
    const query = (textToSend || inputVal).trim();
    if (!query || isTyping) return;

    // Immediately clear previous AI overlay before processing the new prompt
    mapActionController.clearAIOverlay();

    const userMsgId = `msg-u-${Date.now()}`;
    const userMsg: ChatMessage = {
      id: userMsgId,
      sender: "user",
      text: query,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputVal("");
    setIsTyping(true);

    try {
      const selectedSensor = mapContext?.selected_sensor;
      const contextStationId = typeof selectedSensor === "string" && /^S0[1-5]$/.test(selectedSensor)
        ? selectedSensor
        : null;
      const res: AgentResponse = await api.sendAgentMessage(query, contextStationId, userId, mapContext, conversationId);
      
      const answerObj = typeof res.answer === "object" && res.answer !== null ? res.answer : { summary: res.reply || "", details: "" };
      const aiReply = res.reply || answerObj.summary || "";

      // Execute Declarative Map Actions on Leaflet AI Layer
      if (res.map_actions && Array.isArray(res.map_actions) && res.map_actions.length > 0) {
        mapActionController.executeAll(res.map_actions as MapAction[]);
      }

      const aiMsg: ChatMessage = {
        id: `msg-ai-${Date.now()}`,
        sender: "ai",
        text: aiReply,
        summary: answerObj.summary,
        details: answerObj.details,
        intent: res.intent,
        time_context: res.time_context,
        data_mode: res.data_mode,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        used_tools: res.used_tools,
        evidence: res.evidence,
        map_actions: res.map_actions as MapAction[],
        follow_up_actions: res.follow_up_actions,
        proposal_created: res.proposal_created,
        showEvidence: false,
      };

      if (res.proposal_id) {
        setPendingApprovalsCount((count) => count + 1);
      }

      setMessages((prev) => [...prev, aiMsg]);
    } catch (err: any) {
      const errorMsg: ChatMessage = {
        id: `msg-err-${Date.now()}`,
        sender: "ai",
        text: formatAgentRequestError(err),
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        isError: true,
        retryQuery: query,
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleRetry = async (queryToRetry: string) => {
    if (isTyping) return;
    setIsTyping(true);

    try {
      const selectedSensor = mapContext?.selected_sensor;
      const contextStationId = typeof selectedSensor === "string" && /^S0[1-5]$/.test(selectedSensor)
        ? selectedSensor
        : null;
      const res: AgentResponse = await api.sendAgentMessage(queryToRetry, contextStationId, userId, mapContext, conversationId);

      const answerObj = typeof res.answer === "object" && res.answer !== null ? res.answer : { summary: res.reply || "", details: "" };
      const aiReply = res.reply || answerObj.summary || "";

      if (res.map_actions && Array.isArray(res.map_actions) && res.map_actions.length > 0) {
        mapActionController.executeAll(res.map_actions as MapAction[]);
      }

      const aiMsg: ChatMessage = {
        id: `msg-ai-${Date.now()}`,
        sender: "ai",
        text: aiReply,
        summary: answerObj.summary,
        details: answerObj.details,
        intent: res.intent,
        time_context: res.time_context,
        data_mode: res.data_mode,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        used_tools: res.used_tools,
        evidence: res.evidence,
        map_actions: res.map_actions as MapAction[],
        follow_up_actions: res.follow_up_actions,
        proposal_created: res.proposal_created,
        showEvidence: false,
      };

      if (res.proposal_id) {
        setPendingApprovalsCount((count) => count + 1);
      }

      setMessages((prev) => [...prev.filter((m) => !m.isError), aiMsg]);
    } catch (err: any) {
      const newErrorMsg: ChatMessage = {
        id: `msg-err-${Date.now()}`,
        sender: "ai",
        text: formatAgentRequestError(err),
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        isError: true,
        retryQuery: queryToRetry,
      };
      setMessages((prev) => [...prev, newErrorMsg]);
    } finally {
      setIsTyping(false);
    }
  };

  const toggleEvidence = (msgId: string) => {
    setMessages((prev) =>
      prev.map((m) => (m.id === msgId ? { ...m, showEvidence: !m.showEvidence } : m))
    );
  };

  const getRouteAction = (actions?: MapAction[]): MapAction | undefined => {
    return actions?.find((a) => a.type === "highlight_route");
  };

  return (
    <aside {...containerProps} className="contextual-drawer right-drawer ai-chat-drawer" style={{ width: "min(440px, 100vw)", ...containerProps.style }}>
      {/* Header */}
      <div className="drawer-header-bar ai-header">
        <div className="ai-header-brand" {...handleProps}>
          <div className="ai-sparkle-badge" style={{ background: "linear-gradient(135deg, #10b981, #06b6d4)", color: "#fff", boxShadow: "0 4px 12px rgba(16, 185, 129, 0.4)" }}>
            <Sparkles size={18} />
          </div>
          <div style={{ minWidth: 0 }}>
            <h2 className="drawer-main-title">AirGuard Geospatial AI</h2>
            <span className="drawer-sub-meta">Tương tác thực & nhớ ngữ cảnh hội thoại OCP1</span>
          </div>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
          <button
            className="no-drag drawer-close-btn"
            data-no-drag="true"
            onClick={handleResetConversation}
            title="Bắt đầu cuộc trò chuyện mới"
            aria-label="Cuộc trò chuyện mới"
            style={{ width: "32px", height: "32px" }}
          >
            <RotateCcw size={15} />
          </button>
          <button className="no-drag drawer-close-btn" data-no-drag="true" onClick={onClose} aria-label="Đóng" style={{ width: "32px", height: "32px" }}>
            <X size={18} />
          </button>
        </div>
      </div>

      {/* Suggested Quick Questions with Icons */}
      <div className="ai-suggested-chips-bar" style={{ padding: "10px 16px", display: "flex", gap: "8px", overflowX: "auto" }}>
        {DEFAULT_QUESTIONS.map((q, idx) => (
          <button
            key={idx}
            className="ai-chip-pill"
            style={{
              whiteSpace: "nowrap",
              fontSize: "12px",
              fontWeight: 600,
              padding: "6px 12px",
              borderRadius: "9999px",
              background: "#ffffff",
              border: "1px solid #cbd5e1",
              boxShadow: "0 1px 3px rgba(0,0,0,0.04)",
              color: "#1e293b",
              cursor: "pointer",
            }}
            onClick={() => handleSend(q.replace(/^[^\w\s]+\s*/, ""))}
            disabled={isTyping}
          >
            {q}
          </button>
        ))}
      </div>

      {/* Message Chat Flow */}
      <div className="ai-chat-messages-container" style={{ flex: 1, overflowY: "auto", padding: "16px", display: "flex", flexDirection: "column", gap: "14px" }}>
        {messages.map((msg) => {
          const routeAction = getRouteAction(msg.map_actions);

          return (
            <div key={msg.id} className={`chat-bubble-wrap ${msg.sender} ${msg.isError ? "error" : ""}`} {...(msg.isError ? { role: "alert", "data-testid": "ai-error-message" } : {})}>
              <div className="bubble-avatar">
                {msg.sender === "ai" ? <Bot size={16} /> : <User size={16} />}
              </div>
              <div className="bubble-content-box" style={{ background: msg.sender === "ai" ? "#ffffff" : "#3b82f6", color: msg.sender === "ai" ? "#0f172a" : "#ffffff", borderRadius: "16px", padding: "14px", boxShadow: "0 3px 12px rgba(0,0,0,0.06)", border: msg.sender === "ai" ? "1px solid #e2e8f0" : "none" }}>
                {/* Header Mode Badge */}
                {msg.time_context && (
                  <div style={{ display: "inline-flex", alignItems: "center", gap: 5, padding: "3px 9px", borderRadius: "6px", fontSize: "11px", fontWeight: 800, background: msg.data_mode === "forecast" ? "#fef3c7" : "#ecfdf5", color: msg.data_mode === "forecast" ? "#92400e" : "#065f46", marginBottom: 8 }}>
                    {msg.data_mode === "forecast" ? `🔮 DỰ BÁO ${msg.time_context.label?.toUpperCase()}` : "⚡ THỜI GIAN THỰC"}
                  </div>
                )}

                {/* If it's a running route recommendation, render the Rich Visual Route Card */}
                {(msg.intent === "recommend_running_route" || msg.intent === "recommend_personalized_running_route") && routeAction ? (
                  <div className="ai-route-rich-card">
                    <div className="ai-route-header-banner">
                      <div className="ai-route-header-title">
                        <Activity size={16} /> {routeAction.short_name || routeAction.name}
                      </div>
                      <div className="ai-route-header-badge">
                        {routeAction.distance_km} KM
                      </div>
                    </div>
                    <div className="ai-route-body">
                      <div className="ai-route-metrics-grid">
                        <div className="ai-metric-stat-box">
                          <div className="ai-metric-stat-label">Cự ly</div>
                          <div className="ai-metric-stat-val">{routeAction.distance_km} km</div>
                        </div>
                        <div className="ai-metric-stat-box">
                          <div className="ai-metric-stat-label">PM2.5 hít vào ước tính</div>
                          <div className="ai-metric-stat-val">{routeAction.estimated_inhaled_mass_ug ?? "N/A"} µg</div>
                        </div>
                        <div className="ai-metric-stat-box">
                          <div className="ai-metric-stat-label">Thời gian</div>
                          <div className="ai-metric-stat-val">{routeAction.duration_minutes ?? "N/A"} phút</div>
                        </div>
                        <div className="ai-metric-stat-box">
                          <div className="ai-metric-stat-label">Giảm so với đối chứng</div>
                          <div className="ai-metric-stat-val">
                            {routeAction.exposure_reduction_pct == null ? "N/A" : `${routeAction.exposure_reduction_pct}%`}
                          </div>
                        </div>
                      </div>

                      <div className="ai-route-timeline">
                        <div className="ai-timeline-row">
                          <div className="ai-timeline-dot"></div>
                          <span><strong>Nguồn graph:</strong> {routeAction.graph_source ?? "N/A"}</span>
                        </div>
                        <div className="ai-timeline-row">
                          <div className="ai-timeline-dot" style={{ background: "#06b6d4" }}></div>
                          <span><strong>Lộ trình:</strong> {routeAction.name}</span>
                        </div>
                      </div>

                      <button
                        className="ai-route-cta-btn"
                        onClick={() => {
                          mapActionController.clearAIOverlay();
                          mapActionController.executeAll(msg.map_actions);
                        }}
                      >
                        <Zap size={15} /> Nhấp nháy & Xem lộ trình trên bản đồ
                      </button>
                    </div>
                  </div>
                ) : msg.intent === "recommend_indoor_activity" ? (
                  /* Indoor Activity Pivot Card */
                  <div className="ai-route-rich-card" style={{ border: "1px solid #fecaca" }}>
                    <div className="ai-route-header-banner" style={{ background: "linear-gradient(135deg, #dc2626 0%, #b91c1c 100%)" }}>
                      <div className="ai-route-header-title">
                        <ShieldAlert size={16} /> CẢNH BÁO MÔI TRƯỜNG: VẬN ĐỘNG TRONG NHÀ
                      </div>
                      <div className="ai-route-header-badge" style={{ background: "rgba(0,0,0,0.3)" }}>
                        AN TOÀN HÔ HẤP
                      </div>
                    </div>
                    <div className="ai-route-body">
                      <div style={{ fontSize: "13px", lineHeight: "1.55", color: "#334155", marginBottom: "12px", whiteSpace: "pre-line" }}>
                        {renderInlineMarkdown(msg.text)}
                      </div>

                      <button
                        className="ai-route-cta-btn"
                        style={{ background: "linear-gradient(135deg, #0284c7 0%, #0369a1 100%)", boxShadow: "0 4px 14px rgba(2, 132, 199, 0.35)" }}
                        onClick={() => {
                          mapActionController.clearAIOverlay();
                          mapActionController.executeAll(msg.map_actions);
                        }}
                      >
                        <MapPin size={15} /> Xem các địa điểm thể thao trong nhà trên bản đồ
                      </button>
                    </div>
                  </div>
                ) : (
                  /* Standard rich text reply */
                  <div className="bubble-text" style={{ fontSize: "13.5px", lineHeight: "1.6", whiteSpace: "pre-line" }}>
                    {renderInlineMarkdown(
                      typeof msg.text === "string"
                        ? msg.text
                        : typeof msg.summary === "string"
                          ? msg.summary
                          : JSON.stringify(msg.text || "")
                    )}
                  </div>
                )}

                {/* Interactive Follow-up Action Chips */}
                {msg.follow_up_actions && msg.follow_up_actions.length > 0 && (
                  <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginTop: 10 }}>
                    {msg.follow_up_actions.map((actionText, idx) => (
                      <button
                        key={`action-${idx}`}
                        onClick={() => handleSend(actionText.replace(/^[^\w\s]+\s*/, ""))}
                        disabled={isTyping}
                        style={{
                          padding: "5px 10px",
                          background: "#f1f5f9",
                          color: "#0f172a",
                          border: "1px solid #cbd5e1",
                          borderRadius: "14px",
                          fontSize: "12px",
                          fontWeight: 500,
                          cursor: "pointer",
                          transition: "all 0.15s ease",
                        }}
                      >
                        {actionText}
                      </button>
                    ))}
                  </div>
                )}

                {/* Interactive Map Actions Trigger Button for other inquiries */}
                {msg.map_actions && msg.map_actions.length > 0 && msg.intent !== "recommend_running_route" && (
                  <div style={{ marginTop: 10, display: "flex", gap: 8 }}>
                    <button
                      onClick={() => {
                        mapActionController.clearAIOverlay();
                        mapActionController.executeAll(msg.map_actions);
                      }}
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: 5,
                        padding: "6px 12px",
                        background: "#f0fdf4",
                        color: "#166534",
                        border: "1px solid #bbf7d0",
                        borderRadius: "8px",
                        fontSize: "12px",
                        fontWeight: 700,
                        cursor: "pointer",
                      }}
                    >
                      <MapPin size={13} /> Xem trực tiếp trên bản đồ
                    </button>

                    {msg.evidence && (
                      <button
                        onClick={() => toggleEvidence(msg.id)}
                        style={{
                          display: "flex",
                          alignItems: "center",
                          gap: 4,
                          padding: "6px 12px",
                          background: "#f8fafc",
                          color: "#475569",
                          border: "1px solid #e2e8f0",
                          borderRadius: "8px",
                          fontSize: "12px",
                          fontWeight: 600,
                          cursor: "pointer",
                        }}
                      >
                        <HelpCircle size={13} />
                        {msg.showEvidence ? "Ẩn số liệu" : "Tại sao? (Bằng chứng)"}
                        {msg.showEvidence ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
                      </button>
                    )}
                  </div>
                )}

                {/* Collapsible Evidence Inspector (Task 11) */}
                {msg.showEvidence && msg.evidence && (
                  <div style={{ marginTop: 10, padding: 10, background: "#f8fafc", borderRadius: 10, fontSize: "11px", color: "#334155", border: "1px solid #e2e8f0" }}>
                    <div style={{ fontWeight: 700, marginBottom: 6, color: "#0f172a", display: "flex", alignItems: "center", gap: 5 }}>
                      <span>📊</span> Nguồn dữ liệu quan trắc & mô phỏng:
                    </div>
                    {Array.isArray(msg.evidence) && msg.evidence.length > 0 ? (
                      <div style={{ display: "flex", flexDirection: "column", gap: 6, marginBottom: 6 }}>
                        {msg.evidence.map((ev: any, evIdx: number) => {
                          const name = ev.location_name || ev.name || ev.station_id || ev.poi_id || `Dữ liệu #${evIdx + 1}`;
                          const aqiVal = ev.aqi !== undefined ? ev.aqi : ev.value;
                          const pm25Val = ev.pm25;
                          const src = ev.source || "simulator";
                          const time = ev.timestamp ? new Date(ev.timestamp).toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" }) : "vừa xong";

                          return (
                            <div key={`ev-${evIdx}`} style={{ background: "#ffffff", padding: "6px 10px", borderRadius: 6, border: "1px solid #cbd5e1" }}>
                              <div style={{ fontWeight: 600, color: "#1e293b" }}>{name}</div>
                              <div style={{ display: "flex", gap: 10, marginTop: 2, color: "#475569" }}>
                                {aqiVal !== undefined && <span>AQI: <strong>{aqiVal}</strong></span>}
                                {pm25Val !== undefined && <span>PM2.5: <strong>{pm25Val} µg/m³</strong></span>}
                                <span>Cập nhật: {time}</span>
                                <span>Nguồn: <em>{src}</em></span>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    ) : null}
                    <details style={{ marginTop: 4, cursor: "pointer" }}>
                      <summary style={{ color: "#64748b", fontSize: "10.5px" }}>Xem JSON kỹ thuật (Developer)</summary>
                      <pre style={{ margin: "6px 0 0", fontFamily: "monospace", fontSize: "10px", whiteSpace: "pre-wrap", maxHeight: 120, overflowY: "auto", background: "#f1f5f9", padding: 6, borderRadius: 4 }}>
                        {JSON.stringify(msg.evidence, null, 2)}
                      </pre>
                    </details>
                  </div>
                )}

                {/* Retry Button on Error */}
                {msg.isError && msg.retryQuery && (
                  <button
                    className="retry-send-btn"
                    data-testid="ai-retry-button"
                    style={{ marginTop: 8, display: "flex", alignItems: "center", gap: 4, padding: "5px 10px", background: "#fee2e2", color: "#991b1b", border: "none", borderRadius: 6, fontSize: "11px", cursor: "pointer" }}
                    onClick={() => handleRetry(msg.retryQuery || "")}
                  >
                    <RotateCcw size={12} /> Thử lại
                  </button>
                )}
              </div>
            </div>
          );
        })}

        {isTyping && (
          <div className="chat-bubble-wrap ai typing">
            <div className="bubble-avatar">
              <Bot size={16} />
            </div>
            <div className="bubble-content-box typing-indicator-box" style={{ background: "#f8fafc", padding: "12px 16px", borderRadius: 14, border: "1px solid #e2e8f0" }}>
              <div className="typing-dots">
                <span></span>
                <span></span>
                <span></span>
              </div>
              <span style={{ fontSize: "12px", fontWeight: 600, color: "#10b981", marginLeft: 8 }}>AI đang tính toán tuyến đường & vẽ bản đồ...</span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Box */}
      <div className="ai-chat-input-bar" style={{ padding: "14px 16px", borderTop: "1px solid #e2e8f0", background: "#ffffff" }}>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          style={{ display: "flex", gap: "8px" }}
        >
          <input
            type="text"
            className="ai-text-input"
            data-testid="ai-chat-input"
            style={{ flex: 1, padding: "11px 16px", borderRadius: "12px", border: "1.5px solid #cbd5e1", fontSize: "13.5px", outline: "none", transition: "border-color 0.2s" }}
            placeholder="Hỏi về cung đường chạy bộ, ô nhiễm, so sánh..."
            value={inputVal}
            onChange={(e) => setInputVal(e.target.value)}
            disabled={isTyping}
          />
          <button
            type="submit"
            className="ai-send-btn"
            data-testid="ai-send-button"
            style={{ width: "44px", height: "44px", borderRadius: "12px", background: "linear-gradient(135deg, #10b981 0%, #059669 100%)", color: "#fff", border: "none", display: "flex", alignItems: "center", justifyContent: "center", cursor: "pointer", boxShadow: "0 4px 12px rgba(16, 185, 129, 0.35)" }}
            disabled={!inputVal.trim() || isTyping}
          >
            <Send size={18} />
          </button>
        </form>
      </div>
    </aside>
  );
};
