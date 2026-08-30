import asyncio
import re
from contextlib import asynccontextmanager, suppress
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal
from uuid import NAMESPACE_URL, uuid4, uuid5

from fastapi import BackgroundTasks, Body, Depends, FastAPI, Header, Query, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse, Response
from pydantic import BaseModel, ConfigDict, Field, StrictBool

from .core import Settings
from .dependencies.auth import (
    get_auth_service,
    get_current_user,
    get_optional_user,
    require_admin,
    require_manager,
    set_auth_service,
)
from .schemas.measurements import MeasurementIngestionRequest
from .services.agent_service import AgentService, AgentServiceError
from .services.alert_engine import AlertEngine
from .services.approval_service import ApprovalService, configure_default_service
from .services.audit_service import MANAGER_AUDIT_ACTIONS, AuditService
from .services.auth_service import AuthService
from .services.automatic_proposal_service import AutomaticProposalService
from .services.clean_running_route_service import CleanRunningRouteService
from .services.conversational_agent_service import conversational_agent
from .services.csrf_service import (
    CSRF_COOKIE_NAME,
    generate_csrf_token,
    validate_csrf,
)
from .services.database import Database, ServiceError
from .services.device_service import DeviceService
from .services.email_service import AuthEmailService
from .services.forecast_service import InsufficientForecastHistory, trend_forecast
from .services.prophet_forecast_service import prophet_service
from .services.geospatial_agent_service import geospatial_agent
from .services.ingestion_service import MeasurementIngestionService
from .services.inhaled_dose_service import InhaledDoseService
from .services.job_service import get_job, mark_job_failed, reserve_job
from .services.live_telemetry_engine import live_engine
from .services.notification_preference_service import NotificationPreferenceService
from .services.personalized_alert_repository import PersonalizedAlertRepository
from .services.predictive_warning_service import (
    PREDICTIVE_WARNING_DISCLAIMER,
    PredictiveWarningNotificationService,
    PredictiveWarningService,
)
from .services.report_generator_service import ReportGeneratorService
from .services.report_narrative_service import HttpReportNarrator
from .services.report_policy import ReportPolicy
from .services.report_repository import PostgresReportRepository
from .services.resident_alert_notification_service import ResidentAlertNotificationService
from .services.spatial_dispersion_service import SpatialDispersionService
from .services.station_service import StationService
from .services.temporal_resolver import temporal_resolver
from .services.user_admin_service import UserAdminService
from .services.user_service import UserService
from .services.ventilation_service import VentilationService
from .services.weather_service import WeatherService

try:
    from .tasks.agent_tasks import run_agent_job
    from .tasks.forecast_tasks import run_forecast_job
    from .tasks.notification_tasks import publish_approved_device_command, send_notification_job
    from .tasks.predictive_warning_tasks import send_predictive_warning_notification
except ModuleNotFoundError:
    run_agent_job = None
    run_forecast_job = None
    publish_approved_device_command = None
    send_notification_job = None
    send_predictive_warning_notification = None


class AgentChatRequest(BaseModel):
    user_id: str = Field(
        ...,
        min_length=1,
        max_length=120,
        pattern=r"^[A-Za-z0-9_.:@-]+$",
        examples=["demo-user"],
    )
    message: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        examples=["Hien tai co nen chay bo o cong vien khong?"],
    )
    station_id: str | None = Field(default=None, pattern=r"^S0[1-5]$", examples=["S05"])
    map_context: dict[str, Any] | None = Field(default=None, description="Current map view state, selected POI, and user location")
    conversation_id: str | None = Field(default=None, max_length=120, description="Optional conversation session ID for multi-turn memory")


class AgentJobRequest(AgentChatRequest):
    idempotency_key: str | None = Field(default=None, min_length=8, max_length=200)


class ForecastJobRequest(BaseModel):
    station_id: str = Field(..., examples=["S03"])
    hours: int = Field(default=3, ge=1, le=3)
    idempotency_key: str | None = Field(default=None, min_length=8, max_length=200)


class CompareStationsRequest(BaseModel):
    station_ids: list[str] = Field(min_length=1, max_length=5)


class DemoStationOverrideRequest(BaseModel):
    pm25: float = Field(ge=1, le=500)
    co2: float = Field(ge=350, le=5000)
    noise_db: float = Field(ge=30, le=130)
    temperature: float = Field(ge=-10, le=60)


class UserProfileResponse(BaseModel):
    user_id: str
    role: str
    user_group: str | None = None


class ApprovalCreateRequest(BaseModel):
    request_type: str = Field(default="warning_proposal", min_length=3, max_length=50)
    station_id: str | None = Field(default=None, examples=["S03"])
    device_id: str | None = Field(default=None, examples=["FILTER-01"])
    proposed_action: str = Field(..., min_length=3, max_length=100, examples=["notify_sensitive_users"])
    reason: str = Field(..., min_length=3)
    evidence: dict = Field(default_factory=dict)
    duration_minutes: int | None = Field(default=None, ge=5, le=180)
    intensity_percent: int | None = Field(default=None, ge=1, le=100)
    created_by: str = Field(default="ai_agent", min_length=2, max_length=50)


class ApprovalReviewRequest(BaseModel):
    version: int = Field(..., ge=1)
    note: str | None = Field(default=None, max_length=1000)


class DeviceControlProposalRequest(BaseModel):
    action: Literal["eco_mode", "standby"]
    reason: str = Field(..., min_length=5, max_length=1000)


class ReportGenerateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["daily", "weekly"]
    period_start: datetime | None = None
    period_end: datetime | None = None
    timezone: str | None = Field(default=None, min_length=1, max_length=80)


class EnvironmentalReportResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    report_id: str
    report_type: Literal["daily", "weekly"]
    period_start: datetime
    period_end: datetime
    timezone: str
    status: Literal["generating", "completed", "failed"]
    schema_version: str = "periodic-report-v1"
    statistics: dict[str, Any] = Field(default_factory=dict)
    evidence_summary: dict[str, Any] = Field(default_factory=dict)
    narrative: str | None = None
    generation_mode: str
    model_source: str
    content_checksum_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    generated_by: str | None = None
    failure_code: str | None = None
    created_at: datetime
    completed_at: datetime | None = None
    reused: bool | None = None


class EnvironmentalReportListResponse(BaseModel):
    items: list[EnvironmentalReportResponse]


class RegisterRequest(BaseModel):
    email: str = Field(..., min_length=5, max_length=200, examples=["user@example.com"])
    password: str = Field(..., min_length=8, max_length=1024, examples=["SecurePassword123!"])
    full_name: str | None = Field(default=None, max_length=150, examples=["Nguyen Van B"])
    sensitivity_group: str | None = Field(default="normal", examples=["normal", "sensitive", "outdoor_sport"])


class ProfileUpdateRequest(BaseModel):
    """Self-service profile fields supported by the MVP.

    A group is a recommendation policy selector, not a diagnosis or medical record.
    """

    full_name: str | None = Field(default=None, min_length=1, max_length=150)
    sensitivity_group: Literal["normal", "sensitive", "outdoor_sport"] | None = None


class AdminUserUpdateRequest(BaseModel):
    role: Literal["resident", "manager", "admin"] | None = None
    status: Literal["active", "disabled"] | None = None
    reason: str = Field(..., min_length=3, max_length=500)


class DemoLoginRequest(BaseModel):
    persona: Literal["resident", "sensitive", "outdoor_sport", "manager", "admin"] = Field(
        ...,
        examples=["resident", "sensitive", "outdoor_sport", "manager", "admin"],
    )


class LoginRequest(BaseModel):
    email: str = Field(..., min_length=1, max_length=200, examples=["resident@vinuni.edu.vn"])
    password: str = Field(..., min_length=1, max_length=1024, examples=["AirGuard@2026"])


class VerifyEmailRequest(BaseModel):
    token: str = Field(..., min_length=6, max_length=256, examples=["123456"])


class ResendVerificationRequest(BaseModel):
    email: str = Field(..., min_length=5, max_length=200, examples=["user@example.com"])


