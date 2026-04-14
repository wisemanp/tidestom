# Tides TOM

[![CI Test](https://github.com/TiDES-4MOST/tidestom/actions/workflows/test_deploy.yml/badge.svg)](https://github.com/TiDES-4MOST/tidestom/actions/workflows/test_deploy.yml)

This repository contains the Tides TOM (Target and Observation Manager) project, built using the [TOM Toolkit](https://tom-toolkit.readthedocs.io/en/stable/). Follow the instructions below to set up the project, contribute to its development, and run the server.

---
## Local Docker Intallation for Development

These instructions relate to building and deploying a local version of the Dockerised version of the TiDES TOM, this is the most feature full version and is closest to the version which will be deployed.

**Note currently this version does not have API support**

SNID and NGSF will not run on this version. Attempting to run them may lead to unexpected results.

### Prerequsists

Make sure you have Docker installed on your machine, you can download it [here](https://www.docker.com/get-started/)

### Installation

To build and deploy the TiDES TOM follow these steps:

1. **Make sure Docker is running**

2. **Clone the repository**:  
   Go to the [Tides TOM GitHub repository](https://github.com/TiDES-4MOST/tidestom.git) and click the "Code" button and the follow the instructions to Clone the repository

3. **Download the test data**:  
   Download the test data from the following [link](https://drive.google.com/file/d/1HxkHGde8RTyMZWAeSsQjQqdPiWQTlu3s/view?usp=sharing) and save it in the same directory as the repository directory, eg.
   ```bash
   Documents
   |
   |tidestom
   |test_data
   ```

5. **Build the Docker images and start the server**:
   This will take a few minutes the first time you run it, it should be faster on subsquent runs
   ```bash
   docker compose -f docker-compose-local.yml up --build -d
   ```
   It is very important that you build using the -local file version, the other files are for deployment building or for intgration and deployment tests. 
   
   **If you are switching branches or already have a local container from another branch:**
   You may need to reset the local database volume so migrations can run cleanly.
   **Warning: this deletes local data.**
   ```bash
   docker compose -f docker-compose-local.yml down -v
   docker volume rm tidestom_postgres_data_local 2>/dev/null || true
   docker compose -f docker-compose-local.yml up --build -d
   ```

6. **Create a superuser**:   
   This creates a superuser for you to test everything on your local installation; this is necessary because the deployed user list is managed on the live database.
   ```bash
   docker exec -it tidestom-web-1 python manage.py createsuperuser
   ```
   Follow the prompts to create a superuser. If that fails see common issues below.

7. **Open your browser and navigate to:**
   ```
   localhost:8080
   ```
   You should now see the Tides TOM application running locally, connected to a local databse. You can login in using the superuser credentials you've just created.

### Common Issues

1. I wasn't able to create a superuser account, I can't log in to anything beyond the home page!
 
   This is probably because you didn't run the ```createsuperuser``` command earlier. If you did it might not have been in the correct container, it might not be called ```tidestom-web-1```
   1. Having completed at least to step 5 above run:
      ```bash
      docker ps
      ```
      This will show you created containers. Find the name of the container created from the image called ```tidestom-web``` 
   2. Substitute this name into the command in step 5 and run
     
2. I just get a 504 error when I try to go to the webpage.

   This probably means that nginx, the load manager, is a little confused about the web service and needs restarted
   1. Open a Docker Desktop window
   2. In the side bar select ```Containers```
   3. Expand the ```tidestom``` container to see the images contained within it
   4. Locate the ```nginx``` container and on the far right of the page under actions, between the stop button and the delete button open the menu with the 3 stacked dots and select *Restart*
   5. Reload the page
  
---
## Contributing to Development

If you want to contribute to the development of this project, follow these steps:

1. **Create a new branch**:  
   Create a branch for your changes from the ```prod``` branch:
    ```bash
    git checkout -b $your-branch-name prod
    ```
    ```$your-branch-name``` should take the format of bugfix/feature-item-username, eg. ```feature-authentication-joeBlogs1``` or ```bugfix-UI-joeBlogs1```

2. **Make your changes**:  
   Make the necessary changes to the codebase. Anytime you want to test a change on your local version just run the command from step 5 of the installation instructions.

3. **Edit `.gitignore`**:  
   Make sure that any files you don't want to commit such as .DS_store etc. are not going to be committed by checking ```git status``` or GitHub Desktop. If they are then add them to `.gitignore` so they are not tracked by Git.

4. **Commit your changes**:  
   Stage and commit your changes:
    ```bash
    git add changed_filename
    git commit -m "Description of your changes"
    ```
    Or use GitHub Desktop

5. **Push your branch**:  
   Push your branch to your cloned repository:
    ```bash
    git push origin $your-branch-name
    ```
    Or use GitHub Desktop

6. **Open a pull request**:  
   Return to the respositiory and open a Pull Request to request to merge your branch into the ```dev-deploy``` branch. Here it will be subject to code review and/or CI/CD tests. You may be asked to make changes to your submitted code at this point. When it is approved it will be merged into ```dev-deploy``` where admins will evaluate your changes on a live system to make sure they are stable before merging them into ```prod```. You do not need to be involved after your changes are merged into ```dev-deploy``` 

---

## Legacy Instructions

These instructions are to deploy only the TiDESTOM without the supporting API which engages with a local instance of the database and runs in a python `venv`. These instructions are *highly* unlikely to work with the current architecture and are provided purely for reference.

### Installation

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
### Running the Server

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
### Setting Up Test Data

To use the Tides TOM with test data, follow these steps:

1. **Download the test data**:  
   Download the test data from the following link: [Test Data](https://drive.google.com/file/d/1HxkHGde8RTyMZWAeSsQjQqdPiWQTlu3s/view?usp=sharing)
   

4. **Add the following line to the end of the file**:
    ```bash
    export TIDES_TEST_DIR="/path/to/extracted/test/data"
    ```

---

### Using tides_unmanaged_tables.sql with TiDES TOM

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

4) Apply the TiDES unmanaged tables (must run after migrate):
- Clone the tides_db schema: https://github.com/TiDES-4MOST/tides-db-scripts
```bash
psql "host=localhost port=5432 user=tides password=tides dbname=tides_db" \
  -f ../tides-db-scripts/tides_unmanaged_tables.sql
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
