from fastapi import Request


def is_htmx_request(request: Request) -> bool:
    """
    FastAPI dependency that returns True if the request includes the HX-Request header.
    """
    return request.headers.get("HX-Request") is not None
