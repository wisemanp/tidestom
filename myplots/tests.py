from django.test import TestCase
#from tom_targets.tests.factories import SiderealTargetFactory
from tom_targets.models import Target

import warnings
import pandas as pd
from myplots.templatetags.photometry_settings import fetch_ztf_lasair
from tidestom.settings import BROKERS
lasair_token = BROKERS['LASAIR']['api_key']

class TestPhotometry(TestCase):
    def setUp(self):
        self.target = Target.objects.create(name='test_target')  # ZTF25aacedrs
        self.target.ra = 49.1384664
        self.target.dec = 44.9725084
        
    def test_ztf_photometry(self):
        if lasair_token is None or lasair_token == "":
            warnings.warn("Warning: Lasair API key not set!", UserWarning)
        else:
            photometry = fetch_ztf_lasair(self.target.ra, self.target.dec)
            assert isinstance(photometry, pd.DataFrame), f"Photometry object is not a DataFrame! Check {fetch_ztf_lasair}."