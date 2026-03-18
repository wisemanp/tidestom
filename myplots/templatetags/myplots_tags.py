import warnings
import pandas as pd
from plotly import offline
import plotly.graph_objs as go
from datetime import datetime
from astropy.time import Time
from django import template
import glob
import numpy as np
import os

from .spectroscopy_settings import (
        add_snid_templates,
        add_snid_select_template,
        add_ngsf_templates,
        load_spectra
)
from .photometry_settings import plot_lightcurves, fetch_target_lasair
from tidestom.settings import BROKERS
from custom_code.models import PipelineClassificationGlobal, PipelineClassificationSnid
lasair_ztf_token = BROKERS['LASAIR']['ztf_api_key']
lasair_lsst_token = BROKERS['LASAIR']['lsst_api_key']

register = template.Library()

@register.inclusion_tag('myplots/target_spectroscopy.html', takes_context=True)
def target_spectroscopy(context, target, dataproduct=None, snid_path=None, snid_index=None, ngsf_path=None):
    """
    Render a spectroscopic plot for a Target.
    Overlays all available spectra from tides_spec (FITS/TXT with WAVE/FLUX columns).
    """
    try:
        spectra, specs = load_spectra(target, last=False)
    except Exception as exc:
        return {'target': target, 'plot': f'<p>Failed to load spectrum: {exc}</p>'}
    if not specs:
        return {'target': target, 'plot': f'<p>No spectrum available for this target:{target}.</p>'}
    plot_data = []
    ymins = []
    ymaxs = []
    colors = [
        '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
        '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
    
    for i, (spectrum, spec) in enumerate(zip(spectra, specs)):
        label = (
            spec.obs_date.strftime('%d/%m/%Y')
            if getattr(spec, 'obs_date', None)
            else datetime.now().strftime('%d/%m/%Y')
        )
        # Include exposure where available
        try:
            exp = spec.additional_info.get('EXPOSURE_TIME_S') if spec.additional_info else None
            if exp:
                label = f"{label} (exp {float(exp):.0f}s)"
        except Exception:
            pass

        c = colors[i % len(colors)]
        plot_data.append(
            go.Scatter(
                x=spectrum.spectral_axis.value,
                y=spectrum.flux.value,
                name=label,
                marker=dict(color=c),
                opacity=0.6,
            )
        )
        # Track y-axis ranges to set a reasonable global range
        try:
            ymins.append(np.nanpercentile(spectrum.flux.value, 0.1))
            ymaxs.append(np.nanpercentile(spectrum.flux.value, 99.9))
        except Exception:
            pass

    fig = go.Figure(data=plot_data)
    if ymins and ymaxs:
        fig.update_yaxes(range=[min(ymins), max(ymaxs)])


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


    if snid_path is not None:
        try:
            pysnid_file = snid_path
            spectrum_ref = spectra[-1]
            if snid_index is None:
                fig = add_snid_templates(
                    pysnid_file,
                    spectrum_ref.spectral_axis.value,
                    spectrum_ref.flux.value,
                    fig,
                    n=3,
                )
            else:
                fig = add_snid_select_template(
                    pysnid_file,
                    spectrum_ref.spectral_axis.value,
                    spectrum_ref.flux.value,
                    fig,
                    idx=snid_index,
                )
        except Exception as exc:
            print(exc)
            pass

    else:
        # Query database for SNID results file from pipeline_classification_snid
        try:
            # Get the most recent classification with results_file
            classification = PipelineClassificationSnid.objects.filter(
                tides_id=target.id,
                results_file__isnull=False
            ).order_by('-id').first()

            if classification and classification.results_file:
                auto_snid = classification.results_file
                # Verify file exists before attempting to plot
                if os.path.exists(auto_snid):
                    try:
                        spectrum_ref = spectra[-1]
                        fig = add_snid_templates(
                            auto_snid,
                            spectrum_ref.spectral_axis.value,
                            spectrum_ref.flux.value,
                            fig,
                            n=3,
                        )
                    except Exception as exc:
                        print(f"Error adding SNID templates: {exc}")
                        pass
                else:
                    print(f"[DEBUG] SNID results file not found: {auto_snid}")
            else:
                print(f"[DEBUG] No SNID classification found for target {target}")
        except Exception as exc:
            print(f"[DEBUG] Error loading SNID classification: {exc}")
            pass

    if ngsf_path is not None:
        try:
            ngsf_file = ngsf_path
            spectrum_ref = spectra[-1]
            fig = add_ngsf_templates(
                ngsf_file,
                spectrum_ref.spectral_axis.value,
                spectrum_ref.flux.value,
                fig,
                n=3,
            )
        except Exception as exc:
            return {'target': target, 'plot': f'<p>NGSF failed: {exc}</p>'}

    try:
        xmin = min(np.nanmin(spectrum.spectral_axis.value) for spectrum in spectra)
        xmax = max(np.nanmax(spectrum.spectral_axis.value) for spectrum in spectra)
        ymin = min(ymins) if ymins else 0.0
    except Exception:
        xmin, xmax, ymin = 3600, 9600, 0.0

    fig.add_trace(
        go.Scatter(
            x=[xmin, xmax],
            y=[ymin, ymin],
            xaxis='x2',
            yaxis='y',
            mode='lines',
            line=dict(color='rgba(0,0,0,0)', width=1),
            hoverinfo='skip',
            showlegend=False,
        )
    )

    fig.update_layout(
        autosize=True,
        height=650,
        xaxis=dict(
            title='Observed Wavelength (Å)',
            showticklabels=True,
            ticks='outside',
            linewidth=2,
            side='bottom',
            tickformat=".0f"
        ),
        xaxis2=dict(
            title=dict(
                text='Rest Wavelength (Å)',
                standoff=10
            ),
            overlaying='x',
            side='top',
            anchor='y',
            showgrid=False,
            zeroline=False,
            ticks='outside',
            showticklabels=True,
            showline=True,
            linewidth=2,
            tickmode='sync',
            visible=True
        ),
        yaxis=dict(
            title='Flux (erg/s/cm²/Å)',
            showticklabels=True,
            ticks='outside',
            linewidth=2
        ),
        margin=dict(t=180),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.18,
            xanchor="center",
            x=0.5,
            entrywidth=0.5,
            entrywidthmode="fraction",
            font=dict(size=14)
        ),
        showlegend=True,
        font_family="P052",
        font_size=16
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
