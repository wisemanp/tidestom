import json
from django import template
from django.http import JsonResponse
from django.db.models import Count
from custom_code.models import PipelineClassificationGlobal
from tom_dataproducts.models import ReducedDatum
from custom_code.models import HumanClassification, TagProposal, TargetTag
from django.db.models.functions import TruncMonth

# initialization of the template library
register = template.Library()

@register.inclusion_tag('custom_code/partials/recent_photometry.html')
def recent_photometry(target, num_points=1, limit=None):
    photometry = ReducedDatum.objects.filter(data_type='photometry').order_by('-timestamp')[:num_points]
    return {'recent_photometry': [(datum.timestamp, json.loads(datum.value)['magnitude']) for datum in photometry]}

# Template tag for fetching classification data
@register.inclusion_tag('custom_code/partials/classification_chart.html')
def classification_data(request):
    '''fetches the classification data (type and counts) for the pie chart'''
    data = (
        PipelineClassificationGlobal.objects
        .values('sn_type')
        .annotate(count=Count('id'))
        .order_by('sn_type')
    )
    labels = [entry['sn_type'] for entry in data]
    counts = [entry['count'] for entry in data]
    return JsonResponse({'labels': labels, 'counts': counts})

@register.inclusion_tag('custom_code/partials/classification_timeline.html')
def classification_timeline_data(request):
    data = (
        TargetTag.objects
        .annotate(month=TruncMonth('created'))
        .values('month')
        .annotate(count=Count('id'))
        .order_by('month')
    )
    labels = [entry['month'].strftime('%B %Y') for entry in data]
    counts = [entry['count'] for entry in data]
    return JsonResponse({'labels': labels, 'counts': counts})