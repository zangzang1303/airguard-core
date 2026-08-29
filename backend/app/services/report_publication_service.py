from __future__ import annotations

import html
import os
from io import BytesIO
from typing import Any

from .database import ServiceError


def build_publication_view_model(report: dict[str, Any]) -> dict[str, Any]:
    statistics = report.get("statistics")
    if not isinstance(statistics, dict):
        raise ServiceError("report_record_invalid", "Stored report statistics are invalid.", 500)
    required = {"measurements", "trends", "alerts", "proposals", "ventilation", "data_quality"}
    if not required.issubset(statistics):
        raise ServiceError("report_record_invalid", "Stored report statistics are incomplete.", 500)
    schema_version = str(report.get("schema_version") or "periodic-report-v1")
    policy = statistics.get("policy_snapshot") if isinstance(statistics.get("policy_snapshot"), dict) else {}
    reference = statistics.get("reference_comparison")
    matrix = statistics.get("weekly_matrix")
    esg = statistics.get("esg_metrics")
    view = {
        "report_id": str(report.get("report_id")),
        "report_type": str(report.get("report_type")),
        "period_start": _iso(report.get("period_start")),
        "period_end": _iso(report.get("period_end")),
        "timezone": str(report.get("timezone") or ""),
        "schema_version": schema_version,
        "content_checksum_sha256": report.get("content_checksum_sha256"),
        "generation_mode": str(report.get("generation_mode") or "deterministic_grounded"),
        "model_source": str(report.get("model_source") or "backend_deterministic_report_v1"),
        "policy_snapshot": policy,
        "measurements": statistics["measurements"],
        "trends": statistics["trends"],
        "alerts": statistics["alerts"],
        "proposals": statistics["proposals"],
        "ventilation": statistics["ventilation"],
        "esg_metrics": esg if isinstance(esg, dict) else {},
        "reference_comparison": reference if isinstance(reference, dict) else {"station_days": []},
        "weekly_matrix": matrix if isinstance(matrix, dict) else {"status": "legacy_unavailable", "views": []},
        # Persisted narratives can originate from an optional provider in another language.
        # Reader-facing exports use the deterministic Vietnamese summary below instead.
        "narrative": str(report.get("narrative") or "Không có diễn giải nền."),
        "data_quality": statistics["data_quality"],
        "legacy": schema_version != "b7-esg-reports-v1",
    }
    view["reader_summary"] = _build_reader_summary(view)
    view["reader_narrative"] = _build_reader_narrative(view)
    return view


def _build_reader_summary(view: dict[str, Any]) -> dict[str, Any]:
    measurements = view["measurements"]
    alerts = view["alerts"]
    ventilation = view["ventilation"]
    trends = view["trends"]
    station_count = measurements.get("station_count", 0)
    valid_samples = measurements.get("valid_sample_count", 0)
    excluded_samples = measurements.get("excluded_sample_count", 0)
    average_aqi = _display(measurements.get("overall_avg_aqi"))
    highest_station = str(measurements.get("worst_station_id") or "chưa xác định")
    trend = {
        "improving": "cải thiện",
        "worsening": "xấu đi",
        "stable": "ổn định",
        "insufficient_data": "chưa đủ dữ liệu",
    }.get(str(trends.get("direction")), "chưa đủ dữ liệu")
    return {
        "headline": f"{station_count} trạm mô phỏng · {valid_samples} mẫu hợp lệ trong kỳ báo cáo",
        "items": [
            {
                "label": "Chất lượng dữ liệu",
                "value": f"{valid_samples} mẫu hợp lệ",
                "detail": f"{excluded_samples} mẫu bị loại khỏi tổng hợp.",
            },
            {
                "label": "Chất lượng không khí",
                "value": f"AQI trung bình {average_aqi}",
                "detail": f"Trạm có AQI cao nhất: {highest_station}.",
            },
            {
                "label": "Vận hành và cảnh báo",
                "value": f"{alerts.get('total_count', 0)} cảnh báo",
                "detail": f"{ventilation.get('activation_count', 0)} lượt thông gió đã được xác nhận.",
            },
            {
                "label": "Xu hướng quan sát",
                "value": trend.capitalize(),
                "detail": "Chỉ mô tả mẫu quan sát trong dữ liệu đã lưu.",
            },
        ],
    }


