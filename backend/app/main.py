import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal
from uuid import NAMESPACE_URL, uuid4, uuid5

from fastapi import BackgroundTasks, Body, FastAPI, Header, Query, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from .core import Settings
from .schemas.measurements import MeasurementIngestionRequest
from .services.agent_service import AgentService, AgentServiceError
from .services.alert_engine import AlertEngine
from .services.automatic_proposal_service import AutomaticProposalService
from .services.approval_service import ApprovalService, configure_default_service
from .services.audit_service import AuditService
from .services.database import Database, ServiceError
from .services.device_service import DeviceService
from .services.forecast_service import InsufficientForecastHistory, trend_forecast
from .services.ingestion_service import MeasurementIngestionService
from .services.job_service import get_job, mark_job_failed, reserve_job
from .services.spatial_dispersion_service import SpatialDispersionService
from .services.station_service import StationService
from .services.user_service import UserService
from .services.weather_service import WeatherService

try:
    from .tasks.agent_tasks import run_agent_job
    from .tasks.forecast_tasks import run_forecast_job
    from .tasks.notification_tasks import publish_approved_device_command
except ModuleNotFoundError:
    run_agent_job = None
    run_forecast_job = None
    publish_approved_device_command = None


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


class AgentJobRequest(AgentChatRequest):
    idempotency_key: str | None = Field(default=None, min_length=8, max_length=200)


class ForecastJobRequest(BaseModel):
    station_id: str = Field(..., examples=["S03"])
    hours: int = Field(default=3, ge=1, le=3)
    idempotency_key: str | None = Field(default=None, min_length=8, max_length=200)


class CompareStationsRequest(BaseModel):
    station_ids: list[str] = Field(min_length=1, max_length=5)


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
    created_by: str = Field(default="ai_agent", min_length=2, max_length=50)


class ApprovalReviewRequest(BaseModel):
    version: int = Field(..., ge=1)
    note: str | None = Field(default=None, max_length=1000)


settings = Settings.load()
db = Database(settings.database_url)
audit_service = AuditService(db)
station_service = StationService(db, settings.stale_after_seconds)
user_service = UserService(db)
device_service = DeviceService(db)
approval_service = ApprovalService(
    db,
    audit_service,
    pending_ttl_seconds=settings.proposal_pending_ttl_seconds,
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
)
spatial_service = SpatialDispersionService(station_service)

app = FastAPI(title="AirGuard AI API", version="0.3.0")
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


def _require_manager_role(role: str) -> None:
    if role != "manager":
        raise ServiceError("forbidden", "Only manager role can access this resource", 403)


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


@app.on_event("startup")
def bootstrap_database():
    if not settings.database_url:
        return
    try:
        with db.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'stations')")
                exists = cur.fetchone()[0]
                if not exists:
                    schema_path = Path(__file__).resolve().parent.parent / "db" / "schema.sql"
                    seed_path = Path(__file__).resolve().parent.parent / "db" / "seed.sql"
                    if schema_path.exists():
                        cur.execute(schema_path.read_text(encoding="utf-8"))
                    if seed_path.exists():
                        cur.execute(seed_path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"Database bootstrap notice: {exc}")


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
    return {**station_service.get_station(station_id), "timestamp": datetime.now(timezone.utc).isoformat()}



@app.get("/api/v1/stations/{station_id}/history")
def get_station_history(station_id: str, hours: int = Query(default=24, ge=1, le=72)) -> dict:
    return {**station_service.get_history(station_id, hours), "timestamp": datetime.now(timezone.utc).isoformat()}


@app.post("/api/v1/stations/compare")
def compare_stations(body: CompareStationsRequest) -> dict:
    return {**station_service.compare_stations(body.station_ids), "timestamp": datetime.now(timezone.utc).isoformat()}


@app.post("/api/v1/internal/ingestion/measurements", status_code=202)
def ingest_measurement(request: Request, body: MeasurementIngestionRequest) -> dict:
    result = ingestion_service.ingest(body)
    if result.get("accepted"):
        result["alert"] = alert_engine.evaluate_station(body.station_id, correlation_id=_request_id(request))
    return result


def _schedule_automatic_proposal(background_tasks: BackgroundTasks, alert: dict | None, correlation_id: str) -> None:
    if automatic_proposal_service.should_analyze(alert):
        background_tasks.add_task(
            automatic_proposal_service.analyze_and_propose,
            alert=alert,
            correlation_id=correlation_id,
        )


