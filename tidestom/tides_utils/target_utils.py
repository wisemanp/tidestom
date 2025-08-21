import os
import matplotlib.pyplot as plt
from astropy.io import fits
from django.conf import settings
from tom_targets.models import Target
from django.core.management.base import BaseCommand
from tom_dataproducts.models import DataProduct
from tom_dataproducts.data_processor import run_data_processor
from datetime import datetime
from pathlib import Path  # Import pathlib

def generate_light_curve_plot(target):
    # Generate the light curve plot for the target
    plt.figure()
    # Example plot code
    plt.plot([1, 2, 3], [4, 5, 6])
    plt.title(f'Light Curve for {target.name}')
    
    # Ensure the directory exists
    plot_dir = Path(settings.STATICFILES_DIRS[0]) / 'plots'
    plot_dir.mkdir(parents=True, exist_ok=True)
    
    # Save the plot
    plot_path = plot_dir / f'light_curve_{target.id}.png'
    plt.savefig(plot_path)
    plt.close()

def generate_spectrum_plot(target, spec_fn):
    # Generate the spectrum plot for the target
    f, ax = plt.subplots()
    try:
        spec = fits.getdata(spec_fn)
        # Example plot code
        ax.step(spec['WAVE'][0], spec['FLUX'][0], where='mid')
        ax.set_xlim(4000, 9300)
    except OSError:
        pass
    
    # Ensure the directory exists
    plot_dir = Path(settings.STATICFILES_DIRS[0]) / 'plots'
    plot_dir.mkdir(parents=True, exist_ok=True)
    
    # Save the plot
    plot_path = plot_dir / f'spectrum_{target.id}.png'
    plt.savefig(plot_path)
    print("Saved spectrum plot to", plot_path)
    plt.close()

def create_target(name, other_fields, update_existing=False, generate_plots=False, spec_fn=None):
    if update_existing:
        target, created = Target.objects.update_or_create(
            name=name,
            # external_id=name,
            defaults={'name': name, **other_fields}
        )
    else:
        target = Target.objects.create(name=name, **other_fields)
    
    if generate_plots:
        # Generate the light curve and spectrum plots
        # generate_light_curve_plot(target, spec_fn)
        generate_spectrum_plot(target, spec_fn)
    
    return target

def add_spectrum_to_database(target, spectrum_file_path):
    #try:
    if os.path.exists(spectrum_file_path):
        # Determine the symlink path
        if os.path.basename(spectrum_file_path).startswith('l1_obs_joined_'):
            tom_file_path = os.path.join(settings.BASE_DIR, 'data/spectra/test/', os.path.basename(spectrum_file_path))
        else:
            tom_file_path = os.path.join(settings.BASE_DIR, 'data/spectra/', os.path.basename(spectrum_file_path))
        

        if os.path.islink(tom_file_path):
            print(f"Symlink already exists: {tom_file_path}")
        else:
            print(f"Creating symlink: {tom_file_path}")
            os.symlink(spectrum_file_path, tom_file_path)
        
        # Add the spectrum to the database
        print(f"Adding spectrum to database for target: {target.name}")
        print(f"File path: {tom_file_path}")
        data_product = DataProduct.objects.create(
            target=target,
            data_product_type='spectroscopy',
            product_id=f'{target.name}' + datetime.now().strftime('%Y%m%d%H%M%S'),
            data=tom_file_path
        )
        run_data_processor(data_product)
        return f'Added spectrum for {target.name} to the database'
    else:
        return f'Spectrum file for {target.name} does not exist'
    #except Exception as e:
    #    return f'Error adding spectrum for {target.name}: {e}'