class ForgotPasswordRequest(BaseModel):
    email: str = Field(..., min_length=5, max_length=200, examples=["user@example.com"])


class ResetPasswordRequest(BaseModel):
    token: str = Field(..., min_length=16, max_length=256)
    new_password: str = Field(..., min_length=8, max_length=1024, examples=["NewSecurePassword123!"])


class InhaledMassRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    station_id: str = Field(pattern=r"^S0[1-5]$")
    activity: str
    duration_minutes: int
    data_mode: str = "current"
    forecast_hour: int | None = None


class RouteOriginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    lat: float
    lon: float
    source: str


class CleanRunningRouteRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    origin: RouteOriginRequest
    target_distance_km: float
    pace_minutes_per_km: float | None = None
    data_mode: str = "current"
    forecast_hour: int | None = None


class NotificationPreferencesPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    environmental_email_enabled: StrictBool | None = None
    predictive_email_enabled: StrictBool | None = None


class PredictiveWarningEvaluateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    station_id: str = Field(pattern=r"^S0[1-5]$")
    dry_run: StrictBool = True


class ChecklistItemUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    completed: StrictBool


def _enqueue_manager_proposal_notification(
    *,
    proposal_id: str,
    station_id: str,
    proposed_action: str,
    correlation_id: str,
) -> None:
    if send_notification_job is None:
        audit_service.record(
            actor_type="system",
            actor_role="backend",
            action="proposal.notification.skipped",
            entity_type="approval_request",
            entity_id=proposal_id,
            correlation_id=correlation_id,
            outcome="skipped",
            details={"reason": "notification_dependency_missing"},
        )
        return

    recipients = user_service.list_manager_notification_recipients()
    if not recipients:
        audit_service.record(
            actor_type="system",
            actor_role="backend",
            action="proposal.notification.skipped",
            entity_type="approval_request",
            entity_id=proposal_id,
            correlation_id=correlation_id,
            outcome="skipped",
            details={"reason": "manager_recipient_unavailable"},
        )
        return

    for recipient in recipients:
        idempotency_key = f"proposal-notification:{proposal_id}:{recipient['user_id']}"
        task_id = str(uuid5(NAMESPACE_URL, f"airguard:{idempotency_key}"))
        payload = {
            "recipient": recipient["email"],
            "message": (
                f"AirGuard có proposal {proposal_id} đang chờ Manager duyệt cho trạm "
                f"{station_id}, hành động {proposed_action}."
            ),
            "idempotency_key": idempotency_key,
        }
        job, created = reserve_job(task_id, "proposal_notification", idempotency_key, payload)
        dispatch_task_id = str(job.get("task_id") or task_id)
        if not created and job.get("status") != "FAILURE":
            continue
        try:
            send_notification_job.apply_async(kwargs=payload, task_id=dispatch_task_id)
            audit_service.record(
                actor_type="system",
                actor_role="backend",
                action="proposal.notification.enqueued",
                entity_type="approval_request",
                entity_id=proposal_id,
                correlation_id=correlation_id,
                details={"recipient_user_id": recipient["user_id"]},
            )
        except Exception as exc:
            mark_job_failed(dispatch_task_id, "proposal_notification_enqueue_failed", retrying=False)
            audit_service.record(
                actor_type="system",
                actor_role="backend",
                action="proposal.notification.failure",
                entity_type="approval_request",
                entity_id=proposal_id,
                correlation_id=correlation_id,
                outcome="failure",
                details={
                    "recipient_user_id": recipient["user_id"],
                    "reason": exc.__class__.__name__,
                },
            )


settings = Settings.load()
db = Database(settings.database_url)
audit_service = AuditService(db)
station_service = StationService(db, settings.stale_after_seconds)
user_service = UserService(db)
personalized_alert_repository = PersonalizedAlertRepository(db)
notification_preference_service = NotificationPreferenceService(
    personalized_alert_repository,
    audit_service,
)
inhaled_dose_service = InhaledDoseService(
    station_service,
    observation_max_age_seconds=settings.stale_after_seconds,
    min_forecast_confidence=settings.predictive_warning_min_confidence,
    forecast_max_age_seconds=settings.predictive_warning_forecast_max_age_seconds,
)
clean_running_route_service = CleanRunningRouteService(
    station_service,
    observation_max_age_seconds=settings.stale_after_seconds,
    min_forecast_confidence=settings.predictive_warning_min_confidence,
    forecast_max_age_seconds=settings.predictive_warning_forecast_max_age_seconds,
)
geospatial_agent.clean_route_service = clean_running_route_service
predictive_warning_notifier = PredictiveWarningNotificationService(
    personalized_alert_repository,
    audit_service,
    notification_task=send_predictive_warning_notification,
    enabled=settings.predictive_warning_notifications_enabled,
)
predictive_warning_service = PredictiveWarningService(
    personalized_alert_repository,
    station_service,
    audit_service,
    notifier=predictive_warning_notifier,
    policy_version=settings.predictive_warning_policy_version,
    threshold_rule_version=settings.alert_rule_version,
    warning_threshold=settings.alert_warning_threshold,
    critical_threshold=settings.alert_critical_threshold,
    observation_max_age_seconds=settings.stale_after_seconds,
    min_confidence=settings.predictive_warning_min_confidence,
    forecast_max_age_seconds=settings.predictive_warning_forecast_max_age_seconds,
    clear_evaluations=settings.predictive_warning_clear_evaluations,
    lead_minutes=settings.predictive_warning_lead_minutes,
    lead_tolerance_minutes=settings.predictive_warning_lead_tolerance_minutes,
)
user_admin_service = UserAdminService(db, audit_service)
device_service = DeviceService(db)
email_service = AuthEmailService(frontend_url=settings.frontend_url)
auth_service = AuthService(
    db,
    audit_service,
    email_service,
    session_ttl_seconds=settings.session_ttl_seconds,
    verification_token_ttl_seconds=settings.verification_token_ttl_seconds,
    reset_token_ttl_seconds=settings.reset_token_ttl_seconds,
    rate_limit_max_attempts=settings.rate_limit_login_max_attempts,
    rate_limit_lockout_seconds=settings.rate_limit_lockout_seconds,
    demo_mode_enabled=settings.auth_demo_mode,
    google_client_id=settings.google_client_id,
    google_client_secret=settings.google_client_secret,
    google_redirect_uri=settings.google_redirect_uri,
)
set_auth_service(auth_service)
ventilation_service = VentilationService(
    db,
    pm25_threshold=settings.alert_warning_threshold,
    co2_threshold=settings.co2_warning_threshold,
    trigger_duration_seconds=settings.ventilation_trigger_seconds,
    recovery_duration_seconds=settings.ventilation_recovery_minutes * 60,
    safe_pm25_threshold=settings.ventilation_safe_pm25_threshold,
    safe_co2_threshold=settings.ventilation_safe_co2_threshold,
    stale_after_seconds=settings.stale_after_seconds,
    max_gap_seconds=settings.ventilation_max_gap_seconds,
    default_duration_minutes=settings.ventilation_default_duration_minutes,
    default_intensity_percent=settings.ventilation_intensity_percent,
    demo_override_provider=live_engine.get_demo_override_evidence,
)
approval_service = ApprovalService(
    db,
    audit_service,
    pending_ttl_seconds=settings.proposal_pending_ttl_seconds,
    default_duration_minutes=settings.ventilation_default_duration_minutes,
    default_intensity_percent=settings.ventilation_intensity_percent,
    ventilation_service=ventilation_service,
)
ingestion_service = MeasurementIngestionService(
    db,
    stale_after_seconds=settings.stale_after_seconds,
    audit_service=audit_service,
)
alert_engine = AlertEngine(
    db,
    station_service,
    audit_service,
    warning_threshold=settings.alert_warning_threshold,
    critical_threshold=settings.alert_critical_threshold,
    rule_version=settings.alert_rule_version,
    consecutive_measurements=settings.alert_consecutive_measurements,
    stale_after_seconds=settings.stale_after_seconds,
    environmental_rule_version=settings.environmental_alert_rule_version,
    aqi_warning_threshold=settings.aqi_warning_threshold,
    aqi_critical_threshold=settings.aqi_critical_threshold,
    co2_warning_threshold=settings.co2_warning_threshold,
    co2_critical_threshold=settings.co2_critical_threshold,
    noise_warning_threshold=settings.noise_warning_threshold,
    noise_critical_threshold=settings.noise_critical_threshold,
    temperature_warning_threshold=settings.temperature_warning_threshold,
    temperature_critical_threshold=settings.temperature_critical_threshold,
    ventilation_service=ventilation_service,
)
configure_default_service(approval_service)
agent_service = AgentService(
    settings.agent_service_url,
    timeout_seconds=settings.agent_service_timeout_seconds,
)
automatic_proposal_service = AutomaticProposalService(
    agent_service=agent_service,
    approval_service=approval_service,
    audit_service=audit_service,
    enabled=settings.auto_proposal_enabled,
    allowed_stations=settings.auto_proposal_stations,
    proposal_notifier=_enqueue_manager_proposal_notification,
)
resident_alert_notification_service = ResidentAlertNotificationService(
    user_service=user_service,
    audit_service=audit_service,
    notification_task=send_notification_job,
    enabled=settings.resident_alert_notifications_enabled,
    cooldown_seconds=settings.resident_alert_notification_cooldown_seconds,
)
report_narrator = (
    HttpReportNarrator(
        settings.report_narrative_endpoint,
        timeout_seconds=settings.report_narrative_timeout_seconds,
        service_token=settings.report_narrative_service_token,
    )
    if settings.report_narrative_endpoint
    else None
)
report_service = ReportGeneratorService(
    PostgresReportRepository(db),
    narrator=report_narrator,
    policy=ReportPolicy(
        report_policy_version=settings.report_policy_version,
        expected_sample_interval_seconds=settings.report_expected_sample_interval_seconds,
        minimum_coverage_ratio=settings.report_minimum_coverage_ratio,
        matrix_min_eligible_stations=settings.report_matrix_min_eligible_stations,
    ),
)
weather_service = WeatherService(
    settings.weather_api_base_url,
    latitude=settings.weather_latitude,
    longitude=settings.weather_longitude,
    timeout_seconds=settings.weather_timeout_seconds,
    max_age_seconds=settings.weather_max_age_seconds,
)
spatial_service = SpatialDispersionService(station_service, weather_provider=weather_service)


