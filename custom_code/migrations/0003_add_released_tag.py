from django.db import migrations

# The 'released' attribute has moved from a Tag to a boolean column on
# tides_cand (managed by SQL scripts, not Django).  This migration is
# kept as a no-op so the migration chain is not broken for databases
# that already applied the original version.

class Migration(migrations.Migration):

    dependencies = [
        ('custom_code', '0002_targettag_fk_state'),
    ]

    operations = [
        # originally: RunPython(add_released_tag) – now intentionally empty
    ]
