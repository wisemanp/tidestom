from plotly import offline
import plotly.graph_objs as go
from django import template
from custom_code.models import TidesSpec
import numpy as np

from astropy.io import fits

register = template.Library()

@register.inclusion_tag('myplots/target_spectroscopy.html', takes_context=True)
def target_spectroscopy(context, target):
    """
    Renders a spectroscopic plot for a ``Target`` using the spectrum filepath from the tides_spec table.
    """
    # Query the tides_spec table for the spectrum filepath
    try:
        tides_spec = TidesSpec.objects.get(tides_id=target.tides_id)
        spectrum_filepath = tides_spec.filepath
    except TidesSpec.DoesNotExist:
        return {
            'target': target,
            'plot': '<p>No spectrum available for this target.</p>'
        }

    # Load the spectrum data from the filepath
    try:
        if spectrum_filepath.endswith(['.txt', '.spec','.csv','.dat']):
            # Load text file
            spectrum_data = np.loadtxt(spectrum_filepath, delimiter=',')  # Assuming CSV format
            wavelength = spectrum_data[:, 0]  # First column: Wavelength
            flux = spectrum_data[:, 1]  # Second column: Flux
        elif spectrum_filepath.endswith('.fits'):
            spectrum_data = fits.getdata(spectrum_filepath)  # Assuming FITS format
            wavelength = spectrum_data['WAVE']  # Assuming 'WAVE' is the column name for wavelength
            flux = spectrum_data['FLUX']  # Assuming 'FLUX' is the column name for flux
    except Exception as e:
        return {
            'target': target,
            'plot': f'<p>Failed to load spectrum: {e}</p>'
        }

    # Create the plot
    plot_data = [go.Scatter(x=wavelength, y=flux, name='Spectrum')]
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