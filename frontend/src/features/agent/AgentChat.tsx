import React, { useState } from "react";
import { api } from "../../api/client";
import { useAuth } from "../../context/AuthContext";
import { AgentResponse } from "../../types";

interface ChatMessage {
  id: string;
  sender: "user" | "agent";
  text: string;
  timestamp: string;
  used_tools?: string[];
  proposal_created?: any;
}

export const AgentChat: React.FC = () => {
  const { selectedStationId, userGroup, role, navigateTo, setPendingApprovalsCount } = useAuth();
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "msg-1",
      sender: "agent",
      text: `Xin chào! Tôi là Trợ lý AI AirGuard. Bạn đang quan tâm đến trạm [${selectedStationId}] hoặc nhóm rủi ro sức khỏe [${userGroup}]. Bạn cần giúp đỡ thông tin gì về nồng độ PM2.5, thời tiết hay khuyến nghị sức khỏe?`,
      timestamp: new Date().toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" }),
      used_tools: ["get_user_profile", "get_current_pm25"]
    }
  ]);
  const [input, setInput] = useState<string>("");
  const [sending, setSending] = useState<boolean>(false);

  const handleSend = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!input.trim() || sending) return;

    const userText = input.trim();
    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      sender: "user",
      text: userText,
      timestamp: new Date().toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" })
    };

    setMessages(prev => [...prev, userMsg]);
    setInput("");
    setSending(true);

    try {
      const res: AgentResponse = await api.sendAgentMessage(userText, selectedStationId, userGroup);

      const agentMsg: ChatMessage = {
        id: `agent-${Date.now()}`,
        sender: "agent",
        text: res.reply,
        timestamp: new Date().toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" }),
        used_tools: res.used_tools,
        proposal_created: res.proposal_created
      };

      setMessages(prev => [...prev, agentMsg]);

      if (res.proposal_created) {
        setPendingApprovalsCount(c => c + 1);
      }
    } catch (err) {
      setMessages(prev => [
        ...prev,
        {
          id: `err-${Date.now()}`,
          sender: "agent",
          text: "⚠️ Đã xảy ra lỗi kết nối với dịch vụ Agent. Không thể tự đưa ra giả định ngoài dữ liệu quan trắc.",
          timestamp: new Date().toLocaleTimeString("vi-VN")
        }
      ]);
    } finally {
      setSending(false);
    }
  };

  const presetPrompts = [
    `Chất lượng không khí trạm ${selectedStationId} hiện tại thế nào?`,
    "Dự báo nồng độ PM2.5 3 giờ tới tại Ocean Park?",
    "Khuyên người tập thể thao ngoài trời hôm nay?",
    "Tạo đề xuất cảnh báo cho Manager nếu PM2.5 vượt 50 ug/m3!"
  ];

  return (
    <div className="chat-container">
      <div className="chat-header">
        <div>
          <h2>🤖 AI Agent Assistant (Grounded Tool Calling)</h2>
          <span className="chat-subtitle">Trบริ context: Trạm {selectedStationId} | Nhóm rủi ro: {userGroup}</span>
        </div>
        <button className="btn-secondary-sm" onClick={() => setMessages([messages[0]])}>
          🗑️ Xóa hội thoại
        </button>
      </div>

      {/* Preset Prompt Pills */}
      <div className="preset-pills">
        {presetPrompts.map((p, idx) => (
          <button key={idx} className="pill-btn" onClick={() => setInput(p)}>
            💬 {p}
          </button>
        ))}
      </div>

      {/* Message List */}
      <div className="chat-messages">
        {messages.map((msg) => (
          <div key={msg.id} className={`message-bubble ${msg.sender}`}>
            <div className="message-header">
              <span className="sender-name">{msg.sender === "user" ? "👤 Bạn" : "🤖 AirGuard Agent"}</span>
              <span className="message-time">{msg.timestamp}</span>
            </div>
            <div className="message-text">{msg.text}</div>

            {/* Used Tools Badge */}
            {msg.used_tools && msg.used_tools.length > 0 && (
              <div className="used-tools">
                <span className="tools-label">🛠️ Tools gọi:</span>
                {msg.used_tools.map((t, i) => (
                  <span key={i} className="tool-tag">{t}</span>
                ))}
              </div>
            )}

            {/* Warning Proposal Card if Created */}
            {msg.proposal_created && (
              <div className="proposal-card-chat">
                <div className="proposal-badge">⚠️ Đã tạo Warning Proposal (Pending Manager HITL)</div>
                <div><strong>Mục tiêu:</strong> {msg.proposal_created.target}</div>
                <div><strong>Hành động:</strong> {msg.proposal_created.action}</div>
                <div><strong>Lý do:</strong> {msg.proposal_created.rationale}</div>
                {role === "manager" || role === "admin" ? (
                  <button
                    className="btn-primary-sm"
                    style={{ marginTop: 8 }}
                    onClick={() => navigateTo("approvals")}
                  >
                    👉 Mở Hàng chờ Phê duyệt (HITL) →
                  </button>
                ) : (
                  <small style={{ color: '#f59e0b', marginTop: 4, display: 'block' }}>
                    🔒 Chỉ tài khoản Manager/Admin mới có quyền Phê duyệt proposal này.
                  </small>
                )}
              </div>
            )}
          </div>
        ))}
        {sending && (
          <div className="message-bubble agent sending">
            <div className="typing-indicator">🤖 Agent đang xử lý & gọi tools backend...</div>
          </div>
        )}
      </div>

      {/* Input Form */}
      <form onSubmit={handleSend} className="chat-input-form">
        <input
          type="text"
          placeholder="Nhập câu hỏi của bạn cho Agent..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          className="chat-input"
          disabled={sending}
        />
        <button type="submit" className="btn-primary" disabled={sending || !input.trim()}>
          {sending ? "Đang gửi..." : "Gửi 🚀"}
        </button>
      </form>
    </div>
  );
};
