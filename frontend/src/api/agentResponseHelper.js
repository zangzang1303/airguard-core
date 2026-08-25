/**
 * agentResponseHelper.js — Production helpers for parsing and formatting agent responses and errors.
 * Used by both frontend UI components (AiAssistantDrawer, client.ts) and regression test suites.
 */

/**
 * Format any HTTP or network error into a user-friendly Vietnamese notification message.
 * @param {any} error
 * @returns {string}
 */
export function formatAgentRequestError(error) {
  if (error?.code === "agent_malformed_success") {
    return "Dịch vụ AI Agent trả phản hồi không đúng định dạng. Vui lòng thử lại sau ít phút.";
  }
  if (error?.status === 422) {
    return "Yêu cầu gửi tới AI chưa hợp lệ. Vui lòng thử lại hoặc đăng nhập để cá nhân hóa kết quả.";
  }
  if ([502, 503, 504].includes(error?.status)) {
    return "Dịch vụ AI Agent đang tạm thời gián đoạn. Vui lòng thử lại sau ít phút.";
  }
  return "Không thể kết nối tới dịch vụ AI Agent hoặc xảy ra lỗi mạng. Vui lòng kiểm tra kết nối và thử lại.";
}

/**
 * Fail-closed parser for AgentChatResponse payloads.
 * Validates that an HTTP 200 payload actually contains a non-empty response, reply, or answer.
 * If all are missing or empty, throws a typed `agent_malformed_success` error so the UI
 * renders a failure alert rather than a fake default message.
 *
 * @param {Record<string, any>} response
 * @returns {{ reply: string, summary: string, details: string }}
 */
export function extractAgentReply(response) {
  if (!response || typeof response !== "object") {
    const contractErr = new Error(
      "Agent service returned HTTP 200 but the response body is not a valid JSON object.",
    );
    contractErr.status = 200;
    contractErr.code = "agent_malformed_success";
    contractErr.details = { request_id: null };
    contractErr.request_id = null;
    throw contractErr;
  }

  const rawAnswer = response.answer;
  let summaryStr = "";
  let detailsStr = "";

  if (typeof rawAnswer === "string") {
    summaryStr = rawAnswer;
  } else if (rawAnswer && typeof rawAnswer === "object") {
    summaryStr =
      typeof rawAnswer.summary === "string"
        ? rawAnswer.summary
        : typeof rawAnswer.summary === "object"
          ? JSON.stringify(rawAnswer.summary)
          : String(rawAnswer.summary || "");
    detailsStr =
      typeof rawAnswer.details === "string"
        ? rawAnswer.details
        : typeof rawAnswer.details === "object"
          ? JSON.stringify(rawAnswer.details)
          : String(rawAnswer.details || "");
  }

  let textReply = "";
  if (typeof response.response === "string" && response.response.trim()) {
    textReply = response.response;
  } else if (typeof response.reply === "string" && response.reply.trim()) {
    textReply = response.reply;
  } else {
    textReply = summaryStr + (detailsStr ? `\n\n${detailsStr}` : "");
  }

  if (!textReply.trim()) {
    const contractErr = new Error(
      "Agent service returned HTTP 200 but the response body is missing required contract fields (response / reply / answer).",
    );
    contractErr.status = 200;
    contractErr.code = "agent_malformed_success";
    contractErr.details = { request_id: response.request_id ?? null };
    contractErr.request_id = response.request_id ?? null;
    throw contractErr;
  }

  return {
    reply: textReply,
    summary: summaryStr,
    details: detailsStr,
  };
}
