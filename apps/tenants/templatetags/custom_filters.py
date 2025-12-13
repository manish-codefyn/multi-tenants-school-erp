from django import template

register = template.Library()

@register.filter
def placeholder_filter(value):
    return value
