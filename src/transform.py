from datetime import datetime, timedelta, timezone

try:
    from zoneinfo import ZoneInfo
    LOCAL_TZ = ZoneInfo("America/Vancouver")
except Exception:  # sandbox without tzdata: fall back to PDT
    LOCAL_TZ = timezone(timedelta(hours=-7))

# Extra time over the usual (historic) drive, as a fraction, mapped to a label.
TRAFFIC_LEVELS = [
    (0.10, "Light traffic"),
    (0.30, "Moderate traffic"),
]


def clock(dt):
    return dt.strftime("%I:%M").lstrip("0")


def traffic_note(status, delay_min):
    if status == "Light traffic":
        return "Traffic is normal"
    return f"{status}, {delay_min} min slower than usual"


def traffic_label(eta_s, typical_s):
    ratio = (eta_s - typical_s) / typical_s if typical_s else 0
    for threshold, label in TRAFFIC_LEVELS:
        if ratio < threshold:
            return label
    return "Heavy traffic"


def error_message(input):
    # TomTom reports errors as {"detailedError": {"message": ...}} or {"error": ...}.
    detailed = input.get("detailedError") or {}
    error = input.get("error")
    if isinstance(error, dict):
        error = error.get("message") or error.get("description")
    return detailed.get("message") or error or "No route returned"


def run(input):
    now = datetime.now(LOCAL_TZ)
    routes = input.get("routes") or []

    if not routes:
        return {"error": error_message(input), "updated_at": clock(now)}

    summary = routes[0]["summary"]
    eta_s = summary["travelTimeInSeconds"]
    typical_s = summary.get("historicTrafficTravelTimeInSeconds") or eta_s
    delay_min = max(0, round((eta_s - typical_s) / 60))
    status = traffic_label(eta_s, typical_s)

    return {
        "eta_min": round(eta_s / 60),
        "typical_min": round(typical_s / 60),
        "delay_min": delay_min,
        "arrive_at": clock(now + timedelta(seconds=eta_s)),
        "distance_km": round(summary.get("lengthInMeters", 0) / 1000),
        "status": status,
        "traffic_note": traffic_note(status, delay_min),
        "leave_at": clock(now),
        "updated_at": clock(now),
    }
