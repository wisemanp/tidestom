from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('custom_code', '0001_tags'),
        ('tom_targets', '0001_initial'),  # update if your tom_targets latest is different
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.AlterField(
                    model_name='targettag',
                    name='tides',
                    field=models.ForeignKey(
                        to='tom_targets.Target',
                        on_delete=models.CASCADE,
                        db_column='tides_id',
                        related_name='target_tags',
                    ),
                ),
            ],
        ),
    ]