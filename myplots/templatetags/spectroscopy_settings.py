import numpy as np
import pandas as pd
from pathlib import Path
import os
import zipfile

import extinction
from extinction import apply
from astropy.time import Time
import plotly.graph_objs as go

from astropy.io import fits
from astropy import units as u
from specutils import Spectrum1D
from django.conf import settings
from custom_code.models import TidesSpec

import NGSF
from pysnid.snid import SNIDReader
ngsf_path = Path(NGSF.__path__[0])
max_df = pd.read_csv(ngsf_path / 'mjd_of_maximum_brightness.csv')

def load_spectra(target, last: bool = False) -> tuple[list, list]:
    """Loads the spectra of a TiDES target.
    
    Parameters
    ----------
    target: TiDES target object.
    last: Whether to query only the last spectrum.
    
    Returns
    -------
    spectra: Target's spectra.
    specs: Queries of spectra.
    """
    # Pick the latest spectrum for this target
    if not last:
        specs = (
            TidesSpec.objects
            .filter(tides=target)
            .order_by('obs_date', 'qmost_id')
        )
        if not specs:
            return None
    else:
        # single query
        spec = (
            TidesSpec.objects
            .filter(tides=target)
            .order_by('-obs_date', '-qmost_id')
            .first()
        )
        if not spec:
            return None
        specs = [spec]
    
    spectra = []
    # Resolve file path (use stored path; fallback to symlink convention if missing)
    for spec in specs:
        p = Path(spec.filepath)
        if not p.exists():
            candidate = Path(settings.BASE_DIR) / 'data' / 'spectra' / 'test' / p.name
            if candidate.exists():
                p = candidate

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
        spectra.append(spectrum)
    return  spectra, specs 

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
    m = 0
    for _, row in snidres.get_bestmatches().iterrows():
        if m == n:
            break
        else:
            m+=1
        i = int(row['no.'])
        model_df = snidres.get_modeldata(i, fluxcorr=True)
        model_wave = model_df.wavelength.values
        model_flux = model_df.flux.values
        # normalise back
        model_flux = model_flux / 1.05
        model_flux = model_flux * mean
        # match observed grid
        model_wave, model_flux = match_grid(obs_wave, model_wave, model_flux)

        temp_info = snidres.results.iloc[i-1]
        fig.add_trace(go.Scatter(
            x=model_wave,
            y=model_flux,
            name=f"SNID: {m}. {temp_info.sn}<br>{temp_info.type}<br>Phase:{temp_info.age}, z={temp_info.z}",
            hovertemplate=(f'Name: {temp_info.sn}<br>Type: {temp_info.type}<br>'
                           f'Phase: {temp_info.age} d<br>Wave.:%{{x}}'),
            showlegend=True,
            visible='legendonly',
        ))
    return fig

def add_snid_select_template(pysnid_file: str, obs_wave: np.ndarray, obs_flux: np.ndarray,
                             fig: go.Figure, idx) -> go.Figure:
    """Adds gets a user selcted SNID template for the figure.

    Parameters
    ----------
    pysnid_file: Pysnid output file ('.h5' extension).
    obs_wave: Observed spectrum wavelength.
    obs_flux: Observed spectrum flux.
    fig: Figure with the plot.
    idx: index or mutliple of the desired template

    Returns:
    fig: Updated figure with SNID templates.
    """
    mean = np.nanmean(obs_flux)
    snidres = get_pysnid_results(pysnid_file)
    if type(idx) is not list:
        idx = [idx]
    for i in idx:
        model_df = snidres.get_modeldata(int(i), fluxcorr=True)
        model_wave = model_df.wavelength.values
        model_flux = model_df.flux.values
        # normalise back
        model_flux = model_flux / 1.05
        model_flux = model_flux * mean
        # match observed grid
        model_wave, model_flux = match_grid(obs_wave, model_wave, model_flux)

        temp_info = snidres.results.iloc[int(i)]
        fig.add_trace(go.Scatter(
            x=model_wave,
            y=model_flux,
            name=f"SNID: {i}. {temp_info.sn}<br>{temp_info.type}<br>Phase:{temp_info.age}, z={temp_info.z}",
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

    if not os.path.exists(ngsf_path / 'bank'):
        os.system('git clone https://github.com/temuller/superfit_bank.git')
        file_path = 'superfit_bank/supyfit_bank.zip'

        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            zip_ref.extractall(ngsf_path)

        os.system('rm -rf superfit_bank')

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
