"""
Ensure guardian's initial migration runs before tom_targets 0025.

tom_targets 0025 uses guardian models but doesn't declare the dependency,
causing LookupError on fresh databases. This no-op migration fixes the
ordering via run_before, which is a standard Django migration mechanism.
"""
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('guardian', '0001_initial'),
        ('custom_code', '0004_tag_system_fields'),
    ]

    run_before = [
        ('tom_targets', '0025_auto_20250206_2017'),
    ]

    operations = []
