from django.core.management.base import BaseCommand
from custom_code.models import TidesCand, MirroredTidesTarget

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        for cand in TidesCand.objects.all():
            MirroredTidesTarget.objects.update_or_create(
                tides_id=cand.tides_id,
                defaults={
                    'name': f'TIDES_{cand.tides_id}',
                    'ra': 0.0,  # Put RA/Dec if available from another table
                    'dec': 0.0,
                    'type': 'SIDEREAL',
                }
            )
        self.stdout.write(self.style.SUCCESS('Synced Tides Candidates to TOM Target Table'))