async def _telemetry_ticker() -> None:
    while True:
        try:
            from .services.live_telemetry_engine import live_engine

            live_engine.sync_ventilation_devices(device_service.list_devices())
            live_engine.tick()
        except Exception:
            pass
        await asyncio.sleep(10)


def _bootstrap_database() -> None:
    if not settings.database_url:
        return
    try:
        with db.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'stations')")
                exists = cur.fetchone()[0]
                db_dir = Path(__file__).resolve().parent.parent / "db"
                if not exists:
                    schema_path = db_dir / "schema.sql"
                    seed_path = db_dir / "seed.sql"
                    if schema_path.exists():
                        cur.execute(schema_path.read_text(encoding="utf-8"))
                    if seed_path.exists():
                        cur.execute(seed_path.read_text(encoding="utf-8"))

                migrations_dir = db_dir / "migrations"
                if migrations_dir.exists():
                    for migration_file in sorted(migrations_dir.glob("*.sql")):
                        try:
                            cur.execute(migration_file.read_text(encoding="utf-8"))
                        except Exception as mig_exc:
                            print(f"Migration {migration_file.name} notice: {mig_exc}")
    except Exception as exc:
        print(f"Database bootstrap notice: {exc}")


@asynccontextmanager
async def app_lifespan(_app: FastAPI):
    _bootstrap_database()
    telemetry_task = asyncio.create_task(_telemetry_ticker())
    try:
        yield
    finally:
        telemetry_task.cancel()
        with suppress(asyncio.CancelledError):
            await telemetry_task


app = FastAPI(title="AirGuard AI API", version="0.3.0", lifespan=app_lifespan)
REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9_.:-]{1,120}$")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_request_id(request: Request, call_next):
    candidate = request.headers.get("X-Request-ID")
    request_id = candidate if candidate and REQUEST_ID_PATTERN.fullmatch(candidate) else str(uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


def _request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "unknown")


def _is_ocean_park_area_overview(message: str) -> bool:
    """Return true for an Ocean Park-wide question without a station target.

    A selected pin is navigation state, not an implicit user intent. In
    particular, map POIs must not become the answer target for a broad Ocean
    Park question merely because a user last viewed that POI.
    """
    normalized = message.casefold()
    mentions_ocean_park = any(term in normalized for term in ("ocean park", "oceanpark", "ocp1", "ocp 1"))
    has_explicit_station = re.search(r"\bs0?[1-5]\b", normalized, flags=re.IGNORECASE) is not None
    return mentions_ocean_park and not has_explicit_station


def _spatial_overview_response(*, agent_result: dict[str, Any], request_id: str) -> dict[str, Any]:
    """Build a map-neutral response for a grounded whole-area overview."""
    trace = agent_result.get("trace", {})
    return {
        "answer": {"summary": agent_result["answer"], "details": ""},
        "response": agent_result["answer"],
        "intent": trace.get("intent", "spatial"),
        "evidence": [],
        "sources": agent_result.get("sources", []),
        # Preserve the user's current map view; do not replay a POI fallback.
        "map_actions": [],
        "used_tools": agent_result.get("used_tools", []),
        "request_id": request_id,
        "trace": {
            **trace,
            "map_planner": "agent_spatial_overview",
            "map_intent": "spatial_overview",
        },
    }


def _error_response(request: Request, *, status_code: int, code: str, message: str, details: dict | list | None = None):
    return JSONResponse(
        status_code=status_code,
        content={
            "code": code,
            "message": message,
            "request_id": _request_id(request),
            "details": details or {},
        },
    )


@app.exception_handler(ServiceError)
async def service_error_handler(request: Request, exc: ServiceError):
    return _error_response(
        request,
        status_code=exc.status_code,
        code=exc.code,
        message=exc.message,
        details=exc.details,
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    return _error_response(
        request,
        status_code=422,
        code="validation_error",
        message="Request validation failed",
        details=jsonable_encoder(exc.errors()),
    )


@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, exc: Exception):
    return _error_response(
        request,
        status_code=500,
        code="internal_error",
        message="Internal server error",
    )


@app.get("/api/v1/auth/config")
def get_auth_config() -> dict:
    return {
        "demo_mode": settings.auth_demo_mode,
        "google_auth_enabled": bool(settings.google_client_id),
    }


@app.get("/api/v1/auth/csrf")
def get_csrf_token() -> JSONResponse:
    csrf_token = generate_csrf_token()
    res = JSONResponse(
        content={
            "csrf_token": csrf_token,
            "demo_mode": settings.auth_demo_mode,
            "google_auth_enabled": bool(settings.google_client_id),
        }
    )
    res.set_cookie(
        key=CSRF_COOKIE_NAME,
        value=csrf_token,
        httponly=False,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        max_age=settings.session_ttl_seconds,
        path="/",
    )
    return res


@app.post("/api/v1/auth/demo-login")
def auth_demo_login(
    request: Request,
    body: DemoLoginRequest,
    auth_svc: AuthService = Depends(get_auth_service),
) -> JSONResponse:
    validate_csrf(request)
    client_ip = request.client.host if request.client else None
    raw_session_token, user_info = auth_svc.demo_login(
        persona=body.persona,
        correlation_id=_request_id(request),
        ip_address=client_ip,
    )
    csrf_token = generate_csrf_token()
    response = JSONResponse(
        content={
            "user": user_info,
            "csrf_token": csrf_token,
            "message": f"Đăng nhập thành công với vai trò {user_info['role']}.",
        }
    )
    response.set_cookie(
        key="airguard_session",
        value=raw_session_token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        max_age=settings.session_ttl_seconds,
        path="/",
    )
    response.set_cookie(
        key=CSRF_COOKIE_NAME,
        value=csrf_token,
        httponly=False,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        max_age=settings.session_ttl_seconds,
        path="/",
    )
    return response


