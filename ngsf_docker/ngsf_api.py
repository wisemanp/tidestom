from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from astropy.table import Table
import logging
import pandas as pd
import numpy as np
import shutil
import os
import asyncio
import hashlib

logger = logging.getLogger("startup")

class Params(BaseModel):
    spectrum: str | None = 'sn2003jo.dat'
    z: float | None = 0.0
    z_min: float | None = 0.0
    z_max: float | None = 0.1
    z_int: float | None = 0.01
    resolution: float | None = 10
    lower_lam: float | None = 0.00
    upper_lam: float | None = 0.0
    mask_galaxy: bool | None = True
    mask_telluric: bool | None = True
    epoch_high: int | None = 0
    epoch_low: int | None = 0
    alam_high: float | None = 2.0
    alam_low: float | None = -2.0
    alam_interval: float | None = 0.2

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    global ngsf_startup_complete
    try:
        logger.info("Running startup proceedures for NGSF...")

        cmd = "python run_ngsf.py sn2003jo.dat -z 1 --how_many_plots 0"
        result = os.system(cmd)
        if result != 0:
            ngsf_startup_complete = False
            os.remove('sn2003jo.csv')
            os.remove('sn2003jo_binned.txt')
            raise RuntimeError("Setup Failed!!")

        ngsf_startup_complete = True
        logger.info("Setup Complete!")
    except Exception as e:
        ngsf_startup_complete = False
        logger.error(f"Startup failed: {e}")
        raise

@app.get("/health")
async def health():
    if not ngsf_startup_complete:
        return JSONResponse(
                status_code=503,
                content={
                    "status": "starting",
                    "Config Downloaded": ngsf_startup_complete
                    }
                )
        return {
                "status": "ok",
                "Config Downloaded": ngsf_startup_complete,
                }

_running_requests = {}
_running_lock = asyncio.Lock()

def _hash_params(params: dict):
    key_str = f"{params['z']}-{params['z_min']}-{params['z_max']}-{params['z_int']}\
            -{params['spectrum']}"
    return hashlib.md5(key_str.encode()).hexdigest()

@app.post("/ngsf_params/")
async def run_ngsf(params: Params):

    key = _hash_params(params.dict())

    async with _running_lock:
        if key in _running_requests:
            return await _running_requests[key]

        task = asyncio.create_task(_run_ngsf_task(params))
        _running_requests[key] = task

    try:
        result = await task
        return result
    finally:
        _running_requests.pop(key, None)

async def _run_ngsf_task(params: Params):
    params = params.dict()
    print(params)

    if not params['mask_galaxy']:
        params['mask_galaxy'] = 0
    else:
        params['mask_galaxy'] = 1

    if not params['mask_telluric']:
        params['mask_telluric'] = 0
    else:
        params['mask_telluric'] = 1

    if os.path.exists('./tmp_save') is False:
        os.mkdir('./tmp_save/')

    move_path='/'
    hdult = Table.read(params['spectrum'], format='fits')
    wl = hdult['WAVE'][0]
    fl = hdult['FLUX'][0]

    to_dat = np.column_stack([wl, fl])
    np.savetxt(f"{move_path}spectrum.ascii",
               to_dat, fmt=['%.2f', '%.4e'])

    os.system(f"python run_ngsf.py /spectrum.ascii -z {params['z']} \
            --z_range_begin {params['z_min']} --z_range_end {params['z_max']} \
            --z_int {params['z_int']} --lower_lam {params['lower_lam']} \
            --upper_lam {params['upper_lam']} --mask_galaxy {params['mask_galaxy']} \
            --mask_telluric {params['mask_telluric']} \
            --epoch_high {params['epoch_high']} --epoch_low {params['epoch_low']} \
            --Alam_high {params['alam_high']} --Alam_low {params['alam_low']} \
            --Alam_interval {params['alam_interval']} --how_many_plots 0 -s tmp_save/")

    df = pd.read_csv('tmp_save/spectrum.csv')
    shutil.move("tmp_save/spectrum.csv", '/ngsf_api_runs/spectrum.csv')

    return {"sucess": True, "data": {"file_path": "/ngsf_api_runs/spectrum.csv",
                                     "table": df.to_dict(orient='records')[:10]}}
