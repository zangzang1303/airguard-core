# ADR 0013: Migrate email delivery from SMTP to Resend Email API

## Status

Accepted on 2026-08-23.

## Context

AirGuard AI previously relied on SMTP relay configuration (`SMTP_HOST`, `SMTP_PORT`, `SMTP_STARTTLS`, `SMTP_FROM`, `SMTP_USERNAME`, `SMTP_PASSWORD`) for two distinct workflows:
1. Synchronous authentication lifecycle emails (email verification, resend verification, password reset, and password changed notification).
2. Asynchronous proposal notifications dispatched to managers via Celery workers.

Using direct SMTP relays in modern containerized microservices introduces several operational drawbacks:
- Blocking socket handshakes and STARTTLS negotiation increase synchronous request latency.
- SMTP connection failures cannot be easily distinguished into transient vs permanent failure categories without fragile socket exception parsing.
- Lack of native HTTP API idempotency keys leads to potential duplicate email delivery upon worker retries or network timeouts.
- Managing raw SMTP credentials across multi-container topologies increases secret sprawl.

## Decision

1. **Official Python SDK (`resend==2.36.0`)**: Replace all direct `smtplib` usage with the official Resend Python SDK over HTTPS.
2. **Shared Resend Provider**: Consolidate email dispatch logic into a single shared adapter (`ResendEmailProvider`) shared by both `AuthEmailService` and Celery tasks (`send_notification_job`).
3. **Idempotency by Design**: Every email dispatch request transmits a deterministic, non-sensitive `idempotency_key` (e.g. `auth-verification/{token_id}`, `auth-password-reset/{token_id}`, `proposal-notification/{proposal_id}/{recipient_user_id}`).
4. **Delivery Semantics (`accepted`)**: Resend API returning a message ID confirms acceptance by the API, represented synchronously as `accepted` (not `delivered` or `sent`).
5. **Clean Status Mapping**:
   - `accepted`: Request accepted by Resend API with message ID.
   - `not_configured`: Provider is disabled (`NOTIFICATION_PROVIDER=disabled`) or missing required credentials (`RESEND_API_KEY`, `RESEND_FROM_EMAIL`).
   - `failed`: Provider rejection or network error.
6. **Transparent Retry Policies**:
   - 401/403/400/422/409 (payload conflict): marked non-retryable.
   - 429/409 (concurrent)/5xx/timeout: marked retryable (`TransientTaskError` in Celery).

## Consequences

- All `SMTP_*` environment variables are retired and removed from active runtime, `.env.example`, and `docker-compose.yml`.
- Replaced by `NOTIFICATION_PROVIDER=resend`, `RESEND_API_KEY`, `RESEND_FROM_EMAIL`, `RESEND_FROM_NAME`, `RESEND_REPLY_TO`, `RESEND_TIMEOUT_SECONDS`.
- Authentication endpoints return structured `email_delivery_status` ("accepted" | "not_configured" | "failed") to frontend.
- Proposal notifications and HITL mechanisms remain uncompromised; email dispatch failure does not alter pending proposal state or bypass human approval.
