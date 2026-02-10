from django import template


register = template.Library()


@register.filter
def duration_weeks_days_hours(value):
    if value is None:
        return ""

    try:
        total_seconds = int(value.total_seconds())
    except AttributeError:
        return ""

    if total_seconds < 0:
        total_seconds = 0

    total_hours = total_seconds // 3600
    weeks = total_hours // (7 * 24)
    days = (total_hours % (7 * 24)) // 24
    hours = total_hours % 24

    parts = []
    if weeks:
        parts.append(f"{weeks}w")
    if days or weeks:
        parts.append(f"{days}d")
    parts.append(f"{hours}h")

    return " ".join(parts)