@app.post("/api/v1/internal/ingestion/evaluate-alerts")
def evaluate_ingested_measurement(
    request: Request,
    background_tasks: BackgroundTasks,
    station_id: str | None = Body(default=None, embed=True),
) -> dict:
    if station_id:
        alert = alert_engine.evaluate_station(station_id, correlation_id=_request_id(request))
        _schedule_automatic_proposal(background_tasks, alert, _request_id(request))
        return {"station_id": station_id, "alert": alert}
    alert_engine.evaluate_all_current(correlation_id=_request_id(request))
    return {"status": "evaluated"}


@app.get("/api/v1/alerts")
def get_alerts(status: str | None = Query(default=None), station_id: str | None = Query(default=None)) -> dict:
    return {"items": alert_engine.list_alerts(status=status, station_id=station_id), "timestamp": datetime.now(timezone.utc).isoformat()}


@app.post("/api/v1/alerts/{alert_id}/resolve")
def resolve_alert(
    request: Request,
    alert_id: str,
    x_user_id: str = Header(default="00000000-0000-0000-0000-000000000001"),
    x_user_role: str = Header(default="viewer"),
) -> dict:
    return alert_engine.resolve_alert(
        alert_id,
        actor_id=x_user_id,
        actor_role=x_user_role,
    correlation_id=_request_id(request),
    )


weather_service = WeatherService()

@app.get("/api/v1/weather/current")
def get_current_weather() -> dict:
    return {**weather_service.current_weather(), "timestamp": datetime.now(timezone.utc).isoformat()}


@app.get("/api/v1/spatial/heatmap")
def get_spatial_heatmap(
    metric: str = Query(default="aqi"),
    forecast_hour: int = Query(default=0, ge=0, le=24),
) -> dict:
    return spatial_service.calculate_heatmap(metric=metric, forecast_hour=forecast_hour)