@app.get("/api/v1/auth/google/start")
def auth_google_start(
    request: Request,
    auth_svc: AuthService = Depends(get_auth_service),
) -> RedirectResponse:
    if not auth_svc.google_client_id:
        return RedirectResponse(
            url=f"{settings.frontend_url}/?auth=google_error&error=not_configured",
            status_code=307,
        )
    auth_url = auth_svc.get_google_auth_url()
    return RedirectResponse(url=auth_url, status_code=307)


@app.get("/api/v1/auth/google/callback")
def auth_google_callback(
    request: Request,
    code: str = Query(None),
    state: str = Query(None),
    error: str = Query(None),
    auth_svc: AuthService = Depends(get_auth_service),
) -> RedirectResponse:
    if error or not code:
        reason = error or "cancelled"
        return RedirectResponse(url=f"{settings.frontend_url}/?auth=google_error&error={reason}", status_code=307)
    try:
        client_ip = request.client.host if request.client else None
        raw_session_token, user_info = auth_svc.handle_google_callback(
            code=code,
            state=state,
            client_ip=client_ip,
            correlation_id=_request_id(request),
        )
        csrf_token = generate_csrf_token()
        response = RedirectResponse(url=f"{settings.frontend_url}/?auth=google_success", status_code=307)
        response.set_cookie(
            key="airguard_session",
            value=raw_session_token,
            httponly=True,
            secure=settings.cookie_secure,
            samesite=settings.cookie_samesite,
            max_age=settings.session_ttl_seconds,
            path="/",
        )
        response.set_cookie(
            key=CSRF_COOKIE_NAME,
            value=csrf_token,
            httponly=False,
            secure=settings.cookie_secure,
            samesite=settings.cookie_samesite,
            max_age=settings.session_ttl_seconds,
            path="/",
        )
        return response
    except Exception:
        return RedirectResponse(url=f"{settings.frontend_url}/?auth=google_error&error=server_error", status_code=307)


@app.post("/api/v1/auth/register", status_code=201)
def auth_register(
    request: Request,
    body: RegisterRequest,
    auth_svc: AuthService = Depends(get_auth_service),
) -> dict:
    validate_csrf(request)
    return auth_svc.register(
        email=body.email,
        password=body.password,
        full_name=body.full_name,
        sensitivity_group=body.sensitivity_group,
        correlation_id=_request_id(request),
    )


@app.post("/api/v1/auth/verify-email")
def auth_verify_email(
    request: Request,
    body: VerifyEmailRequest,
    auth_svc: AuthService = Depends(get_auth_service),
) -> dict:
    validate_csrf(request)
    return auth_svc.verify_email(raw_token=body.token, correlation_id=_request_id(request))


@app.post("/api/v1/auth/resend-verification")
def auth_resend_verification(
    request: Request,
    body: ResendVerificationRequest,
    auth_svc: AuthService = Depends(get_auth_service),
) -> dict:
    validate_csrf(request)
    return auth_svc.resend_verification(email=body.email, correlation_id=_request_id(request))


@app.post("/api/v1/auth/login")
def auth_login(
    request: Request,
    body: LoginRequest,
    auth_svc: AuthService = Depends(get_auth_service),
) -> JSONResponse:
    client_ip = request.client.host if request.client else None
    raw_session_token, user_info = auth_svc.login(
        email=body.email,
        password=body.password,
        correlation_id=_request_id(request),
        ip_address=client_ip,
    )
    csrf_token = generate_csrf_token()
    response = JSONResponse(
        content={
            "user": user_info,
            "csrf_token": csrf_token,
            "message": "Đăng nhập thành công.",
        }
    )
    response.set_cookie(
        key="airguard_session",
        value=raw_session_token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        max_age=settings.session_ttl_seconds,
        path="/",
    )
    response.set_cookie(
        key=CSRF_COOKIE_NAME,
        value=csrf_token,
        httponly=False,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        max_age=settings.session_ttl_seconds,
        path="/",
    )
    return response


@app.get("/api/v1/auth/me")
def auth_me(current_user: dict = Depends(get_current_user)) -> dict:
    return {"user": current_user}


@app.patch("/api/v1/auth/profile")
def auth_update_profile(
    request: Request,
    body: ProfileUpdateRequest,
    current_user: dict = Depends(get_current_user),
    auth_svc: AuthService = Depends(get_auth_service),
) -> dict:
    validate_csrf(request)
    return {
        "user": auth_svc.update_profile(
            user_id=str(current_user["user_id"]),
            full_name=body.full_name,
            sensitivity_group=body.sensitivity_group,
            correlation_id=_request_id(request),
        )
    }


@app.get("/api/v1/auth/notification-preferences")
def get_notification_preferences(current_user: dict = Depends(get_current_user)) -> dict:
    return {
        "preferences": notification_preference_service.get(str(current_user["user_id"])),
        "contract_version": "b7-personalized-alerts-v1",
    }


@app.patch("/api/v1/auth/notification-preferences")
def update_notification_preferences(
    request: Request,
    body: NotificationPreferencesPatch,
    current_user: dict = Depends(get_current_user),
) -> dict:
    validate_csrf(request)
    values = body.model_dump(exclude_none=True)
    if not values:
        raise ServiceError(
            "notification_preferences_empty_update",
            "At least one notification preference is required",
            422,
        )
    return {
        "preferences": notification_preference_service.update(
            user_id=str(current_user["user_id"]),
            actor_role=str(current_user["role"]),
            values=values,
            correlation_id=_request_id(request),
        ),
        "contract_version": "b7-personalized-alerts-v1",
    }


@app.post("/api/v1/auth/logout")
def auth_logout(
    request: Request,
    auth_svc: AuthService = Depends(get_auth_service),
) -> JSONResponse:
    session_cookie = request.cookies.get("airguard_session") or ""
    auth_svc.logout(raw_session_token=session_cookie, correlation_id=_request_id(request))
    response = JSONResponse(content={"success": True, "message": "Đã đăng xuất an toàn."})
    response.delete_cookie(key="airguard_session", path="/")
    response.delete_cookie(key=CSRF_COOKIE_NAME, path="/")
    return response


@app.post("/api/v1/auth/forgot-password")
def auth_forgot_password(
    request: Request,
    body: ForgotPasswordRequest,
    auth_svc: AuthService = Depends(get_auth_service),
) -> dict:
    validate_csrf(request)
    return auth_svc.forgot_password(email=body.email, correlation_id=_request_id(request))


@app.post("/api/v1/auth/reset-password")
def auth_reset_password(
    request: Request,
    body: ResetPasswordRequest,
    auth_svc: AuthService = Depends(get_auth_service),
) -> dict:
    validate_csrf(request)
    return auth_svc.reset_password(
        raw_token=body.token,
        new_password=body.new_password,
        correlation_id=_request_id(request),
    )


@app.get("/health")
def health_check() -> dict:
    return {"status": "ok", "service": "airguard-api", "version": "0.3.0"}


@app.get("/ready")
def readiness_check() -> dict:
    db.ping()
    return {"status": "ready", "dependencies": {"database": "ok"}}



@app.get("/api/v1/stations")
def get_stations() -> dict:
    return {"items": station_service.list_stations()}



@app.get("/api/v1/stations/{station_id}")
def get_station(station_id: str) -> dict:
    return station_service.get_station(station_id)



@app.get("/api/v1/stations/{station_id}/current")
def get_station_current(station_id: str) -> dict:
    station = station_service.get_station(station_id)
    # ``timestamp`` is the observation timestamp, not the request time. This
    # prevents an old measurement from appearing fresh merely because it was read.
    return {**station, "timestamp": station.get("updated_at")}


@app.get("/api/v1/demo/station-overrides")
def get_demo_station_overrides(current_user: dict = Depends(require_manager)) -> dict:
    return {"demo_mode": True, "overrides": live_engine.get_demo_overrides()}


