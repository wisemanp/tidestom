from plotly import offline
import plotly.graph_objs as go
from datetime import datetime
from django import template
from django.conf import settings

from pathlib import Path
from astropy.io import fits
from astropy import units as u
from specutils import Spectrum1D

from custom_code.models import TidesSpec

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
        data = fits.getdata(str(p))
        wave = data['WAVE'][0] * u.Angstrom
        flux = data['FLUX'][0] * u.Unit('erg cm-2 s-1 AA-1')
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

###### Below is an example from the TOM Documentation
# @register.inclusion_tag('myplots/targets_reduceddata.html')
# def targets_reduceddata(targets=Target.objects.all()):
#     # order targets by creation date
#     targets = targets.order_by('-created')
#     # x axis: target names. y axis datum count
#     data = [go.Bar(
#         x=[target.name for target in targets],
#         y=[target.reduceddatum_set.count() for target in targets]
#     )]
#     # Create plot
#     figure = offline.plot(go.Figure(data=data), output_type='div', show_link=False)
#     # Add plot to the template context
#     return {'figure': figure}