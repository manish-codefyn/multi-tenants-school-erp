from django import forms

class DateInput(forms.DateInput):
    """
    Custom DateInput widget with HTML5 date type.
    """
    input_type = 'date'
    
    def __init__(self, attrs=None):
        default_attrs = {'class': 'form-control'}
        if attrs:
            default_attrs.update(attrs)
        super().__init__(attrs=default_attrs)

class PhoneInput(forms.TextInput):
    """
    Custom TextInput widget for phone numbers.
    """
    input_type = 'tel'
    
    def __init__(self, attrs=None):
        default_attrs = {'class': 'form-control', 'pattern': '[0-9+ -]*'}
        if attrs:
            default_attrs.update(attrs)
        super().__init__(attrs=default_attrs)

class SelectWithSearch(forms.Select):
    """
    Select widget that can be initialized with Select2 or similar libraries.
    """
    def __init__(self, attrs=None):
        default_attrs = {'class': 'form-control select2'}
        if attrs:
            if 'class' in attrs:
                attrs['class'] += ' select2'
            else:
                attrs.update({'class': 'form-control select2'})
        else:
            attrs = default_attrs
        super().__init__(attrs=attrs)

class SelectMultipleWithSearch(forms.SelectMultiple):
    """
    SelectMultiple widget that can be initialized with Select2 or similar libraries.
    """
    def __init__(self, attrs=None):
        default_attrs = {'class': 'form-control select2'}
        if attrs:
            if 'class' in attrs:
                attrs['class'] += ' select2'
            else:
                attrs.update({'class': 'form-control select2'})
        else:
            attrs = default_attrs
        super().__init__(attrs=attrs)


class TimeInput(forms.TimeInput):
    """
    Custom TimeInput widget with HTML5 time type.
    """
    input_type = 'time'

    def __init__(self, attrs=None):
        default_attrs = {'class': 'form-control'}
        if attrs:
            default_attrs.update(attrs)
        super().__init__(attrs=default_attrs)