@app.put("/api/v1/demo/stations/{station_id}/override")
def set_demo_station_override(
    station_id: str,
    body: DemoStationOverrideRequest,
    request: Request,
    current_user: dict = Depends(require_manager),
) -> dict:
    if station_id not in {"S01", "S02", "S03", "S04", "S05"}:
        raise ServiceError("station_not_found", "Station was not found", 404, {"station_id": station_id})
    values = body.model_dump()
    station = live_engine.set_demo_override(station_id, values)
    audit_service.record(
        actor_type="user", actor_id=current_user["user_id"], actor_role=current_user["role"],
        action="demo_station_override.set", entity_type="station", entity_id=station_id,
        correlation_id=_request_id(request), outcome="success", details={"metrics": values},
    )
    return {"station": station, "demo_override": True, "message": "Demo override is active; automatic simulation remains running."}


@app.delete("/api/v1/demo/stations/{station_id}/override")
def clear_demo_station_override(
    station_id: str, request: Request, current_user: dict = Depends(require_manager)
) -> dict:
    live_engine.clear_demo_override(station_id)
    audit_service.record(
        actor_type="user", actor_id=current_user["user_id"], actor_role=current_user["role"],
        action="demo_station_override.clear", entity_type="station", entity_id=station_id,
        correlation_id=_request_id(request), outcome="success", details={},
    )
    return {"station_id": station_id, "demo_override": False, "message": "Returned to automatic simulator values."}



@app.get("/api/v1/stations/{station_id}/history")
def get_station_history(station_id: str, hours: int = Query(default=24, ge=1, le=72)) -> dict:
    return {**station_service.get_history(station_id, hours), "timestamp": datetime.now(UTC).isoformat()}


@app.post("/api/v1/stations/compare")
def compare_stations(body: CompareStationsRequest) -> dict:
    return {**station_service.compare_stations(body.station_ids), "timestamp": datetime.now(UTC).isoformat()}


@app.post("/api/v1/internal/ingestion/measurements", status_code=202)
def ingest_measurement(
    request: Request,
    body: MeasurementIngestionRequest,
    background_tasks: BackgroundTasks,
) -> dict:
    result = ingestion_service.ingest(body)
    if result.get("accepted"):
        result["alert"], evaluated_alerts = alert_engine.evaluate_station_with_alerts(
            body.station_id,
            correlation_id=_request_id(request),
        )
        _schedule_alert_side_effects(
            background_tasks,
            result["alert"],
            evaluated_alerts,
            _request_id(request),
        )
    return result


def _schedule_alert_side_effects(
    background_tasks: BackgroundTasks,
    primary_alert: dict | None,
    evaluated_alerts: list[dict],
    correlation_id: str,
) -> None:
    for alert in evaluated_alerts:
        if resident_alert_notification_service.should_notify(alert):
            background_tasks.add_task(
                resident_alert_notification_service.notify,
                alert=alert,
                correlation_id=correlation_id,
            )
    if automatic_proposal_service.should_analyze(primary_alert):
        background_tasks.add_task(
            automatic_proposal_service.analyze_and_propose,
            alert=primary_alert,
            correlation_id=correlation_id,
        )


@app.post("/api/v1/internal/ingestion/evaluate-alerts")
def evaluate_ingested_measurement(
    request: Request,
    background_tasks: BackgroundTasks,
    station_id: str | None = Body(default=None, embed=True),
) -> dict:
    if station_id:
        alert, evaluated_alerts = alert_engine.evaluate_station_with_alerts(
            station_id,
            correlation_id=_request_id(request),
        )
        _schedule_alert_side_effects(background_tasks, alert, evaluated_alerts, _request_id(request))
        return {"station_id": station_id, "alert": alert}
    evaluations = alert_engine.evaluate_all_current_with_alerts(correlation_id=_request_id(request))
    for alert, evaluated_alerts in evaluations:
        _schedule_alert_side_effects(background_tasks, alert, evaluated_alerts, _request_id(request))
    return {"status": "evaluated", "alert_count": sum(alert is not None for alert, _ in evaluations)}


@app.get("/api/v1/alerts")
def get_alerts(status: str | None = Query(default=None), station_id: str | None = Query(default=None)) -> dict:
    return {"items": alert_engine.list_alerts(status=status, station_id=station_id), "timestamp": datetime.now(UTC).isoformat()}


@app.post("/api/v1/alerts/{alert_id}/resolve")
def resolve_alert(
    request: Request,
    alert_id: str,
    current_user: dict = Depends(require_manager),
) -> dict:
    validate_csrf(request)
    return alert_engine.resolve_alert(
        alert_id,
        actor_id=current_user["user_id"],
        actor_role=current_user["role"],
        correlation_id=_request_id(request),
    )


@app.get("/api/v1/weather/current")
def get_current_weather() -> dict:
    return {**weather_service.current_weather(), "timestamp": datetime.now(UTC).isoformat()}


@app.post("/api/v1/exposure/inhaled-mass")
def estimate_inhaled_mass(body: InhaledMassRequest) -> dict:
    return {
        **inhaled_dose_service.estimate(
            station_id=body.station_id,
            activity=body.activity,
            duration_minutes=body.duration_minutes,
            data_mode=body.data_mode,
            forecast_hour=body.forecast_hour,
        ),
        "contract_version": "b7-personalized-alerts-v1",
    }


@app.post("/api/v1/routes/clean-running")
def recommend_clean_running_route(body: CleanRunningRouteRequest) -> dict:
    return {
        **clean_running_route_service.recommend(
            origin=body.origin.model_dump(),
            target_distance_km=body.target_distance_km,
            pace_minutes_per_km=body.pace_minutes_per_km,
            data_mode=body.data_mode,
            forecast_hour=body.forecast_hour,
        ),
        "contract_version": "b7-personalized-alerts-v1",
    }


@app.get("/api/v1/predictive-warnings")
def list_predictive_warnings(
    status: str | None = Query(default=None),
    station_id: str | None = Query(default=None, pattern=r"^S0[1-5]$"),
    _current_user: dict = Depends(require_manager),
) -> dict:
    return {
        "items": personalized_alert_repository.list_episodes(status=status, station_id=station_id),
        "contract_version": "b7-personalized-alerts-v1",
    }


@app.post("/api/v1/predictive-warnings/evaluate")
def evaluate_predictive_warning(
    request: Request,
    body: PredictiveWarningEvaluateRequest,
    _current_user: dict = Depends(require_manager),
) -> dict:
    validate_csrf(request)
    return {
        **predictive_warning_service.evaluate(
            body.station_id,
            dry_run=body.dry_run,
            correlation_id=_request_id(request),
        ),
        "station_id": body.station_id,
        "contract_version": "b7-personalized-alerts-v1",
    }


@app.get("/api/v1/predictive-warnings/{episode_id}")
def get_predictive_warning(
    episode_id: str,
    current_user: dict = Depends(get_current_user),
) -> dict:
    return {
        "episode": personalized_alert_repository.get_episode(episode_id),
        "checklist": personalized_alert_repository.get_checklist(
            episode_id,
            str(current_user["user_id"]),
        ),
        "disclaimer": PREDICTIVE_WARNING_DISCLAIMER,
        "contract_version": "b7-personalized-alerts-v1",
    }


@app.put("/api/v1/predictive-warnings/{episode_id}/checklist/{item_key}")
def update_predictive_warning_checklist(
    request: Request,
    episode_id: str,
    item_key: str,
    body: ChecklistItemUpdateRequest,
    current_user: dict = Depends(get_current_user),
) -> dict:
    validate_csrf(request)
    if current_user.get("role") != "resident":
        raise ServiceError("permission_denied", "Only residents can update their checklist", 403)
    item = personalized_alert_repository.put_checklist(
        episode_id,
        str(current_user["user_id"]),
        item_key,
        body.completed,
    )
    audit_service.record(
        actor_type="user",
        actor_id=str(current_user["user_id"]),
        actor_role="resident",
        action="predictive_warning.checklist_updated",
        entity_type="predictive_warning_episode",
        entity_id=episode_id,
        correlation_id=_request_id(request),
        details={"item_key": item_key, "completed": body.completed},
    )
    return {"item": item, "contract_version": "b7-personalized-alerts-v1"}


