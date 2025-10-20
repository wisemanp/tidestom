from astropy.table import Table
from specutils import Spectrum1D
from specutils.manipulation import FluxConservingResampler
import astropy.units as u
import numpy as np
import pysnid
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
import logging
import shutil
import pandas as pd
import os
import asyncio
import hashlib
import uuid
from fastapi import Request


logger = logging.getLogger("startup")

class Params(BaseModel):
    spectrum: str
    wmin: Optional[float] = 4000 ##Done
    wmax: Optional[float] = 9000 ##Done
    zmin: Optional[float] = 0 ##Done
    zmax: Optional[float] = 1.2 ##Done
    emclip: Optional[float] = None #Done
    emwid: Optional[float] = 40 #DONE
    agemin: Optional[float] = -90 #Done
    agemax: Optional[float] = 1000 #Done
    use: object #Done
    avoid: object #Done
    avoidsub: object #Done
    usesub: object
    aband: Optional[bool] = False #Done


app = FastAPI()

@app.on_event('startup')
async def startup_event():
    global snid_startup_complete
    try:
        logger.info("Running SNID startup...")

        subtypes = []
        for file in os.listdir('templates-2.0'):
            if file.endswith('lnw'):
                df = pd.read_table(f"templates-2.0/{file}")
                names = df.columns[0].split()
                subtype = names[7]
                if subtype not in subtypes:
                    subtypes.append(subtype)
        if len(subtypes) == 0:
            snid_startup_complete = False
            raise RuntimeError("No Subtypes found, startup may have failed!")
        os.makedirs('/media/snid_template_options', exist_ok=True)
        with open('/media/snid_template_options/subtypes.txt', 'w') as f:
            f.write("\n".join(subtypes))
            snid_startup_complete = True

        logger.info("Startup successful!")
    except Exception as e:
        snid_startup_complete = False
        logger.error(f"Startup failed: {e}")
        raise

@app.get("/health")
async def health():
    file_path = "/media/snid_template_options/subtypes.txt"
    if not snid_startup_complete:
        return JSONResponse(
                status_code=503,
                content={
                    "status": "starting",
                    "file_exists": os.path.exists(file_path)
                    }
                )
    return {
            "status": "ok",
            "file_exists": os.path.exists(file_path),
            }

_running_requests = {}
_running_lock = asyncio.Lock()

def _hash_params(params: dict):
    key_str = f"{params['spectrum']}-{params['wmin']}-{params['wmax']}-{params['zmin']}\
            -{params['zmax']}"
    return hashlib.md5(key_str.encode()).hexdigest()

@app.post("/snid_params/")
async def run_snid(request: Request, params: Params):

    key = _hash_params(params.dict())

    async with _running_lock:
        if key in _running_requests:
            return await _running_requests[key]

        task = asyncio.create_task(_run_snid_task(params))
        _running_requests[key] = task

    try:
        result = await task
        return result
    finally:
        _running_requests.pop(key, None)

async def _run_snid_task(params: Params):
    request_id = uuid.uuid4()

    # Log request info
    print("\n=== SNID Request ===")
    print(f"Request ID: {request_id}")
    print(f"Params: {params.dict()}\n")

    params = params.dict()
    use_type = []
    avoid_type = []

    if len(params['use']) > 0:
        use_type += params['use']

    if len(params['usesub']) > 0:
        use_type += params['usesub']

    if len(params['avoid']) > 0:
        avoid_type += params['avoid']

    if len(params['avoidsub']) > 0:
        avoid_type += params['avoidsub']

    if len(use_type) == 0:
        use_type = None

    if len(avoid_type) == 0:
        avoid_type = None

    file_spec_binned_path='/home/sniduser/snid-5.0/examples'

    file_table = Table.read(params['spectrum'])
    print(file_table)

    #read fits spec
    hdult =  Table.read(params['spectrum'], format='fits')
    wl=hdult['WAVE'][0]
    fl=hdult['FLUX'][0]

    # create a Spectrum1D object for specutils
    spec = Spectrum1D(spectral_axis=wl* u.AA , flux=fl* u.Unit('erg cm-2 s-1 AA-1') )

    # binned wavelength array, at 15 Angstroms
    wl_smooth = np.arange(wl[0], wl[-1], 15) * u.AA

    # binned flux array
    fluxcon = FluxConservingResampler()
    fl_smooth = fluxcon(spec, wl_smooth)

    # make an ascii file of the binned spectrum to run pysnid
    data_spec = np.column_stack([fl_smooth.spectral_axis.value, fl_smooth.flux.value])
    np.savetxt(f"{file_spec_binned_path}/binned.ascii",
               data_spec, fmt=['%.2f','%.4e'])

    #run pysnid
    snidres = pysnid.run_snid(f"{file_spec_binned_path}/binned.ascii",
                              get_results=False,lbda_range=
                              [params['wmin'],params['wmax']], redshift_bounds=
                              [params['zmin'],params['zmax']], phase_range=
                              [params['agemin'], params['agemax']], emwid=
                              params['emwid'], usetype = use_type, avoidtype=
                              avoid_type, emclip=params['emclip'],
                              aband=params['aband'])

    #test = snidres.get_results()
    shutil.move(snidres, '/snid_api_runs/test.h5')
    #this will create a file named file_spec_binned_ascii+'_snid.h5'
    test = pysnid.snid.SNIDReader.from_filename('/snid_api_runs/test.h5')
    df = test.results.copy()

    # Replace non-finite values with None
    df = df.replace([np.inf, -np.inf], np.nan).where(pd.notnull(df), None)
    df = df[['sn', 'typing', 'subtyping', 'lap', 'rlap', 'z', 'zerr', 'age']]

    return {"success": True, "data": {"file_path": "/snid_api_runs/test.h5" ,
                                      "table": df.to_dict(orient='records')[:10]}}

#Remove age_flag, type, grade

#Show the first match of different type
