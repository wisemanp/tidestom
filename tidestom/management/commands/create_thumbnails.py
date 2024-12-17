import os
from django.core.management.base import BaseCommand
from tom_targets.models import Target
from tidestom.tides_utils.target_utils import generate_light_curve_plot, generate_spectrum_plot

class Command(BaseCommand):
    help = 'Generate light curve and spectrum plots for existing targets'

    def handle(self, *args, **kwargs):
        targets = Target.objects.all()
        for target in targets:
            
            spectrum_file_path = f'/Users/pwise/4MOST/tides/testdata/spec_simulations/sims/l1_obs_joined_{target.name}.fits'
            if os.path.exists(spectrum_file_path):
                generate_spectrum_plot(target,spectrum_file_path)
                self.stdout.write(self.style.SUCCESS(f'Successfully updated plots for target {target.name}'))