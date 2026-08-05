
from uuid import NAMESPACE_URL, uuid4, uuid5

from fastapi import Body, FastAPI, Header, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field

from .core import Settings
from .schemas.measurements import MeasurementIngestionRequest
from .services.agent_service import build_placeholder_answer
from .services.alert_engine import AlertEngine
from .services.approval_service import ApprovalService, configure_default_service
from .services.audit_service import AuditService
from .services.database import Database, ServiceError
from .services.forecast_service import baseline_forecast
from .services.job_service import get_job, mark_job_failed, reserve_job
from .services.ingestion_service import MeasurementIngestionService
from .services.station_service import StationService
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
    user_id: str = Field(..., examples=["demo-user"])
    message: str = Field(..., examples=["Hien tai co nen chay bo o cong vien khong?"])


class AgentJobRequest(AgentChatRequest):
    idempotency_key: str | None = Field(default=None, min_length=8, max_length=200)


class ForecastJobRequest(BaseModel):
    station_id: str = Field(..., examples=["S03"])
    hours: int = Field(default=3, ge=1, le=3)
    idempotency_key: str | None = Field(default=None, min_length=8, max_length=200)


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
approval_service = ApprovalService(db, audit_service)
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
)
configure_default_service(approval_service)

app = FastAPI(title="AirGuard AI API", version="0.3.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid4())
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
    return station_service.get_station(station_id)



@app.get("/api/v1/stations/{station_id}/history")
def get_station_history(station_id: str, hours: int = Query(default=24, ge=1, le=72)) -> dict:
    return station_service.get_history(station_id, hours)


@app.post("/api/v1/internal/ingestion/measurements", status_code=202)
def ingest_measurement(request: Request, body: MeasurementIngestionRequest) -> dict:
    result = ingestion_service.ingest(body)
    if result.get("accepted"):
        result["alert"] = alert_engine.evaluate_station(body.station_id, correlation_id=_request_id(request))
    return result


@app.post("/api/v1/internal/ingestion/evaluate-alerts")
def evaluate_ingested_measurement(
    request: Request,
    station_id: str | None = Body(default=None, embed=True),
) -> dict:
    if station_id:
        alert = alert_engine.evaluate_station(station_id, correlation_id=_request_id(request))
        return {"station_id": station_id, "alert": alert}
    alert_engine.evaluate_all_current(correlation_id=_request_id(request))
    return {"status": "evaluated"}


@app.get("/api/v1/alerts")
def get_alerts(status: str | None = Query(default=None), station_id: str | None = Query(default=None)) -> dict:
    return {"items": alert_engine.list_alerts(status=status, station_id=station_id)}


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
    return weather_service.current_weather()



@app.get("/api/v1/stations/{station_id}/forecast")
def get_station_forecast(station_id: str, hours: int = Query(default=3, ge=1, le=3)) -> dict:
    station = station_service.get_station(station_id)
    if station["pm25"] is None or station["is_stale"]:
        raise ServiceError("insufficient_fresh_data", "Fresh PM2.5 data is required for forecast", 503)
    return {
        "station_id": station_id,
        "items": baseline_forecast(float(station["pm25"]), hours),
        "source": "baseline_current_pm25",
    }


@app.post("/api/v1/agent/chat")
def agent_chat(request: Request, body: AgentChatRequest) -> dict:
    return {"user_id": body.user_id, "request_id": _request_id(request), **build_placeholder_answer(body.message)}


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
    payload = {"user_id": request.user_id, "message": request.message}
    return dispatch_job(run_agent_job, "agent", payload, request.idempotency_key)


@app.post("/api/v1/forecast/jobs", status_code=202)
def create_forecast_job(request: ForecastJobRequest) -> dict:
    station = station_service.get_station(request.station_id)
    if station["pm25"] is None or station["is_stale"]:
        raise ServiceError("insufficient_fresh_data", "Fresh PM2.5 data is required for forecast", 503)
    payload = {"station_id": request.station_id, "current_pm25": station["pm25"], "hours": request.hours}

    return dispatch_job(run_forecast_job, "forecast", payload, request.idempotency_key)


@app.get("/api/v1/jobs/{task_id}")
def get_background_job(task_id: str) -> dict:
    record = get_job(task_id)
    if not record:
        raise ServiceError("job_not_found", "Job was not found", 404, {"task_id": task_id})
    return record


@app.post("/api/v1/approvals", status_code=201)
def create_approval(request: Request, body: ApprovalCreateRequest) -> dict:
    return approval_service.create_request(
        request_type=body.request_type,
        station_id=body.station_id,
        device_id=body.device_id,
        proposed_action=body.proposed_action,
        reason=body.reason,
        evidence=body.evidence,
        created_by=body.created_by,
        correlation_id=_request_id(request),
    )


@app.get("/api/v1/approvals")
def get_approvals(status: str | None = Query(default=None), x_user_role: str = Header(default="viewer")) -> dict:
    _require_manager_role(x_user_role)
    return {"items": approval_service.list_requests(status=status)}


@app.get("/api/v1/approvals/{request_id}")
def get_approval(request_id: str, x_user_role: str = Header(default="viewer")) -> dict:
    _require_manager_role(x_user_role)
    return approval_service.get_request(request_id)


@app.post("/api/v1/approvals/{request_id}/approve")
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
        except Exception:
            pass
    return result


@app.post("/api/v1/approvals/{request_id}/reject")
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
    with db.connection() as conn:
        from .services.database import dict_cursor

        with dict_cursor(conn) as cur:
            cur.execute(
                """
                SELECT device_id, device_name, device_type, station_id, status, is_simulated, last_seen_at
                FROM devices
                ORDER BY device_id
                """
            )
            return {"items": [dict(row) for row in cur.fetchall()]}



@app.get("/api/v1/devices/{device_id}/status")
def get_device_status(device_id: str) -> dict:
    with db.connection() as conn:
        from .services.database import dict_cursor

        with dict_cursor(conn) as cur:
            cur.execute(
                """
                SELECT device_id, device_name, device_type, station_id, status, is_simulated, last_seen_at
                FROM devices
                WHERE device_id = %s
                """,
                (device_id,),
            )
            row = cur.fetchone()
            if not row:
                raise ServiceError("device_not_found", "Device was not found", 404, {"device_id": device_id})
            return dict(row)



