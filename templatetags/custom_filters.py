from django import template

register = template.Library()

@register.filter
def first_word(value):
    """Return only the first word from a string."""
    if not value:
        return ""
    return value.split()[0]



@register.filter
def get_first_word(value):
    """Return the first word of a string"""
    if value:
        return value.split()[0]
    return value



@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)