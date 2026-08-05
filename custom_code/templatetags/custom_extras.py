import json
from django import template
from django.http import JsonResponse
from django.db.models import Count
from custom_code.models import (
    PipelineClassificationGlobal, 
    TidesSpec
)
from tom_dataproducts.models import ReducedDatum
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
        TidesSpec.objects
        .filter(obs_date__isnull=False)  # needed because obs_date can have null values, which dont work with strftime
        .annotate(month=TruncMonth('obs_date'))
        .values('month')
        .annotate(count=Count('tides_specid'))
        .order_by('month')
    )
    labels = [entry['month'].strftime('%B %Y') for entry in data]
    counts = [entry['count'] for entry in data]
    return JsonResponse({'labels': labels, 'counts': counts})

@register.inclusion_tag('custom_code/partials/redshift_plot.html')
def redshift_plot_data(request):
    data = (
        PipelineClassificationGlobal.objects
        #.exclude(z__isnull=True)
        #.exclude(sn_type__isnull=True)
        .values('sn_type', 'z')
    )
    sn_types = [entry['sn_type'] for entry in data]
    redshifts = [entry['z'] for entry in data]
    return JsonResponse({'sn_types': sn_types, 'redshifts': redshifts})


