from fastapi import FastAPI
from pydantic import BaseModel
import os

class Params(BaseModel):
    z: float | None = 0.1


app = FastAPI()

@app.post("/ngsf_params/")
def run_ngsf(params: Params):
    params = params.dict()

    os.system(f"python run_ngsf.py sn2003jo.dat.txt -z {params['z']} --how_many_plots 0")

    return {"test": f"test:{params['z']}"}
