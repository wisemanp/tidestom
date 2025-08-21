import warnings
import numpy as np
import pandas as pd
from astropy.time import Time
import plotly.graph_objects as go

from lasair import lasair_client
from tidestom.settings import BROKERS
lasair_token = BROKERS['LASAIR']['api_key']

##########
# Lasair #
##########
def find_ztfname_lasair(ra: float, dec: float) -> str | None:
    """Finds the nearest ZTF target from the given coordinates.

    The objects are queried from Lasair.

    Parameters
    ----------
    ra: right ascension in degrees.
    dec: declination in degrees.

    Returns
    -------
    ztfname: ZTF internal name or 'None' if not found.
    """
    # query objects
    lasair = lasair_client(lasair_token, endpoint = "https://lasair-ztf.lsst.ac.uk/api")
    objects_list = lasair.cone(ra, dec)
    if len(objects_list) == 0:
        return None
    # get the object with the minimum separation
    separations = [obj_dict['separation'] for obj_dict in objects_list]
    id_target = np.argmin(separations)
    ztfname = objects_list[id_target]['object']
    return ztfname
    
def fetch_ztf_lasair(ra: float, dec: float, name: str=None) -> pd.DataFrame:
    """
    Fetches the ZTF light curve of a target from the Lasair broker.
    
    Parameters
    ----------
    ra: right ascension in degrees.
    dec: declination in degrees.
    
    Returns
    -------
    ztf_df: ZTF light curve.
    """
    # get name of target
    if name is None:
        ztfname = find_ztfname_lasair(ra, dec)
    elif name.startswith("ZTF"):
        ztfname = find_ztfname_lasair(ra, dec)
    else:
        ztfname = name
    if ztfname is None:
        return None
        
    # query photometry from Lasair
    lasair = lasair_client(lasair_token, endpoint = "https://lasair-ztf.lsst.ac.uk/api")
    target_info = lasair.lightcurves([ztfname])
    phot_list = target_info[0]['candidates']
    det_list = []  # detections
    nondet_list = []  #non-detections
    # convert to dataframe
    for phot_dict in phot_list:
        # convert values into list to convert to dataframe
        phot_dict = {key:[value] for key, value in phot_dict.items()}
        phot_df = pd.DataFrame(phot_dict)
        if 'magpsf' in phot_dict.keys():
            det_list.append(phot_df)
        else:
            nondet_list.append(phot_df)
    with warnings.catch_warnings():
        # ignore annoying pandas future warning
        warnings.simplefilter("ignore")
        det_df = pd.concat(det_list)
        nondet_df = pd.concat(nondet_list)
    ztf_df = pd.concat([det_df, nondet_df])  # for non detection use diffmaglim
    jds = Time(ztf_df['jd'].values, format='jd')
    ztf_df['mjd'] = jds.mjd
    
    # rename columns
    ztf_df.rename(columns={'fid':'filter', 
                           'magpsf':'mag', 
                           'sigmapsf':'mag_err',
                           'diffmaglim':'upper_mag'
                          }, 
                  inplace=True)
    # Replace photometric filter numbers with human-readable names
    filter_dict = {1: 'ztf_g', 2: 'ztf_r', 3: 'ztf_i'}
    ztf_df['filter'] = [filter_dict[fid] for fid in ztf_df['filter']]
    # Sort the table on filter and time:
    ztf_df.sort_values(['filter', 'mjd'], inplace=True)
    ztf_df = ztf_df[['filter', 'mjd', 'mag', 'mag_err', 'upper_mag']]
    return ztf_df

def get_hovertemplates(df: pd.DataFrame, columns: list) -> str:
    """Creates the hover template to show information when hovering 
    over the data.

    Parameters
    ----------
    df: light-curves information.
    columns: columns used for displaying the information (e.g. mag, MJD).

    Returns
    -------
    hovertemplate: hover information.
    """
    df_columns = df.columns.to_list()
    hovertemplate = "".join(f"{col}: %{{customdata[{df_columns.index(col)}]}}<br>" 
                            for col in columns)
    return hovertemplate
    