def _build_reader_narrative(view: dict[str, Any]) -> str:
    measurements = view["measurements"]
    alerts = view["alerts"]
    ventilation = view["ventilation"]
    trend = view["reader_summary"]["items"][3]["value"].lower()
    average_aqi = _display(measurements.get("overall_avg_aqi"))
    station = str(measurements.get("worst_station_id") or "chưa xác định")
    return (
        f"Trong kỳ này, hệ thống có {measurements.get('valid_sample_count', 0)} mẫu hợp lệ từ "
        f"{measurements.get('station_count', 0)} trạm mô phỏng. AQI trung bình là {average_aqi}; "
        f"trạm có AQI cao nhất là {station}. Backend ghi nhận {alerts.get('total_count', 0)} cảnh báo và "
        f"{ventilation.get('activation_count', 0)} lượt thông gió đã được xác nhận. "
        f"Xu hướng quan sát là {trend}; thông tin này không dùng để kết luận nguyên nhân hoặc mức độ tuân thủ."
    )


def render_publication_markdown(report: dict[str, Any]) -> str:
    view = build_publication_view_model(report)
    measurements = view["measurements"]
    lines = [
        f"# AirGuard - Báo cáo chất lượng môi trường ({_report_type_label(view['report_type'])})",
        "",
        f"- Kỳ báo cáo: {_readable_period(view)} ({view['timezone']})",
        f"- Mã báo cáo: {view['report_id']}",
        f"- Schema: {view['schema_version']}",
        f"- Checksum SHA-256: {view['content_checksum_sha256'] or 'legacy-unavailable'}",
        "",
        "## Tóm tắt điều hành",
        "",
        view["reader_narrative"],
        "",
        *[
            f"- **{item['label']}**: {item['value']}. {item['detail']}"
            for item in view["reader_summary"]["items"]
        ],
        "",
        "## Thống kê theo trạm",
        "",
        "| Station | Samples | Avg AQI | Max AQI | Avg PM2.5 | Max PM2.5 |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in measurements.get("stations", []):
        lines.append(
            f"| {row.get('station_id')} | {row.get('sample_count', 0)} | {_display(row.get('avg_aqi'))} | "
            f"{_display(row.get('max_aqi'))} | {_display(row.get('avg_pm25'))} | {_display(row.get('max_pm25'))} |"
        )
    lines.extend(["", "## Chỉ số ESG ước tính", ""])
    for key, label in (
        ("estimated_pm25_removed_kg", "PM2.5 ước tính (kg)"),
        ("estimated_energy_saved_kwh", "Điện năng ước tính (kWh)"),
    ):
        item = view["esg_metrics"].get(key, {})
        lines.append(
            f"- {label}: {_display(item.get('value'))} "
            f"(status={item.get('status', 'legacy_unavailable')}, reason={item.get('reason_code') or 'none'})"
        )
    lines.extend(["", "## Đối chiếu tham chiếu", ""])
    station_days = view["reference_comparison"].get("station_days", [])
    if station_days:
        lines.extend(
            [
                "| Station/day | Avg PM2.5 | Coverage | QCVN | WHO | Good-hour KPI |",
                "|---|---:|---:|---|---|---:|",
            ]
        )
        for item in station_days:
            lines.append(
                f"| {item.get('station_id')}/{item.get('local_date')} | {_display(item.get('avg_pm25_ug_m3'))} | "
                f"{_percent(item.get('coverage_ratio'))} | {item.get('qcvn', {}).get('status', 'N/A')} | "
                f"{item.get('who', {}).get('status', 'N/A')} | "
                f"{_percent(item.get('good_hour_kpi', {}).get('good_hour_rate'))} |"
            )
    else:
        lines.append("Chưa có đối chiếu tham chiếu cho báo cáo legacy này.")
    lines.extend(
        [
            "",
            "> QCVN dùng ug/Nm3 và không thể so sánh pháp lý với dữ liệu simulator ug/m3. WHO là hướng dẫn, không phải quy chuẩn pháp lý. Báo cáo không đánh giá tuân thủ trung bình năm.",
            "",
            "## Ma trận theo giờ",
            "",
            _matrix_markdown(view["weekly_matrix"]),
            "",
            f"> {view['data_quality'].get('disclaimer', 'Simulator-derived MVP data; not certified monitoring.')}",
            "",
        ]
    )
    return "\n".join(lines)


def render_publication_html(report: dict[str, Any]) -> str:
    view = build_publication_view_model(report)
    stations = "".join(
        "<tr>"
        f"<td>{_h(row.get('station_id'))}</td><td>{_h(row.get('sample_count'))}</td>"
        f"<td>{_h(_display(row.get('avg_aqi')))}</td><td>{_h(_display(row.get('max_aqi')))}</td>"
        f"<td>{_h(_display(row.get('avg_pm25')))}</td><td>{_h(_display(row.get('max_pm25')))}</td>"
        "</tr>"
        for row in view["measurements"].get("stations", [])
    )
    references = "".join(
        "<tr>"
        f"<td>{_h(item.get('station_id'))}</td><td>{_h(item.get('local_date'))}</td>"
        f"<td>{_h(_display(item.get('avg_pm25_ug_m3')))}</td><td>{_h(_percent(item.get('coverage_ratio')))}</td>"
        f"<td>{_h(item.get('qcvn', {}).get('status'))}</td><td>{_h(item.get('who', {}).get('status'))}</td>"
        f"<td>{_h(_percent(item.get('good_hour_kpi', {}).get('good_hour_rate')))}</td></tr>"
        for item in view["reference_comparison"].get("station_days", [])
    )
    esg = view["esg_metrics"]
    return f"""<!doctype html>
<html lang="vi"><head><meta charset="utf-8"><meta name="airguard-report-id" content="{_h(view['report_id'])}">
<meta name="airguard-content-checksum" content="{_h(view['content_checksum_sha256'] or 'legacy-unavailable')}">
<title>AirGuard - Báo cáo chất lượng môi trường</title><style>
body{{font-family:Arial,sans-serif;color:#172033;margin:2rem;line-height:1.45}}h1,h2{{color:#123f50}}
.meta,.disclaimer{{color:#52606d}}.card{{border:1px solid #dce5e8;border-radius:10px;padding:1rem;margin:1rem 0}}
table{{border-collapse:collapse;width:100%;font-size:.88rem}}th,td{{border:1px solid #cbd6da;padding:.42rem;text-align:left}}
th{{background:#e8f1f2}}.na{{background:repeating-linear-gradient(135deg,#fff,#fff 4px,#e6eaec 4px,#e6eaec 8px)}}
</style></head><body>
<header><h1>AirGuard - Báo cáo chất lượng môi trường</h1>
<p class="meta">Loại: {_h(_report_type_label(view['report_type']))}<br>Kỳ: {_h(_readable_period(view))} ({_h(view['timezone'])})</p></header>
<section class="card"><h2>Tóm tắt có căn cứ</h2><p>{_h(view['reader_narrative'])}</p></section>
<section><h2>Thống kê theo trạm</h2><table><thead><tr><th>Trạm</th><th>Mẫu</th><th>AQI TB</th><th>AQI cao nhất</th><th>PM2.5 TB</th><th>PM2.5 cao nhất</th></tr></thead><tbody>{stations}</tbody></table></section>
<section class="card"><h2>Chỉ số ESG ước tính</h2>{_esg_html(esg)}</section>
<section><h2>Đối chiếu tham chiếu</h2><table><thead><tr><th>Trạm</th><th>Ngày địa phương</th><th>PM2.5 TB</th><th>Độ phủ</th><th>QCVN</th><th>WHO</th><th>KPI giờ tốt</th></tr></thead><tbody>{references}</tbody></table>
<p class="disclaimer">QCVN dùng đơn vị µg/Nm³ nên không tương đương pháp lý với dữ liệu mô phỏng µg/m³. WHO là hướng dẫn, không phải quy chuẩn pháp lý. Báo cáo không đánh giá tuân thủ trung bình năm.</p></section>
<section><h2>Ma trận theo giờ</h2>{_matrix_html(view['weekly_matrix'])}</section>
<footer class="disclaimer"><p>Dữ liệu mô phỏng cho MVP, không phải quan trắc được chứng nhận.</p></footer></body></html>"""


def render_publication_pdf(report: dict[str, Any]) -> bytes:
    try:
        from pypdf import PdfReader, PdfWriter
        from reportlab.graphics.shapes import Drawing, Rect, String
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import mm
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.pdfgen.canvas import Canvas
        from reportlab.platypus import KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    except ImportError as exc:
        raise ServiceError(
            "pdf_export_dependency_missing",
            "PDF export is unavailable because reportlab is not installed.",
            503,
        ) from exc

    view = build_publication_view_model(report)
    font_name, bold_font = _register_pdf_fonts(pdfmetrics, TTFont)
    styles = getSampleStyleSheet()
    for style in styles.byName.values():
        style.fontName = font_name
    styles["Title"].fontName = bold_font
    styles.add(ParagraphStyle(name="AGHeading", parent=styles["Heading2"], fontName=bold_font, textColor=colors.HexColor("#123F50"), spaceBefore=12, spaceAfter=7))
    styles.add(ParagraphStyle(name="AGSmall", parent=styles["BodyText"], fontName=font_name, fontSize=7.5, leading=10, textColor=colors.HexColor("#52606D")))
    styles.add(ParagraphStyle(name="AGCenter", parent=styles["BodyText"], fontName=font_name, alignment=TA_CENTER, fontSize=8))
    styles.add(ParagraphStyle(name="AGOverline", parent=styles["BodyText"], fontName=bold_font, fontSize=7.5, leading=10, textColor=colors.HexColor("#087B73"), alignment=TA_LEFT))
    styles.add(ParagraphStyle(name="AGReportTitle", parent=styles["Title"], fontName=bold_font, fontSize=23, leading=28, textColor=colors.HexColor("#123F50"), spaceAfter=4))
    styles.add(ParagraphStyle(name="AGKpiLabel", parent=styles["BodyText"], fontName=bold_font, fontSize=7.2, leading=9, textColor=colors.HexColor("#4E7372")))
    styles.add(ParagraphStyle(name="AGKpiValue", parent=styles["BodyText"], fontName=bold_font, fontSize=13, leading=16, textColor=colors.HexColor("#123F50"), spaceBefore=3, spaceAfter=3))
    styles.add(ParagraphStyle(name="AGKpiDetail", parent=styles["BodyText"], fontName=font_name, fontSize=7.2, leading=9, textColor=colors.HexColor("#607478")))
    styles.add(ParagraphStyle(name="AGNarrative", parent=styles["BodyText"], fontName=font_name, fontSize=9.2, leading=14, textColor=colors.HexColor("#334F56"), leftIndent=8, rightIndent=8))

    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=14 * mm,
        leftMargin=14 * mm,
        topMargin=18 * mm,
        bottomMargin=23 * mm,
        title="AirGuard - Báo cáo chất lượng môi trường",
        author="AirGuard AI",
    )
    story: list[Any] = [
        Paragraph("AIRGUARD · THEO DÕI MÔI TRƯỜNG", styles["AGOverline"]),
        Paragraph("Báo cáo chất lượng môi trường", styles["AGReportTitle"]),
        Paragraph(
            f"Kỳ báo cáo: {_h(_readable_period(view))} · Loại: {_h(_report_type_label(view['report_type']))}",
            styles["AGSmall"],
        ),
        Spacer(1, 12),
        Paragraph("Tóm tắt điều hành", styles["AGHeading"]),
        Paragraph(_h(view["reader_summary"]["headline"]), styles["AGSmall"]),
        Spacer(1, 7),
        _pdf_reader_summary(view, Table, TableStyle, Paragraph, styles, colors),
        Paragraph("Nhận định có căn cứ", styles["AGHeading"]),
        Paragraph(
            "Các ý chính dưới đây được tổng hợp từ cùng bản ghi báo cáo; không suy diễn nguyên nhân hoặc kết luận tuân thủ.",
            styles["AGSmall"],
        ),
        Spacer(1, 4),
        Paragraph(_h(view["reader_narrative"]), styles["AGNarrative"]),
        Paragraph("Thống kê theo trạm", styles["AGHeading"]),
        _pdf_station_table(view, Table, TableStyle, colors, font_name, bold_font),
        Paragraph("Chỉ số ESG ước tính", styles["AGHeading"]),
        _pdf_esg_table(view, Table, TableStyle, colors, font_name, bold_font),
        Paragraph("Các giá trị là ước tính mô phỏng, không phải bụi loại bỏ thực đo hoặc điện năng từ công tơ.", styles["AGSmall"]),
        PageBreak(),
        Paragraph("Đối chiếu tham chiếu và KPI nội bộ", styles["AGHeading"]),
        Paragraph("QCVN dùng đơn vị µg/Nm³ nên không tương đương pháp lý với dữ liệu simulator µg/m³. WHO là guideline, không phải quy chuẩn pháp lý. Báo cáo không đánh giá tuân thủ trung bình năm.", styles["AGSmall"]),
        Spacer(1, 5),
        _pdf_reference_table(view, Table, TableStyle, colors, font_name, bold_font),
        Paragraph("QCVN dùng đơn vị µg/Nm³ nên không tương đương pháp lý với dữ liệu simulator µg/m³. WHO là guideline, không phải quy chuẩn pháp lý. Báo cáo không đánh giá tuân thủ trung bình năm.", styles["AGSmall"]),
    ]
    matrix = _pdf_matrix(view, Drawing, Rect, String, colors, font_name, bold_font)
    if matrix is not None:
        story.extend([Paragraph("Ma trận PM2.5 theo giờ", styles["AGHeading"]), KeepTogether([matrix])])
    else:
        story.extend([Paragraph("Ma trận PM2.5 theo giờ", styles["AGHeading"]), Paragraph("Không áp dụng hoặc không có trong báo cáo legacy.", styles["BodyText"])])
    story.extend([Spacer(1, 8), Paragraph("Dữ liệu mô phỏng cho MVP, không phải quan trắc được chứng nhận.", styles["AGSmall"])])

    document.build(story)

    reader = PdfReader(BytesIO(buffer.getvalue()))
    writer = PdfWriter()
    for page_number, report_page in enumerate(reader.pages, start=1):
        overlay_buffer = BytesIO()
        overlay = Canvas(overlay_buffer, pagesize=A4)
        width, height = A4
        overlay.setFont("Helvetica", 7)
        overlay.setFillColor(colors.HexColor("#66757D"))
        overlay.drawString(14 * mm, height - 10 * mm, "AirGuard | Báo cáo môi trường")
        overlay.drawRightString(width - 18 * mm, 9 * mm, f"Trang {page_number}")
        overlay.setFillColor(colors.Color(0.1, 0.35, 0.4, alpha=0.06))
        overlay.setFont("Helvetica-Bold", 28)
        overlay.translate(width / 2, height / 2)
        overlay.rotate(34)
        overlay.drawCentredString(0, 0, "DỮ LIỆU MÔ PHỎNG")
        overlay.save()
        overlay_page = PdfReader(BytesIO(overlay_buffer.getvalue())).pages[0]
        report_page.merge_page(overlay_page, over=True)
        writer.add_page(report_page)
    writer.add_metadata({"/Title": "AirGuard - Báo cáo chất lượng môi trường", "/Author": "AirGuard AI"})
    output = BytesIO()
    writer.write(output)
    return output.getvalue()


