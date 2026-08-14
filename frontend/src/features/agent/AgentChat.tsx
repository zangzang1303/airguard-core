import React, { useState } from "react";
import { Bot, Clock3, LockKeyhole, MessageSquare, Plus, Send, ShieldAlert, Trash2, UserRound } from "lucide-react";
import { api } from "../../api/client";
import { Button } from "../../components/common/Button";
import { PageHeader } from "../../components/common/PageHeader";
import { TechnicalDetails } from "../../components/common/TechnicalDetails";
import { useAuth } from "../../context/AuthContext";
import { AgentResponse, Proposal } from "../../types";

interface ChatMessage {
  id: string;
  sender: "user" | "agent";
  text: string;
  timestamp: string;
  used_tools?: string[];
  proposal_created?: Proposal | null;
}

export const AgentChat: React.FC = () => {
  const { selectedStationId, userGroup, userId, role, navigateTo, setPendingApprovalsCount } = useAuth();
  const initialMessage: ChatMessage = {
    id: "msg-1",
    sender: "agent",
    text: `Xin chào! Tôi là Trợ lý AI AirGuard. AQI là chỉ số tổng quan cho trạm [${selectedStationId}]. Bạn cần xem AQI, các thành phần môi trường hay cảnh báo?`,
    timestamp: new Date().toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" }),
  };
  const [messages, setMessages] = useState<ChatMessage[]>([initialMessage]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);

  const handleSend = async (event?: React.FormEvent) => {
    event?.preventDefault();
    if (!input.trim() || sending) return;

    const userText = input.trim();
    setMessages((previous) => [...previous, {
      id: `user-${Date.now()}`,
      sender: "user",
      text: userText,
      timestamp: new Date().toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" }),
    }]);
    setInput("");
    setSending(true);

    try {
      const response: AgentResponse = await api.sendAgentMessage(userText, selectedStationId, userId);
      setMessages((previous) => [...previous, {
        id: `agent-${Date.now()}`,
        sender: "agent",
        text: response.reply,
        timestamp: new Date().toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" }),
        used_tools: response.used_tools,
        proposal_created: response.proposal_created,
      }]);

      if (response.proposal_id) setPendingApprovalsCount((count) => count + 1);
    } catch {
      setMessages((previous) => [...previous, {
        id: `error-${Date.now()}`,
        sender: "agent",
        text: "Đã xảy ra lỗi kết nối với dịch vụ Agent. Không thể đưa ra giả định ngoài dữ liệu backend.",
        timestamp: new Date().toLocaleTimeString("vi-VN"),
      }]);
    } finally {
      setSending(false);
    }
  };

  const presetPrompts = [
    `Chất lượng không khí trạm ${selectedStationId} hiện tại thế nào?`,
    `Đánh giá mức độ ảnh hưởng môi trường tại trạm ${selectedStationId}.`,
    "AQI tại Ocean Park trong 3 giờ tới có xu hướng thế nào?",
    "Khuyên người tập thể thao ngoài trời hôm nay?",
    "Tạo đề xuất cảnh báo cho Manager nếu PM2.5 vượt 50 ug/m3!",
  ];

  return (
    <div className="agent-page">
      <PageHeader
        title="AI Agent"
        description={`Hỏi đáp dựa trên dữ liệu backend · Trạm ${selectedStationId} · Nhóm người dùng ${userGroup}.`}
        actions={(
          <Button variant="ghost" size="sm" onClick={() => setMessages([initialMessage])}>
            <Trash2 size={16} aria-hidden="true" />
            Xóa hội thoại
          </Button>
        )}
      />

      <div className="agent-workspace">
        <aside className="chat-history-panel" aria-label="Lịch sử hội thoại">
          <Button variant="primary" size="sm" onClick={() => setMessages([initialMessage])}><Plus size={16} />Cuộc trò chuyện mới</Button>
          <div className="chat-history-panel__title">Gần đây</div>
          <button type="button" className="chat-history-item is-active">
            <MessageSquare size={16} />
            <span><strong>Phiên hiện tại</strong><small>Trạm {selectedStationId} · {messages.length} tin nhắn</small></span>
          </button>
          <div className="chat-history-empty"><Clock3 size={18} /><span>Lịch sử được lưu khi backend session được cấu hình.</span></div>
        </aside>

        <div className="chat-container">
        <div className="preset-pills" aria-label="Câu hỏi gợi ý">
          {presetPrompts.map((prompt) => (
            <button key={prompt} type="button" className="pill-btn" onClick={() => setInput(prompt)}>
              <MessageSquare size={15} aria-hidden="true" />
              {prompt}
            </button>
          ))}
        </div>

        <div className="chat-messages" aria-live="polite">
          {messages.map((message) => (
            <div key={message.id} className={`message-bubble ${message.sender}`}>
              <div className="message-header">
                <span className="sender-name">
                  {message.sender === "user" ? <UserRound size={15} aria-hidden="true" /> : <Bot size={15} aria-hidden="true" />}
                  {message.sender === "user" ? "Bạn" : "AirGuard Agent"}
                </span>
                <span className="message-time">{message.timestamp}</span>
              </div>
              <div className="message-text">{message.text}</div>

              {message.used_tools && <TechnicalDetails tools={message.used_tools} />}

              {message.proposal_created && (
                <div className="proposal-card-chat">
                  <div className="proposal-badge">
                    <ShieldAlert size={16} aria-hidden="true" />
                    Đề xuất đang chờ Manager phê duyệt
                  </div>
                  <div><strong>Mục tiêu:</strong> {message.proposal_created.target}</div>
                  <div><strong>Hành động:</strong> {message.proposal_created.action}</div>
                  <div><strong>Lý do:</strong> {message.proposal_created.rationale}</div>
                  {role === "manager" || role === "admin" ? (
                    <Button variant="primary" size="sm" className="proposal-card-chat__action" onClick={() => navigateTo("approvals")}>
                      Mở hàng chờ phê duyệt
                    </Button>
                  ) : (
                    <small className="proposal-card-chat__permission">
                      <LockKeyhole size={14} aria-hidden="true" />
                      Chỉ Manager/Admin có quyền phê duyệt đề xuất này.
                    </small>
                  )}
                </div>
              )}
            </div>
          ))}
          {sending && (
            <div className="message-bubble agent sending">
              <div className="typing-indicator"><Bot size={16} aria-hidden="true" /> Agent đang xử lý yêu cầu...</div>
            </div>
          )}
        </div>

        <form onSubmit={handleSend} className="chat-input-form">
          <input
            type="text"
            aria-label="Câu hỏi cho AI Agent"
            placeholder="Nhập câu hỏi của bạn cho Agent..."
            value={input}
            onChange={(event) => setInput(event.target.value)}
            className="chat-input"
            disabled={sending}
          />
          <Button type="submit" variant="primary" disabled={sending || !input.trim()}>
            <Send size={16} aria-hidden="true" />
            {sending ? "Đang gửi" : "Gửi"}
          </Button>
        </form>
        </div>
      </div>
    </div>
  );
};
