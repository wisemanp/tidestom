# Tides TOM

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
   [Test Data](https://drive.google.com/file/d/1HxkHGde8RTyMZWAeSsQjQqdPiWQTlu3s/view?usp=sharing)
   

2. **Unzip the test data**:  
   Extract the downloaded file to a directory of your choice:
    ```bash
    tar -xvf /path/to/downloaded/file.tar.gz -C /path/to/extract/
    ```

3. **Set the test directory path**:  
   Add the test directory path to your environment by editing the `tom_env/bin/activate` script:
    ```bash
    nano /path/to/tom_env/bin/activate
    ```

4. Add the following line to the end of the file:
    ```bash
    export TIDES_TEST_DIR="/path/to/extracted/test/data"
    ```

   Save the file and exit. Then, source the environment again to apply the changes:
    ```bash
    source /path/to/tom_env/bin/activate
    ```

   Verify that the environment variable is set:
    ```bash
    echo $TIDES_TEST_DIR
    ```   

5. **Run the `populate_tidesclasses` command**:  
    Before adding targets, make sure to populate the `TidesClass` and `TidesClassSubClass` tables by running the following command:
    ```bash
    python manage.py migrate
    python manage.py populate_tidesclasses
    ```
---
## Loading Test Data into the Database

Once the test data is set up, you can load it into the database using the following commands:

1. **Add targets**:  
   Run the following command to add targets from the test data:
    ```bash
    python manage.py add_targets
    ```

2. **Add spectra**:  
   Run the following command to add spectra from the test data:
    ```bash
    python manage.py add_spectra_to_db --mock
    ```

These commands will populate the database with the test targets and spectra.



## Notes

- Ensure you have all required dependencies installed as per the TOM Toolkit manual installation guide.
- If you encounter any issues, please refer to the [TOM Toolkit documentation](https://tom-toolkit.readthedocs.io/en/stable/) or open an issue in this repository.

---

TiDES: Industrialising Transient Science!