from django import template
from django.conf import settings

register = template.Library()

@register.inclusion_tag('custom_code/partials/target_data.html')
def tides_target_data(target):
    """
    Render extra target fields from settings.EXTRA_FIELDS.
    Prefers Target.extra_fields JSON (from TOM), falling back to model attributes.
    """
    exclude_fields = {
        'name',
        'tidesclass',
        'tidesclass_other',
        'tidesclass_subclass',
        'auto_tidesclass',
        'auto_tidesclass_other',
        'auto_tidesclass_subclass',
        'auto_tidesclass_prob',
        'human_tidesclass',
        'human_tidesclass_other',
        'human_tidesclass_subclass',
    }

    extra_fields_spec = getattr(settings, 'EXTRA_FIELDS', []) or []
    extra_store = getattr(target, 'extra_fields', None) or {}

    extras = {}
    for spec in extra_fields_spec:
        name = spec.get('name')
        if not name or spec.get('hidden', False) or name in exclude_fields:
            continue
        # Prefer JSON value; fall back to attribute/property
        val = extra_store.get(name)
        if val is None:
            val = getattr(target, name, '')
        extras[name] = val

    return {'target': target, 'extras': extras}

@register.inclusion_tag('custom_code/partials/target_classifications.html')
def target_classifications(target):
    return {'target': target}

@register.inclusion_tag('custom_code/partials/aladin_finderchart.html')
def aladin_finderchart(target):
    """
    Displays Aladin skyview of the given target along with basic finder chart annotations including a compass
    and a scale bar. The resulting image is downloadable. This templatetag only works for sidereal targets.
    """

    return {'target': target}

