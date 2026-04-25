from datetime import datetime

from jinja2 import Environment


def relative_time(timestamp):
    """Jinja filter: returns French relative time string."""
    if not timestamp:
        return ""
    now = datetime.now()
    if isinstance(timestamp, datetime):
        delta = now - timestamp
    else:
        delta = now - datetime.fromtimestamp(timestamp)

    total_seconds = int(delta.total_seconds())
    if total_seconds < 0:
        return "Créé dans le futur"

    minutes = total_seconds // 60
    hours = minutes // 60
    days = hours // 24
    months = days // 30

    if months > 0:
        return f"Créé il y a {months} mois" if months > 1 else "Créé il y a 1 mois"
    if days > 0:
        return f"Créé il y a {days} jours" if days > 1 else "Créé il y a 1 jour"
    if hours > 0:
        return f"Créé il y a {hours} heures" if hours > 1 else "Créé il y a 1 heure"
    if minutes > 0:
        return (
            f"Créé il y a {minutes} minutes" if minutes > 1 else "Créé il y a 1 minute"
        )
    return "Créé à l'instant"


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
