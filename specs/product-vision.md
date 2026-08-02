# Product Vision

## Problem
Nguoi hoc, nhan vien va nguoi tap ngoai troi khong co mot diem xem PM2.5 de hieu cho khu vuc campus. AirGuard AI cung cap minh hoa data-driven va luong canh bao co nguoi phe duyet.

## Vision
Trong MVP, nguoi dung mo dashboard, xem 5 tram PM2.5 gia lap, nhan biet data freshness, hoi Agent dua tren tool data va gui de xuat canh bao qua manager. San pham khong thay the co quan quan trac hay tu van y te.

## Users and jobs
| User | Can lam | Success |
|---|---|---|
| Viewer | xem station/current/history/alerts | biet data nao fresh va tram nao can chu y |
| Sensitive user | nhan recommendation can trong | khuyen nghi co source, khong chan doan |
| Outdoor sport user | hoi xu huong 1-3h | phan biet forecast va observation |
| Manager | review warning proposal | approve/reject co evidence/audit |
| Team demo | chay luong MVP | tai lap tu runbook |

## MVP boundaries
In scope: S01-S05, simulator, MQTT, DB, REST, map, alert, baseline forecast, tool-grounded Agent, HITL, audit. Out of scope: sensor that, medical guidance, autonomous device control, public emergency system, long-term forecast, production identity provider.

## Success metrics
- 5 tram co the trace simulator den UI.
- Spike valid/fresh tao alert dung rule; stale/invalid khong tao.
- 100% demo Agent facts truy ve duoc tool trace.
- 100% approve/reject demo co audit event.

## Assumptions to confirm
Threshold/severity, station coordinates, manager identity, weather provider va forecast quality can Mentor/nhom xac nhan.