def _pdf_meta_table(view: dict[str, Any], table_cls: Any, table_style_cls: Any, colors: Any, font: str, bold: str) -> Any:
    data = [
        ["Mã báo cáo", view["report_id"]],
        ["Kỳ / múi giờ", f"{_readable_period(view)} / {view['timezone']}"],
        ["Schema", view["schema_version"]],
        ["SHA-256", view["content_checksum_sha256"] or "Legacy - không có checksum"],
    ]
    table = table_cls(data, colWidths=[85, 390])
    table.setStyle(table_style_cls([("FONTNAME", (0, 0), (0, -1), bold), ("FONTNAME", (1, 0), (1, -1), font), ("FONTSIZE", (0, 0), (-1, -1), 7.5), ("GRID", (0, 0), (-1, -1), .35, colors.HexColor("#B8C7CC")), ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#E8F1F2")), ("VALIGN", (0, 0), (-1, -1), "TOP")]))
    return table


def _pdf_reader_summary(
    view: dict[str, Any],
    table_cls: Any,
    table_style_cls: Any,
    paragraph_cls: Any,
    styles: Any,
    colors: Any,
) -> Any:
    cards = []
    for item in view["reader_summary"]["items"]:
        cards.append(
            [
                paragraph_cls(_h(item["label"]), styles["AGKpiLabel"]),
                paragraph_cls(_h(item["value"]), styles["AGKpiValue"]),
                paragraph_cls(_h(item["detail"]), styles["AGKpiDetail"]),
            ]
        )
    rows = [cards[:2], cards[2:]]
    table = table_cls(rows, colWidths=[237.5, 237.5])
    table.setStyle(
        table_style_cls(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F2FAF7")),
                ("BOX", (0, 0), (-1, -1), 0.45, colors.HexColor("#CBE7DE")),
                ("INNERGRID", (0, 0), (-1, -1), 0.45, colors.HexColor("#DCECE7")),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
                ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                ("TOPPADDING", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ]
        )
    )
    return table


def _pdf_station_table(view: dict[str, Any], table_cls: Any, table_style_cls: Any, colors: Any, font: str, bold: str) -> Any:
    data = [["Trạm", "Mẫu", "AQI TB", "AQI max", "PM2.5 TB", "PM2.5 max"]]
    for row in view["measurements"].get("stations", []):
        data.append([str(row.get("station_id")), str(row.get("sample_count", 0)), _display(row.get("avg_aqi")), _display(row.get("max_aqi")), _display(row.get("avg_pm25")), _display(row.get("max_pm25"))])
    table = table_cls(data, repeatRows=1, colWidths=[65, 55, 72, 72, 95, 95])
    table.setStyle(_pdf_table_style(table_style_cls, colors, font, bold))
    return table


def _pdf_esg_table(view: dict[str, Any], table_cls: Any, table_style_cls: Any, colors: Any, font: str, bold: str) -> Any:
    data = [["Chỉ số", "Giá trị", "Trạng thái", "Reason code"]]
    for key, label in (("estimated_pm25_removed_kg", "PM2.5 ước tính (kg)"), ("estimated_energy_saved_kwh", "Điện năng ước tính (kWh)")):
        item = view["esg_metrics"].get(key, {})
        data.append([label, _display(item.get("value")), str(item.get("status") or "legacy_unavailable"), str(item.get("reason_code") or "-")])
    table = table_cls(data, colWidths=[155, 75, 95, 150])
    table.setStyle(_pdf_table_style(table_style_cls, colors, font, bold))
    return table


def _pdf_reference_table(view: dict[str, Any], table_cls: Any, table_style_cls: Any, colors: Any, font: str, bold: str) -> Any:
    data = [["Trạm/ngày", "PM2.5 TB", "Coverage", "QCVN", "WHO", "KPI giờ tốt"]]
    for item in view["reference_comparison"].get("station_days", []):
        data.append([f"{item.get('station_id')}\n{item.get('local_date')}", _display(item.get("avg_pm25_ug_m3")), _percent(item.get("coverage_ratio")), str(item.get("qcvn", {}).get("status")), str(item.get("who", {}).get("status")), _percent(item.get("good_hour_kpi", {}).get("good_hour_rate"))])
    table = table_cls(data, repeatRows=1, colWidths=[90, 70, 70, 90, 90, 75])
    table.setStyle(_pdf_table_style(table_style_cls, colors, font, bold))
    return table


def _pdf_table_style(table_style_cls: Any, colors: Any, font: str, bold: str) -> Any:
    return table_style_cls([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#DCECEE")), ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#123F50")), ("FONTNAME", (0, 0), (-1, 0), bold), ("FONTNAME", (0, 1), (-1, -1), font), ("FONTSIZE", (0, 0), (-1, -1), 7), ("LEADING", (0, 0), (-1, -1), 8.5), ("GRID", (0, 0), (-1, -1), .35, colors.HexColor("#AABBC0")), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7FAFA")])])


def _pdf_matrix(view: dict[str, Any], drawing_cls: Any, rect_cls: Any, string_cls: Any, colors: Any, font: str, bold: str) -> Any | None:
    matrix = view["weekly_matrix"]
    if matrix.get("status") != "available" or not matrix.get("views"):
        return None
    matrix_view = next((item for item in matrix["views"] if item.get("station_selector") == "all_stations"), matrix["views"][0])
    cells = matrix_view.get("cells", [])
    if len(cells) != 168:
        return None
    cell_w, cell_h, label_w = 17.6, 13.5, 49
    width, height = label_w + 24 * cell_w, 20 + 7 * cell_h + 30
    drawing = drawing_cls(width, height)
    drawing.add(string_cls(0, height - 9, f"View: {matrix_view.get('station_selector')}", fontName=bold, fontSize=7, fillColor=colors.HexColor("#123F50")))
    for hour in range(24):
        drawing.add(string_cls(label_w + hour * cell_w + cell_w / 2, height - 21, str(hour), textAnchor="middle", fontName=font, fontSize=5.5))
    for index, cell in enumerate(cells):
        row, column = divmod(index, 24)
        x = label_w + column * cell_w
        y = height - 27 - (row + 1) * cell_h
        if column == 0:
            drawing.add(string_cls(0, y + 3.5, str(cell.get("local_date")), fontName=font, fontSize=5.5))
        if cell.get("status") == "eligible" and cell.get("value") is not None:
            fill = colors.HexColor(_matrix_color(float(cell["value"])))
            drawing.add(rect_cls(x, y, cell_w, cell_h, fillColor=fill, strokeColor=colors.white, strokeWidth=.25))
        else:
            drawing.add(rect_cls(x, y, cell_w, cell_h, fillColor=colors.HexColor("#F1F3F4"), strokeColor=colors.HexColor("#B9C2C6"), strokeWidth=.25))
            drawing.add(string_cls(x + cell_w / 2, y + 4, "N/A", textAnchor="middle", fontName=font, fontSize=4.2, fillColor=colors.HexColor("#66757D")))
    legend_y = 3
    for index, value in enumerate((0, 15, 35, 45, 75, 150)):
        x = label_w + index * 58
        drawing.add(rect_cls(x, legend_y, 15, 7, fillColor=colors.HexColor(_matrix_color(float(value))), strokeColor=None))
        drawing.add(string_cls(x + 18, legend_y, str(value), fontName=font, fontSize=5.3))
    return drawing


def _register_pdf_fonts(pdfmetrics: Any, tt_font_cls: Any) -> tuple[str, str]:
    regular_candidates = [
        os.getenv("REPORT_PDF_FONT_PATH", ""),
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "C:/Windows/Fonts/arial.ttf",
    ]
    bold_candidates = [
        os.getenv("REPORT_PDF_BOLD_FONT_PATH", ""),
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
    ]
    regular = next((path for path in regular_candidates if path and os.path.isfile(path)), None)
    bold = next((path for path in bold_candidates if path and os.path.isfile(path)), None)
    if not regular or not bold:
        return "Helvetica", "Helvetica-Bold"
    try:
        pdfmetrics.registerFont(tt_font_cls("AirGuardSans", regular))
        pdfmetrics.registerFont(tt_font_cls("AirGuardSans-Bold", bold))
        return "AirGuardSans", "AirGuardSans-Bold"
    except Exception:
        return "Helvetica", "Helvetica-Bold"


def _matrix_markdown(matrix: dict[str, Any]) -> str:
    if matrix.get("status") != "available":
        return "Not applicable for this report."
    views = matrix.get("views") or []
    return f"Persisted matrix has {len(views)} station view(s); each available view contains 168 cells. Color scale: {matrix.get('color_scale', {}).get('version', 'N/A')}. Missing cells are N/A."


def _matrix_html(matrix: dict[str, Any]) -> str:
    if matrix.get("status") != "available" or not matrix.get("views"):
        return "<p>Không áp dụng hoặc không có trong báo cáo legacy.</p>"
    view = next((item for item in matrix["views"] if item.get("station_selector") == "all_stations"), matrix["views"][0])
    cells = view.get("cells", [])
    header = "".join(f"<th>{hour}</th>" for hour in range(24))
    rows = []
    for row in range(7):
        subset = cells[row * 24 : (row + 1) * 24]
        if len(subset) != 24:
            continue
        day = _h(subset[0].get("local_date"))
        rendered = "".join(
            f'<td class="{"" if cell.get("status") == "eligible" else "na"}" title="samples={cell.get("valid_sample_count")}; expected={cell.get("expected_sample_count")}; coverage={cell.get("coverage_ratio")}; stations={cell.get("eligible_station_count")}">{_h(_display(cell.get("value"))) if cell.get("status") == "eligible" else "N/A"}</td>'
            for cell in subset
        )
        rows.append(f"<tr><th>{day}</th>{rendered}</tr>")
    return f'<p>View: {_h(view.get("station_selector"))}; scale: {_h(matrix.get("color_scale", {}).get("version"))}</p><div style="overflow:auto"><table><thead><tr><th>Ngày/giờ</th>{header}</tr></thead><tbody>{"".join(rows)}</tbody></table></div>'


def _esg_html(esg: dict[str, Any]) -> str:
    parts = []
    for key, label in (("estimated_pm25_removed_kg", "PM2.5 ước tính"), ("estimated_energy_saved_kwh", "Điện năng ước tính")):
        item = esg.get(key, {})
        parts.append(f"<p><strong>{_h(label)}:</strong> {_h(_display(item.get('value')))} {_h(item.get('unit') or '')} - status={_h(item.get('status') or 'legacy_unavailable')}; reason={_h(item.get('reason_code') or '-')}</p>")
    return "".join(parts)


def _matrix_color(value: float) -> str:
    stops = (0, 15, 35, 45, 75, 150)
    palette = ("#E8F5E9", "#B9E4C9", "#F4E38B", "#F6B26B", "#E06666", "#8E3B63")
    for index, stop in enumerate(stops):
        if value <= stop:
            return palette[index]
    return palette[-1]


def _display(value: Any) -> str:
    if value is None:
        return "N/A"
    if isinstance(value, float):
        return f"{value:g}"
    return str(value)


def _percent(value: Any) -> str:
    try:
        return f"{float(value) * 100:.1f}%"
    except (TypeError, ValueError):
        return "N/A"


def _h(value: Any) -> str:
    return html.escape(str(value if value is not None else ""), quote=True)


def _iso(value: Any) -> str:
    return value.isoformat() if hasattr(value, "isoformat") else str(value or "")


def _readable_period(view: dict[str, Any]) -> str:
    return f"{_readable_timestamp(view['period_start'])} - {_readable_timestamp(view['period_end'])}"


def _readable_timestamp(value: Any) -> str:
    raw = str(value or "")
    try:
        from datetime import datetime

        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        return parsed.strftime("%H:%M %d/%m/%Y")
    except ValueError:
        return raw


def _report_type_label(value: str) -> str:
    return {"daily": "Hàng ngày", "weekly": "Hàng tuần"}.get(value, value)