@app.get("/api/v1/spatial/heatmap")
def get_spatial_heatmap(
    metric: str = Query(default="aqi"),
    forecast_hour: int = Query(default=0, ge=0, le=24),
) -> dict:
    return spatial_service.calculate_heatmap(metric=metric, forecast_hour=forecast_hour)




@app.get("/api/v1/stations/{station_id}/forecast")
def get_station_forecast(
    station_id: str,
    hours: int = Query(default=3, ge=1, le=24),
    metric: Literal["pm25", "aqi", "co2", "noise_db", "temperature"] = Query(default="pm25"),
    model: Literal["baseline", "extended"] = Query(default="baseline"),
) -> dict:
    if model == "baseline" and hours > 3:
        raise ServiceError(
            "forecast_horizon_unsupported",
            "The baseline model supports only 1-3 hours; use model=extended for 1-24 hours",
            422,
            {"hours": hours, "model": model},
        )
    history = (
        station_service.get_forecast_history(station_id)
        if model == "baseline"
        else station_service.get_extended_forecast_history(station_id)
    )
    try:
        forecast = (
            trend_forecast(history, hours, metric=metric)
            if model == "baseline"
            else prophet_service.forecast(station_id, history, hours, metric)
        )
    except InsufficientForecastHistory as exc:
        raise ServiceError(
            "insufficient_forecast_history",
            "Fresh valid history is insufficient for baseline forecasting",
            503,
            {"station_id": station_id},
        ) from exc
    except ValueError as exc:
        raise ServiceError(
            "invalid_extended_forecast_input",
            str(exc),
            422,
            {"station_id": station_id, "model": model},
        ) from exc
    return {"station_id": station_id, "horizon_hours": hours, "is_stale": False, **forecast, "timestamp": datetime.now(UTC).isoformat()}


@app.get("/api/v1/forecast/golden-windows")
def get_golden_windows(
    station_id: str = Query(..., pattern=r"^S0[1-5]$"),
    minimum_wind_speed: float = Query(default=2.0, ge=0, le=20),
) -> dict:
    history = station_service.get_extended_forecast_history(station_id)
    try:
        forecast = prophet_service.forecast(station_id, history, 24, "aqi")
        return prophet_service.golden_windows(
            forecast,
            minimum_wind_speed=minimum_wind_speed,
        )
    except ValueError as exc:
        raise ServiceError(
            "golden_window_unavailable",
            str(exc),
            503,
            {"station_id": station_id},
        ) from exc


@app.get("/api/v1/users/{user_id}/profile", response_model=UserProfileResponse)
def get_user_profile(user_id: str) -> UserProfileResponse:
    canonical_user_id = (
        "00000000-0000-0000-0000-000000000101" if user_id == "demo-user" else user_id
    )
    row = user_service.get_profile(canonical_user_id)
    return UserProfileResponse(
        user_id=str(row["user_id"]), role=row["role"], user_group=row.get("sensitivity_group")
    )


@app.post("/api/v1/agent/chat")
async def agent_chat(
    request: Request,
    body: AgentChatRequest,
    current_user: dict | None = Depends(get_optional_user),
) -> dict:
    req_id = _request_id(request)
    # An authenticated browser cannot impersonate another profile by editing the
    # client payload. Public Demo Day visitors retain the explicit demo profile.
    effective_user_id = str(current_user.get("user_id") or body.user_id) if current_user else body.user_id
    try:
        conversation = conversational_agent.classify(
            body.message,
            station_id=body.station_id,
            map_context=body.map_context,
        )
        if (
            conversation.intent in {"greeting", "social", "clarification", "out_of_scope"}
            or conversation.intent.startswith("social.")
            or conversation.intent.startswith("conversation.")
        ):
            # Social, identity, capability, and out-of-scope replies are deliberately
            # local and deterministic: they do not need telemetry, map planning, or an LLM call.
            return conversational_agent.deterministic_response(conversation, request_id=req_id)

        # The public map's stable alias resolves to the seeded resident profile;
        # all profile fields still come from PostgreSQL rather than client input.
        profile_user_id = (
            "00000000-0000-0000-0000-000000000101"
            if effective_user_id == "demo-user"
            else effective_user_id
        )
        try:
            profile = user_service.get_profile(profile_user_id)
        except ServiceError:
            raise
        except Exception as exc:
            raise ServiceError(
                "user_profile_unavailable",
                "The user profile required for personalized analysis is unavailable",
                503,
                {"user_id": effective_user_id},
            ) from exc
        user_group = profile.get("sensitivity_group")
        if not user_group:
            raise ServiceError(
                "user_profile_incomplete",
                "A sensitivity group is required for personalized analysis",
                422,
                {"user_id": effective_user_id},
            )

        snapshots = {
            station["station_id"]: station
            for station in station_service.list_stations(allow_fallback=False)
        }
        time_context = temporal_resolver.resolve(body.message.lower().strip())
        histories: dict[str, list[dict[str, Any]]] = {}
        if time_context["is_forecast"]:
            for station_id, snapshot in snapshots.items():
                if snapshot.get("status") != "online" or snapshot.get("freshness") != "fresh":
                    continue
                try:
                    histories[station_id] = station_service.get_forecast_history(station_id)
                except ServiceError as exc:
                    if exc.code != "insufficient_forecast_history":
                        raise

        effective_station_id = body.station_id
        if not effective_station_id and body.map_context:
            effective_station_id = body.map_context.get("selected_sensor")

        agent_result = await agent_service.chat(
            message=body.message,
            user_id=effective_user_id,
            station_id=effective_station_id,
            request_id=req_id,
        )

        # Safety decisions from the canonical Agent graph are terminal. A
        # deterministic geospatial fallback must never replace a HITL refusal
        # with a clarification or route response.
        safety_category = agent_result.get("trace", {}).get("safety_category")
        if safety_category:
            canonical_answer = str(agent_result.get("answer") or "")
            return {
                "answer": {"summary": canonical_answer, "details": ""},
                "response": canonical_answer,
                "intent": agent_result.get("intent") or "safety_refusal",
                "conversation_kind": agent_result.get("conversation_kind"),
                "evidence": [],
                "sources": [],
                "map_actions": [],
                "used_tools": agent_result.get("used_tools", []),
                "tool_arguments": agent_result.get("tool_arguments", []),
                "proposal_id": None,
                "request_id": req_id,
                "trace": agent_result.get("trace", {}),
            }

        result = geospatial_agent.process_query(
            message=body.message,
            user_id=effective_user_id,
            conversation_id=body.conversation_id or f"conv_{effective_user_id}",
            station_id=effective_station_id,
            map_context=body.map_context,
            request_id=req_id,
            user_group=user_group,
            station_snapshots=snapshots,
            station_histories=histories,
        )
        # The Agent graph is the authority for the answer, tool trace and source
        # list. The deterministic geospatial service contributes UI map actions,
        # structured route geometry, and fallback for map-grounded intents.
        agent_sources = agent_result.get("sources")
        canonical_intent = agent_result.get("intent") or agent_result.get("trace", {}).get("intent", "domain")
        canonical_kind = agent_result.get("conversation_kind") or agent_result.get("trace", {}).get(
            "conversation_kind"
        )
        canonical_arguments = agent_result.get("tool_arguments", [])

        # Priority 1: Geospatial Interactive and Domain-specific Spatial/Route Intents
        if result.get("intent") in {
            "get_location_environment",
            "get_noise_metric",
            "get_temperature_metric",
            "find_worst_location",
            "compare_locations",
            "recommend_running_route",
            "recommend_personalized_running_route",
            "recommend_indoor_activity",
            "recommend_outdoor_location",
            "unsupported_precipitation_weather",
            "unknown_location",
        }:
            evidence_source = "prophet_time_series_v1" if time_context["is_forecast"] else None
            for evidence_item in result.get("evidence", []):
                evidence_station_id = evidence_item.get("station_id")
                evidence_snapshot = snapshots.get(evidence_station_id)
                if not evidence_snapshot:
                    continue
                evidence_item["source"] = evidence_source or evidence_snapshot.get("source")
                evidence_item["observed_at"] = evidence_snapshot.get("updated_at")
                evidence_item["timestamp"] = (
                    time_context.get("target_datetime")
                    if time_context["is_forecast"]
                    else evidence_snapshot.get("updated_at")
                )

            map_intent = result.get("intent")
            is_canonical_route = map_intent in {
                "recommend_running_route",
                "recommend_personalized_running_route",
            }
            if isinstance(agent_sources, list) and agent_sources and not is_canonical_route:
                result["sources"] = agent_sources
                result["intent"] = canonical_intent
            elif "sources" not in result or not result["sources"]:
                result["sources"] = [
                    f"station_{item['station_id']}"
                    for item in result.get("evidence", [])
                    if isinstance(item, dict) and item.get("station_id")
                ] or ["simulator_engine"]

            result["used_tools"] = list(
                dict.fromkeys(
                    [
                        *result.get("used_tools", []),
                        *agent_result.get("used_tools", []),
                    ]
                )
            )
            result["tool_arguments"] = canonical_arguments
            result["proposal_id"] = agent_result.get("proposal_id")
            result["trace"] = {
                **agent_result.get("trace", {}),
                "map_planner": "deterministic_grounded_geospatial",
                "map_intent": map_intent,
                "data_mode": result.get("data_mode"),
            }
            return result

        if not isinstance(agent_sources, list) or not agent_sources:
            return {
                "answer": result.get("answer") or {"summary": agent_result["answer"], "details": ""},
                "response": result.get("response") or agent_result["answer"],
                "intent": canonical_intent,
                "conversation_kind": canonical_kind,
                "evidence": result.get("evidence", []),
                "sources": [],
                "map_actions": result.get("map_actions", []),
                "used_tools": agent_result.get("used_tools", []),
                "tool_arguments": canonical_arguments,
                "proposal_id": agent_result.get("proposal_id"),
                "request_id": req_id,
                "trace": agent_result.get("trace", {}),
            }

        evidence_source = "prophet_time_series_v1" if time_context["is_forecast"] else None
        for evidence_item in result.get("evidence", []):
            evidence_station_id = evidence_item.get("station_id")
            evidence_snapshot = snapshots.get(evidence_station_id)
            if not evidence_snapshot:
                continue
            evidence_item["source"] = evidence_source or evidence_snapshot.get("source")
            evidence_item["observed_at"] = evidence_snapshot.get("updated_at")
            evidence_item["timestamp"] = (
                time_context.get("target_datetime")
                if time_context["is_forecast"]
                else evidence_snapshot.get("updated_at")
            )
        map_intent = result.get("intent")
        if not result.get("answer") or not result["answer"].get("summary"):
            result["answer"] = {"summary": agent_result["answer"], "details": ""}
            result["response"] = agent_result["answer"]
        result["intent"] = canonical_intent
        result["conversation_kind"] = canonical_kind
        result["used_tools"] = agent_result.get("used_tools", [])
        result["tool_arguments"] = canonical_arguments
        result["sources"] = agent_sources
        result["proposal_id"] = agent_result.get("proposal_id")
        result["trace"] = {
            **agent_result.get("trace", {}),
            "map_planner": "deterministic_grounded_geospatial",
            "map_intent": map_intent,
            "data_mode": result.get("data_mode"),
        }
        return result
    except ServiceError:
        raise
    except AgentServiceError as exc:
        raise ServiceError(exc.code, exc.message, exc.status_code) from exc
    except Exception as exc:
        raise ServiceError(
            "agent_processing_failed",
            "The Agent could not process the request using grounded data",
            503,
        ) from exc


