import os
import hashlib
import pandas as pd
from datetime import datetime
from pathlib import Path

from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils.timezone import now
from django.utils import timezone as dj_timezone

from astropy.io import fits
from astropy.time import Time

from custom_code.models import TidesTarget as Target
from custom_code.models import TidesClassSubClass
from custom_code.models import TidesSpec
from custom_code.models import PipelineClassificationGlobal

from tidestom.tides_utils.target_utils import (
    generate_spectrum_plot  # removed add_spectrum_to_database
)

class Command(BaseCommand):
    help = 'Add spectra details to tides_spec and update auto classifications (no DataProducts)'

    def add_arguments(self, parser):
        parser.add_argument('--mock', action='store_true', help='Add spectra from mock database')
        parser.add_argument('--pipeline', action='store_true', help='Add spectra from pipeline results')
        parser.add_argument('--pipeline-results', type=str, help='Path to the pipeline results file')

    def handle(self, *args, **kwargs):
        if kwargs['mock']:
            self.add_spectra_from_mock_db()
        elif kwargs['pipeline']:
            pipeline_results_path = kwargs['pipeline_results']
            if not pipeline_results_path:
                print("ERROR: Pipeline results path must be provided when using --pipeline option")
                return
            self.add_spectra_from_pipeline(pipeline_results_path)
        else:
            print("ERROR: Either --mock or --pipeline option must be specified")

    # ---------------- helpers ----------------

    def _compute_qmost_id(self, target_id: int, filepath: Path) -> int:
        """
        Stable 63-bit integer derived from (target_id|filepath). Fits in BIGINT.
        """
        h = hashlib.sha1(f"{target_id}|{str(filepath)}".encode('utf-8')).hexdigest()
        # take 15 hex digits (~60 bits) to stay below 2^63-1
        return int(h[:15], 16)

    def _extract_obs_times(self, file_path: Path):
        """
        Try to get obs_date (timezone-aware) and obs_mjd from FITS headers.
        Fallback to now()/None.
        """
        for ext in (1, 0, None):
            try:
                hdr = fits.getheader(str(file_path), ext=ext) if ext is not None else fits.getheader(str(file_path))
                break
            except Exception:
                hdr = None
        if hdr:
            mjd = hdr.get('MJD-OBS') or hdr.get('MJDOBS') or hdr.get('MJD')
            date_obs = hdr.get('DATE-OBS')
            if mjd is not None:
                try:
                    t = Time(float(mjd), format='mjd', scale='utc')
                    return t.to_datetime(timezone=dj_timezone.utc), float(mjd)
                except Exception:
                    pass
            if date_obs:
                try:
                    t = Time(date_obs, scale='utc')  # lets astropy guess format (isot/fits/iso)
                    return t.to_datetime(timezone=dj_timezone.utc), t.mjd
                except Exception:
                    pass
        return now(), None

    def _ensure_tides_spec(self, target, spectrum_file_path):
        """
        Ensure a tides_spec row exists for this target+file (no DataProducts).
        Deduplicate by (tides, filepath) considering original and symlinked paths.
        """
        original = Path(spectrum_file_path)
        symlinked = Path(settings.BASE_DIR) / 'data' / 'spectra' / 'test' / original.name

        # Decide which path to store (prefer original if it exists)
        store_path = original if original.exists() else (symlinked if symlinked.exists() else original)

        # Check for existing rows by either path
        existing_qs = TidesSpec.objects.filter(
            tides=target, filepath__in=[str(original), str(symlinked)]
        ).order_by('-obs_date', '-qmost_id')
        if existing_qs.exists():
            count = existing_qs.count()
            if count > 1:
                print(f"WARNING: Found {count} tides_spec rows for {target.name} and {original.name}. "
                      f"Skipping insert to avoid duplicates.")
            else:
                print(f"tides_spec already exists for target {target.name} and {original.name}; skipping insert.")
            return

        obs_date, obs_mjd = self._extract_obs_times(store_path)
        qmost_id = self._compute_qmost_id(target.id, store_path)

        TidesSpec.objects.create(
            qmost_id=qmost_id,
            tides=target,
            filepath=str(store_path),
            obs_date=obs_date,
            obs_mjd=obs_mjd,
        )
        print(f"Inserted tides_spec for target {target.name} -> {store_path.name}")

    def _upsert_auto_classification(self, target, sn_type, sn_subtype, probability, source_version):
        if not sn_type and probability is None:
            return
        obj, created = PipelineClassificationGlobal.objects.update_or_create(
            tides=target,
            version=source_version,
            defaults={'sn_type': sn_type, 'probability': probability, 'notes': sn_subtype or ''},
        )
        if created:
            print(f'Inserted auto classification [{source_version}] for target {target.name}: '
                  f'{sn_type} (p={probability})')
        else:
            print(f'Updated auto classification [{source_version}] for target {target.name}: '
                  f'{sn_type} (p={probability})')

    # ---------------- main loaders ----------------

    def add_spectra_from_mock_db(self):
        target_csv_path = os.path.join(settings.TEST_DIR, "mock_DB.csv")
        if not os.path.exists(target_csv_path):
            print(f"ERROR: Target CSV file not found at {target_csv_path}")
            return

        dbdf = pd.read_csv(target_csv_path, index_col=0)
        targets = Target.objects.all()
        for target in targets:
            spectrum_file_path = os.path.join(settings.TEST_DIR, f'sims/l1_obs_joined_{target.name}.fits')

            if os.path.exists(spectrum_file_path):
                # Update plots (optional; keep this)
                generate_spectrum_plot(target, spectrum_file_path)
                print(f'Successfully updated plots for target {target.name}')
                # Ensure tides_spec exists
                self._ensure_tides_spec(target, spectrum_file_path)

                # Auto classification from mock CSV
                int_name = int(target.name)
                if int_name in dbdf.index:
                    auto_class = dbdf.at[int_name, 'AutoClass']
                    auto_class_subclass = dbdf.at[int_name, 'AutoClass_SubClass']
                    auto_class_prob = dbdf.at[int_name, 'AutoClassProb']
                    if auto_class:
                        if auto_class_subclass:
                            exists = TidesClassSubClass.objects.filter(sub_class=auto_class_subclass).exists()
                            if not exists:
                                print(f"WARNING: Subclass '{auto_class_subclass}' not found for target {target.name}.")
                        self._upsert_auto_classification(
                            target, auto_class, auto_class_subclass, auto_class_prob, source_version='mock'
                        )
                    else:
                        print(f'WARNING: No auto classification found for target {target.name}.')
                else:
                    print(f'WARNING: {target.name} not found in mock catalogue index.')
            else:
                print(f'WARNING: Spectrum file {spectrum_file_path} not found for target {target.name}')

    def add_spectra_from_pipeline(self, pipeline_results_path):
        pipeline_results = pd.read_csv(pipeline_results_path)
        for _, row in pipeline_results.iterrows():
            obj_name = row['obj_name']
            spectrum_file_path = row['spectrum_file']
            auto_class = row.get('auto_class_agg')
            auto_class_subclass = row.get('auto_class_subclass_agg')
            auto_class_prob = row.get('auto_class_prob_agg')

            target = Target.objects.filter(name=obj_name).first()
            if not target:
                print(f'WARNING: Target {obj_name} not found in the database')
                continue

            if not spectrum_file_path or not os.path.exists(spectrum_file_path):
                print(f'WARNING: Spectrum file {spectrum_file_path} not found for target {obj_name}.')
                continue

            # Update plot and ensure tides_spec
            generate_spectrum_plot(target, spectrum_file_path)
            print(f'Successfully updated plots for target {target.name}.')
            self._ensure_tides_spec(target, spectrum_file_path)

            # Auto classification
            if auto_class:
                if auto_class_subclass:
                    exists = TidesClassSubClass.objects.filter(sub_class=auto_class_subclass).exists()
                    if not exists:
                        print(f"WARNING: Subclass '{auto_class_subclass}' not found in TidesClassSubClass "
                              f"for target {target.name}.")
                self._upsert_auto_classification(
                    target, auto_class, auto_class_subclass, auto_class_prob, source_version='pipeline'
                )
            else:
                print(f'WARNING: No auto classification found for target {target.name}')
