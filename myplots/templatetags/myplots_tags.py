import warnings
import pandas as pd
from plotly import offline
import plotly.graph_objs as go
from datetime import datetime
from astropy.time import Time
from django import template

from .spectroscopy_settings import add_snid_templates, add_ngsf_templates, load_spectra
from .photometry_settings import plot_lightcurves, fetch_target_lasair
from tidestom.settings import BROKERS
lasair_ztf_token = BROKERS['LASAIR']['ztf_api_key']
lasair_lsst_token = BROKERS['LASAIR']['lsst_api_key']

register = template.Library()

@register.inclusion_tag('myplots/target_spectroscopy.html', takes_context=True)
def target_spectroscopy(context, target, dataproduct=None, snid_path=None, ngsf_path=None):
    """
    Render a spectroscopic plot for a Target.
    Loads the latest spectrum from tides_spec (FITS with WAVE/FLUX columns).
    """
    try:
        # last spectrum only
        spectra, specs = load_spectra(target, last=True)
    except Exception as exc:
        return {'target': target, 'plot': f'<p>Failed to load spectrum: {exc}</p>'}
    if not specs:
        return {'target': target, 'plot': f'<p>No spectrum available for this target:{target}.</p>'}
    spectrum, spec = spectra[0], specs[0]
    
    """
    # Pick the latest spectrum for this target
    spec = (
        TidesSpec.objects
        .filter(tides=target)
        .order_by('-obs_date', '-qmost_id')
        .first()
    )
    if not spec:
        return {'target': target, 'plot': f'<p>No spectrum available for this target:{target}.</p>'}
    
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
    """
    plot_data = [
        go.Scatter(
            x=spectrum.spectral_axis.value,
            y=spectrum.flux.value,
            name=(spec.obs_date.strftime('%Y%m%d-%H:%M:%S') if getattr(spec, 'obs_date', None)
                    else datetime.now().strftime('%Y%m%d-%H:%M:%S'))
        )
    ]

    fig = go.Figure(data=plot_data)

    # add templates - best matches
    # SNID - mock templates for now
    #data_mean = np.mean(spectrum.flux.value)

    if snid_path is not None:
        try:
            pysnid_file = snid_path
            fig = add_snid_templates(pysnid_file,
                             spectrum.spectral_axis.value,
                             spectrum.flux.value,
                             fig,
                             n=3
                             )
        except Exception as exc:
            print(exc)
            pass

    # NGSF - mock templates for now
    if ngsf_path is not None:
        try:
            ngsf_file = ngsf_path
            fig = add_ngsf_templates(ngsf_file,
                             spectrum.spectral_axis.value,
                             spectrum.flux.value,
                             fig,
                             n=3
                             )
        except Exception as exc:
            #TODO add better handling
            print(exc)
            pass
    fig.update_layout(autosize=True,
                      xaxis_title='Observed Wavelength (Å)',
                      yaxis_title='Flux (erg/s/cm²/Å)',
                      xaxis = dict(showticklabels=True, ticks='outside', linewidth=2),
                      yaxis = dict(showticklabels=True, ticks='outside', linewidth=2),
                      legend_title="Best Templates",
                      showlegend=True,
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
    if lasair_ztf_token is None or lasair_ztf_token == "":
        warnings.warn("Warning: Lasair API key for ZTF not set!", UserWarning)
        return {'target': target}
    if lasair_lsst_token is None or lasair_lsst_token == "":
        warnings.warn("Warning: Lasair API key for LSST not set!", UserWarning)
        return {'target': target}

    photometry_list = []
    for survey in ["ztf", "lsst"]:
        #phot = fetch_target_lasair(49.1384664, 44.9725084, survey)  # ZTF25aacedrs for testing
        phot = fetch_target_lasair(target.ra, target.dec, survey)
        photometry_list.append(phot)
    photometry = pd.concat(photometry_list)
    if photometry is None:
        return {'target': target}

    # plot photometry
    fig = plot_lightcurves(photometry)

    # add epochs with spectra
    try:
        _, specs = load_spectra(target)
        for spec in specs:
            mjd = Time(spec.obs_date, scale="utc").mjd
            fig.add_vline(mjd, line_width=2, line_dash="dot", line_color="black",
                                annotation_text="s", annotation_position="top left")
    except Exception as exc:
        print(exc)
    
    return {
        'target': target,
        'plot': offline.plot(fig, output_type='div', show_link=False)
    }
