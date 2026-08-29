# ADR 0020: ESG report policy, coverage and publication integrity

## Status

Accepted for the simulator MVP on 2026-08-29. This ADR extends ADR 0011 and does not rewrite its
historical decision.

## Context

ADR 0011 established persisted daily/weekly reports, deterministic statistics, optional grounded
narrative and export without recomputation. B7-05 needs a versioned coverage policy, reference
comparison, conditional device-impact estimates, a weekly 7x24 matrix and one integrity marker shared
by the API, UI and all exporters. Simulator measurements cannot establish legal compliance, causal
device effectiveness, health benefit or metered energy use.

## Decision

The additive contract is `b7-esg-reports-v1`. A completed v1 report snapshots cadence, coverage,
station gate, KPI, reference, ESG formula and fixed color-scale versions inside `statistics`.
Legacy `periodic-report-v1` rows retain a compatibility rendering path and do not receive a fabricated
checksum.

Coverage uses half-open UTC intervals projected into the report IANA timezone. Expected samples are
elapsed UTC seconds divided by the snapshotted cadence. A station-hour is eligible at 75 percent
coverage. A station-day also requires 75 percent overall coverage and every applicable local hour to
be eligible. DST missing hours are not applicable and repeated hours use their full elapsed duration.
The internal good-hour KPI uses `internal-good-hour-v1`, PM2.5 at or below 35 ug/m3 and a provisional
85 percent target. It is not a compliance metric.

QCVN 05:2023/BTNMT is represented as reference metadata at 45 ug/Nm3 effective 2026-01-01. Simulator
data remains `not_comparable`, with no relation or annual compliance decision. WHO 2021 is represented
as a non-legal 24-hour guideline at 15 ug/m3. These blocks and the internal KPI remain separate.

Device impact uses only successful ACK events correlated to a command intent and a versioned
`device_operating_profiles` row that covers the complete acknowledged interval. Intervals are
half-open and clipped by the next successful ACK, intended duration and report end, preventing overlap
and double-counting. PM2.5 uses covered 15-minute before and final-after windows. Energy uses the
declared `boost_baseline_v1` counterfactual. Missing or invalid inputs produce null,
`insufficient_data` and an allow-listed reason code; zero is reserved for a complete calculation whose
result is zero. The bundled profile is explicitly simulated and is not field calibration.

Weekly reports persist exactly 168 wall-clock cells per view. `all_stations` is the unweighted mean of
eligible station-hours and requires both three stations and 75 percent of the active-station snapshot.
The fixed `pm25-fixed-scale-v1` stops are 0, 15, 35, 45, 75 and 150 ug/m3. Missing cells remain N/A.

The live narrative provider returns typed claim sentences. Allowed types are trend, coverage,
reference, acknowledged activity and estimate availability, and each requires its evidence block.
Digits, URLs, email, HTML, causal/legal/health-benefit language or any malformed sentence rejects the
whole provider response and selects the deterministic composer.

After statistics, evidence and narrative are final, the backend serializes the canonical payload as
compact, sorted-key UTF-8 JSON with Unicode preserved and NaN/Infinity forbidden. SHA-256 lowercase
hex is persisted outside the payload. Markdown, HTML, PDF and the UI consume only the same persisted
publication view-model. The checksum is an integrity marker, not a digital signature.

PDF remains ReportLab Platypus with vector tables/drawing and a bundled DejaVu runtime font. We do not
introduce WeasyPrint.

## Consequences

- Migration `20260829_007_esg_reports.sql` is additive and idempotent, creates the profile exclusion
  constraint and leaves legacy reports readable.
- Missing ESG or narrative provider input never fails environmental aggregation.
- Manual and Beat generation continue to share the ADR 0011 report identity and lease semantics.
- QCVN/WHO/KPI/estimate disclaimers are required in the UI and all publication formats.
- Any formula, field meaning, coverage gate, checksum payload or color-scale change requires a new
  contract version and a superseding ADR.

## Compatibility

This ADR extends ADR 0011 and preserves ADR 0003/0009 HITL boundaries. It does not authorize device
control, legal compliance claims, production calibration assumptions or environmental defaults.
