import json
from django import template
from tom_dataproducts.models import ReducedDatum

# initialization of the template library
register = template.Library()

@register.inclusion_tag('custom_code/partials/recent_photometry.html')
def recent_photometry(target, num_points=1, limit=None):
    photometry = ReducedDatum.objects.filter(data_type='photometry').order_by('-timestamp')[:num_points]
    return {'recent_photometry': [(datum.timestamp, json.loads(datum.value)['magnitude']) for datum in photometry]}