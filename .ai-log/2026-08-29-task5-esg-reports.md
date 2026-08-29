# AI log — B7-05 ESG reports

## Goal

Implement `b7-esg-reports-v1` end-to-end without overwriting the existing B7-02 worktree changes.

## Main changes

- Added ADR 0020, report policy/config/OpenAPI fields and additive API/domain documentation.
- Added idempotent migration 007, legacy report metadata, canonical checksum and a versioned simulated
  FILTER-01 operating profile with a non-overlap exclusion constraint.
- Added deterministic coverage/reference/DST, ACK/profile ESG and 7x24 matrix services.
- Added typed narrative claims with whole-response fallback and one persisted publication view-model
  for UI, Markdown, HTML and ReportLab PDF.
- Added React matrix selector/tooltip/N-A hatch, ESG/reference/KPI blocks, checksum and legacy states.
- Connected the Manager reports entry point, preserved `/reports` deep links across session restore and
  rendered special screens standalone so the map/polling surface is not mounted behind the report hub.
- Added backend targeted tests, frontend `test:reports`, Docker font support and runbook/test evidence.

## Decisions

- Internal `internal-good-hour-v1` classifies a covered station-hour as good at PM2.5 <= 35 ug/m3;
  the 85 percent target is explicitly non-compliance.
- QCVN is always `not_comparable` for simulator data. WHO remains a guideline. Annual evaluation is false.
- Missing ESG inputs are nullable insufficient-data blocks; complete zero is never used as a fallback.
- DejaVu is installed in the backend image so ReportLab can render Vietnamese without HTML-to-PDF;
  a clean ReportLab overlay is merged with pypdf so split tables cannot cover fixed page decorations.

## Validation run

- Final container pytest: 46/46 report tests passed in 77.27 seconds, including the existing report
  generator/schema tests; JUnit evidence was written under ignored `tmp/`.
- Ruff passed for the complete B7-05 Python surface after the final PDF change.
- `npm run test:reports`: passed (15 contract checks).
- `npm run build`: passed; 2319 modules transformed.
- `docker compose config --quiet`: passed.
- `docker compose build backend`: passed.
- Full migration chain run twice: both passed; migration 007 second pass emitted only safe existing-object
  notices and upserted one simulated profile.
- Service smoke against PostgreSQL: daily completed and reused; checksum length 64; ESG insufficient did
  not fail; weekly all-stations view had 168 cells; provider-not-configured fallback persisted.
- Real async smoke passed after rebuilding Celery images: RabbitMQ worker pinged, the weekly task completed,
  the repeated identity reused report `e17bd537-5c91-4a68-932f-7aac95d411b2`, and its six views each had
  168 cells. A deliberately invalid non-UUID `generated_by` was rejected with `invalid_generated_by`.
- PDF QA: A4, three pages, 144-DPI render inspected; Vietnamese font, watermark, tables/page breaks,
  disclaimer and vector N/A matrix were readable with no clipping/overlap. Final artifact was 110,191 bytes.
- Live frontend QA passed with a Manager session on `/reports`: daily and weekly persisted reports loaded,
  schema/checksum and the weekly matrix rendered, refresh recovered a transient 10-second request timeout,
  and the 390x844 responsive check had no horizontal overflow. The async worker/Beat containers were
  stopped after smoke validation while the core Compose services remained healthy.
- Reports Hub visual refresh completed: added an executive hero/publishing panel, evidence and integrity
  trust signals, structured period controls, publication header, semantic KPI cards, modernized tables,
  ESG/matrix/narrative surfaces and responsive styling. Live QA passed at 1280x800 and 390x844 with no
  horizontal overflow or report-level error; the 15 report UI checks and production build still pass.
- Reader-focused follow-up completed: the report screen now puts a four-card Vietnamese executive summary
  ahead of technical detail and collapses the raw backend narrative. Publication exports use the same
  stored statistics to produce a Vietnamese reader summary, move report ID/schema/checksum under
  "Thông tin kiểm tra", and keep legacy behavior. A newly rendered PDF was visually checked at 144 DPI.

## User-owned changes preserved

The pre-existing B7-02 changes in core/main/schema/Compose/frontend types-client/specs/docs and migration
006 were retained. Migration 007 follows them and Compose executes both in order.

## Remaining limitations

- FILTER-01 coefficients are simulated seed values, not field calibration.
- No paid/live narrative provider or real inbox delivery was invoked.
- The checked-in `.venv` launcher is stale and points at a missing Windows Store Python; validation used
  the rebuilt Docker images instead.
- The smoke report used a no-measurement future period to prove graceful insufficiency; deterministic
  formula/matrix fixture values are covered by automated tests.
