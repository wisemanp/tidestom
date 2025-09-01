from fastapi import FastAPI
from pydantic import BaseModel
import shutil
import os

class Params(BaseModel):
    file: str | None = 'sn2003jo.dat'
    z: float | None = 0.0
    z_min: float | None = 0.0
    z_max: float | None = 0.1
    z_int: float | None = 0.01
    resolution: float | None = 10
    lower_lam: float | None = 0.00
    upper_lam: float | None = 0.0
    mask_galaxy: bool | None = True
    mask_telluric: bool | None = True
    epoch_high: float | None = 0.0
    epoch_low: float | None = 0.0
    alam_high: float | None = 2
    alam_low: float | None = -2
    alam_interval: float | None = 0.2

app = FastAPI()

@app.post("/ngsf_params/")
def run_ngsf(params: Params):
    params = params.dict()

    if os.path.exists('./tmp_save') is False:
        os.mkdir('./tmp_save/')

    os.system(f"python run_ngsf.py {params['file']} -z {params['z']} --how_many_plots 0 -s tmp_save/")

    shutil.move(f"tmp_save/{params['file'][:-3]}csv", '/ngsf_api_runs/')

    return {"path": f"{params['file'][:-3]}csv"}
