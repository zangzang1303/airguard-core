def baseline_forecast(current_pm25: float, hours: int) -> list[dict]:
    """Simple placeholder forecast that holds current PM2.5 constant."""
    return [
        {
            "hour_offset": hour,
            "pm25": round(current_pm25, 2),
            "method": "placeholder_constant_baseline",
        }
        for hour in range(1, hours + 1)
    ]
