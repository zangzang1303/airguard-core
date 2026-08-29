from __future__ import annotations

from html import escape
from urllib.parse import urlencode, urlsplit, urlunsplit
from uuid import UUID

from .database import ServiceError


def build_predictive_deep_link(frontend_url: str, station_id: str, episode_id: str) -> str:
    if station_id not in {"S01", "S02", "S03", "S04", "S05"}:
        raise ServiceError("station_not_found", "Station was not found", 404)
    try:
        canonical_episode_id = str(UUID(episode_id))
    except (TypeError, ValueError) as exc:
        raise ServiceError("predictive_warning_not_found", "Predictive warning id is invalid", 404) from exc
    parsed = urlsplit(frontend_url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ServiceError("frontend_url_invalid", "FRONTEND_URL is invalid", 503)
    base_path = parsed.path.rstrip("/") + "/"
    base = urlunsplit((parsed.scheme, parsed.netloc, base_path, "", ""))
    query = urlencode(
        {
            "panel": "alerts",
            "station_id": station_id,
            "predictive_warning_id": canonical_episode_id,
        }
    )
    return f"{base}?{query}"


# Descriptive public alias retained for contract-oriented callers/tests.
build_predictive_warning_deep_link = build_predictive_deep_link


def render_predictive_warning_email(episode: dict, *, frontend_url: str) -> dict[str, str]:
    link = build_predictive_deep_link(frontend_url, str(episode["station_id"]), str(episode["episode_id"]))
    station_id = escape(str(episode["station_id"]))
    severity = "nghiêm trọng" if episode.get("severity") == "critical" else "cảnh báo"
    target = escape(str(episode["forecast_target_at"]))
    predicted_min = escape(str(episode["predicted_min"]))
    predicted_max = escape(str(episode["predicted_max"]))
    confidence = escape(f"{float(episode['confidence']) * 100:.0f}%")
    model = escape(str(episode["model_version"]))
    source = escape(str(episode["source"]))
    policy = escape(str(episode["policy_version"]))
    safe_link = escape(link, quote=True)
    subject = f"AirGuard — Cảnh báo sớm PM2.5 tại {station_id}"
    text = (
        f"AirGuard dự báo advisory mức {severity} tại {station_id} quanh {target}.\n"
        f"Khoảng PM2.5: {predicted_min}-{predicted_max} µg/m³; độ tin cậy {confidence}.\n"
        f"Mô hình: {model}; nguồn: {source}; policy: {policy}.\n"
        "Dữ liệu simulator cho mô hình demo, không phải quan trắc chính thức hoặc tư vấn y tế.\n"
        f"Mở AirGuard và checklist: {link}"
    )
    html = f"""<!doctype html>
<html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<style>
body{{margin:0;background:#f3f7f5;color:#17352b;font-family:Arial,sans-serif}}.card{{max-width:640px;margin:24px auto;background:#fff;border-radius:16px;padding:28px;box-sizing:border-box}}.actions{{display:flex;gap:10px;flex-wrap:wrap}}.button{{display:inline-block;background:#087f5b;color:#fff!important;text-decoration:none;padding:13px 18px;border-radius:10px}}.button.secondary{{background:#315f52}}.meta{{font-size:14px;color:#50675f}}@media(max-width:480px){{.card{{margin:0;padding:20px;border-radius:0}}.actions{{display:block}}.button{{display:block;text-align:center;margin-bottom:10px}}}}
</style></head><body><main class="card">
<p class="meta">AirGuard · predictive advisory</p><h1>Cảnh báo sớm PM2.5 tại {station_id}</h1>
<p>Mô hình baseline của simulator cho thấy PM2.5 có nguy cơ vượt ngưỡng policy quanh <strong>{target}</strong>.</p>
<p>Khoảng dự báo: <strong>{predicted_min}-{predicted_max} µg/m³</strong> · Độ tin cậy: <strong>{confidence}</strong></p>
<p class="meta">Model: {model}<br>Source: {source}<br>Policy: {policy}</p>
<p class="actions"><a class="button" href="{safe_link}">Xem Bản Đồ Trực Tiếp</a><a class="button secondary" href="{safe_link}">Checklist Hành Động</a></p>
<p class="meta">Dữ liệu simulator cho mô hình demo, không phải quan trắc chính thức, chẩn đoán hoặc tư vấn y tế. Resend accepted chỉ thể hiện nhà cung cấp đã tiếp nhận yêu cầu.</p>
</main></body></html>"""
    return {"subject": subject, "text": text, "html": html, "deep_link": link}
