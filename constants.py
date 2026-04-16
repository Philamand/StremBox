import os

MANIFEST = {
    "id": "StremBox/Philamand/org.codeberg",
    "version": "1.0.0",
    "name": "StremBox",
    "description": "Sample addon made with FastAPI providing a few public domain movies",
    "types": ["movie", "series"],
    "catalogs": [],
    "resources": [
        {"name": "stream", "types": ["movie", "series"], "idPrefixes": ["tt", "hpy"]}
    ],
}

STREAMS_BASE_URL: str = os.getenv("STREAMS_BASE_URL", "http://127.0.0.1:5000")
