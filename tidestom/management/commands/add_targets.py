import os
import pandas as pd
from django.core.management.base import BaseCommand
from tom_targets.models import Target
from tidestom.tides_utils.target_utils import create_target
from django.conf import settings
from django.db import connection
### TODO: WRITE CORRECT DIRECTORY IN HER, USING AN ENVIRONMENT VARIABLE


class Command(BaseCommand):
    # Placeholder code that currently looks at a set of simulated spectra from Georgios.
    help = 'Add new targets from a distant directory'

    def handle(self, *args, **kwargs):
        #directory = os.environ['TARGET_DB']
        target_csv_path = os.path.join(settings.TEST_DIR, "mock_DB.csv")

        if not os.path.exists(target_csv_path):
            self.stdout.write(self.style.ERROR(f"Target CSV file not found at {target_csv_path}"))
            return
        dbdf = pd.read_csv(target_csv_path, index_col=0)   
        for index, row in dbdf.iterrows(): 
            name=index
            if row['OBS_STATUS_4MOST']:  # Check if the target has been observed by 4MOST
                external_id = name
                other_fields = {
                    'ra': row['ra'],
                    'dec': row['dec'],
                    'created': row['MJD_DET'],
                    'type':'SIDEREAL'
                    # Add other fields as needed
                }

                # Check if the target already exists
                target, created = Target.objects.update_or_create(
                    name=name,
                    defaults=other_fields
                )

                if created:
                    self.stdout.write(self.style.SUCCESS(f'Successfully added target {name}'))
                else:
                    self.stdout.write(self.style.SUCCESS(f'Successfully updated target {name}'))

                # Ensure a child row exists in tides_cand for this Target
                with connection.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO public.tides_cand (tides_id)
                        VALUES (%s)
                        ON CONFLICT (tides_id) DO NOTHING
                        """,
                        [target.id],
                    )
                self.stdout.write(f'Ensured tides_cand row for target id={target.id}')
            else:
                self.stdout.write(self.style.WARNING(f'Target {name} has not been observed by 4MOST and will not be added'))