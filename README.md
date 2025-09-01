# Tides TOM

[![CI Test](https://github.com/TiDES-4MOST/tidestom/actions/workflows/test_deploy.yml/badge.svg)](https://github.com/TiDES-4MOST/tidestom/actions/workflows/test_deploy.yml)

This repository contains the Tides TOM (Target and Observation Manager) project, built using the [TOM Toolkit](https://tom-toolkit.readthedocs.io/en/stable/). Follow the instructions below to set up the project, contribute to its development, and run the server.

---

## Installation

To set up the Tides TOM, follow these steps:

1. **Fork the repository**:  
   Go to the [Tides TOM GitHub repository](https://github.com/TiDES-4MOST/tidestom.git) and click the "Fork" button in the top-right corner to create your own copy of the repository.


2. **Clone your fork**:  
   Clone your forked repository to your local machine:
    ```bash
    git clone https://github.com/TiDES-4MOST/tidestom.git
    cd tidestom
    ```

3. **Run the setup script**:  
   Set up the virtual environment and install dependencies:
    ```bash
    ./setup.sh
    ```

Once you have installed the TOM Toolkit and the required dependencies, you can proceed to set up and run the Tides TOM.

---

## Contributing to Development

If you want to contribute to the development of this project, follow these steps:

1. **Create a new branch**:  
   Create a branch for your changes:
    ```bash
    git checkout -b <your-branch-name>
    ```

2. **Make your changes**:  
   Make the necessary changes to the codebase.


3. **Edit `.gitignore`**:  
   Make sure that any data directories and the database (e.g., `db.sqlite`) are added to `.gitignore` so they are not tracked by Git.


4. **Commit your changes**:  
   Stage and commit your changes:
    ```bash
    git add .
    git commit -m "Description of your changes"
    ```

5. **Push your branch**:  
   Push your branch to your forked repository:
    ```bash
    git push origin <your-branch-name>
    ```

6. **Open a pull request**:  
   Go to the original repository on GitHub and open a pull request to merge your changes into the main branch.



---
## Running the Server

To run the Tides TOM server, follow these steps:

1. Navigate to the project directory:
    ```bash
    cd tides_tom
    ```

2. Run database migrations to initialize the database:
    ```bash
    python manage.py migrate
    ```

3. Create a superuser:  
   To access the Django admin interface and manage the application, create a superuser account:
    ```bash
    python manage.py createsuperuser
    ```
   Follow the prompts to set up a username and password. You can leave the e-mail blank for development purposes.

4. Start the development server:
    ```bash
    python manage.py runserver
    ```

5. Open your browser and navigate to:
    ```
    http://127.0.0.1:8000/
    ```

You should now see the Tides TOM application running locally.

---
## Setting Up Test Data

To use the Tides TOM with test data, follow these steps:

1. **Download the test data**:  
   Download the test data from the following link:  
   [Test Data](https://drive.google.com/file/d/1H_7whYmBWRzPRep8oYmlWWhUJhY2x18Z/view?usp=sharing)
   

    ```

4. **Add the following line to the end of the file**:
    ```bash
    export TIDES_TEST_DIR="/path/to/extracted/test/data"
    ```

---

## Using tides_merged_schema.sql with TiDES TOM

This sets up a local Postgres schema compatible with TiDES and TOM, then seeds targets from a MEC file so you can run the pipeline locally.

Prerequisites:
- PostgreSQL running locally (psql available)
- A Python virtualenv with TOM Toolkit and this project installed

Steps:

1) Create database and role (adjust user/password as needed):
```bash
createdb tides_db
psql -d tides_db -c "CREATE USER tides WITH PASSWORD 'tides';"
psql -d tides_db -c "GRANT ALL PRIVILEGES ON DATABASE tides_db TO tides;"
```

2) Add DB credentials to your YAML config (used by scripts and pipeline):
```yaml
db_creds:
  host: "localhost"
  port: 5432
  user: "tides"
  password: "tides"
  name: "tides_db"
```

3) Run Django migrations so TOM base tables exist:
```bash
cd tidestom
python manage.py migrate
```

4) Apply the TiDES schema additions:
- Clone the tides_db schema: https://github.com/TiDES-4MOST/tides-db-scripts
```bash
psql "host=localhost port=5432 user=tides password=tides dbname=tides_db" \
  -f ../tides-db-scripts/tides_merged_schema.sql
```

5) Seed targets from a MEC file-with-transient-spectra:
- The seeding script reads OBJ_NME from FIBMETATAB and creates matching rows in:
  - public.tom_targets_basetarget (filling required fields)
  - public.tides_cand (FK to BaseTarget)
```bash
python ../tides-db-scripts/populate_db_from_MEC.py \
  --mec /path/to/deliveries_dir/mec_with_transients.fits \
  --config ../tides_pipe/config/config.yml
```
Note: If your tides_cand.tides_id is INTEGER, the script downcasts IDs; for BIGINT, it uses full IDs.

6) (Optional) Ingest spectra into tides_spec with the pipeline:
- Clone the tides backend pipeline: https://github.com/TiDES-4MOST/tides_pipe
- Configure data paths in tides_pipe/config/config.yml
- Place your MEC delivery under deliveries_dir/<night> and run:
```bash
python -c "from tides_pipe.modules.data_ingestion import DataIngestion; \
import yaml; cfg=yaml.safe_load(open('tides_pipe/config/config.yml')); \
DataIngestion(cfg).process_night('<night>')"
```

Troubleshooting:
- Check tables exist and FKs: psql -d tides_db -c "\d+ public.tides_cand" and "\d+ public.tom_targets_basetarget"
- Verify seeded rows: psql -d tides_db -c "SELECT COUNT(*) FROM public.tides_cand;"
- If FK errors occur, ensure BaseTarget rows are created before inserting tides_cand.
- If JSON serialization errors occur in tides_spec, ensure metadata fields are native Python types.

---

## Notes

- Ensure you have all required dependencies installed as per the TOM Toolkit manual installation guide.
- If you encounter any issues, please refer to the [TOM Toolkit documentation](https://tom-toolkit.readthedocs.io/en/stable/) or open an issue in this repository.

---

TiDES: Industrialising Transient Science!
