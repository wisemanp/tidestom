import os
import json
import pandas as pd
from django.core.management.base import BaseCommand
from tom_targets.models import Target
from tidestom.tides_utils.target_utils import create_target
### TODO: WRITE CORRECT DIRECTORY IN HER, USING AN ENVIRONMENT VARIABLE


class Command(BaseCommand):
    # Placeholder code that currently looks at a set of simulated spectra from Georgios.
    help = 'Add new targets from a distant directory'

    def handle(self, *args, **kwargs):
        #directory = os.environ['TARGET_DB']
        dbdf = pd.read_csv('/Users/pwise/4MOST/tides/testdata/mock_DB.csv')   
        for index, row in dbdf.iterrows(): 
            name = row['name']
            if row['OBS_STATUS_4MOST']==True:
                external_id = name
                other_fields = {
                    'ra': row['ra'],
                    'dec': row['dec'],
                    'created':row['MJD_DET']
                    # Add other fields as needed
                }
                create_target(name,other_fields,update_existing=False)
                self.stdout.write(self.style.SUCCESS(f'Successfully added target {name}'))
        