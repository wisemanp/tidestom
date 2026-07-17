import json
import numpy as np
from astropy.io import fits
from scipy.interpolate import interp1d
from django import template
from django.http import JsonResponse
from django.db.models import Count
from custom_code.models import PipelineClassificationGlobal, TidesSpec
from tom_dataproducts.models import ReducedDatum

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

@register.inclusion_tag('custom_code/partials/average_spectrum.html') #partial doesn't exist, fine because returns JsonResponse
def average_spectrum_data():
    print("Fetching average spectrum data...")  # debugging: indicate that the function has been called
    filepaths = TidesSpec.objects.filter(filepath__isnull=False).values_list('filepath', flat=True)
   
    print(f"Number of filepaths found: {filepaths.count()}") # debugging: print the number of filepaths found
    print(f"First few filepaths: {list(filepaths)[:5]}")  # Print the first few filepaths for debugging

    all_wavelengths = []
    all_fluxes = []

    # opens .txt files and reads the data into numpy arrays 
    #for filepath in filepaths:
        #try:
            #data = np.loadtxt(filepath, comments='#')
            #all_wavelengths.append(data[:, 0])
            #all_fluxes.append(data[:, 1])
            #print(f"Successfully read: {filepath}")
        #except Exception as e:
            #print(f"Failed to read {filepath}: {e}")
            #continue

    for filepath in filepaths:
        try:
            from astropy.io import fits
            with fits.open(filepath) as hdul:
                # read wavelength and flux from fits file
                wavelengths = hdul[1].data['WAVELENGTH']
                fluxes = hdul[1].data['FLUX']
                all_wavelengths.append(wavelengths)
                all_fluxes.append(fluxes)
        except Exception as e:
            print(f"Failed to read {filepath}: {e}")
            continue
    # assessing structure of .fits files 
    #with fits.open('filepath') as hdul:
        #hdul.info()  # shows the structure of the file
        #print(f"Columns in extension 1: {hdul[1].columns}")

    if not all_wavelengths:
        return {'wavelengths': [], 'flux': []}

    common_wavelengths = all_wavelengths[0] # allows for comparison between the different spectra, maps all onto first spectrum

    interpolated_fluxes = []
    # incase the flux values aren't the same across all spectra
    for wavelengths, fluxes in zip(all_wavelengths, all_fluxes):
        interpolator = interp1d(wavelengths, fluxes, bounds_error=False, fill_value=0)
        interpolated_fluxes.append(interpolator(common_wavelengths))

    average_flux = list(np.mean(interpolated_fluxes, axis=0))

    return {'wavelengths': common_wavelengths, 'flux': average_flux}

