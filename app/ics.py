"""Hand-written iCalendar export. No third-party calendar library."""

from datetime import datetime, timezone


def _escape(text: str) -> str:
    return (
        text.replace("\\", "\\\\")
        .replace("\r\n", "\\n")
        .replace("\n", "\\n")
        .replace("\r", "")
        .replace(";", "\\;")
        .replace(",", "\\,")
    )


def build_ics(items, car_label: str) -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//CalculadoraCombustible//Mantenimiento//ES",
    ]
    for item in items:
        due = item.get("due_date")
        if due is None or item.get("status") == "sin_datos":
            continue
        summary = _escape(f"{item['label']} · {car_label}")
        lines.extend(
            [
                "BEGIN:VEVENT",
                f"UID:{item['key']}-{due.strftime('%Y%m%d')}@calculadora-combustible",
                f"DTSTAMP:{stamp}",
                f"DTSTART;VALUE=DATE:{due.strftime('%Y%m%d')}",
                f"SUMMARY:{summary}",
                "BEGIN:VALARM",
                "ACTION:DISPLAY",
                "TRIGGER:-P3D",
                f"DESCRIPTION:{summary}",
                "END:VALARM",
                "END:VEVENT",
            ]
        )
    lines.append("END:VCALENDAR")
    return "\r\n".join(lines) + "\r\n"
