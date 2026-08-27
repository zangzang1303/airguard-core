def build_placeholder_answer(message: str) -> dict:
    """Return a constrained placeholder until the real tool-calling agent exists."""
    return {
        "answer": (
            "Agent skeleton only. Future implementation will call backend tools "
            "for PM2.5, weather, forecast, alerts, and HITL proposals."
        ),
        "used_tools": [],
        "received_message": message,
        "todo": "Implement AI Agent tool-calling with HITL constraints.",
    }
