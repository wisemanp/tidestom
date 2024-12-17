import os
import matplotlib.pyplot as plt
from astropy.io import fits
from django.conf import settings
from tom_targets.models import Target

def generate_light_curve_plot(target):
    # Generate the light curve plot for the target
    plt.figure()
    # Example plot code
    plt.plot([1, 2, 3], [4, 5, 6])
    plt.title(f'Light Curve for {target.name}')
    plt.savefig(os.path.join(settings.STATICFILES_DIRS[0], f'plots/light_curve_{target.id}.png'))
    plt.close()

def generate_spectrum_plot(target,spec_fn):
    # Generate the spectrum plot for the target
    f,ax=plt.subplots()
    try:
        spec=fits.getdata(spec_fn)
        # Example plot code
        ax.step(spec['WAVE'][0],spec['FLUX'][0],where='mid')
        ax.set_xlim(4000,9300)
    except OSError:
        pass
    plt.title(f'TiDES {target.name}')
    plt.savefig(os.path.join(settings.STATICFILES_DIRS[0], f'plots/spectrum_{target.id}.png'))
    print("Saved spectrum plot to", os.path.join(settings.STATICFILES_DIRS[0], f'plots/spectrum_{target.id}.png'))
    plt.close()

def create_target(name, other_fields, update_existing=False,generate_plots=False,spec_fn=None):
    if update_existing:
        target, created = Target.objects.update_or_create(
            name=name,
            #external_id=name,
            defaults={'name': name, **other_fields}
        )
    else:
        target = Target.objects.create(name=name, **other_fields)
    
    if generate_plots:
        # Generate the light curve and spectrum plots
        #generate_light_curve_plot(target,spec_fn)
        generate_spectrum_plot(target,spec_fn)
    
    return target