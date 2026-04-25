from datetime import datetime


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