def dispatch_job(task, job_type: str, payload: dict, idempotency_key: str | None) -> dict:
    if task is None:
        raise ServiceError("background_job_dependency_missing", "Background job dependency is not installed", 503)

    key = idempotency_key or str(uuid4())
    task_id = str(uuid5(NAMESPACE_URL, f"airguard:{job_type}:{key}"))
    record, created = reserve_job(task_id, job_type, key, payload)
    if not created:
        return {**record, "reused": True, "status_url": f"/api/v1/jobs/{record['task_id']}"}

    try:
        task.apply_async(kwargs={**payload, "idempotency_key": key}, task_id=task_id)
    except Exception as exc:
        mark_job_failed(task_id, f"Task dispatch failed: {exc}", retrying=False)
        raise ServiceError("background_job_service_unavailable", "Background job service is unavailable", 503) from exc


    current = get_job(task_id) or record
    return {**current, "reused": False, "status_url": f"/api/v1/jobs/{task_id}"}


@app.post("/api/v1/agent/jobs", status_code=202)
def create_agent_job(request: AgentJobRequest) -> dict:
    payload = {"user_id": request.user_id, "message": request.message, "station_id": request.station_id}
    return dispatch_job(run_agent_job, "agent", payload, request.idempotency_key)


@app.post("/api/v1/forecast/jobs", status_code=202)
def create_forecast_job(request: ForecastJobRequest) -> dict:
    station = station_service.get_station(request.station_id)
    if station["pm25"] is None or station["is_stale"]:
        raise ServiceError("insufficient_fresh_data", "Fresh PM2.5 data is required for forecast", 503)
    history = station_service.get_forecast_history(request.station_id)
    try:
        trend_forecast(history, request.hours)
    except InsufficientForecastHistory as exc:
        raise ServiceError(
            "insufficient_forecast_history",
            "At least three recent valid measurements are required for forecast",
            503,
        ) from exc
    payload = {"station_id": request.station_id, "history": history, "hours": request.hours}

    return dispatch_job(run_forecast_job, "forecast", payload, request.idempotency_key)


@app.get("/api/v1/jobs/{task_id}")
def get_background_job(task_id: str) -> dict:
    record = get_job(task_id)
    if not record:
        raise ServiceError("job_not_found", "Job was not found", 404, {"task_id": task_id})
    return record


