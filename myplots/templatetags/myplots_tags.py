import warnings
import pandas as pd
from plotly import offline
import plotly.graph_objs as go
from datetime import datetime
from astropy.time import Time
from django import template
import glob
import numpy as np

from .spectroscopy_settings import (
        add_snid_templates,
        add_snid_select_template,
        add_ngsf_templates,
        load_spectra
)
from .photometry_settings import plot_lightcurves, fetch_target_lasair
from tidestom.settings import BROKERS
lasair_ztf_token = BROKERS['LASAIR']['ztf_api_key']
lasair_lsst_token = BROKERS['LASAIR']['lsst_api_key']

register = template.Library()

@register.inclusion_tag('myplots/target_spectroscopy.html', takes_context=True)
def target_spectroscopy(context, target, dataproduct=None, snid_path=None, snid_index=None, ngsf_path=None):
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

    scale_factor = 1 #setting 1 currently as SNID plots wrongly right now with this

    plot_data = [
        go.Scatter(
            x=spectrum.spectral_axis.value,
            y=spectrum.flux.value/scale_factor,
            name=(spec.obs_date.strftime('%Y%m%d-%H:%M:%S') if getattr(spec, 'obs_date', None)
                    else datetime.now().strftime('%Y%m%d-%H:%M:%S')),
            marker=dict(color='darkslategray'),
            opacity=0.5,
            #visible='legendonly',
        )
    ]

    fig = go.Figure(data=plot_data)
    fig.update_yaxes(range=[np.nanpercentile(spectrum.flux.value/scale_factor, 0.1),
                            np.nanpercentile(spectrum.flux.value/scale_factor,99.9)])

    ### tellurics ###
    # Hinkle et al. 2003 “Infrared Atlas of the Arcturus Spectrum”
    # Wallace et al. 1996 “An Atlas of the Spectrum of the Solar Photosphere from 296 to 1300 nm”
    telluric_bands = {
        #'O2 B-band': (6867, 6884),
        #'O2 gamma-band': (6280, 6310),
        'O2 A-band': (7590, 7700),
        'H2O band1': (7150, 7350),
        'H2O band2': (8100, 8400),
        #'H2O band3': (8900, 9800)
    }
    # add shaded regions for each telluric band
    for label, (start, end) in telluric_bands.items():
        fig.add_vrect(
            x0=start, x1=end,
            fillcolor="grey",
            opacity=0.2,
            layer="below",
            line_width=0,
            annotation_text="⊕",
            annotation_position="top",
            annotation_font=dict(size=12, color="black")
        )


    ### arm joins ###
    # Inclusion of the 4MOST (low res) spectrograph arm overlap arm regions
    # Taken from the 4MOST manual : https://www.4most.eu/cms/files/VIS-MAN-4MOST-47110-9800-0001_2_00-4MOST-User-Manual.pdf

    overlap_bands = {
        'blue-green' : (5240,5540),
        'green-red': (6910,7210)
    }

    for label, (start, end) in overlap_bands.items():
        fig.add_vrect(
            x0=start, x1=end,
            fillcolor="brown",
            opacity=0.2,
            layer="below",
            line_width=0,
            annotation_text="AJ",
            annotation_position="top",
            annotation_font=dict(size=12, color="black")
        )


    ### templates ###
    if snid_path is not None:
        if snid_index is None:
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
        elif snid_index is not None:
            try:
                pysnid_file = snid_path
                fig = add_snid_select_template(pysnid_file,
                                         spectrum.spectral_axis.value,
                                         spectrum.flux.value,
                                         fig,
                                         idx=snid_index
                                         )
            except Exception as exc:
                print(exc)
                pass
    else:
        tar = f"{target}"
        paths= glob.glob(f'/snid_api_runs/pipeline_out/*/{tar[6:]}/*h5')
        try:
            auto_snid = f'{paths[0]}'
            try:
                fig = add_snid_templates(auto_snid,
                                spectrum.spectral_axis.value,
                                spectrum.flux.value/scale_factor,
                                fig,
                                n=3
                                )
            except Exception as exc:
                print(exc)
                pass
        except IndexError:
            warnings.warn(f"{target}", UserWarning)
            pass

    if ngsf_path is not None:
        try:
            ngsf_file = ngsf_path
            fig = add_ngsf_templates(ngsf_file,
                             spectrum.spectral_axis.value,
                             spectrum.flux.value/scale_factor,
                             fig,
                             n=3
                             )
        except Exception as exc:
            return {'target': target, 'plot': f'<p>NGSF failed: {exc}</p>'}

    fig.update_layout(autosize=True,
                      height=650,
                      xaxis_title='Observed Wavelength (Å)',
                      yaxis_title='Flux (erg/s/cm²/Å)',
                      xaxis = dict(showticklabels=True, ticks='outside', linewidth=2),
                      yaxis = dict(showticklabels=True, ticks='outside', linewidth=2),
                      legend_title="Best Matches",
                      margin=dict(t=150),
                      legend=dict(orientation="h",yanchor="bottom",y=1.05,xanchor="center",x=0.5,entrywidth=0.5,entrywidthmode="fraction",font=dict(size=14)),
                      showlegend=True,
                      font_family="P052",
                      font_size=16,
                      )

    return {
        'target': target,
        'plot': offline.plot(fig, output_type='div', show_link=False),
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
    tokens = {"ztf": lasair_ztf_token,
              "lsst": lasair_lsst_token,
              }
    photometry_list = []
    for survey, token in tokens.items():
        # check if the Lasair's API key is set
        if token is None or token == "":
            warnings.warn(f"Warning: Lasair API key for {survey.upper()} not set!", UserWarning)
            continue
        try:
            #phot = fetch_target_lasair(49.1384664, 44.9725084, survey)  # ZTF25aacedrs for testing
            phot = fetch_target_lasair(target.ra, target.dec, survey)
            photometry_list.append(phot)
        except Exception as exc:
            return {'target': target, 'plot': exc}

    if len(photometry_list) == 0:
        # tokens not set
        return {'target': target}
    try:
        photometry = pd.concat(photometry_list)
    except ValueError:
        return {'target': target}
    if photometry is None:
        # no photometry found
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
