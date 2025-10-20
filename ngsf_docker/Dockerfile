FROM python:3.11

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt 

COPY . .

CMD ["uvicorn", "ngsf_api:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4" ,"--log-level", "debug"]
