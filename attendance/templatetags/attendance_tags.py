"""Custom template tags for the attendance app."""
from django import template

register = template.Library()


@register.filter(name='get_field_by_name')
def get_field_by_name(form, field_name):
    """Render a specific form field by its name, e.g. form|get_field_by_name:'student_5'."""
    bound_field = form[field_name] if field_name in form.fields else ''
    if bound_field == '':
        return ''
    return bound_field
