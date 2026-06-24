"""Weather information via wttr.in — no API key required."""
import requests

_WIND_DIRS = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
              "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]

_WMO_ICONS = {
    113: "☀️",  116: "⛅",  119: "☁️",  122: "☁️",
    143: "🌫️", 176: "🌦️", 179: "🌨️", 182: "🌧️", 185: "🌧️",
    200: "⛈️",  227: "❄️",  230: "❄️",  248: "🌫️", 260: "🌫️",
    263: "🌦️", 266: "🌦️", 281: "🌧️", 284: "🌧️",
    293: "🌦️", 296: "🌦️", 299: "🌧️", 302: "🌧️", 305: "🌧️",
    308: "🌧️", 311: "🌧️", 314: "🌧️", 317: "🌨️", 320: "🌨️",
    323: "🌨️", 326: "🌨️", 329: "❄️",  332: "❄️",  335: "❄️",
    338: "❄️",  350: "🌧️", 353: "🌦️", 356: "🌧️", 359: "🌧️",
    362: "🌨️", 365: "🌨️", 368: "🌨️", 371: "❄️",  374: "🌨️",
    377: "🌨️", 386: "⛈️",  389: "⛈️",  392: "⛈️",  395: "❄️",
}


def _wind_dir(degree: int) -> str:
    return _WIND_DIRS[round(degree / 22.5) % 16]


def _fetch(location: str) -> dict:
    url = f"https://wttr.in/{location}?format=j1"
    resp = requests.get(url, timeout=10, headers={"User-Agent": "palmiche-jarvis/1.0"})
    resp.raise_for_status()
    return resp.json()


def get_weather(city: str = "", units: str = "metric") -> str:
    """Get current weather conditions for *city* (empty = auto-detect by IP)."""
    u = (units or "metric").strip().lower()
    if u not in ("metric", "imperial"):
        u = "metric"
    deg = "°C" if u == "metric" else "°F"

    try:
        data = _fetch(city.strip() if city else "")
    except Exception as exc:
        return f"Error obteniendo el clima: {exc}"

    try:
        cur = data["current_condition"][0]
        area = data["nearest_area"][0]
        location_name = f"{area['areaName'][0]['value']}, {area['country'][0]['value']}"

        wmo = int(cur.get("weatherCode", 113))
        icon = _WMO_ICONS.get(wmo, "🌡️")
        desc = cur["weatherDesc"][0]["value"]

        temp = cur["temp_C"] if u == "metric" else cur["temp_F"]
        feels = cur["FeelsLikeC"] if u == "metric" else cur["FeelsLikeF"]
        wind_spd = cur.get("windspeedKmph") if u == "metric" else cur.get("windspeedMiles")
        wind_unit = "km/h" if u == "metric" else "mph"
        wind_d = _wind_dir(int(cur.get("winddirDegree", 0)))

        lines = [
            f"{icon} {desc} — {location_name}",
            f"Temperatura: {temp}{deg} (sensación {feels}{deg})",
            f"Humedad: {cur.get('humidity', '?')}%",
            f"Viento: {wind_spd} {wind_unit} {wind_d}",
            f"Visibilidad: {cur.get('visibility', '?')} km",
            f"Presión: {cur.get('pressure', '?')} hPa",
        ]

        if data.get("weather"):
            today = data["weather"][0]
            max_t = today["maxtempC"] if u == "metric" else today["maxtempF"]
            min_t = today["mintempC"] if u == "metric" else today["mintempF"]
            lines.append(f"Hoy: máx {max_t}{deg} / mín {min_t}{deg}")

        return "\n".join(lines)
    except (KeyError, IndexError, TypeError) as exc:
        return f"Error procesando datos del clima: {exc}"


def get_forecast(city: str = "", days: int = 3, units: str = "metric") -> str:
    """Get a multi-day weather forecast for *city* (1-3 days)."""
    u = (units or "metric").strip().lower()
    if u not in ("metric", "imperial"):
        u = "metric"
    deg = "°C" if u == "metric" else "°F"
    try:
        days = max(1, min(3, int(days)))
    except (TypeError, ValueError):
        days = 3

    try:
        data = _fetch(city.strip() if city else "")
    except Exception as exc:
        return f"Error obteniendo el pronóstico: {exc}"

    try:
        area = data["nearest_area"][0]
        location_name = f"{area['areaName'][0]['value']}, {area['country'][0]['value']}"

        lines = [f"Pronóstico — {location_name}:"]
        for day in data.get("weather", [])[:days]:
            max_t = day["maxtempC"] if u == "metric" else day["maxtempF"]
            min_t = day["mintempC"] if u == "metric" else day["mintempF"]
            hourly = day.get("hourly", [])
            # Noon entry for representative description
            noon = next((h for h in hourly if h.get("time") == "1200"), hourly[len(hourly) // 2] if hourly else {})
            desc = noon.get("weatherDesc", [{}])[0].get("value", "?") if noon else "?"
            wmo = int(noon.get("weatherCode", 113)) if noon else 113
            icon = _WMO_ICONS.get(wmo, "🌡️")
            rain_total = sum(float(h.get("precipMM", 0)) for h in hourly)
            lines.append(
                f"{day['date']}: {icon} {desc} | {max_t}{deg}/{min_t}{deg} | "
                f"Lluvia: {rain_total:.1f} mm"
            )

        return "\n".join(lines)
    except (KeyError, IndexError, TypeError) as exc:
        return f"Error procesando pronóstico: {exc}"