@app.post("/api/v1/approvals", status_code=201)
@app.post("/api/v1/proposals", status_code=201)
def create_approval(
    request: Request,
    body: ApprovalCreateRequest,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> dict:
    if idempotency_key is not None and len(idempotency_key) < 8:
        raise ServiceError("invalid_idempotency_key", "Idempotency-Key must be at least 8 characters", 422)
    evidence = dict(body.evidence)
    if body.request_type == "warning_proposal":
        if not body.station_id or not body.evidence:
            raise ServiceError("proposal_evidence_required", "Warning proposals require station_id and evidence", 422)
        station = station_service.get_station(body.station_id)
        if station["status"] in {"offline", "stale"} or station["pm25"] is None:
            raise ServiceError("proposal_data_not_eligible", "Fresh online station data is required", 409)
        active_alerts = alert_engine.list_alerts(status="active", station_id=body.station_id)
        if not active_alerts:
            raise ServiceError("proposal_alert_required", "An active alert is required for a warning proposal", 409)
    if body.duration_minutes is not None or body.intensity_percent is not None:
        control = dict(evidence.get("control") or {})
        if body.duration_minutes is not None:
            control["duration_minutes"] = body.duration_minutes
        if body.intensity_percent is not None:
            control["intensity_percent"] = body.intensity_percent
        evidence["control"] = control
    return approval_service.create_request(
        request_type=body.request_type,
        station_id=body.station_id,
        device_id=body.device_id,
        proposed_action=body.proposed_action,
        reason=body.reason,
        evidence=evidence,
        created_by=body.created_by,
        correlation_id=_request_id(request),
        idempotency_key=idempotency_key,
    )


@app.get("/api/v1/approvals")
@app.get("/api/v1/proposals")
def get_approvals(
    request: Request,
    status: str | None = Query(default=None),
    current_user: dict = Depends(require_manager),
) -> dict:
    approval_service.expire_pending_requests(correlation_id=_request_id(request))
    return {"items": approval_service.list_requests(status=status)}


@app.get("/api/v1/approvals/{request_id}")
@app.get("/api/v1/proposals/{request_id}")
def get_approval(request_id: str, current_user: dict = Depends(require_manager)) -> dict:
    return approval_service.get_request(request_id)


@app.post("/api/v1/approvals/{request_id}/approve")
@app.post("/api/v1/proposals/{request_id}/approve")
def approve_request(
    request: Request,
    request_id: str,
    body: ApprovalReviewRequest,
    current_user: dict = Depends(require_manager),
) -> dict:
    validate_csrf(request)
    result = approval_service.approve(
        request_id=request_id,
        expected_version=body.version,
        reviewer_id=current_user["user_id"],
        reviewer_role=current_user["role"],
        note=body.note,
        correlation_id=_request_id(request),
    )
    _enqueue_approved_command(request, request_id, result)
    return result


def _enqueue_approved_command(request: Request, request_id: str, result: dict[str, Any]) -> None:
    """Reserve one durable dispatch job and allow a broker-enqueue failure to be retried."""
    command_intent = result.get("command_intent")
    if publish_approved_device_command is None or not command_intent:
        return
    payload = {
        "approval_request_id": request_id,
        "device_id": command_intent["device_id"],
        "command": command_intent["command"],
        "idempotency_key": command_intent["idempotency_key"],
    }
    task_id = f"device-command-{command_intent['command_intent_id']}"
    job, created = reserve_job(
        task_id,
        "device_command",
        command_intent["idempotency_key"],
        payload,
    )
    if not created and job.get("status") != "FAILURE":
        return
    dispatch_task_id = str(job.get("task_id") or task_id)
    try:
        publish_approved_device_command.apply_async(
            kwargs=payload,
            task_id=dispatch_task_id,
        )
    except Exception as exc:
        mark_job_failed(dispatch_task_id, "device_dispatch_enqueue_failed", retrying=False)
        audit_service.record(
            actor_type="system",
            actor_role="backend",
            action="approval.dispatch.failure",
            entity_type="approval_request",
            entity_id=request_id,
            correlation_id=_request_id(request),
            outcome="failure",
            details={"error": str(exc)[:200]},
        )


@app.post("/api/v1/approvals/{request_id}/quick-approve")
@app.post("/api/v1/proposals/{request_id}/quick-approve")
def quick_approve_request(
    request: Request,
    request_id: str,
    body: ApprovalReviewRequest,
    idempotency_key: str = Header(..., alias="Idempotency-Key", min_length=8, max_length=200),
    current_user: dict = Depends(require_manager),
) -> dict:
    validate_csrf(request)
    result = approval_service.quick_approve(
        request_id=request_id,
        expected_version=body.version,
        reviewer_id=current_user["user_id"],
        reviewer_role=current_user["role"],
        note=body.note,
        correlation_id=_request_id(request),
        idempotency_key=idempotency_key,
    )
    _enqueue_approved_command(request, request_id, result)
    return result


@app.post("/api/v1/approvals/{request_id}/reject")
@app.post("/api/v1/proposals/{request_id}/reject")
def reject_request(
    request: Request,
    request_id: str,
    body: ApprovalReviewRequest,
    current_user: dict = Depends(require_manager),
) -> dict:
    validate_csrf(request)
    return approval_service.reject(
        request_id=request_id,
        expected_version=body.version,
        reviewer_id=current_user["user_id"],
        reviewer_role=current_user["role"],
        note=body.note or "",
        correlation_id=_request_id(request),
    )


@app.get("/api/v1/reports", response_model=EnvironmentalReportListResponse)
def list_environmental_reports(
    type: Literal["daily", "weekly"] | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    current_user: dict = Depends(require_manager),
) -> dict:
    return {
        "items": report_service.list_reports(
            report_type=type,
            limit=limit,
            offset=offset,
        )
    }


@app.post("/api/v1/reports/generate", status_code=201, response_model=EnvironmentalReportResponse)
def generate_environmental_report(
    request: Request,
    body: ReportGenerateRequest,
    current_user: dict = Depends(require_manager),
) -> dict:
    validate_csrf(request)
    return report_service.generate_report(
        body.type,
        period_start=body.period_start,
        period_end=body.period_end,
        timezone_name=body.timezone or settings.report_timezone,
        generated_by=current_user["user_id"],
    )


@app.get("/api/v1/reports/{report_id}", response_model=EnvironmentalReportResponse)
def get_environmental_report(
    report_id: str,
    current_user: dict = Depends(require_manager),
) -> dict:
    return report_service.get_report(report_id)


@app.get("/api/v1/reports/{report_id}/export")
def export_environmental_report(
    report_id: str,
    format: Literal["markdown", "html", "pdf"] = Query(default="markdown"),
    current_user: dict = Depends(require_manager),
) -> Response:
    exported = report_service.export_report(report_id, format)
    return Response(
        content=exported.content,
        media_type=exported.media_type,
        headers={"Content-Disposition": f'attachment; filename="{exported.filename}"'},
    )


@app.get("/api/v1/audit-logs")
def get_audit_logs(
    entity_type: str | None = Query(default=None),
    entity_id: str | None = Query(default=None),
    scope: Literal["all", "manager"] = Query(default="all"),
    limit: int = Query(default=100, ge=1, le=500),
    current_user: dict = Depends(require_manager),
) -> dict:
    actions = MANAGER_AUDIT_ACTIONS if scope == "manager" else None
    return {
        "items": audit_service.list_logs(
            entity_type=entity_type,
            entity_id=entity_id,
            actions=actions,
            limit=limit,
        ),
        "scope": scope,
    }


@app.get("/api/v1/users")
def get_users(current_user: dict = Depends(require_manager)) -> dict:
    return {"items": user_admin_service.list_users()}


@app.patch("/api/v1/users/{user_id}")
def update_user_admin(
    user_id: str,
    body: AdminUserUpdateRequest,
    request: Request,
    current_user: dict = Depends(require_admin),
) -> dict:
    validate_csrf(request)
    return user_admin_service.update_user(
        target_user_id=user_id,
        actor_user_id=str(current_user["user_id"]),
        actor_role=str(current_user["role"]),
        role=body.role,
        status=body.status,
        reason=body.reason,
        correlation_id=_request_id(request),
    )



@app.get("/api/v1/devices")
def get_devices() -> dict:
    return {"items": device_service.list_devices()}


@app.get("/api/v1/ventilation-devices")
def get_ventilation_devices(
    station_id: str | None = Query(default=None, pattern=r"^S0[1-5]$"),
) -> dict:
    return {
        "items": device_service.list_ventilation_devices(station_id=station_id),
        "timestamp": datetime.now(UTC).isoformat(),
        "source": "simulator",
    }



@app.get("/api/v1/devices/{device_id}/status")
def get_device_status(device_id: str) -> dict:
    return device_service.get_status(device_id)


@app.post("/api/v1/devices/{device_id}/proposals", status_code=201)
def create_device_control_proposal(
    request: Request,
    device_id: str,
    body: DeviceControlProposalRequest,
    idempotency_key: str = Header(..., alias="Idempotency-Key", min_length=8, max_length=200),
    current_user: dict = Depends(require_manager),
) -> dict:
    validate_csrf(request)
    device = device_service.get_status(device_id)
    station_id = device.get("station_id")
    if not station_id:
        raise ServiceError("device_station_required", "Device is not mapped to a station", 409)
    latest_command = device.get("latest_command") or {}
    evidence: dict[str, Any] = {
        "source": "backend_device_registry",
        "device_status": {
            "device_id": device_id,
            "operating_mode": device.get("operating_mode"),
            "started_at": device.get("started_at"),
            "ends_at": device.get("ends_at"),
        },
        "control": {"action": body.action},
    }
    if body.action == "eco_mode" and latest_command.get("command_intent_id"):
        evidence["source_command_intent_id"] = latest_command["command_intent_id"]
    proposal = approval_service.create_request(
        request_type="device_control_proposal",
        station_id=str(station_id),
        device_id=device_id,
        proposed_action=body.action,
        reason=body.reason,
        evidence=evidence,
        created_by=str(current_user["user_id"]),
        correlation_id=_request_id(request),
        idempotency_key=f"manager-device:{device_id}:{body.action}:{idempotency_key}",
    )
    if not proposal.get("reused"):
        _enqueue_manager_proposal_notification(
            proposal_id=str(proposal["request_id"]),
            station_id=str(station_id),
            proposed_action=body.action,
            correlation_id=_request_id(request),
        )
    return proposal



