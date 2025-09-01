from astropy.table import Table
from specutils import Spectrum1D
from specutils.manipulation import FluxConservingResampler
import astropy.units as u
import numpy as np
import pysnid
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
import shutil

class Params(BaseModel):
    wmin: Optional[float] = 4000
    wmax: Optional[float] = 9000
    zmin: Optional[float] = 0
    zmax: Optional[float] = 1.2
    emclip: Optional[float] = None #Not yet added to PySNID
    emwid: Optional[float] = 40 #Not yet added to PySNID
    agemin: Optional[float] = -90
    agemax: Optional[float] = 1000 #Needs added to PySNID
    use: object #Need to apply logic to get these working Dummy for now
    usesub: object
    avoid: object
    avoidsub: object
    aband: Optional[bool] = False


app = FastAPI()

@app.post("/snid_params/")
def run_snid(params: Params):
    params  = params.dict()
    print(params)
    file_spec='/home/sniduser/snid-5.0/examples/sn2003jo.dat'
    file_spec_ascii='/home/sniduser/snid-5.0/examples/sn2003jo.ascii'
    file_spec_binned_ascii='/home/sniduser/snid-5.0/examples/sn2003jo_binned.ascii'

    #read fits spec
    hdult =  Table.read(file_spec, format='ascii')
    wl=hdult['col1']
    fl=hdult['col2']

    # create a Spectrum1D object for specutils
    spec = Spectrum1D(spectral_axis=wl* u.AA , flux=fl* u.Unit('erg cm-2 s-1 AA-1') )

    # binned wavelength array, at 15 Angstroms
    wl_smooth = np.arange(wl[0], wl[-1], 15) * u.AA

    # binned flux array
    fluxcon = FluxConservingResampler()
    fl_smooth = fluxcon(spec, wl_smooth)

    # make an ascii file of the binned spectrum to run pysnid
    data_spec = np.column_stack([fl_smooth.spectral_axis.value, fl_smooth.flux.value])
    np.savetxt(file_spec_binned_ascii , data_spec, fmt=['%.2f','%.4e'])

    #run pysnid
    snidres = pysnid.run_snid(file_spec_binned_ascii,get_results=False,lbda_range=
                              [params['wmin'],params['wmax']], redshift_bounds=
                              [params['zmin'],params['zmax']], aband=params['aband'])

    #test = snidres.get_results()
    shutil.move(snidres, '/snid_api_runs/test.h5')
# this will create a file named file_spec_binned_ascii+'_snid.h5'
    return {"path": snidres}
