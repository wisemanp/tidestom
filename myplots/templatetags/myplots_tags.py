import warnings
from plotly import offline
import plotly.graph_objs as go
from datetime import datetime
from astropy.time import Time
from django import template
from django.conf import settings

from pathlib import Path
from astropy.io import fits
from astropy import units as u
from specutils import Spectrum1D
import numpy as np

from custom_code.models import TidesSpec
from tidestom.settings import BROKERS
lasair_token = BROKERS['LASAIR']['api_key']
from .photometry_settings import plot_lightcurves, fetch_ztf_lasair

register = template.Library()

@register.inclusion_tag('myplots/target_spectroscopy.html', takes_context=True)
def target_spectroscopy(context, target, dataproduct=None):
    """
    Render a spectroscopic plot for a Target.
    Loads the latest spectrum from tides_spec (FITS with WAVE/FLUX columns).
    """
    # Pick the latest spectrum for this target
    spec = (
        TidesSpec.objects
        .filter(tides=target)
        .order_by('-obs_date', '-qmost_id')
        .first()
    )
    if not spec:
        return {'target': target, 'plot': '<p>No spectrum available for this target.</p>'}

    # Resolve file path (use stored path; fallback to symlink convention if missing)
    p = Path(spec.filepath)
    if not p.exists():
        candidate = Path(settings.BASE_DIR) / 'data' / 'spectra' / 'test' / p.name
        if candidate.exists():
            p = candidate

    try:
        if str(p).endswith('fits'):
            data = fits.getdata(str(p))
            wave = data['WAVE'][0] * u.Angstrom
            flux = data['FLUX'][0] * u.Unit('erg cm-2 s-1 AA-1')
        elif str(p).endswith('txt'):
            data = np.loadtxt(str(p))
            wave = data[:,0] * u.Angstrom
            flux = data[:,1] * u.Unit('erg cm-2 s-1 AA-1')
        else:
            raise ValueError(f'Unsupported spectrum file format: {p}')
        spectrum = Spectrum1D(flux=flux, spectral_axis=wave)

        plot_data = [
            go.Scatter(
                x=spectrum.spectral_axis.value,
                y=spectrum.flux.value,
                name=(spec.obs_date.strftime('%Y%m%d-%H:%M:%S') if getattr(spec, 'obs_date', None)
                      else datetime.now().strftime('%Y%m%d-%H:%M:%S'))
            )
        ]
    except Exception as e:
        return {'target': target, 'plot': f'<p>Failed to load spectrum: {e}</p>'}

    fig = go.Figure(data=plot_data)
    fig.update_layout(
        autosize=True,
        xaxis_title='Observed Wavelength [Å]',
        yaxis_title='Flux',
        xaxis=dict(showticklabels=True, ticks='outside', linewidth=2),
        yaxis=dict(showticklabels=True, ticks='outside', linewidth=2),
        shapes=[]
    )

    return {
        'target': target,
        'plot': offline.plot(fig, output_type='div', show_link=False)
    }


##############
# Photometry #
##############

@register.inclusion_tag('myplots/target_photometry.html', takes_context=True)
def target_photometry(context, target, dataproduct=None):
    """
    Renders a photometry plot for a ``Target``. If a ``DataProduct`` is specified, it will only render a plot with
    that photometry.
    """
    # check if the Lasair's API key is set
    if lasair_token is None or lasair_token == "":
        warnings.warn("Warning: Lasair API key not set!", UserWarning)
        return {'target': target}
    
    photometry = fetch_ztf_lasair(49.1384664, 44.9725084)  # ZTF25aacedrs for testing
    #photometry = fetch_ztf_lasair(target.ra, target.dec)
    
    # plot photometry
    fig = plot_lightcurves(photometry)
    
    # add epochs with spectra
    try:
        spectroscopy_data_type = settings.DATA_PRODUCT_TYPES['spectroscopy'][0]
    except (AttributeError, KeyError):
        spectroscopy_data_type = 'spectroscopy'
    spectral_dataproducts = DataProduct.objects.filter(target=target,
                                                       data_product_type=spectroscopy_data_type)
    datums = ReducedDatum.objects.filter(data_product__in=spectral_dataproducts)
    for datum in datums:
        mjd = Time(datum.timestamp, scale="utc").mjd
        fig.add_vline(mjd, line_width=2, line_dash="dot", line_color="black", 
                            annotation_text="s", annotation_position="top left")
        
    return {
        'target': target,
        'plot': offline.plot(fig, output_type='div', show_link=False)
    }
