from django import template
from django.conf import settings
from tom_targets.models import Target
from custom_code.models import PipelineClassificationGlobal, HumanClassification

register = template.Library()

@register.inclusion_tag('custom_code/partials/target_data.html')
def tides_target_data(target):
    """
    Displays the data of a target.
    """
    exclude_fields = ['name', 'classification', 'z_best', 'z_sn', 'z_gal', 'z_source', 'confidence']
    extras = {k['name']: target.extra_fields.get(k['name'], '') for k in settings.EXTRA_FIELDS if not k.get('hidden') and k['name'] not in exclude_fields}
    print(target.as_dict())
    return {
        'target': target,
        'extras': extras
    }

@register.inclusion_tag('custom_code/partials/target_classifications.html')
def target_classifications(target):
    """
    Displays the classifications of a target.
    """
    auto_classifications = PipelineClassificationGlobal.objects.filter(tides_id=target.tides_id).order_by('-probability')
    human_classifications = HumanClassification.objects.filter(tides_id=target.tides_id).order_by('-created')
    aggregated_human_class = HumanClassification.aggregate_human_tidesclass(target.tides_id)

    return {
        'target': target,
        'auto_classifications': auto_classifications,
        'human_classifications': human_classifications,
        'aggregated_human_class': aggregated_human_class,
    }
    return {'target': target}

@register.inclusion_tag('custom_code/partials/aladin_finderchart.html')
def aladin_finderchart(target):
    """
    Displays Aladin skyview of the given target along with basic finder chart annotations including a compass
    and a scale bar. The resulting image is downloadable. This templatetag only works for sidereal targets.
    """

    return {'target': target}

