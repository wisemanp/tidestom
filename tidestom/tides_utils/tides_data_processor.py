from datetime import datetime
import os
from astropy.time import Time
from tom_dataproducts.data_processor import DataProcessor
from tom_dataproducts.processors.data_serializers import SpectrumSerializer
from astropy.io import fits
from specutils import Spectrum1D
from astropy import units as u


class QMOSTSpectroscopyProcessor(DataProcessor):

    def process_data(self, data_product, test: bool = False):
        if os.path.basename(data_product.data.path).startswith(
            'l1_obs_joined_'
        ):
            spectrum, obs_date, source_id = self._process_test_spectrum(
                data_product=data_product
            )

        serialized_spectrum = SpectrumSerializer().serialize(spectrum)

        return [(obs_date, serialized_spectrum, source_id)]

    def _process_test_spectrum(self, data_product):
        spec = fits.getdata(data_product.data.path)
        wave = spec['WAVE'][0] * u.Angstrom
        flux = spec['FLUX'][0] * u.Unit('erg cm-2 s-1 AA-1')
        spectrum = Spectrum1D(flux=flux, spectral_axis=wave)
        # TODO change obs date!
        return spectrum, Time(datetime.now()).to_datetime(), '4MOST'

    def _process_L1_spectrum(self, data_product):
        '''Some code to process real 4MOST L1 spectra'''