def photometry_trace(df: pd.DataFrame, colour: str, phot_type: str='mag', name: str=None, legendgroup: str=None, hovertemplate: str=None) -> go.Scatter:
    """Creates a trace to display the light curve photometry.

    Parameters
    ----------
    df: light-curves information.
    colour: colour for plotting.
    phot_type: column to use in the y axis.
    name: name to identify the trace.
    legendgroup: name of the legend to group up traces.
    hovertemplate: hover information to display.

    Returns
    -------
    trace: light-curve trace.
    """
    trace = go.Scatter(x=df['mjd'],
                       y=df[phot_type],
                       mode='markers',
                       name=name,
                       marker=dict(color=colour),
                       customdata=df,
                       hovertemplate=hovertemplate,
                       legendgroup=legendgroup,  # group markers and error bars together
                      ) 
    return trace
    
def error_trace(df: pd.DataFrame, colour: str, phot_type: str='mag', name: str=None, legendgroup: str=None) -> go.Scatter:
    """Creates a trace to display the light curve photometry uncertainty.

    Parameters
    ----------
    df: light-curves information.
    colour: colour for plotting.
    phot_type: column to use in the y axis.
    name: name to identify the trace.
    legendgroup: name of the legend to group up traces.

    Returns
    -------
    trace: light-curve error trace.
    """
    trace = go.Scatter(x=df['mjd'],
                       y=df[phot_type],
                       mode='lines',
                       name=name,
                       line=dict(width=0),  # Invisible line for error bars
                       error_y=dict(type='data',
                                    symmetric=True,
                                    array=df[f'{phot_type}_err'],
                                    color=colour
                                   ),
                       showlegend=False,
                       legendgroup=legendgroup
                      )
    return trace

def upperlimit_trace(df: pd.DataFrame, colour: str, phot_type: str='mag', name: str=None, legendgroup: str=None, hovertemplate: str=None) -> go.Scatter:
    """Creates a trace to display the light curve photometry upper limits.

    Parameters
    ----------
    df: light-curves information.
    colour: colour for plotting.
    phot_type: column to use in the y axis.
    name: name to identify the trace.
    legendgroup: name of the legend to group up traces.
    hovertemplate: hover information to display.

    Returns
    -------
    trace: light-curve upper-limits trace.
    """
    trace = go.Scatter(x=df['mjd'],
                       y=df[f"upper_{phot_type}"],
                       mode='markers',
                       name=name,
                       marker_symbol="triangle-down-open",
                       marker_size=12,
                       marker=dict(color=colour),
                       opacity=0.7,
                       customdata=df,
                       hovertemplate=hovertemplate,
                       showlegend=False,
                       legendgroup=legendgroup,
                      )
    return trace

def create_toggling_buttons(fig: go.Figure) -> list[dict, dict]:
    """Creates the buttons for toggling between magnitude and flux.

    Parameters
    ----------
    fig.: plotly figure.

    Returns
    -------
    buttons: magnitude/flux buttons.
    """
    mag_visibility = [False if "flux" in trace.legendgroup else True for trace in fig.data]
    flux_visibility = [False if "mag" in trace.legendgroup else True for trace in fig.data]
    
    buttons = [
        dict(
            label='Magnitude',
            method='update',
            args=[
                {'visible': mag_visibility},  # Show magnitude, hide flux
                {'yaxis': {'title': 'AB Magnitude', 'autorange': 'reversed'}},
            ]
        ),
        dict(
            label='Flux',
            method='update',
            args=[
                {'visible': flux_visibility},  # Show flux, hide magnitude
                {'yaxis': {'title': 'Flux (μJy)'}},
            ]
        )
    ]
    return buttons

