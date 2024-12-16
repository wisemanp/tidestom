import os
from django.core.management.base import BaseCommand
from tom_targets.models import Target
from utils.target_utils import generate_light_curve_plot, generate_spectrum_plot

class Command(BaseCommand):
    help = 'Generate light curve and spectrum plots for existing targets'

    def handle(self, *args, **kwargs):
        targets = Target.objects.all()
        for target in targets:
            spectrum_file_path = f'/path/to/spectrum/files/spectrum_{target.id}.fits'
            if os.path.exists(spectrum_file_path):
                generate_light_curve_plot(target)
                generate_spectrum_plot(target)
                self.stdout.write(self.style.SUCCESS(f'Successfully updated plots for target {target.name}'))