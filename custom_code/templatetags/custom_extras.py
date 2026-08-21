import json
import math
import numpy as np
from astropy.io import fits
from scipy.interpolate import interp1d
from django import template
from django.http import JsonResponse
from django.db.models import Count
from custom_code.models import PipelineClassificationGlobal, TidesSpec
from tom_dataproducts.models import ReducedDatum
import numpy as np
from scipy.interpolate import interp1d
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
@register.inclusion_tag('custom_code/partials/classification_chart.html') #partial doesn't exist, fine because returns JsonResponse
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

@register.inclusion_tag('custom_code/partials/average_spectrum.html')
def average_spectrum_data():
    sn_types = list(PipelineClassificationGlobal.objects
                    .exclude(sn_type__isnull=True)
                    .values_list(
                        'sn_type', flat=True))
    # remove duplicates and sort the list of supernova types
    unique_types = sorted(set(i.strip() for i in sn_types))

    return {'sn_types': unique_types}

def average_spectrum_by_type(request, sn_type):
    specids = PipelineClassificationGlobal.objects.filter(
        sn_type=sn_type
    ).values_list('tides_specid', flat=True)

    filepaths = (TidesSpec.objects
        .filter(tides_specid__in=specids)
        .filter(filepath__isnull=False)
        .values_list('filepath', flat=True))
    
    all_wavelengths = []
    all_fluxes = []

    for filepath in filepaths:
        if filepath.endswith('.fits'):
            try:
                from astropy.io import fits
                with fits.open(filepath) as hdul:
                    #need 1d array for interpolation
                    wavelengths = hdul[1].data['WAVE'].flatten()
                    fluxes = hdul[1].data['FLUX'].flatten()
                    all_wavelengths.append(wavelengths)
                    all_fluxes.append(fluxes)
            except Exception as e:
                print(f"Failed to read {filepath}: {e}")
        elif filepath.endswith('.txt'):
            try:
                data = np.loadtxt(filepath)
                wavelengths = data[:, 0]
                fluxes = data[:, 1]
                all_wavelengths.append(wavelengths)
                all_fluxes.append(fluxes)
            except Exception as e:
                print(f"Failed to read {filepath}: {e}")
        else:
            print(f"Unsupported file format for {filepath}")
            continue

    if not all_wavelengths:
        return JsonResponse({'wavelengths': [], 'flux': []})

    common_wavelengths = list(all_wavelengths[0])
    # allows for comparison between the different spectra, maps all onto first spectrum
    interpolated_fluxes = []
    # incase the flux values aren't the same across all spectra
    for wavelengths, fluxes in zip(all_wavelengths, all_fluxes):
        interpolator = interp1d(wavelengths, fluxes, bounds_error=False, fill_value=0)
        interpolated_fluxes.append(interpolator(common_wavelengths))

    average_flux = np.nan_to_num(np.mean(interpolated_fluxes, axis=0), nan=0, posinf=0, neginf=0)

    return JsonResponse({
        'wavelengths': [float(w) for w in common_wavelengths],
        'flux': [float(f) for f in average_flux]
    })
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

@register.inclusion_tag('custom_code/partials/average_spectrum.html')
def average_spectrum_data():
    sn_types = list(PipelineClassificationGlobal.objects
                    .exclude(sn_type__isnull=True)
                    .values_list(
                        'sn_type', flat=True))
    # remove duplicates and sort the list of supernova types
    unique_types = sorted(set(i.strip() for i in sn_types))

    return {'sn_types': unique_types}

def average_spectrum_by_type(request, sn_type):
    specids = PipelineClassificationGlobal.objects.filter(
        sn_type=sn_type
    ).values_list('tides_specid', flat=True)

    filepaths = (TidesSpec.objects
        .filter(tides_specid__in=specids)
        .filter(filepath__isnull=False)
        .values_list('filepath', flat=True))
    
    all_wavelengths = []
    all_fluxes = []

    for filepath in filepaths:
        try:
            from astropy.io import fits
            with fits.open(filepath) as hdul:
                #need 1d array for interpolation
                wavelengths = hdul[1].data['WAVE'].flatten()
                fluxes = hdul[1].data['FLUX'].flatten()
                all_wavelengths.append(wavelengths)
                all_fluxes.append(fluxes)
        except Exception as e:
            print(f"Failed to read {filepath}: {e}")
            continue

    if not all_wavelengths:
        return JsonResponse({'wavelengths': [], 'flux': []})

    common_wavelengths = list(all_wavelengths[0])
    # allows for comparison between the different spectra, maps all onto first spectrum
    interpolated_fluxes = []
    # incase the flux values aren't the same across all spectra
    for wavelengths, fluxes in zip(all_wavelengths, all_fluxes):
        interpolator = interp1d(wavelengths, fluxes, bounds_error=False, fill_value=0)
        interpolated_fluxes.append(interpolator(common_wavelengths))

    average_flux = np.nan_to_num(np.mean(interpolated_fluxes, axis=0), nan=0, posinf=0, neginf=0)

    return JsonResponse({
        'wavelengths': [float(w) for w in common_wavelengths],
        'flux': [float(f) for f in average_flux]
    })


