import os
import matplotlib.pyplot as plt
from django.conf import settings
from tom_targets.models import Target

def generate_light_curve_plot(target):
    # Generate the light curve plot for the target
    plt.figure()
    # Example plot code
    plt.plot([1, 2, 3], [4, 5, 6])
    plt.title(f'Light Curve for {target.name}')
    plt.savefig(os.path.join(settings.STATIC_ROOT, f'plots/light_curve_{target.id}.png'))
    plt.close()

def generate_spectrum_plot(target):
    # Generate the spectrum plot for the target
    plt.figure()
    # Example plot code
    plt.plot([1, 2, 3], [6, 5, 4])
    plt.title(f'Spectrum for {target.name}')
    plt.savefig(os.path.join(settings.STATIC_ROOT, f'plots/spectrum_{target.id}.png'))
    plt.close()

def create_target_and_generate_plots(name, external_id, other_fields, update_existing=False):
    if update_existing:
        target, created = Target.objects.update_or_create(
            external_id=external_id,
            defaults={'name': name, **other_fields}
        )
    else:
        target = Target.objects.create(name=name, external_id=external_id, **other_fields)
    
    # Generate the light curve and spectrum plots
    generate_light_curve_plot(target)
    generate_spectrum_plot(target)
    
    return target