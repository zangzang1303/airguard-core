# Manual Test Results — Pending Final Run

## Run metadata

| Trường | Giá trị |
|---|---|
| Commit | `a939966` |
| Tester | **NEEDS VERIFICATION** |
| Ngày/giờ | **NEEDS VERIFICATION** |
| Local/Public URL | **NEEDS VERIFICATION** |
| Browser/viewport | **NEEDS VERIFICATION** |
| `SENSOR_SCENARIO` | **NEEDS VERIFICATION** |
| Kết luận | **NOT EXECUTED ON FINAL COMMIT** |

Tài liệu này không thay thế checklist chi tiết tại
[`../../manual-test-checklist.md`](../../manual-test-checklist.md). Nó là bảng sign-off rút gọn cần hoàn thành
trên release stack cuối.

## P0 release checklist

| ID | Luồng bắt buộc | Trạng thái | Evidence/ghi chú |
|---|---|---|---|
| M-01 | Compose startup, health/readiness và frontend access | NEEDS VERIFICATION | Stack đang dừng ngày 31/08. |
| M-02 | S01–S05 simulator → MQTT → DB → API → UI | NEEDS VERIFICATION | Cần lưu message ID và timestamp. |
| M-03 | Dashboard current/history đa metric | NEEDS VERIFICATION | Chụp source/freshness. |
| M-04 | Forecast 1–24h, bounds, Golden Window | NEEDS VERIFICATION | Đối chiếu API và UI. |
| M-05 | Timeline Play/Pause và spatial heatmap | NEEDS VERIFICATION | Kiểm tra 0→24h, pause và thiếu dữ liệu. |
| M-06 | Multi-metric alert sau đủ consecutive samples | NEEDS VERIFICATION | Chạy `spike`, sau đó `recovery`. |
| M-07 | Agent current/compare/forecast có grounding | NEEDS VERIFICATION | Lưu used tools/source/time. |
| M-08 | Personalized route và indoor fallback | NEEDS VERIFICATION | Automated route tests đang có failure. |
| M-09 | Agent/backend fail closed khi stale/offline/outage | NEEDS VERIFICATION | Không fixture giả live. |
| M-10 | Proposal bắt đầu pending, Resident nhận 403 | NEEDS VERIFICATION | Lưu proposal/version/audit ID. |
| M-11 | Reject không dispatch | NEEDS VERIFICATION | Lưu decision và command absence. |
| M-12 | Approve → dispatch → ACK đúng command ID | NEEDS VERIFICATION | Không báo running trước ACK. |
| M-13 | Agent từ chối bypass HITL | NEEDS VERIFICATION | Không có mutation trái phép. |
| M-14 | Audit create/review/dispatch/failure đầy đủ | NEEDS VERIFICATION | Không lộ secret/PII/raw prompt. |
| M-15 | Report daily/weekly và Markdown/HTML/PDF | NEEDS VERIFICATION | Automated report tests còn 2 failure. |
| M-16 | Duplicate, station-silence và recovery | NEEDS VERIFICATION | Xác nhận data-quality gate. |
| M-17 | Retest Agent chat UI failure ngày 24/08 | NEEDS VERIFICATION | Cần screenshot và network status mới. |

## P1 checklist

| ID | Luồng nâng cao | Trạng thái | Evidence/ghi chú |
|---|---|---|---|
| M-18 | Ba nhóm user nhận khuyến nghị đúng policy | NEEDS VERIFICATION | normal/sensitive/outdoor_sport. |
| M-19 | Notification disabled và provider configured | NEEDS VERIFICATION | Không đưa API key vào evidence. |
| M-20 | PDF tiếng Việt, watermark, matrix và page break | NEEDS VERIFICATION | Email snapshot test cũng cần runtime. |
| M-21 | Responsive UI/mobile | NEEDS VERIFICATION | Gợi ý 375px và 1280px. |
| M-22 | Public URL incognito, HTTPS/CORS | NEEDS VERIFICATION | Chỉ chạy khi URL cuối đã freeze. |

## Evidence tối thiểu cần gắn

- [ ] `docker compose ps` và health/readiness.
- [ ] Dashboard đủ 5 trạm; current/history/forecast/heatmap.
- [ ] Agent grounded answer, personalized route, insufficient-data và HITL refusal.
- [ ] Proposal/version/decision/command/ACK/audit chain.
- [ ] Report ID và ba export formats.
- [ ] Failure/recovery log với request/correlation IDs.

## Final sign-off

- [ ] Tất cả P0 là PASS hoặc có disposition được QA/Tech Lead chấp nhận.
- [ ] Không còn Agent hallucination, HITL bypass, stale-data usage hoặc secret leak.
- [ ] Kết quả manual trỏ tới cùng final commit với automated report.
