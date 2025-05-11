from django import template

register = template.Library()

@register.filter
def multiply(value, arg):
    """Nhân value với arg."""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0 