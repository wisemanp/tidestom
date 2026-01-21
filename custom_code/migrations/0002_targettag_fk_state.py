from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('custom_code', '0001_tags'),
        # depend on a tom_targets migration at/after the rename; 0021 is fine
        ('tom_targets', '0021_rename_target_basetarget_alter_basetarget_options'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.AlterField(
                    model_name='targettag',
                    name='tides',
                    field=models.ForeignKey(
                        to='tom_targets.BaseTarget',   # was 'tom_targets.Target'
                        on_delete=models.CASCADE,
                        db_column='tides_id',
                        related_name='target_tags',
                    ),
                ),
            ],
        ),
    ]