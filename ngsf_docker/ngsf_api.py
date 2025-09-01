from fastapi import FastAPI
from pydantic import BaseModel
import shutil
import os

class Params(BaseModel):
    file: str | None = 'sn2003jo.dat'
    z: float | None = 0.0
    z_min: float | None = 0.0


app = FastAPI()

@app.post("/ngsf_params/")
def run_ngsf(params: Params):
    params = params.dict()

    if os.path.exists('./tmp_save') is False:
        os.mkdir('./tmp_save/')

    os.system(f"python run_ngsf.py {params['file']} -z {params['z']} --how_many_plots 0 -s tmp_save/")

    shutil.move(f"tmp_save/{params['file'][:-3]}csv", '/ngsf_api_runs/')

    return {"path": f"{params['file'][:-3]}csv"}
