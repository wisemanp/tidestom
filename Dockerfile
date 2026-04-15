FROM python:3.11

RUN apt-get update && apt-get install -y postgresql-client && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir tomtoolkit==2.26.2

RUN pip install --no-cache-dir -r requirements.txt

# Patch: tom_targets migration 0025 uses guardian models but doesn't declare
# the dependency, causing LookupError on fresh databases.
RUN python -c "\
import pathlib; \
p = pathlib.Path('/usr/local/lib/python3.11/site-packages/tom_targets/migrations/0025_auto_20250206_2017.py'); \
t = p.read_text(); \
p.write_text(t.replace('dependencies = [', \"dependencies = [\\n        ('guardian', '0001_initial'),\")) \
if \"('guardian',\" not in t else None"

COPY . .

COPY entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/entrypoint.sh
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]

#CMD ["gunicorn", "--bind", "0.0.0.0:8000", "tidestom.wsgi:application"]

