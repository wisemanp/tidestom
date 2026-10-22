from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone

# This is the real public classifications migration
class Migration(migrations.Migration):

    dependencies = [
        ('custom_code', '0005_guardian_before_tom_targets'),
        ('custom_code', '0006_humanclassification_pipelineclassificationdash_and_more'), 
    ]

    operations = [
        migrations.CreateModel(
            name='PublicClassification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('released_at', models.DateTimeField(auto_now_add=True)),
                ('source', models.CharField(
                    choices=[('auto', 'Auto (pipeline)'), ('human', 'Human')],
                    default='auto',
                    max_length=10,
                )),
                ('sn_type', models.CharField(blank=True, max_length=50, null=True)),
                ('z', models.FloatField(blank=True, null=True)),
                ('zerr', models.FloatField(blank=True, null=True)),
                ('probability', models.FloatField(blank=True, null=True)),
                ('phase', models.FloatField(blank=True, null=True)),
                ('notes', models.TextField(blank=True, null=True)),
                # FKs use db_constraint=False — targets and class tables may live on a separate DB
                ('tides', models.OneToOneField(
                    db_column='tides_id',
                    db_constraint=False,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='public_classification',
                    to='custom_code.TidesTarget',
                )),
                ('tidesclass', models.ForeignKey(
                    blank=True,
                    db_constraint=False,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='public_classifications',
                    to='custom_code.TidesClass',
                )),
                ('tidesclass_subclass', models.ForeignKey(
                    blank=True,
                    db_constraint=False,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='public_classifications',
                    to='custom_code.TidesClassSubClass',
                )),
            ],
            options={
                'db_table': 'public_classification',
                'ordering': ['-released_at'],
            },
        ),
    ]