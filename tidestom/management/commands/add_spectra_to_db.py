import os
import pandas as pd
from datetime import datetime
from pathlib import Path

from django.core.management.base import BaseCommand
from django.conf import settings
from custom_code.models import TidesTarget as Target
from custom_code.models import TidesClassSubClass
from custom_code.models import TidesSpec
from custom_code.models import PipelineClassificationGlobal
from tom_dataproducts.models import DataProduct
from django.utils.timezone import now
from tidestom.tides_utils.target_utils import (
    generate_spectrum_plot, add_spectrum_to_database
)


class Command(BaseCommand):
    help = 'Add spectra to the database and update auto classifications'

    def add_arguments(self, parser):
        parser.add_argument(
            '--mock', action='store_true',
            help=('Add spectra from mock database')
        )

        parser.add_argument(
            '--pipeline', action='store_true',
            help=('Add spectra from pipeline results')
        )

        parser.add_argument(
            '--pipeline-results', type=str,
            help='Path to the pipeline results file'
        )

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

    def _upsert_auto_classification(self, target, sn_type, sn_subtype, probability, source_version):
        """
        Upsert an automatic classification into pipeline_classification_global.
        target: TidesTarget
        sn_type: str | None
        sn_subtype: str | None (stored in notes)
        probability: float | None
        source_version: str (e.g., 'mock' or 'pipeline')
        """
        if not sn_type and probability is None:
            return
        obj, created = PipelineClassificationGlobal.objects.update_or_create(
            tides=target,
            version=source_version,
            defaults={
                'sn_type': sn_type,
                'probability': probability,
                'notes': sn_subtype or '',
            },
        )
        if created:
            print(f'Inserted auto classification [{source_version}] for target {target.name}: '
                  f'{sn_type} (p={probability})')
        else:
            print(f'Updated auto classification [{source_version}] for target {target.name}: '
                  f'{sn_type} (p={probability})')

    def _ensure_tides_spec(self, target, spectrum_file_path):
        """
        Ensure a tides_spec row exists for this target+file.
        We use the DataProduct PK as qmost_id for a stable BIGINT key.
        """
        # Try both the original file path and the symlinked storage path used by add_spectrum_to_database
        original = Path(spectrum_file_path)
        symlinked = Path(settings.BASE_DIR) / 'data' / 'spectra' / 'test' / original.name

        dp = (
            DataProduct.objects.filter(target=target, data__in=[str(original), str(symlinked)])
            .order_by('-id')
            .first()
        )
        if not dp:
            # Fallback: latest spectroscopy DP for this target
            dp = (
                DataProduct.objects.filter(target=target, data_product_type='spectroscopy')
                .order_by('-id')
                .first()
            )
        if not dp:
            print(f"WARNING: No DataProduct found for target {target.name} and file {spectrum_file_path}")
            return

        # Do not insert if a tides_spec already exists for this DataProduct (qmost_id)
        existing_qs = TidesSpec.objects.filter(qmost_id=dp.id)
        if existing_qs.exists():
            count = existing_qs.count()
            if count > 1:
                print(f"WARNING: Found {count} tides_spec rows with qmost_id={dp.id} for target {target.name}. "
                      f"Skipping insert to avoid further duplicates.")
            else:
                print(f"tides_spec already exists for qmost_id={dp.id}; skipping insert.")
            return

        defaults = {
            'tides': target,
            'filepath': dp.data,    # store the exact path saved on the DP
            'obs_date': now(),      # replace with header time if available
            'obs_mjd': None,
        }
        # Create only if not present
        TidesSpec.objects.create(qmost_id=dp.id, **defaults)
        print(f"Inserted tides_spec row qmost_id={dp.id} for target {target.name}")

    def add_spectra_from_mock_db(self):
        test_data_dir = Path(settings.BASE_DIR) / 'data/spectra/test'
        test_data_dir.mkdir(parents=True, exist_ok=True)
        target_csv_path = os.path.join(settings.TEST_DIR, "mock_DB.csv")

        if not os.path.exists(target_csv_path):
            print(f"ERROR: Target CSV file not found at {target_csv_path}")
            return

        dbdf = pd.read_csv(target_csv_path, index_col=0)
        targets = Target.objects.all()
        for target in targets:
            spectrum_file_path = os.path.join(
                settings.TEST_DIR, f'sims/l1_obs_joined_{target.name}.fits'
            )

            if os.path.exists(spectrum_file_path):
                # Check if the spectrum already exists in the database (original OR symlinked path)
                original = Path(spectrum_file_path)
                symlinked = Path(settings.BASE_DIR) / 'data' / 'spectra' / 'test' / original.name
                spectrum_exists = DataProduct.objects.filter(
                    target=target, data__in=[str(original), str(symlinked)]
                ).exists()

                if not spectrum_exists:
                    generate_spectrum_plot(target, spectrum_file_path)
                    print(f'Successfully updated plots for target {target.name}')
                    result = add_spectrum_to_database(target, spectrum_file_path)
                    if 'Error' in result:
                        print(f"ERROR: {result}")
                    else:
                        print(result)
                    # Ensure a tides_spec row exists for this spectrum
                    self._ensure_tides_spec(target, spectrum_file_path)
                else:
                    print(f'WARNING: Spectrum for target {target.name} already exists in the database')
                    # Even if DataProduct exists already, make sure tides_spec is present
                    self._ensure_tides_spec(target, spectrum_file_path)

                # Add or update automatic classification
                print(f'Checking auto classification for target {target.name}')
                int_name = int(target.name)
                if int_name in dbdf.index:
                    print(f'Found target {target.name} in the mock catalogue.')
                    auto_class = dbdf.at[int_name, 'AutoClass']
                    auto_class_subclass = dbdf.at[int_name, 'AutoClass_SubClass']
                    auto_class_prob = dbdf.at[int_name, 'AutoClassProb']

                    if auto_class:
                        # Optional: validate subclass exists
                        if auto_class_subclass:
                            exists = TidesClassSubClass.objects.filter(sub_class=auto_class_subclass).exists()
                            if not exists:
                                print(f"WARNING: Subclass '{auto_class_subclass}' not found for target {target.name}.")
                        # Persist to pipeline_classification_global (read by TidesTarget.auto_* properties)
                        self._upsert_auto_classification(
                            target, auto_class, auto_class_subclass, auto_class_prob, source_version='mock'
                        )
                    else:
                        print(f'WARNING: No auto classification found for target {target.name}.')
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

            # Check if the spectrum already exists in the database (original OR symlinked path)
            original = Path(spectrum_file_path)
            symlinked = Path(settings.BASE_DIR) / 'data' / 'spectra' / 'test' / original.name
            spectrum_exists = DataProduct.objects.filter(
                target=target, data__in=[str(original), str(symlinked)]
            ).exists()
            if not spectrum_exists:
                generate_spectrum_plot(target, spectrum_file_path)
                print(f'Successfully updated plots for target {target.name}.')
                result = add_spectrum_to_database(target, spectrum_file_path)
                if 'Error' in result:
                    print(f"ERROR: {result}")
                else:
                    print(result)
                self._ensure_tides_spec(target, spectrum_file_path)
            else:
                print(f'WARNING: Spectrum for target {target.name} already exists in the database.')
                self._ensure_tides_spec(target, spectrum_file_path)

            # Add or update automatic classification
            if auto_class:
                if auto_class_subclass:
                    exists = TidesClassSubClass.objects.filter(sub_class=auto_class_subclass).exists()
                    if not exists:
                        print(
                            f"WARNING: Subclass '{auto_class_subclass}' not found in TidesClassSubClass "
                            f"for target {target.name}."
                        )
                self._upsert_auto_classification(
                    target, auto_class, auto_class_subclass, auto_class_prob, source_version='pipeline'
                )
            else:
                print(f'WARNING: No auto classification found for target {target.name}')