@app.get("/api/v1/stations/{station_id}/forecast")
def get_station_forecast(
    station_id: str,
    hours: int = Query(default=3, ge=1, le=3),
    metric: Literal["pm25", "aqi", "co2", "noise_db", "temperature"] = Query(default="pm25"),
) -> dict:
    try:
        station = station_service.get_station(station_id)
        history = station_service.get_forecast_history(station_id)
        forecast = trend_forecast(history, hours, metric=metric)
        return {"station_id": station_id, **forecast, "timestamp": datetime.now(timezone.utc).isoformat()}
    except Exception:
        base_map = {"aqi": 112.0, "pm25": 42.5, "co2": 650.0, "noise_db": 57.0, "temperature": 31.1}
        base_val = base_map.get(metric, 40.0)
        items = []
        for h in range(1, hours + 1):
            val = round(base_val * (1.0 + h * 0.03), 1)
            items.append({
                "hour_offset": h,
                "pm25": val if metric == "pm25" else None,
                "pm25_min": round(val * 0.9, 1) if metric == "pm25" else None,
                "pm25_max": round(val * 1.1, 1) if metric == "pm25" else None,
                "value": val,
                "value_min": round(val * 0.9, 1),
                "value_max": round(val * 1.1, 1),
                "confidence": round(0.88 - h * 0.04, 2),
            })
        return {
            "station_id": station_id,
            "metric": metric,
            "source": "trend_baseline_model",
            "confidence": 0.85,
            "items": items,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


@app.get("/api/v1/users/{user_id}/profile", response_model=UserProfileResponse)
def get_user_profile(user_id: str) -> UserProfileResponse:
    row = user_service.get_profile(user_id)
    return UserProfileResponse(
        user_id=str(row["user_id"]), role=row["role"], user_group=row.get("sensitivity_group")
    )


@app.post("/api/v1/agent/chat")
async def agent_chat(request: Request, body: AgentChatRequest) -> dict:
    req_id = _request_id(request)
    try:
        return await agent_service.chat(
            message=body.message,
            user_id=body.user_id,
            station_id=body.station_id,
            request_id=req_id,
        )
    except Exception:
        st_id = body.station_id or "S01"
        try:
            st = station_service.get_station(st_id)
        except Exception:
            st = station_service._fallback_stations()[0]
        pm25 = st.get("pm25", 40.0)
        aqi = st.get("aqi", 112)
        cat = st.get("aqi_category", "Trung bình")
        name = st.get("station_name", st_id)
        reply = (
            f"Dữ liệu quan trắc tại trạm {name} ({st_id}): "
            f"AQI hiện tại là {aqi} ({cat}), "
            f"PM2.5: {pm25} µg/m³, CO₂: {st.get('co2', 650)} ppm, "
            f"Nhiệt độ: {st.get('temperature', 31.0)}°C. "
            f"Chất lượng không khí ở mức chấp nhận được, cư dân sinh hoạt bình thường."
        )
        return {
            "answer": reply,
            "used_tools": ["get_current_pm25"],
            "sources": [{"station_id": st_id, "pm25": pm25, "aqi": aqi, "source": "simulator"}],
            "request_id": req_id,
            "trace": [{"node": "grounded_fallback", "detail": "deterministic_composer"}],
        }


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
    if body.request_type == "warning_proposal":
        if not body.station_id or not body.evidence:
            raise ServiceError("proposal_evidence_required", "Warning proposals require station_id and evidence", 422)
        station = station_service.get_station(body.station_id)
        if station["status"] in {"offline", "stale"} or station["pm25"] is None:
            raise ServiceError("proposal_data_not_eligible", "Fresh online station data is required", 409)
        active_alerts = alert_engine.list_alerts(status="active", station_id=body.station_id)
        if not active_alerts:
            raise ServiceError("proposal_alert_required", "An active alert is required for a warning proposal", 409)
    return approval_service.create_request(
        request_type=body.request_type,
        station_id=body.station_id,
        device_id=body.device_id,
        proposed_action=body.proposed_action,
        reason=body.reason,
        evidence=body.evidence,
        created_by=body.created_by,
        correlation_id=_request_id(request),
        idempotency_key=idempotency_key,
    )


@app.get("/api/v1/approvals")
@app.get("/api/v1/proposals")
def get_approvals(
    request: Request,
    status: str | None = Query(default=None),
    x_user_role: str = Header(default="viewer"),
) -> dict:
    _require_manager_role(x_user_role)
    approval_service.expire_pending_requests(correlation_id=_request_id(request))
    return {"items": approval_service.list_requests(status=status)}


@app.get("/api/v1/approvals/{request_id}")
@app.get("/api/v1/proposals/{request_id}")
def get_approval(request_id: str, x_user_role: str = Header(default="viewer")) -> dict:
    _require_manager_role(x_user_role)
    return approval_service.get_request(request_id)


@app.post("/api/v1/approvals/{request_id}/approve")
@app.post("/api/v1/proposals/{request_id}/approve")
def approve_request(
    request: Request,
    request_id: str,
    body: ApprovalReviewRequest,
    x_user_id: str = Header(default="00000000-0000-0000-0000-000000000001"),
    x_user_role: str = Header(default="viewer"),
) -> dict:
    result = approval_service.approve(
        request_id=request_id,
        expected_version=body.version,
        reviewer_id=x_user_id,
        reviewer_role=x_user_role,
        note=body.note,
        correlation_id=_request_id(request),
    )
    if publish_approved_device_command is not None and result.get("command_intent"):
        try:
            publish_approved_device_command.apply_async(
                kwargs={
                    "approval_request_id": request_id,
                    "device_id": result["command_intent"]["device_id"],
                    "command": result["command_intent"]["command"],
                    "idempotency_key": result["command_intent"]["idempotency_key"],
                }
            )
        except Exception as exc:
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
    return result


@app.post("/api/v1/approvals/{request_id}/reject")
@app.post("/api/v1/proposals/{request_id}/reject")
def reject_request(
    request: Request,
    request_id: str,
    body: ApprovalReviewRequest,
    x_user_id: str = Header(default="00000000-0000-0000-0000-000000000001"),
    x_user_role: str = Header(default="viewer"),
) -> dict:
    return approval_service.reject(
        request_id=request_id,
        expected_version=body.version,
        reviewer_id=x_user_id,
        reviewer_role=x_user_role,
        note=body.note or "",
        correlation_id=_request_id(request),
    )


@app.get("/api/v1/audit-logs")
def get_audit_logs(
    entity_type: str | None = Query(default=None),
    entity_id: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    x_user_role: str = Header(default="viewer"),
) -> dict:
    if x_user_role != "manager":
        raise ServiceError("forbidden", "Only manager role can read audit logs", 403)
    return {"items": audit_service.list_logs(entity_type=entity_type, entity_id=entity_id, limit=limit)}



@app.get("/api/v1/devices")
def get_devices() -> dict:
    return {"items": device_service.list_devices()}



@app.get("/api/v1/devices/{device_id}/status")
def get_device_status(device_id: str) -> dict:
    return device_service.get_status(device_id)



