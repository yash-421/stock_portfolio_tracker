from typing import Any


def get_response(status: str, data: Any, message: str) -> dict:
    """Helper function to format API responses."""
    return {
        "status": status,
        "data": data,
        "message": message
    }