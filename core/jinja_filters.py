from datetime import datetime, timedelta, timezone

from jinja2 import Environment


def _format_relative_delta(delta: timedelta) -> str:
    """Format a timedelta as a French relative time string.

    Positive deltas produce "X mois/jours/heures/minutes" strings; negative ones return "dans le futur".
    """
    total_seconds = int(delta.total_seconds())
    if total_seconds < 0:
        return "dans le futur"

    minutes = total_seconds // 60
    hours = minutes // 60
    days = hours // 24
    months = days // 30

    if months > 0:
        return f"{months} mois" if months > 1 else "un mois"
    if days > 0:
        return f"{days} jours" if days > 1 else "un jour"
    if hours > 0:
        return f"{hours} heures" if hours > 1 else "une heure"
    if minutes > 0:
        return f"{minutes} minutes" if minutes > 1 else "une minute"
    return "moins d'une minute"


def relative_time(value: datetime | int | timedelta | None) -> str:
    """Jinja filter: returns French relative time string.

    Accepts a datetime, a POSIX timestamp (int), a timedelta, or None.
      - datetime / int  ->  delta computed from now (UTC)
      - timedelta       ->  used directly
    """
    if not value:
        return ""
    if isinstance(value, timedelta):
        return _format_relative_delta(value)

    now = datetime.now(timezone.utc)
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        delta = now - value
    else:
        delta = now - datetime.fromtimestamp(value, tz=timezone.utc)

    return _format_relative_delta(delta)


def format_size(bytes_count: int) -> str:
    """Jinja filter: converts bytes to human-readable size (B, KB, MB, GB)."""
    if bytes_count < 0:
        return "0B"
    if bytes_count < 1024:
        return f"{bytes_count}B"
    kb = bytes_count / 1024
    if kb < 1024:
        return f"{kb:.1f}KB"
    mb = kb / 1024
    if mb < 1024:
        return f"{mb:.1f}MB"
    gb = mb / 1024
    return f"{gb:.1f}GB"


def register_filters(env: Environment) -> None:
    """Register all custom Jinja filters on the given environment."""
    env.filters["relative_time"] = relative_time
    env.filters["format_size"] = format_size
