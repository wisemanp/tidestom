import re
import numpy as np
import pandas as pd
from pathlib import Path

import extinction
from extinction import apply
from astropy.time import Time
import plotly.graph_objs as go

import pysnid
from pysnid.snid import SNIDReader
import NGSF
#from NGSF.SF_functions import Alam
ngsf_path = Path(NGSF.__path__[0])
max_df = pd.read_csv(ngsf_path / 'mjd_of_maximum_brightness.csv')

def match_grid(x_pred: np.ndarray, x: np.ndarray, y: np.ndarray) -> np.ndarray:
    """Interpolates values to match a desired grip.
    
    For example, for a template spectrum to match the wavelengths
    of the observed spectrum.

    Parameters
    ----------
    x_pred: prediction grid.
    x: x-axis data.
    y: y-axis data.
     
    Returns
    -------
    x_pred, y_pred: interpolated values.
    """
    y_pred = np.interp(x_pred, x, y, left=np.nan, right=np.nan)
    return x_pred.copy(), y_pred

##################
# SNID templates #
##################

def get_pysnid_results(inputfile: str) -> SNIDReader:
    """Reads pysnid results.

    Parameters
    ----------
    inputfile: Pysnid output file ('.h5' extension).

    Returns
    -------
    snidres: SNID fit results.
    """
    snidres = SNIDReader.from_filename(inputfile)
    return snidres

def add_snid_templates(pysnid_file: str, obs_wave: np.ndarray, obs_flux: np.ndarray, 
                       fig: go.Figure, n: int = 3) -> go.Figure:
    """Adds best-match SNID templates to the figure.

    Parameters
    ----------
    pysnid_file: Pysnid output file ('.h5' extension).
    obs_wave: Observed spectrum wavelength.
    obs_flux: Observed spectrum flux.
    fig: Figure with the plot.
    n: Number of best-match templates, sorted by reduced chi square.

    Returns:
    fig: Updated figure with SNID templates.
    """
    mean = np.nanmean(obs_flux)
    snidres = get_pysnid_results(pysnid_file)
    for i in range(1, n + 1):
        model_df = snidres.get_modeldata(i, fluxcorr=True)
        model_wave = model_df.wavelength.values
        model_flux = model_df.flux.values
        # normalise back
        model_flux /= 1.05
        model_flux *= mean
        # match observed grid
        model_wave, model_flux = match_grid(obs_wave, model_wave, model_flux)
        
        temp_info = snidres.results.iloc[i]
        fig.add_trace(go.Scatter(
            x=model_wave,
            y=model_flux,
            name=f"{i}. {temp_info.sn}<br>{temp_info.type} (SNID)",
            hovertemplate=(f'Name: {temp_info.sn}<br>Type: {temp_info.type}<br>'
                           f'Phase: {temp_info.age} d<br>Wave.:%{{x}}'),
            showlegend=True,
            visible='legendonly',
        ))
    return fig

##################
# NGSF templates #
##################

# function from NGSF, but written locally as the other one fails to import
def Alam(lamin, A_v: float = 1, R_v: float = 3.1) -> np.ndarray:
    """Add extinction with R_v = 3.1 and A_v = 1, A_v = 1 in order
    to find the constant of proportionality for
    the extinction law.

    Returns
    -------
    redreturn: extincted flux.
    """
    flux = np.ones(len(lamin))
    flux = [float(x) for x in flux]
    lamin = np.array([float(i) for i in lamin])
    redreturn = apply(extinction.ccm89(lamin, A_v, R_v), flux)

    return redreturn

def add_ngsf_templates(ngsf_file: str, obs_wave: np.ndarray, obs_flux: np.ndarray, 
                       fig: go.Figure, n: int = 3) -> go.Figure:
    """Adds best-match NGSF templates to the figure.

    Parameters
    ----------
    ngsf_file: CSV output file from NGSF.
    obs_wave: Observed spectrum wavelength.
    obs_flux: Observed spectrum flux.
    fig: Figure with the plot.
    n: Number of best-match templates, sorted by reduced chi square.

    Returns:
    fig: Updated figure with NGSF templates.
    """
    median = np.nanmedian(obs_flux)  # to scale the templates
    sn_df = pd.read_csv(ngsf_file)
    for i, row in sn_df[:n].iterrows():
        # template info
        z = row.Z  # redshift
        temp_info = row.SN 
        # get path to template file
        temp_path, _, _, _ = temp_info.split()
        temp_path = Path(temp_path).parent
        temp_type, temp_sn = str(temp_path).split('/')
        temp_dir = ngsf_path / 'bank/original_resolution/sne' / temp_path

        # get phase from best templates to get peak mjd
        temp_phase = float(row.Phase)
        mjd_peak = max_df[max_df.Name==temp_sn].mjd_peak.values[0]
        
        # get phases for all available templates
        wiserep_df = pd.read_csv(temp_dir / 'wiserep_spectra.csv')
        mjds = Time(wiserep_df.JD.values, format='jd').mjd
        phases = (mjds - mjd_peak) / (1 + z)
        # get the file that matches the phase
        temp_id = np.argmin(np.abs(phases - temp_phase))
        temp_file = wiserep_df['Ascii file'].values[temp_id]
        temp_df = pd.read_csv(temp_dir / temp_file, sep='\\s+', comment='#')
        try:
            temp_wave, temp_flux, _ = temp_df.values.T
        except Exception:
            temp_wave, temp_flux = temp_df.values.T
        
        # load host-galaxy template
        gal_file = ngsf_path / 'bank/original_resolution/gal' / row.GALAXY
        host_wave, host_flux = np.loadtxt(gal_file).T
        host_flux = np.interp(temp_wave, host_wave, host_flux, left=np.nan, right=np.nan)  # interpolate to match SN template grid
        # normalise
        temp_flux /= np.nanmedian(temp_flux)
        host_flux /= np.nanmedian(host_flux)
        # apply extinction and redshift
        temp_flux *= 10 ** (-0.4 * row.A_v * Alam(temp_wave)) / (1 + z)
        temp_wave *= (1 + z)
        temp_flux /= (1 + z)
        host_flux /= (1 + z)        
        # scale by constants and add host-galaxy contribution to the SN template
        temp_total_flux = (temp_flux * row.CONST_SN) + (host_flux * row.CONST_GAL)
        temp_total_flux *= median  # add observed spectrum scale
        # match observed grid
        temp_wave, temp_total_flux = match_grid(obs_wave, temp_wave, temp_total_flux)
            
        # update figure with templates
        fig.add_trace(go.Scatter(
            x=temp_wave,
            y=temp_total_flux,
            name=f"{i+1}. {temp_sn}<br>{temp_type} (NGSF)",
            hovertemplate=(f'Name: {temp_sn}<br>Type: {temp_type}<br>'
                           f'Phase: {temp_phase}<br>'
                           f'redshift: {row.Z}<br>Av: {row.A_v}<br>'
                           f'Host: {row.GALAXY}<br>SN frac.: {row["Frac(SN)"] * 100:.1f}%<br>'
                           f'dWave.:%{{x}}<br>'
                           ),
            showlegend=True,
            visible='legendonly',
        ))
    return fig