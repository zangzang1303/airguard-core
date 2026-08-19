import React, { useState, useRef, useEffect } from "react";
import {
  X,
  Send,
  Sparkles,
  Bot,
  User,
  ShieldAlert,
  LockKeyhole,
  RotateCcw,
  Wrench,
  FileCheck2
} from "lucide-react";
import { api } from "../../api/client";
import { useAuth } from "../../context/AuthContext";
import { Proposal, AgentResponse } from "../../types";
import { Button } from "../../components/common/Button";

interface AiAssistantDrawerProps {
  initialPrompt?: string;
  onClose: () => void;
}

interface ChatMessage {
  id: string;
  sender: "user" | "ai";
  text: string;
  timestamp: string;
  used_tools?: string[];
  evidence?: Record<string, any>;
  proposal_created?: Proposal | null;
  isError?: boolean;
  retryQuery?: string;
}

const DEFAULT_QUESTIONS = [
  "Chất lượng không khí hôm nay thế nào?",
  "Tôi có nên tập thể thao ngoài trời tối nay?",
  "Trạm S01 nồng độ PM2.5 là bao nhiêu?",
  "Có đề xuất nào cần Ban quản lý xem xét không?",
  "Gợi ý tuyến đường chạy bộ ít bụi nhất?",
];

export const AiAssistantDrawer: React.FC<AiAssistantDrawerProps> = ({
  initialPrompt,
  onClose,
}) => {
  const { role, userId, navigateTo, setPendingApprovalsCount, selectedStationId } = useAuth();
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "msg-welcome",
      sender: "ai",
      text: "Xin chào! Tôi là AirGuard AI. Tôi chỉ trả lời về môi trường khi có dữ liệu và bằng chứng do backend cung cấp.",
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

  useEffect(() => {
    if (initialPrompt && initialPromptSentRef.current !== initialPrompt) {
      initialPromptSentRef.current = initialPrompt;
      handleSend(initialPrompt);
    }
  }, [initialPrompt]);

  const handleSend = async (textToSend?: string) => {
    const query = (textToSend || inputVal).trim();
    if (!query || isTyping) return;

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
      // Call actual backend AI Agent API
      const res: AgentResponse = await api.sendAgentMessage(query, selectedStationId, userId);
      const aiReply = res.reply || "Agent đã xử lý yêu cầu.";

      const aiMsg: ChatMessage = {
        id: `msg-ai-${Date.now()}`,
        sender: "ai",
        text: aiReply,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        used_tools: res.used_tools,
        evidence: res.evidence,
        proposal_created: res.proposal_created,
      };

      if (res.proposal_id) {
        setPendingApprovalsCount((count) => count + 1);
      }

      setMessages((prev) => [...prev, aiMsg]);
    } catch (err: any) {
      // Error handling with retry button
      const errorMsg: ChatMessage = {
        id: `msg-err-${Date.now()}`,
        sender: "ai",
        text: "Không thể kết nối tới dịch vụ AI Agent hoặc xảy ra lỗi mạng. Vui lòng kiểm tra kết nối và thử lại.",
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        isError: true,
        retryQuery: query,
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <aside className="contextual-drawer right-drawer ai-chat-drawer">
      {/* Header */}
      <div className="drawer-header-bar ai-header">
        <div className="ai-header-brand">
          <div className="ai-sparkle-badge">
            <Sparkles size={18} />
          </div>
          <div>
            <h2 className="drawer-main-title">AirGuard AI Agent</h2>
            <span className="drawer-sub-meta">Trợ lý môi trường grounded backend</span>
          </div>
        </div>
        <button className="drawer-close-btn" onClick={onClose} aria-label="Đóng">
          <X size={18} />
        </button>
      </div>

      {/* Suggested Quick Questions */}
      <div className="ai-suggested-chips-bar">
        {DEFAULT_QUESTIONS.map((q, idx) => (
          <button
            key={idx}
            className="ai-chip-pill"
            onClick={() => handleSend(q)}
            disabled={isTyping}
          >
            {q}
          </button>
        ))}
      </div>

      {/* Message Chat Flow */}
      <div className="ai-chat-messages-container">
        {messages.map((msg) => (
          <div key={msg.id} className={`chat-bubble-wrap ${msg.sender} ${msg.isError ? "error" : ""}`}>
            <div className="bubble-avatar">
              {msg.sender === "ai" ? <Bot size={16} /> : <User size={16} />}
            </div>
            <div className="bubble-content-box">
              <div className="bubble-text">{msg.text}</div>

              {/* Tools Used Badge */}
              {msg.used_tools && msg.used_tools.length > 0 && (
                <div style={{ display: "flex", flexWrap: "wrap", gap: 4, marginTop: 8 }}>
                  <span style={{ fontSize: "0.7rem", color: "#64748b", display: "flex", alignItems: "center", gap: 3 }}>
                    <Wrench size={12} /> Tools:
                  </span>
                  {msg.used_tools.map((t) => (
                    <span
                      key={t}
                      style={{
                        fontSize: "0.68rem",
                        fontFamily: "monospace",
                        background: "#f1f5f9",
                        padding: "1px 6px",
                        borderRadius: 4,
                        color: "#475569",
                        border: "1px solid #e2e8f0",
                      }}
                    >
                      {t}
                    </span>
                  ))}
                </div>
              )}

              {/* Grounded Source Tag */}
              {msg.sender === "ai" && !msg.isError && getEvidenceSources(msg.evidence).length > 0 && (
                <div style={{ fontSize: "0.68rem", color: "#059669", marginTop: 6, display: "flex", alignItems: "center", gap: 4 }}>
                  <FileCheck2 size={12} /> Bằng chứng backend: {getEvidenceSources(msg.evidence).join(", ")}
                </div>
              )}

              {/* Retry Button on Error */}
              {msg.isError && msg.retryQuery && (
                <div style={{ marginTop: 8 }}>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleSend(msg.retryQuery)}
                    style={{ fontSize: "0.78rem", padding: "3px 10px", borderRadius: 6, borderColor: "#fca5a5", color: "#991b1b" }}
                  >
                    <RotateCcw size={13} /> Thử lại
                  </Button>
                </div>
              )}

              {/* Warning Proposal Card */}
              {msg.proposal_created && (
                <div
                  style={{
                    marginTop: 10,
                    padding: 12,
                    borderRadius: 10,
                    background: "#fffbeb",
                    border: "1px solid #fde68a",
                    fontSize: "0.82rem",
                  }}
                >
                  <div style={{ fontWeight: 700, color: "#b45309", display: "flex", alignItems: "center", gap: 6, marginBottom: 4 }}>
                    <ShieldAlert size={16} /> Đề xuất đã được tạo & Đang chờ phê duyệt
                  </div>
                  <div><strong>Mục tiêu:</strong> {msg.proposal_created.target}</div>
                  <div><strong>Hành động:</strong> {msg.proposal_created.action}</div>
                  <div><strong>Lý do:</strong> {msg.proposal_created.rationale}</div>

                  {role === "manager" || role === "admin" ? (
                    <Button
                      variant="primary"
                      size="sm"
                      onClick={() => {
                        onClose();
                        navigateTo("approvals");
                      }}
                      style={{ marginTop: 8, fontSize: "0.78rem" }}
                    >
                      Mở Console Phê duyệt
                    </Button>
                  ) : (
                    <div style={{ fontSize: "0.74rem", color: "#b45309", marginTop: 6, display: "flex", alignItems: "center", gap: 4 }}>
                      <LockKeyhole size={13} /> Đề xuất đã chuyển đến Ban quản lý để xem xét.
                    </div>
                  )}
                </div>
              )}

              <span className="bubble-time">{msg.timestamp}</span>
            </div>
          </div>
        ))}

        {isTyping && (
          <div className="chat-bubble-wrap ai">
            <div className="bubble-avatar">
              <Bot size={16} />
            </div>
            <div className="bubble-content-box typing">
              <div className="typing-dots">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Chat Input Bar */}
      <div className="ai-chat-input-row">
        <input
          type="text"
          className="ai-text-input"
          placeholder="Hỏi AI Agent về chất lượng không khí..."
          value={inputVal}
          onChange={(e) => setInputVal(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") handleSend();
          }}
          disabled={isTyping}
        />
        <button
          className="ai-send-btn"
          onClick={() => handleSend()}
          disabled={!inputVal.trim() || isTyping}
        >
          <Send size={16} />
        </button>
      </div>
    </aside>
  );
};

function getEvidenceSources(evidence?: Record<string, any>): string[] {
  if (!evidence || !Array.isArray(evidence.sources)) return [];
  return evidence.sources
    .map((source: any) => typeof source === "string" ? source : source?.source || source?.tool_name || source?.station_id)
    .filter((source: unknown): source is string => typeof source === "string" && source.length > 0);
}