def plot_lightcurves(photometry: pd.DataFrame) -> go.Figure:
    """Plots the light curves for a transient.

    Parameter
    ---------
    photometry: transient dataframe with photometry.

    Returns
    -------
    fig: plot figure.
    """
    colour_dict = {"ztf_g":"green", "ztf_r":"red", "ztf_i":"gold",
                   "gaia_G":"purple",
                   "atlas_c":"cyan", "atlas_o":"orange",
                   "neowise_W1":"navy", "neowise_W2":"darkred", 
                   "neowise_W3":"indigo", "neowise_W4":"darkslategrey",
                   "tess":"black",
                   "goto_L":"purple",
                   "ps1_g":"green", "ps1_r":"red", "ps1_i":"gold",
                   "clear(VegaMag)":"skyblue",
                  }
    # add extra columns for displaying purposes
    photometry["Filter"] = photometry["filter"].values
    photometry["MJD"] = photometry["mjd"].values
    photometry["Mag"] = photometry["mag"].values
    photometry["MagErr"] = photometry["mag_err"].values
    photometry["MagLimit"] = photometry["upper_mag"].values

    # add ISO time
    photometry["UTC"] = Time(photometry.mjd.values, format="mjd").iso
    
    # add columns
    zp = 23.9  # to get flux in micro jansky
    photometry["flux"] = 10 ** (-0.4 * (photometry.mag.values - zp))
    photometry["flux_err"] = np.abs(photometry.flux.values * 0.4 * np.log(10) * photometry.mag_err.values)
    photometry["upper_flux"] = 10 ** (-0.4 * (photometry.upper_mag.values - zp))
    # add extra columns for displaying purposes
    photometry["Flux"] = photometry["flux"].values
    photometry["FluxErr"] = photometry["flux_err"].values
    photometry["FluxLimit"] = photometry["upper_flux"].values
    
    # update decimal precision
    for col in photometry.columns:
        if photometry[col].dtype == float:
            photometry[col] = photometry[col].apply(lambda x: np.round(x, 3))
    
    ########################
    # Initialize the figure
    fig = go.Figure()
    
    # Add traces for each filter
    for i, (filter, colour) in enumerate(colour_dict.items()):
        filt_df = photometry[photometry["Filter"]==filter]
        # split detections and non-detections
        det_mask = ~filt_df.mag.isna()
        det_df = filt_df[det_mask]
        nondet_df = filt_df[~det_mask]
    
        # hover templates
        hovertemp_mag = get_hovertemplates(det_df, columns=["Filter", "UTC", "MJD", "Mag", "MagErr"])
        hovertemp_flux = get_hovertemplates(filt_df, columns=["Filter", "UTC", "MJD", "Flux", "FluxErr"])
        hovertemp_maglim = get_hovertemplates(nondet_df, columns=["Filter", "UTC", "MJD", "MagLimit"])
        hovertemp_fluxlim = get_hovertemplates(nondet_df, columns=["Filter", "UTC", "MJD", "FluxLimit"])
        
        # photometry
        mag_trace = photometry_trace(det_df, colour, phot_type='mag', name=filter, legendgroup=f"{filter}_mag", hovertemplate=hovertemp_mag)  
        flux_trace = photometry_trace(det_df, colour, phot_type='flux', name=filter, legendgroup=f"{filter}_flux", hovertemplate=hovertemp_flux)  
        # error bars - "legendgroup" needs to match the photometry so their legends are connected
        magerr_trace = error_trace(det_df, colour, phot_type='mag', name=filter, legendgroup=f"{filter}_mag")
        fluxerr_trace = error_trace(det_df, colour, phot_type='flux', name=filter, legendgroup=f"{filter}_flux")
        # upper limits 
        maglim_trace = upperlimit_trace(nondet_df, colour, phot_type='mag', name=filter, legendgroup=f"{filter}_mag", hovertemplate=hovertemp_maglim)
        fluxlim_trace = upperlimit_trace(nondet_df, colour, phot_type='flux', name=filter, legendgroup=f"{filter}_flux", hovertemplate=hovertemp_fluxlim)
    
        fig.add_trace(mag_trace)
        fig.add_trace(magerr_trace)
        fig.add_trace(maglim_trace)
        fig.add_trace(flux_trace)
        fig.add_trace(fluxerr_trace)
        fig.add_trace(fluxlim_trace) # no associated errors at the moment
     
    # assign initial visibility of the traces
    for trace in fig.data:
        if "flux" in trace.legendgroup:
            trace.visible = False
        else:
            trace.visible = True
            
    # discovery date
    #fig.add_vline(obj.discovery_time_mjd, line_width=2, line_dash="solid", line_color="black", 
    #                  annotation_text="disc.", annotation_position="bottom left")
        
    # Define buttons for toggling between magnitude and flux
    buttons = create_toggling_buttons(fig)
    
    # Update layout
    fig.update_layout(
        #title=f"{obj.name} Light Curves",
        xaxis_title="Modified Julian Date",
        yaxis_title="AB Magnitude",
        yaxis=dict(autorange='reversed',  # Inverted y-axis for magnitudes
                  ),  
        #legend_title="Filters",
        #template="plotly_white",
        xaxis_tickformat = '%d',
        width=700,
        height=500,
        font_family="P052",
        font_size=16,
    
        updatemenus=[
            dict(
                type='buttons',
                showactive=True,
                buttons=buttons,
                direction='left',
                x=0.15,
                y=1.15,
                xanchor='center',
                yanchor='top'
            )
        ],
    )
    
    return fig
